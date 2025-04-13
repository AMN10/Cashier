import tkinter as tk
from tkinter import messagebox, simpledialog
import ttkbootstrap as ttkb
from datetime import datetime
import sqlite3

def initialize_database(db_connection):
    """تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة"""
    cursor = db_connection.cursor()

    # إنشاء جدول الورديات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            total_hours REAL
        )
    """)

    # إنشاء جدول الطلبات المرتبطة بالورديات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            order_type TEXT NOT NULL,  -- 'تيكاواي' أو 'ديليفري'
            total_price REAL NOT NULL,
            FOREIGN KEY (shift_id) REFERENCES shifts (id)
        )
    """)

    db_connection.commit()

class ShiftsPage:
    def __init__(self, root, return_callback, open_sales_callback):
        self.root = root
        self.return_callback = return_callback
        self.open_sales_callback = open_sales_callback
        self.db_connection = sqlite3.connect("products.db", check_same_thread=False)
        self.current_shift_id = None  # لتتبع الوردية النشطة

        # تهيئة قاعدة البيانات
        initialize_database(self.db_connection)

        self.create_page()

    def create_page(self):
        """إنشاء واجهة صفحة الورديات"""
        self.clear_frame()

        # تحميل الوردية النشطة (إذا كانت موجودة)
        self.load_active_shift()

        # عنوان الصفحة
        title_label = ttkb.Label(self.root, text="إدارة الورديات", font=("Helvetica", 24, "bold"), bootstyle="inverse-secondary")
        title_label.pack(pady=20)

        # زر بدء وردية جديدة أو الدخول إلى الوردية الحالية
        self.start_shift_button = ttkb.Button(
            self.root,
            text="بدء وردية جديدة" if not self.current_shift_id else "الدخول إلى الوردية الحالية",
            bootstyle="success",
            command=self.start_or_enter_shift
        )
        self.start_shift_button.pack(pady=10)

        # زر عرض الورديات السابقة
        view_shifts_button = ttkb.Button(
            self.root,
            text="عرض الورديات السابقة",
            bootstyle="info",
            command=self.view_shifts
        )
        view_shifts_button.pack(pady=10)

        # زر العودة إلى القائمة الرئيسية
        return_button = ttkb.Button(
            self.root,
            text="العودة إلى القائمة الرئيسية",
            bootstyle="warning",
            command=self.return_callback
        )
        return_button.pack(pady=20)

    def start_or_enter_shift(self):
        """بدء وردية جديدة أو الدخول إلى الوردية الحالية"""
        if self.current_shift_id:
            # إذا كانت هناك وردية نشطة، انتقل إلى صفحة المبيعات
            self.open_sales_callback()
        else:
            # إذا لم تكن هناك وردية نشطة، ابدأ وردية جديدة
            self.start_shift()

    def start_shift(self):
        """بدء وردية جديدة"""
        cursor = self.db_connection.cursor()

        # إدخال اسم الموظف
        employee_name = simpledialog.askstring("بدء وردية", "أدخل اسم الموظف:")
        if not employee_name or not employee_name.replace(" ", "").isalpha():
            messagebox.showwarning("خطأ", "يجب إدخال اسم موظف صالح (بدون أرقام أو رموز خاصة)!")
            return

        # بدء وردية جديدة
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO shifts (employee_name, start_time)
            VALUES (?, ?)
        """, (employee_name, start_time))
        self.db_connection.commit()

        # حفظ معرف الوردية النشطة
        self.current_shift_id = cursor.lastrowid

        # تحديث نص الزر
        self.start_shift_button.config(text="الدخول إلى الوردية الحالية")

        # فتح صفحة المبيعات
        self.open_sales_callback()

    def load_active_shift(self):
        """تحميل الوردية النشطة (إذا كانت موجودة)"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id FROM shifts WHERE end_time IS NULL")
        active_shift = cursor.fetchone()

        if active_shift:
            self.current_shift_id = active_shift[0]
        else:
            self.current_shift_id = None

    def view_shifts(self):
        """عرض الورديات السابقة"""
        self.clear_frame()

        # عنوان الصفحة
        title_label = ttkb.Label(self.root, text="الورديات السابقة", font=("Helvetica", 24, "bold"), bootstyle="inverse-secondary")
        title_label.pack(pady=20)

        # إطار للأزرار
        buttons_frame = ttkb.Frame(self.root)
        buttons_frame.pack(pady=10)

        # زر فرز حسب وقت البدء
        sort_by_start_button = ttkb.Button(
            buttons_frame,
            text="فرز حسب وقت البدء",
            bootstyle="info",
            command=lambda: self.sort_shifts("start_time")
        )
        sort_by_start_button.pack(side="left", padx=5)

        # زر فرز حسب عدد الساعات
        sort_by_hours_button = ttkb.Button(
            buttons_frame,
            text="فرز حسب عدد الساعات",
            bootstyle="info",
            command=lambda: self.sort_shifts("total_hours")
        )
        sort_by_hours_button.pack(side="left", padx=5)

        # زر طباعة تفاصيل الوردية
        print_button = ttkb.Button(
            buttons_frame,
            text="طباعة تفاصيل الوردية",
            bootstyle="primary",
            command=self.print_shift_details
        )
        print_button.pack(side="left", padx=5)

        # جلب البيانات من قاعدة البيانات
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, employee_name, start_time, end_time, total_hours FROM shifts ORDER BY start_time DESC")
        shifts = cursor.fetchall()

        # إنشاء جدول لعرض البيانات
        columns = ("#1", "#2", "#3", "#4", "#5")
        self.tree = ttkb.Treeview(self.root, columns=columns, show="headings", bootstyle="info")
        self.tree.heading("#1", text="معرف الوردية")
        self.tree.heading("#2", text="اسم الموظف")
        self.tree.heading("#3", text="وقت البدء")
        self.tree.heading("#4", text="وقت الانتهاء")
        self.tree.heading("#5", text="عدد الساعات")
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)

        # إضافة البيانات إلى الجدول
        for shift in shifts:
            self.tree.insert("", "end", values=shift)

        # زر العودة إلى صفحة إدارة الورديات
        return_button = ttkb.Button(
            self.root,
            text="العودة إلى إدارة الورديات",
            bootstyle="warning",
            command=self.create_page
        )
        return_button.pack(pady=20)

    def print_shift_details(self):
        """طباعة تفاصيل الوردية المحددة"""
        # الحصول على الوردية المحددة من الجدول
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("تحذير", "يرجى تحديد وردية من الجدول!")
            return
    
        # الحصول على معرف الوردية المحددة
        shift_id = self.tree.item(selected_item, "values")[0]
    
        # جلب بيانات الوردية
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT start_time, end_time FROM shifts WHERE id = ?", (shift_id,))
        shift_data = cursor.fetchone()
        if not shift_data:
            messagebox.showerror("خطأ", "الوردية المحددة غير موجودة!")
            return
    
        start_time, end_time = shift_data
    
        # حساب عدد الطلبات التيكاواي
        cursor.execute("SELECT COUNT(*), SUM(total) FROM takeaway_orders WHERE shift_id = ?", (shift_id,))
        takeaway_count, takeaway_total = cursor.fetchone()
    
        # حساب عدد الطلبات الدليفري
        cursor.execute("SELECT COUNT(*), SUM(total) FROM delivery_orders WHERE shift_id = ?", (shift_id,))
        delivery_count, delivery_total = cursor.fetchone()
    
        # حساب إجمالي السعر
        total_revenue = (takeaway_total or 0) + (delivery_total or 0)
    
        # حساب مدة الوردية
        if end_time:
            start_time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            shift_duration = end_time_obj - start_time_obj
            shift_duration_str = str(shift_duration)
        else:
            shift_duration_str = "الوردية لم تنته بعد"
    
        # إنشاء نص التقرير
        report_text = (
            f"تفاصيل الوردية:\n"
            f"معرف الوردية: {shift_id}\n"
            f"وقت البدء: {start_time}\n"
            f"وقت الانتهاء: {end_time if end_time else 'لم تنته بعد'}\n"
            f"مدة الوردية: {shift_duration_str}\n\n"
            f"عدد طلبات التيكاواي: {takeaway_count}\n"
            f"إجمالي سعر التيكاواي: {takeaway_total or 0:.2f}\n"
            f"عدد طلبات الدليفري: {delivery_count}\n"
            f"إجمالي سعر الدليفري: {delivery_total or 0:.2f}\n\n"
            f"إجمالي السعر لجميع الطلبات: {total_revenue:.2f}"
        )
    
        # عرض التقرير في نافذة منبثقة
        messagebox.showinfo("تفاصيل الوردية", report_text)

    def sort_shifts(self, column):
        """فرز الورديات حسب العمود المحدد"""
        cursor = self.db_connection.cursor()
        cursor.execute(f"SELECT id, employee_name, start_time, end_time, total_hours FROM shifts ORDER BY {column} DESC")
        shifts = cursor.fetchall()

        # مسح الجدول الحالي
        for row in self.tree.get_children():
            self.tree.delete(row)

        # إضافة البيانات المفرزة إلى الجدول
        for shift in shifts:
            self.tree.insert("", "end", values=shift)

    def clear_frame(self):
        """مسح جميع العناصر في الإطار"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def __del__(self):
        """إغلاق اتصال قاعدة البيانات عند إنهاء البرنامج"""
        self.db_connection.close()

if __name__ == "__main__":
    root = ttkb.Window(themename="cosmo")
    root.title("نظام إدارة الورديات")
    root.geometry("800x600")

    def return_to_main():
        print("العودة إلى القائمة الرئيسية")

    def open_sales_page():
        print("فتح صفحة المبيعات")

    # تهيئة قاعدة البيانات
    db_connection = sqlite3.connect("products.db")
    initialize_database(db_connection)
    db_connection.close()

    shifts_page = ShiftsPage(root, return_to_main, open_sales_page)
    root.mainloop()