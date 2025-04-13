import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import sqlite3

class CategoriesPage:
    def __init__(self, root, return_callback):
        self.root = root
        self.return_callback = return_callback
        self.db_connection = sqlite3.connect("products.db")
    
        # تعيين نمط لـ Treeview لتكبير حجم الخط
        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 11, "bold")), #rowheight=30)  # تكبير حجم الخط وارتفاع الصفوف
        style.configure("Treeview.Heading", font=("Helvetica", 15, "bold"))  # تكبير حجم الخط للعناوين
         
        self.create_tables_in_db()  # إنشاء الجداول في قاعدة البيانات إذا لم تكن موجودة
        self.create_page()

    def create_tables_in_db(self):
        """إنشاء الجداول في قاعدة البيانات إذا لم تكن موجودة"""
        cursor = self.db_connection.cursor()

        # إنشاء جدول الأقسام
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # إنشاء جدول المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)

        # إنشاء جدول أحجام المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_sizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                size TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        self.db_connection.commit()

    def create_page(self):
        self.clear_frame()

        # إنشاء PanedWindow لتقسيم النافذة إلى قسمين
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=20, pady=20)

        # القسم الأول: الجدول (ثلث النافذة)
        self.create_table_section()

        # القسم الثاني: عناصر التحكم (ثلثي النافذة)
        self.create_control_section()

        # زر العودة إلى القائمة الرئيسية (في الأسفل)
        back_button = ttkb.Button(
            self.root,
            text="← العودة إلى القائمة الرئيسية",
            bootstyle=PRIMARY,  # تغيير اللون إلى الأزرق
            command=self.return_to_main,
            width=30
        )
        back_button.pack(side=tk.BOTTOM, pady=20)  # وضع الزر في الأسفل

        # تحميل البيانات من قاعدة البيانات وعرضها في الجدول
        self.load_products()

    def create_table_section(self):
        # إنشاء إطار للجدول
        table_frame = ttkb.Frame(self.paned_window)
        self.paned_window.add(table_frame, weight=1)  # الجدول يشغل ثلث النافذة (وزن = 1)

        # عنوان القسم
        title = ttkb.Label(table_frame, text="🗂️ قائمة المنتجات", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)

        # حقل البحث
        self.search_entry = ttkb.Entry(table_frame, width=50)
        self.search_entry.insert(0, "ابحث عن منتج...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END))
        self.search_entry.bind("<KeyRelease>", self.filter_products)  # ربط حدث البحث
        self.search_entry.pack(pady=10)

        # إنشاء الجدول
        self.create_table(table_frame)

    def create_table(self, parent):
        # إنشاء إطار للجدول وشريط التمرير
        table_container = ttk.Frame(parent)
        table_container.pack(fill="both", expand=True, pady=10)
    
        # إنشاء Treeview (جدول)
        columns = ("id", "القسم", "اسم المنتج")  # ترتيب الأعمدة
        self.table = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",  # إظهار عناوين الأعمدة فقط
            style="Treeview"  # تطبيق النمط المخصص
        )
    
        # تعيين عناوين الأعمدة
        self.table.heading("id", text="ID")
        self.table.heading("القسم", text="القسم")
        self.table.heading("اسم المنتج", text="اسم المنتج")
    
        # تعيين عرض الأعمدة
        self.table.column("id", width=50, anchor="center", stretch=False)
        self.table.column("القسم", width=200, anchor="center")  # عرض أقل للقسم
        self.table.column("اسم المنتج", width=300, anchor="center")  # عرض أكبر لاسم المنتج
    
        # إضافة شريط تمرير عمودي
        vertical_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.table.yview)
        vertical_scrollbar.pack(side="right", fill="y")
    
        # إضافة شريط تمرير أفقي (اختياري)
        horizontal_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=self.table.xview)
        horizontal_scrollbar.pack(side="bottom", fill="x")
    
        # ربط شريط التمرير بالجدول
        self.table.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
    
        # ربط حدث عجلة الفأرة بالجدول
        self.table.bind("<MouseWheel>", self.on_mousewheel)
    
        # تعبئة الجدول في الإطار
        self.table.pack(fill="both", expand=True)
    
        # ربط حدث اختيار منتج
        self.table.bind("<<TreeviewSelect>>", self.load_product_sizes)   

    def filter_products(self, event):
        """تصفية المنتجات بناءً على النص المدخل في حقل البحث"""
        search_term = self.search_entry.get().strip().lower()  # الحصول على النص المدخل
        for row in self.table.get_children():
            self.table.detach(row)  # إخفاء جميع الصفوف

        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT products.id, products.name, categories.name 
            FROM products 
            INNER JOIN categories ON products.category_id = categories.id
            WHERE LOWER(products.name) LIKE ?
        """, (f"%{search_term}%",))
        products = cursor.fetchall()

        for product in products:
            self.table.insert("", "end", values=(product[0], product[1], product[2]))

    def create_control_section(self):
        # إنشاء إطار لعناصر التحكم
        control_frame = ttkb.Frame(self.paned_window)
        self.paned_window.add(control_frame, weight=2)  # إطار التحكم يشغل ثلثي النافذة (وزن = 2)
    
        # عنوان القسم
        title = ttkb.Label(control_frame, text="🛠️ التحكم", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)
    
        # إطار للأقسام والأزرار
        category_frame = ttkb.Frame(control_frame)
        category_frame.pack(pady=10)
    
        # زر حذف قسم
        delete_category_button = ttkb.Button(
            category_frame,
            text="🗑️ حذف قسم",
            bootstyle=DANGER,
            command=self.delete_category,
            width=15
        )
        delete_category_button.grid(row=0, column=0, padx=10)  # وضع الزر في الصف الأول، العمود الأول
    
        # قائمة منسدلة للأقسام باستخدام OptionMenu
        self.selected_category = tk.StringVar(value="اختر قسم")  # القيمة الافتراضية
        self.option_menu = ttk.OptionMenu(
            category_frame,
            self.selected_category,
            "اختر قسم",  # النص الافتراضي
            *self.load_categories(),  # تحميل الأقسام
            command=self.update_category  # وظيفة التحديث
        )
        self.option_menu.grid(row=0, column=1, padx=10)  # وضع القائمة المنسدلة في الصف الأول، العمود الثاني
    
        # زر إضافة قسم
        add_category_button = ttkb.Button(
            category_frame,
            text="➕ إضافة قسم",
            bootstyle=INFO,
            command=self.open_add_category_window,  # فتح نافذة إضافة قسم
            width=15
        )
        add_category_button.grid(row=0, column=2, padx=10)  # وضع الزر في الصف الأول، العمود الثالث
    
        # حقل إدخال اسم المنتج مع نص تلميحي (في صف جديد أسفل الأزرار)
        self.product_name_entry = ttkb.Entry(category_frame, width=30)
        self.product_name_entry.insert(0, "اسم المنتج")
        self.product_name_entry.bind("<FocusIn>", lambda e: self.clear_hint(e, self.product_name_entry, "اسم المنتج"))
        self.product_name_entry.bind("<FocusOut>", lambda e: self.restore_hint(e, self.product_name_entry, "اسم المنتج"))
        self.product_name_entry.grid(row=1, column=0, columnspan=3, pady=10)  # وضع الحقل في الصف الثاني، يمتد على 3 أعمدة
    
        # زر إضافة منتج
        add_button = ttkb.Button(
            control_frame,
            text="إضافة منتج",
            bootstyle=SUCCESS,
            command=self.add_product,
            width=15
        )
        add_button.pack(pady=0)
    
        # زر حذف منتج
        delete_button = ttkb.Button(
            control_frame,
            text=" حذف المنتاجات المحددة من الجدول",
            bootstyle=DANGER,
            command=self.delete_product,
            width=30
        )
        delete_button.pack(pady=20)
    
        # إطار لأحجام المنتجات
        sizes_frame = ttkb.Frame(control_frame)
        sizes_frame.pack(pady=20)
    
        # عنوان أحجام المنتجات
        sizes_title = ttkb.Label(sizes_frame, text="📏 أحجام المنتجات", font=("Helvetica", 16, "bold"))
        sizes_title.pack(pady=10)
    
        # جدول أحجام المنتجات
        self.sizes_table = ttk.Treeview(
            sizes_frame,
            columns=("id", "الحجم", "السعر"),
            show="headings",
            style="Treeview"  # تطبيق النمط المخصص
        )
        self.sizes_table.heading("id", text="ID")
        self.sizes_table.heading("الحجم", text="الحجم")
        self.sizes_table.heading("السعر", text="السعر")
        self.sizes_table.column("id", width=50, anchor="center", stretch=False)
        self.sizes_table.column("الحجم", width=150, anchor="center")
        self.sizes_table.column("السعر", width=150, anchor="center")
        self.sizes_table.pack(fill="both", expand=True, pady=10)

        # ربط حدث اختيار حجم
        self.sizes_table.bind("<<TreeviewSelect>>", self.load_selected_size)
    
        # حقول إدخال الحجم والسعر مع نصوص تلميحية
        self.size_entry = ttkb.Entry(sizes_frame, width=20)
        self.size_entry.insert(0, "الحجم")
        self.size_entry.bind("<FocusIn>", lambda e: self.clear_hint(e, self.size_entry, "الحجم"))
        self.size_entry.bind("<FocusOut>", lambda e: self.restore_hint(e, self.size_entry, "الحجم"))
        self.size_entry.pack(side=tk.LEFT, padx=5)
    
        self.price_entry = ttkb.Entry(sizes_frame, width=20)
        self.price_entry.insert(0, "السعر")
        self.price_entry.bind("<FocusIn>", lambda e: self.clear_hint(e, self.price_entry, "السعر"))
        self.price_entry.bind("<FocusOut>", lambda e: self.restore_hint(e, self.price_entry, "السعر"))
        self.price_entry.pack(side=tk.LEFT, padx=5)
    
        # زر إضافة حجم
        add_size_button = ttkb.Button(
            sizes_frame,
            text="➕ إضافة حجم",
            bootstyle=INFO,
            command=self.add_size,
            width=15
        )
        add_size_button.pack(side=tk.LEFT, padx=5)
    
        # زر تعديل حجم
        edit_size_button = ttkb.Button(
            sizes_frame,
            text="✏️ تعديل حجم",
            bootstyle=WARNING,
            command=self.edit_size,
            width=15
        )
        edit_size_button.pack(side=tk.LEFT, padx=5)
    
        # زر حذف حجم
        delete_size_button = ttkb.Button(
            sizes_frame,
            text="🗑️ حذف حجم",
            bootstyle=DANGER,
            command=self.delete_size,
            width=15
        )
        delete_size_button.pack(side=tk.LEFT, padx=5)

    def clear_hint(self, event, widget, hint_text):
        """مسح النص التلميحي عند التركيز على الحقل"""
        if widget.get() == hint_text:
            widget.delete(0, tk.END)
            widget.config(foreground="black")

    def restore_hint(self, event, widget, hint_text):
        """إعادة النص التلميحي إذا كان الحقل فارغًا"""
        if not widget.get():
            widget.insert(0, hint_text)
            widget.config(foreground="gray")

    def load_selected_size(self, event):
        """تحميل بيانات الحجم المحدد في حقول الإدخال"""
        selected_item = self.sizes_table.selection()
        if not selected_item:
            return

        # الحصول على بيانات الحجم المحدد
        size_id, size, price = self.sizes_table.item(selected_item, "values")

        # تحميل البيانات في حقول الإدخال
        self.size_entry.delete(0, tk.END)
        self.size_entry.insert(0, size)

        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, price)

        # تخزين معرف الحجم المحدد للتعديل لاحقًا
        self.selected_size_id = size_id

    def edit_size(self):
        """تعديل حجم وسعر محدد"""
        if not hasattr(self, "selected_size_id"):  # إذا لم يتم تحديد حجم
            messagebox.showwarning("خطأ", "يرجى تحديد حجم لتعديله!")
            return

        # الحصول على البيانات من حقول الإدخال
        new_size = self.size_entry.get()
        new_price = self.price_entry.get()

        if not new_size or not new_price:  # إذا كانت الحقول فارغة
            messagebox.showwarning("خطأ", "يرجى ملء جميع الحقول!")
            return

        # تحديث البيانات في قاعدة البيانات
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "UPDATE product_sizes SET size = ?, price = ? WHERE id = ?",
                (new_size, new_price, self.selected_size_id))
            self.db_connection.commit()
            messagebox.showinfo("نجاح", "تم تعديل الحجم بنجاح!")
            
            # تحديث جدول أحجام المنتجات
            self.load_product_sizes(None)
            
            # مسح حقول الإدخال بعد التعديل
            self.size_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)
            delattr(self, "selected_size_id")  # إزالة معرف الحجم المحدد
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التعديل: {e}")

    def open_add_category_window(self):
        """فتح نافذة لإدخال عدد الأقسام"""
        self.add_category_window = tk.Toplevel(self.root)
        self.add_category_window.title("إضافة أقسام")
        self.add_category_window.geometry("300x150")

        # حقل إدخال عدد الأقسام
        ttkb.Label(self.add_category_window, text="عدد الأقسام:").pack(pady=10)
        self.num_categories_entry = ttkb.Entry(self.add_category_window, width=30)
        self.num_categories_entry.pack(pady=10)

        # زر التالي
        next_button = ttkb.Button(
            self.add_category_window,
            text="التالي",
            bootstyle=SUCCESS,
            command=self.open_category_fields_window
        )
        next_button.pack(pady=10)

    def open_category_fields_window(self):
        """فتح نافذة جديدة لإدخال أسماء الأقسام"""
        try:
            num_categories = int(self.num_categories_entry.get())
            if num_categories <= 0:
                messagebox.showwarning("خطأ", "يرجى إدخال عدد صحيح موجب!")
                return
        except ValueError:
            messagebox.showwarning("خطأ", "يرجى إدخال عدد صحيح!")
            return

        # إغلاق نافذة إدخال العدد
        self.add_category_window.destroy()

        # فتح نافذة جديدة لإدخال أسماء الأقسام
        self.category_fields_window = tk.Toplevel(self.root)
        self.category_fields_window.title("إضافة أقسام")
        self.category_fields_window.geometry("400x300")

        # إطار لحقول إدخال الأقسام
        self.category_entries_frame = ttkb.Frame(self.category_fields_window)
        self.category_entries_frame.pack(pady=20)

        # إنشاء حقول إدخال للأقسام
        self.category_entries = []
        for i in range(num_categories):
            entry = ttkb.Entry(self.category_entries_frame, width=30)
            entry.pack(pady=5)
            self.category_entries.append(entry)

        # زر حفظ الأقسام
        save_button = ttkb.Button(
            self.category_fields_window,
            text="حفظ الأقسام",
            bootstyle=SUCCESS,
            command=self.save_categories
        )
        save_button.pack(pady=10)

    def save_categories(self):
        """حفظ الأقسام في قاعدة البيانات"""
        categories = []
        for entry in self.category_entries:
            category_name = entry.get().strip()
            if category_name:
                categories.append(category_name)

        if not categories:
            messagebox.showwarning("خطأ", "يرجى إدخال أسماء الأقسام!")
            return

        cursor = self.db_connection.cursor()
        try:
            for category in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
            self.db_connection.commit()
            messagebox.showinfo("نجاح", "تمت إضافة الأقسام بنجاح!")
            self.update_option_menu()  # تحديث القائمة المنسدلة
            self.category_fields_window.destroy()  # إغلاق النافذة
        except sqlite3.IntegrityError:
            messagebox.showwarning("خطأ", "بعض الأقسام موجودة بالفعل!")

    def update_option_menu(self):
        """تحديث قائمة OptionMenu بالأقسام الجديدة"""
        categories = self.load_categories()  # تحميل الأقسام من قاعدة البيانات
        menu = self.option_menu["menu"]  # الحصول على القائمة المنسدلة الحالية
        menu.delete(0, "end")  # حذف جميع العناصر الحالية في القائمة

        # إضافة الأقسام الجديدة إلى القائمة المنسدلة
        for category in categories:
            menu.add_command(
                label=category,
                command=lambda value=category: self.selected_category.set(value)
            )

    def load_categories(self):
        """تحميل الأقسام من قاعدة البيانات"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT name FROM categories")
        categories = cursor.fetchall()
        return [category[0] for category in categories]

    def update_category(self, selected_value):
        """تحديث القسم المحدد"""
        self.selected_category.set(selected_value)

    def delete_category(self):
        """حذف قسم من قاعدة البيانات"""
        category_name = self.selected_category.get()  # الحصول على القسم المحدد
        if category_name == "اختر قسم":  # إذا لم يتم تحديد قسم
            messagebox.showwarning("خطأ", "يرجى تحديد قسم لحذفه!")
            return

        # تأكيد من المستخدم قبل الحذف
        confirm = messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف القسم '{category_name}'؟")
        if not confirm:
            return

        cursor = self.db_connection.cursor()
        try:
            # حذف القسم من قاعدة البيانات
            cursor.execute("DELETE FROM categories WHERE name = ?", (category_name,))
            self.db_connection.commit()
            messagebox.showinfo("نجاح", f"تم حذف القسم '{category_name}' بنجاح!")
            
            # تحديث القائمة المنسدلة بعد الحذف
            self.update_option_menu()
            
            # إعادة تعيين القسم المحدد إلى القيمة الافتراضية
            self.selected_category.set("اختر قسم")
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف القسم: {e}")

    def return_to_main(self):
        """العودة إلى القائمة الرئيسية"""
        self.clear_frame()
        self.return_callback()

    def add_product(self):
        """إضافة منتج جديد إلى قاعدة البيانات وعرضه في الجدول"""
        name = self.product_name_entry.get()
        category_name = self.selected_category.get()
    
        if name == "اسم المنتج":
            name = ""
    
        if not name or category_name == "اختر قسم":
            messagebox.showwarning("خطأ", "يرجى اختيار قسم اولا!!")
            return
    
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        category_id = cursor.fetchone()
        if not category_id:
            messagebox.showwarning("خطأ", "القسم المحدد غير موجود!")
            return
    
        # التحقق من وجود المنتج في القسم المحدد
        cursor.execute("SELECT id FROM products WHERE name = ? AND category_id = ?", (name, category_id[0]))
        existing_product = cursor.fetchone()
        if existing_product:
            messagebox.showwarning("خطأ", "هذا المنتج موجود بالفعل في القسم المحدد!")
            return
    
        # إذا لم يكن المنتج موجودًا، قم بإضافته
        cursor.execute("INSERT INTO products (name, category_id) VALUES (?, ?)", (name, category_id[0]))
        self.db_connection.commit()
        self.load_products()
        self.product_name_entry.delete(0, tk.END)
        self.restore_hint_after_add()

    def restore_hint_after_add(self):
        """إعادة النص التلميحي بعد إضافة منتج"""
        self.product_name_entry.insert(0, "اسم المنتج")
        self.product_name_entry.config(foreground="gray")

    def delete_product(self):
        """حذف المنتجات المحددة من قاعدة البيانات"""
        selected_items = self.table.selection()  # الحصول على جميع العناصر المحددة
        if not selected_items:
            messagebox.showwarning("خطأ", "يرجى تحديد منتج أو أكثر لحذفها!")
            return
       
        # تأكيد الحذف مع المستخدم
        confirm = messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف {len(selected_items)} منتج/منتجات؟")
        if not confirm:
            return
       
        cursor = self.db_connection.cursor()
        try:
            for item in selected_items:
                item_id = self.table.item(item, "values")[0]  # الحصول على معرف المنتج
                cursor.execute("DELETE FROM products WHERE id = ?", (item_id,))
            self.db_connection.commit()
            messagebox.showinfo("نجاح", f"تم حذف {len(selected_items)} منتج/منتجات بنجاح!")
            self.load_products()  # إعادة تحميل الجدول بعد الحذف
        except sqlite3.Error as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف المنتجات: {e}")

    def load_products(self):
        """تحميل المنتجات من قاعدة البيانات وعرضها في الجدول"""
        for row in self.table.get_children():
            self.table.delete(row)
    
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT products.id, categories.name, products.name 
            FROM products 
            INNER JOIN categories ON products.category_id = categories.id
        """)
        products = cursor.fetchall()
    
        for product in products:
            self.table.insert("", "end", values=(product[0], product[1], product[2]))  # ترتيب الأعمدة: id, قسم, اسم المنتج
    
    def load_product_sizes(self, event):
        """تحميل أحجام المنتج المحدد"""
        selected_item = self.table.selection()
        if not selected_item:
            return

        product_id = self.table.item(selected_item, "values")[0]
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, size, price FROM product_sizes WHERE product_id = ?", (product_id,))
        sizes = cursor.fetchall()

        for row in self.sizes_table.get_children():
            self.sizes_table.delete(row)

        for size in sizes:
            self.sizes_table.insert("", "end", values=(size[0], size[1], size[2]))

    def add_size(self):
         """إضافة حجم جديد للمنتج"""
         size = self.size_entry.get()
         price = self.price_entry.get()
     
         if size == "الحجم" or price == "السعر":
             messagebox.showwarning("خطأ", "يرجى ملء جميع الحقول!")
             return
     
         selected_item = self.table.selection()
         if not selected_item:
             messagebox.showwarning("خطأ", "يرجى تحديد منتج أولاً!")
             return
     
         product_id = self.table.item(selected_item, "values")[0]
         cursor = self.db_connection.cursor()
     
         # التحقق من وجود الحجم لنفس المنتج
         cursor.execute("SELECT id FROM product_sizes WHERE product_id = ? AND size = ?", (product_id, size))
         existing_size = cursor.fetchone()
     
         if existing_size:
             messagebox.showwarning("خطأ", "هذا الحجم موجود بالفعل لهذا المنتج!")
             return
     
         # إضافة الحجم إذا لم يكن موجودًا
         cursor.execute("INSERT INTO product_sizes (product_id, size, price) VALUES (?, ?, ?)", (product_id, size, price))
         self.db_connection.commit()
         self.load_product_sizes(None)
         self.size_entry.delete(0, tk.END)
         self.price_entry.delete(0, tk.END)

    def delete_size(self):
        """حذف حجم محدد"""
        selected_item = self.sizes_table.selection()
        if not selected_item:
            messagebox.showwarning("خطأ", "يرجى تحديد حجم لحذفه!")
            return

        size_id = self.sizes_table.item(selected_item, "values")[0]
        cursor = self.db_connection.cursor()
        cursor.execute("DELETE FROM product_sizes WHERE id = ?", (size_id,))
        self.db_connection.commit()
        self.load_product_sizes(None)

    def clear_frame(self):
        """حذف جميع العناصر من النافذة الرئيسية"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def on_mousewheel(self, event):
        """تمكين التمرير باستخدام عجلة الفأرة"""
        self.table.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def __del__(self):
        """إغلاق اتصال قاعدة البيانات عند إغلاق النافذة"""
        self.db_connection.close()

# مثال على الاستخدام
if __name__ == "__main__":
    root = ttkb.Window(themename="cosmo")
    root.title("إدارة المنتجات")
    root.geometry("1200x750")

    def return_to_main():
        print("العودة إلى القائمة الرئيسية...")

    categories_page = CategoriesPage(root, return_to_main)
    root.mainloop()