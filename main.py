import os
import sqlite3
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
import ttkbootstrap as ttkb
from login import LoginWindow
from sales import SalesPage  
from categories import CategoriesPage  
from reports import ReportsPage  
from settings import SettingsPage 
from Shifts import ShiftsPage 

def initialize_database(db_connection):
    """تهيئة قاعدة البيانات وإنشاء الجداول إذا لم تكن موجودة"""
    cursor = db_connection.cursor()

    # إنشاء جدول الأقسام
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    # إنشاء جدول المنتجات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # إنشاء جدول أحجام المنتجات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            size TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # إنشاء جدول العملاء
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL
        )
    """)

   
    
    # إنشاء جدول طلبات الديلفيري
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER,  -- إضافة العمود shift_id
            order_number INTEGER,  -- إضافة العمود order_number
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            delivery_person TEXT
           
        )
    """)

    # إنشاء جدول طلبات التيك أواي
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS takeaway_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER,  -- إضافة العمود shift_id
            order_number INTEGER,  -- إضافة العمود order_number
            total REAL NOT NULL          
        )
    """)

 
    # إنشاء جدول الموصلين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
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

    db_connection.commit()
class MainApp:
    def __init__(self, root):
        super().__init__()

        # تغيير السمة الافتراضية إلى "pulse" (فاتحة)
        self.style = ttkb.Style("pulse")
        self.root = root
        self.root.title("Cashier")
        self.is_dark_theme = False  # تغيير القيمة الافتراضية إلى False (فاتحة)

        base_path = Path(__file__).parent
        icon_path = base_path / "D.ico"
        if icon_path.exists():
            self.root.iconbitmap(icon_path)
        else:
            print("Icon file not found")

        self.main_frame = tk.Frame(self.root, bg="#E0E0E0")
        self.main_frame.pack(fill="both", expand=True)

        self.style.configure("Large.TButton", font=("Helvetica", 18, "bold"), padding=10)

        self.show_login_window()

    def show_login_window(self):
        self.clear_frame()
        login_window = LoginWindow(self.main_frame, self.on_login_success)

    def on_login_success(self):
        self.create_main_menu()

    def create_main_menu(self):
        self.clear_frame()

        self.menu_frame = ttkb.Frame(self.main_frame, bootstyle="secondary")
        self.menu_frame.pack(fill="both", expand=True)

        title = ttkb.Label(
            self.menu_frame, text="Dr.Crepe",
            font=("Helvetica", 32, "bold"), bootstyle="inverse-secondary"
        )
        title.pack(pady=40)

        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            image = Image.open(logo_path)
            image = image.resize((100, 100), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(image)
            logo_label = ttkb.Label(self.menu_frame, image=self.logo_image)
            logo_label.pack(pady=0)

        buttons_frame = ttkb.Frame(self.menu_frame)
        buttons_frame.pack(pady=50)

        menu_items = [
            {"text": "📊 المبيعات", "command": self.show_sales},
            {"text": "🗂️ الأصناف", "command": self.show_categories},
            {"text": "📈 التقارير", "command": self.show_reports},
            {"text": "⚙️ الإعدادات", "command": self.show_settings},
        ]

        for i, item in enumerate(menu_items):
            btn = ttkb.Button(
                buttons_frame, text=item["text"],
                bootstyle="light-outline", command=item["command"],
                width=30, style="Large.TButton"
            )
            btn.grid(row=i // 2, column=i % 2, padx=20, pady=15)

        # تعديل زر التبديل ليعكس الحالة بشكل صحيح
        self.theme_var = tk.BooleanVar(value=self.is_dark_theme)
        self.theme_check = ttkb.Checkbutton(
            self.menu_frame,
            text="Dark Mode",
            variable=self.theme_var,
            bootstyle="round-toggle",
            command=self.toggle_theme
        )
        self.theme_check.pack(pady=20)

    def toggle_theme(self):
        # تغيير السمة بناءً على قيمة المتغير
        new_theme = "darkly" if self.theme_var.get() else "pulse"
        self.style.theme_use(new_theme)
        self.style.configure("Large.TButton", font=("Helvetica", 18, "bold"), padding=10)

    def show_sales(self):
        """فتح صفحة الورديات بدلاً من صفحة المبيعات مباشرة"""
        self.clear_frame()
        ShiftsPage(self.main_frame, self.create_main_menu, self.open_sales_page)

    def open_sales_page(self):
        """فتح صفحة المبيعات بعد بدء وردية"""
        self.clear_frame()
        SalesPage(self.main_frame, self.create_main_menu, self.return_to_shifts)

    def return_to_shifts(self):
        """العودة إلى صفحة إدارة الورديات"""
        self.clear_frame()
        ShiftsPage(self.main_frame, self.create_main_menu, self.open_sales_page)

    def show_categories(self):
        CategoriesPage(self.main_frame, self.create_main_menu)

    def show_reports(self):
        ReportsPage(self.main_frame, self.create_main_menu)

    def show_settings(self):
        SettingsPage(self.main_frame, self.create_main_menu)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    # تهيئة قاعدة البيانات
    db_connection = sqlite3.connect("products.db")
    initialize_database(db_connection)
    db_connection.close()
    root.geometry("1400x750")
    root.mainloop()