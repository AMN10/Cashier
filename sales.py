import datetime
from datetime import datetime
import json
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import sqlite3
from PIL import Image, ImageTk, ImageDraw  # لإضافة الأيقونات
import win32print
import win32api

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

class SalesPage:
#1. دوال تهيئة قاعدة البيانات
    def __init__(self, root, return_callback, return_to_shifts_callback):
        self.root = root
        self.return_callback = return_callback
        self.return_to_shifts_callback = return_to_shifts_callback  # تعريف المتغير هنا
        self.db_connection = sqlite3.connect("products.db")
        self.selected_items = []
        self.current_sizes_frame = None
        self.order_type = "takeaway"
        # إضافة السمة current_shift_id وتهيئتها بقيمة None
        self.current_shift_id = None  # <-- إضافة هذا السطر
        
        # التحقق من وجود وردية نشطة
        self.check_active_shift()

        # متغيرات لتتبع النوافذ
        self.delivery_persons_window = None
        self.delivery_orders_window = None

        self.create_page()


#2. دوال الواجهة الرسومية (GUI)
    def create_page(self):
        """إنشاء واجهة المستخدم مع تحسينات"""
        self.clear_frame()

        # ✅ إنشاء شريط القائمة للنافذة الرئيسية
        if isinstance(self.root, tk.Tk) or isinstance(self.root, ttkb.Window):
            menubar = tk.Menu(self.root)

        # ✅ إنشاء إطار الأقسام
        categories_frame = ttkb.Frame(self.root)
        categories_frame.pack(side="left", fill="y", padx=10, pady=10)

        ttkb.Label(categories_frame, text="الأقسام", font=("Helvetica", 16, "bold")).pack(pady=10)

        # إطار لعرض أزرار الأقسام
        self.categories_buttons_frame = ttkb.Frame(categories_frame)
        self.categories_buttons_frame.pack(fill="y", expand=True)

        # تحميل الأقسام
        self.load_categories()

        # ✅ إنشاء إطار المنتجات
        products_frame = ttkb.Frame(self.root)
        products_frame.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        ttkb.Label(products_frame, text="المنتجات", font=("Helvetica", 16, "bold")).pack(pady=10)

       # إضافة حقل بحث
        search_frame = ttkb.Frame(products_frame)
        search_frame.pack(fill="x", pady=5)
        self.search_entry = ttkb.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.insert(0, "ابحث عن منتج...")  # نص تلميح
        self.search_entry.bind("<FocusIn>", lambda e: self.clear_hint(self.search_entry, "ابحث عن منتج..."))  # مسح النص عند التركيز
        self.search_entry.bind("<FocusOut>", lambda e: self.restore_hint(self.search_entry, "ابحث عن منتج..."))  # استعادة النص عند فقدان التركيز
        self.search_entry.bind("<KeyRelease>", self.dynamic_search)  # بحث ديناميكي

        # إطار قابل للتمرير لعرض أزرار المنتجات
        self.products_canvas = tk.Canvas(products_frame)
        self.products_canvas.pack(side="left", fill="both", expand=True)

        # إضافة شريط تمرير عمودي
        scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=self.products_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # ربط الشريط الجانبي بالـ Canvas
        self.products_canvas.configure(yscrollcommand=scrollbar.set)
        self.products_canvas.bind(
            "<Configure>",
            lambda e: self.products_canvas.configure(scrollregion=self.products_canvas.bbox("all"))
        )

        # إطار داخلي لعرض أزرار المنتجات
        self.products_buttons_frame = ttkb.Frame(self.products_canvas)
        self.products_canvas.create_window((0, 0), window=self.products_buttons_frame, anchor="nw")

        # ✅ إنشاء إطار الطلبات
        orders_frame = ttkb.Frame(self.root)
        orders_frame.pack(side="right", fill="y", padx=10, pady=10)

        ttkb.Label(orders_frame, text="الطلبات", font=("Helvetica", 16, "bold")).pack(pady=10)

        # إطار داخلي لتجميع طريقة الاستلام وبيانات الديلفيري
        order_details_frame = ttkb.Frame(orders_frame)
        order_details_frame.pack(fill="x", pady=5)

        # إطار طريقة الاستلام
        order_type_frame = ttkb.Frame(order_details_frame)
        order_type_frame.pack(fill="x", pady=5)

        ttkb.Label(order_type_frame, text="طريقة الاستلام", font=("Helvetica", 14, "bold")).pack(side="left", padx=5)

        # زر التيك أواي
        self.takeaway_button = ttkb.Button(
            order_type_frame,
            text="تيك أواي",
            bootstyle="info",
            command=lambda: self.set_order_type("takeaway")
        )
        self.takeaway_button.pack(side="left", padx=5)

        # زر الديلفيري
        self.delivery_button = ttkb.Button(
            order_type_frame,
            text="ديلفيري",
            bootstyle="info",
            command=lambda: self.set_order_type("delivery")
        )
        self.delivery_button.pack(side="left", padx=5)
        # زر إنهاء الوردية (مضاف هنا)
        self.end_shift_button = ttkb.Button(
            order_type_frame,
            text="إنهاء الوردية",
            bootstyle="danger",
            command=self.end_shift
        )
        self.end_shift_button.pack(side="right", padx=5)  # وضعه على الجانب الأيمن
        
        # إطار بيانات الديلفيري (مخفي في البداية)
        self.delivery_details_frame = ttkb.Frame(order_details_frame)
        self.delivery_details_frame.pack(fill="x", pady=5)
        self.delivery_details_frame.pack_forget()  # إخفاء الإطار في البداية

        # حقل رقم الهاتف مع التحقق من الصحة
        validate_phone = self.root.register(self.validate_phone_input)  # تسجيل دالة التحقق
    
        # حقل رقم الهاتف
        self.customer_phone_entry = ttkb.Entry(self.delivery_details_frame, width=20, validate="key", validatecommand=(validate_phone, "%P"))
        self.customer_phone_entry.pack(side="left", padx=5)
        self.customer_phone_entry.insert(0, "رقم الهاتف...")  # نص تلميح
        self.customer_phone_entry.bind("<FocusIn>", lambda e: self.clear_hint(self.customer_phone_entry, "رقم الهاتف..."))  # مسح النص عند التركيز
        self.customer_phone_entry.bind("<FocusOut>", lambda e: self.restore_hint(self.customer_phone_entry, "رقم الهاتف..."))  # استعادة النص عند فقدان التركيز
        self.customer_phone_entry.bind("<KeyRelease>", self.search_customer_by_phone)  # بحث عن العميل عند الكتابة
        # زر إضافة عميل جديد (أيقونة)
        self.add_customer_icon = self.create_add_customer_icon()  # إنشاء أيقونة افتراضية
        add_customer_button = ttkb.Button(
            self.delivery_details_frame,
            image=self.add_customer_icon,
            bootstyle="light",
            command=self.toggle_add_customer_frame
        )
        add_customer_button.pack(side="left", padx=5)

        # إطار لعرض بيانات العميل
        self.customer_info_frame = ttkb.Frame(self.delivery_details_frame)
        self.customer_info_frame.pack(fill="x", pady=5)
        self.customer_info_frame.pack_forget()  # إخفاء الإطار في البداية

        # تسميات لعرض بيانات العميل
        self.customer_address_label = ttkb.Label(self.customer_info_frame, text="العنوان: -", font=("Helvetica", 14, "bold"), foreground="blue")
        self.customer_address_label.pack(side="left", padx=5)

        self.customer_name_label = ttkb.Label(self.customer_info_frame, text="اسم العميل: -", font=("Helvetica", 14, "bold"), foreground="green")
        self.customer_name_label.pack(side="left", padx=5)

        # إطار إضافة عميل جديد (مخفي في البداية)
        self.add_customer_frame = ttkb.Frame(self.delivery_details_frame)
        self.add_customer_frame.pack(fill="x", pady=5)
        self.add_customer_frame.pack_forget()  # إخفاء الإطار في البداية

        # إطار إضافة عميل جديد (مخفي في البداية)
        self.add_customer_frame = ttkb.Frame(self.delivery_details_frame)
        self.add_customer_frame.pack(fill="x", pady=5)
        self.add_customer_frame.pack_forget()  # إخفاء الإطار في البداية
    
        # حقول إدخال بيانات العميل الجديد في صف واحد
        self.new_customer_name_entry = ttkb.Entry(self.add_customer_frame, width=15)
        self.new_customer_name_entry.pack(side="right", padx=5)
        self.new_customer_name_entry.insert(0, "اسم العميل...")  # نص تلميح
        self.new_customer_name_entry.bind("<FocusIn>", lambda e: self.clear_hint(self.new_customer_name_entry, "اسم العميل..."))  # مسح النص عند التركيز
        self.new_customer_name_entry.bind("<FocusOut>", lambda e: self.restore_hint(self.new_customer_name_entry, "اسم العميل..."))  # استعادة النص عند فقدان التركيز
    
        self.new_customer_address_entry = ttkb.Entry(self.add_customer_frame, width=20)
        self.new_customer_address_entry.pack(side="right", padx=5)
        self.new_customer_address_entry.insert(0, "العنوان...")  # نص تلميح
        self.new_customer_address_entry.bind("<FocusIn>", lambda e: self.clear_hint(self.new_customer_address_entry, "العنوان..."))  # مسح النص عند التركيز
        self.new_customer_address_entry.bind("<FocusOut>", lambda e: self.restore_hint(self.new_customer_address_entry, "العنوان..."))  # استعادة النص عند فقدان التركيز
    
        # زر حفظ العميل الجديد
        save_button = ttkb.Button(
            self.add_customer_frame,
            text="حفظ",
            bootstyle="success",
            command=self.save_new_customer
        )
        save_button.pack(side="right", padx=5)

        # جدول الطلبات
        self.orders_table = ttk.Treeview(
            orders_frame, columns=("ID", "Name", "Size", "Price", "Quantity", "Total"), show="headings"
        )
        self.orders_table.heading("ID", text="ID")
        self.orders_table.heading("Name", text="المنتج")
        self.orders_table.heading("Size", text="الحجم")
        self.orders_table.heading("Price", text="السعر")
        self.orders_table.heading("Quantity", text="الكمية")
        self.orders_table.heading("Total", text="الإجمالي")
        self.orders_table.pack(fill="both", expand=True, pady=10)

        # إطار أزرار تأكيد الطلب
        confirm_frame = ttkb.Frame(orders_frame)
        confirm_frame.pack(fill="x", pady=10)

        # زر تأكيد الطلب
        self.confirm_button = ttkb.Button(
            confirm_frame,
            text="تأكيد الطلب",
            bootstyle="primary",
            command=self.confirm_order
        )
        self.confirm_button.pack(side="left", padx=5)

        # زر تجهيز الطلب (مخفي في البداية)
        self.prepare_button = ttkb.Button(
            confirm_frame,
            text="تجهيز الطلب",
            bootstyle="success",
            command=self.prepare_order
        )
        self.prepare_button.pack(side="left", padx=5)
        self.prepare_button.pack_forget()  # إخفاء الزر في البداية

        # زر طلبات الديلفيري (مخفي في البداية)
        self.delivery_orders_button = ttkb.Button(
            confirm_frame,
            text="طلبات الديلفيري",
            bootstyle="primary",
            command=self.show_delivery_orders
        )
        self.delivery_orders_button.pack(side="left", padx=5)
        self.delivery_orders_button.pack_forget()  # إخفاء الزر في البداية

        # زر إدارة الموصلين (مخفي في البداية)
        self.manage_delivery_persons_button = ttkb.Button(
            confirm_frame,
            text="إدارة الموصلين",
            bootstyle="info",
            command=self.manage_delivery_persons
        )
        self.manage_delivery_persons_button.pack(side="left", padx=5)
        self.manage_delivery_persons_button.pack_forget()  # إخفاء الزر في البداية

         # زر العودة إلى صفحة إدارة الورديات
        return_to_shifts_button = ttkb.Button(
            confirm_frame,
            text="العودة إلى إدارة الورديات",
            bootstyle="warning",
            command=self.return_to_shifts
        )
        return_to_shifts_button.pack(side="right", padx=5)

        # زر العودة إلى الرئيسية
        return_button = ttkb.Button(orders_frame, text="العودة إلى الرئيسية", bootstyle="warning", command=self.return_callback)
        return_button.pack(pady=10)
    
    def clear_frame(self):
        """إزالة جميع العناصر داخل `root`"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def update_scrollregion(self):
        """تحديث منطقة التمرير في Canvas"""
        self.products_canvas.configure(scrollregion=self.products_canvas.bbox("all"))

    def toggle_add_customer_frame(self):
        """تبديل إظهار/إخفاء إطار إضافة عميل جديد مع التحقق من وجود رقم الهاتف"""
        phone = self.customer_phone_entry.get().strip()
    
        # التحقق من أن رقم الهاتف يتكون من 11 رقمًا
        if len(phone) != 11 or not phone.isdigit():
            messagebox.showwarning("خطأ", "رقم الهاتف يجب أن يتكون من 11 رقمًا!")
            return
    
        # التحقق مما إذا كان العميل موجودًا بالفعل
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
        if cursor.fetchone():
            messagebox.showinfo("معلومات", "العميل موجود بالفعل!")
            return  # إيقاف العملية إذا كان العميل موجودًا
    
        # إذا لم يكن العميل موجودًا، قم بتبديل إظهار/إخفاء إطار إضافة العميل
        if self.add_customer_frame.winfo_ismapped():
            self.add_customer_frame.pack_forget()
        else:
            self.add_customer_frame.pack(fill="x", pady=5)

    def validate_phone_input(self, new_value):
        """التحقق من أن المدخل يتكون من أرقام فقط ولا يتجاوز 11 رقمًا"""
        if new_value == "":  # السماح بحذف النص
            return True
        if new_value == "رقم الهاتف...":  # السماح بالنص التوجيهي
            return True
        if new_value.isdigit() and len(new_value) <= 11:  # السماح فقط بالأرقام ولا يزيد عن 11 رقمًا
            return True
        return False

    def clear_hint(self, entry_widget, hint_text):
        """مسح النص التوجيهي عند التركيز على الحقل"""
        if entry_widget.get() == hint_text:
            entry_widget.delete(0, tk.END)

    def restore_hint(self, entry_widget, hint_text):
        """استعادة النص التوجيهي عند فقدان التركيز إذا كان الحقل فارغًا"""
        if not entry_widget.get():
            entry_widget.insert(0, hint_text)

    def create_add_customer_icon(self):
        """إنشاء أيقونة افتراضية لإضافة عميل جديد"""
        # إنشاء صورة بيضاء بحجم 20x20
        icon_image = Image.new("RGB", (20, 20), color="white")
        draw = ImageDraw.Draw(icon_image)

        # رسم علامة "+" (زائد) في وسط الصورة
        draw.line((5, 10, 15, 10), fill="black", width=2)  # خط أفقي
        draw.line((10, 5, 10, 15), fill="black", width=2)  # خط عمودي

        # تحويل الصورة إلى صيغة PhotoImage
        return ImageTk.PhotoImage(icon_image)


#3. دوال إدارة الأقسام والمنتجات
    def load_categories(self):
        """تحميل الأقسام من قاعدة البيانات وعرضها كأزرار"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT name FROM categories")
        categories = cursor.fetchall()

        # مسح الإطار الحالي
        for widget in self.categories_buttons_frame.winfo_children():
            widget.destroy()

        # إضافة أزرار الأقسام
        for category in categories:
            button = ttkb.Button(
                self.categories_buttons_frame,
                text=category[0],
                bootstyle="info-outline",
                command=lambda cat=category[0]: self.load_products(cat)
            )
            button.pack(fill="x", pady=5)

    def load_products(self, category_name):
        """تحميل المنتجات بناءً على القسم المحدد وعرضها كأزرار"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT products.id, products.name 
            FROM products 
            INNER JOIN categories ON products.category_id = categories.id
            WHERE categories.name = ?
        """, (category_name,))
        products = cursor.fetchall()

        # مسح الإطار الحالي
        for widget in self.products_buttons_frame.winfo_children():
            widget.destroy()

        # إنشاء نمط مخصص لأزرار المنتجات
        style = ttk.Style()
        style.configure("Large.TButton", font=("Helvetica", 14), padding=10)

        # إضافة أزرار المنتجات في صفوف (صفين في كل صف)
        row, col = 0, 0
        for product in products:
            product_frame = ttkb.Frame(self.products_buttons_frame)
            product_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # زر المنتج (بحجم أكبر)
            product_button = ttkb.Button(
                product_frame,
                text=product[1],
                bootstyle="info-outline",
                command=lambda prod=product, frame=product_frame: self.toggle_sizes(prod, frame),
                style="Large.TButton"  # تطبيق النمط المخصص
            )
            product_button.pack(fill="both", expand=True)

            # إطار الأحجام (مخفي في البداية)
            sizes_frame = ttkb.Frame(product_frame)
            sizes_frame.pack(fill="x", pady=5)
            sizes_frame.pack_forget()  # إخفاء الإطار في البداية
            product_frame.sizes_frame = sizes_frame  # حفظ الإطار كخاصية

            # تحديث الصف والعمود للزر التالي
            col += 1
            if col == 2:  # إذا وصلنا إلى العمود الثاني، ننتقل إلى الصف التالي
                col = 0
                row += 1

        # ضبط توسيع الأعمدة والصفوف
        self.products_buttons_frame.grid_columnconfigure(0, weight=1)
        self.products_buttons_frame.grid_columnconfigure(1, weight=1)
        for r in range(row + 1):
            self.products_buttons_frame.grid_rowconfigure(r, weight=1)

        # تحديث منطقة التمرير في Canvas
        self.update_scrollregion()

    def toggle_sizes(self, product, product_frame):
        """عرض أو إخفاء أحجام المنتج أسفل زر المنتج"""
        product_id, product_name = product
    
        # إخفاء إطار الأحجام الحالي إذا كان موجودًا
        if self.current_sizes_frame and self.current_sizes_frame.winfo_exists():
            self.current_sizes_frame.pack_forget()
    
        # إذا كانت الأحجام معروضة بالفعل، قم بإخفائها
        if product_frame.sizes_frame.winfo_ismapped():
            product_frame.sizes_frame.pack_forget()
            self.current_sizes_frame = None
            return
    
        # جلب الأحجام المتاحة للمنتج
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT size, price FROM product_sizes 
            WHERE product_id = ?
        """, (product_id,))
        sizes = cursor.fetchall()
    
        # إذا لم يكن هناك أحجام أو أسعار محددة
        if not sizes:
            self.ask_for_price(product_id, product_name)  # فتح نافذة لإدخال السعر يدويًا
            return
    
        # مسح الإطار الحالي للأحجام
        for widget in product_frame.sizes_frame.winfo_children():
            widget.destroy()
    
        # عرض الأحجام كأزرار
        for size, price in sizes:
            button_text = f"{size} (${price})"
            button = ttkb.Button(
                product_frame.sizes_frame,
                text=button_text,
                bootstyle="success",
                command=lambda s=size, p=price, prod_id=product_id, prod_name=product_name: self.add_to_cart(prod_id, prod_name, s, p)
            )
            button.pack(side="left", padx=5)
    
        # إظهار إطار الأحجام
        product_frame.sizes_frame.pack(fill="x", pady=5)
        self.current_sizes_frame = product_frame.sizes_frame  # تحديث الإطار الحالي

    def ask_for_price(self, product_id, product_name):
         """فتح نافذة لإدخال السعر يدويًا"""
         price_window = tk.Toplevel(self.root)
         price_window.title("إدخال السعر")
     
         ttkb.Label(price_window, text="أدخل السعر:").pack(pady=10)
     
         self.price_entry = ttkb.Entry(price_window)
         self.price_entry.pack(pady=10)
     
         confirm_button = ttkb.Button(
             price_window,
             text="تأكيد",
             bootstyle="success",
             command=lambda: self.save_custom_price(product_id, product_name, price_window)
         )
         confirm_button.pack(pady=10)

    def save_custom_price(self, product_id, product_name, price_window):
        """حفظ السعر المخصص وإضافة المنتج إلى الطلبات"""
        try:
            price = float(self.price_entry.get().strip())
            if price <= 0:
                raise ValueError("السعر يجب أن يكون رقمًا موجبًا!")
        except ValueError as e:
            messagebox.showerror("خطأ", "يرجى إدخال سعر صحيح!")
            return
    
        # إضافة المنتج إلى الطلبات
        self.add_to_cart(product_id, product_name, "مخصص", price)
    
        # إغلاق نافذة إدخال السعر
        price_window.destroy()


#4. دوال إدارة الطلبات
    def set_order_type(self, order_type):
        """تحديد طريقة الاستلام (تيك أواي أو ديلفيري)"""
        self.order_type = order_type

        # إظهار أو إخفاء إطار تفاصيل الديلفيري بناءً على طريقة الاستلام
        if order_type == "delivery":
            self.delivery_details_frame.pack(fill="x", pady=5)
            self.confirm_button.pack_forget()  # إخفاء زر تأكيد الطلب
            self.prepare_button.pack(side="left", padx=5)  # إظهار زر تجهيز الطلب
            self.delivery_orders_button.pack(side="left", padx=5)  # إظهار زر طلبات الديلفيري
            self.manage_delivery_persons_button.pack(side="left", padx=5)  # إظهار زر إدارة الموصلين
        else:
            self.delivery_details_frame.pack_forget()
            self.prepare_button.pack_forget()  # إخفاء زر تجهيز الطلب
            self.delivery_orders_button.pack_forget()  # إخفاء زر طلبات الديلفيري
            self.manage_delivery_persons_button.pack_forget()  # إخفاء زر إدارة الموصلين
            self.confirm_button.pack(side="left", padx=5)  # إظهار زر تأكيد الطلب
  
    def add_to_cart(self, product_id, product_name, size, price):
         """إضافة المنتج المحدد إلى الطلبات"""
         # التحقق مما إذا كان المنتج بنفس الحجم موجودًا بالفعل في الطلبات
         for item in self.selected_items:
             if item["id"] == product_id and item["size"] == size:
                 # زيادة الكمية إذا كان المنتج موجودًا
                 item["quantity"] += 1
                 item["total"] = item["price"] * item["quantity"]
                 self.update_orders_table()
                 return
     
         # إذا لم يكن المنتج موجودًا، نضيفه كعنصر جديد
         self.selected_items.append({
             "id": product_id,
             "name": product_name,
             "size": size,
             "price": float(price),
             "quantity": 1,
             "total": float(price)
         })
     
         # تحديث جدول الطلبات
         self.update_orders_table()

    def remove_from_cart(self):
        """إزالة المنتج المحدد من الطلبات"""
        selected_item = self.orders_table.selection()
        if not selected_item:
            messagebox.showwarning("خطأ", "يرجى تحديد منتج أولاً!")
            return

        product_id = self.orders_table.item(selected_item, "values")[0]

        # إزالة المنتج من قائمة الطلبات
        self.selected_items = [item for item in self.selected_items if item["id"] != product_id]

        # تحديث جدول الطلبات
        self.update_orders_table()

    def update_orders_table(self):
        """تحديث جدول الطلبات"""
        # مسح الجدول الحالي
        for row in self.orders_table.get_children():
            self.orders_table.delete(row)

        # إضافة المنتجات المختارة إلى الجدول
        for item in self.selected_items:
            self.orders_table.insert("", "end", values=(
                item["id"],
                item["name"],
                item["size"],
                item["price"],
                item["quantity"],
                item["total"]
            ))

    def confirm_order(self):
        """تأكيد الطلب للتيك أواي"""
        if not self.selected_items:
            messagebox.showwarning("خطأ", "لا توجد منتجات في الطلب!")
            return
    
        # حساب الإجمالي النهائي
        total = sum(item["total"] for item in self.selected_items)
    
        # حساب order_number (عدد الطلبات في الوردية الحالية + 1)
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM takeaway_orders 
            WHERE shift_id = ?
        """, (self.current_shift_id,))
        order_number = cursor.fetchone()[0] + 1  # عدد الطلبات الحالية + 1
    
        # حفظ الطلب في جدول طلبات التيك أواي
        cursor.execute("""
            INSERT INTO takeaway_orders (total, shift_id, order_number)
            VALUES (?, ?, ?)
        """, (total, self.current_shift_id, order_number))
        self.db_connection.commit()
    
        # إنشاء نص البون
        receipt_text = self.generate_receipt_text("تيك أواي", total, order_number)
    
        # طباعة البون
        self.print_receipt(receipt_text)
    
        # عرض تفاصيل الطلب
        order_details = f"تم تأكيد الطلب بنجاح!\nطريقة الاستلام: {self.order_type}\nالإجمالي النهائي: {total}"
        messagebox.showinfo("تفاصيل الطلب", order_details)
    
        # مسح قائمة الطلبات
        self.selected_items.clear()
        self.update_orders_table()
        
    def prepare_order(self):
        """تجهيز الطلب وحفظه في جدول طلبات الديلفيري"""
        if not self.selected_items:
            messagebox.showwarning("خطأ", "لا توجد منتجات في الطلب!")
            return
    
        phone = self.customer_phone_entry.get().strip()
        if not phone:
            messagebox.showwarning("خطأ", "يرجى إدخال رقم الهاتف!")
            return
    
        # البحث عن العميل في قاعدة البيانات
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT name, address FROM customers WHERE phone = ?", (phone,))
        customer = cursor.fetchone()
    
        if not customer:
            messagebox.showwarning("خطأ", "لم يتم العثور على عميل بهذا الرقم!")
            return
    
        customer_name, customer_address = customer
    
        # حساب الإجمالي النهائي
        total = sum(item["total"] for item in self.selected_items)
    
        # حساب order_number (عدد الطلبات في الوردية الحالية + 1)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM delivery_orders 
            WHERE shift_id = ?
        """, (self.current_shift_id,))
        order_number = cursor.fetchone()[0] + 1  # عدد الطلبات الحالية + 1
    
        # حفظ الطلب في جدول طلبات الديلفيري
        cursor.execute("""
            INSERT INTO delivery_orders (customer_name, customer_phone, customer_address, total, status, shift_id, order_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, phone, customer_address, total, "pending", self.current_shift_id, order_number))
        self.db_connection.commit()
    
        # إنشاء نص البون
        receipt_text = self.generate_receipt_text("ديلفيري", total, order_number, customer_name, customer_address)
    
        # طباعة البون
        self.print_receipt(receipt_text)
    
        # عرض رسالة تأكيد
        messagebox.showinfo("تجهيز الطلب", "تم تجهيز الطلب بنجاح!")
    
        # مسح قائمة الطلبات
        self.selected_items.clear()
        self.update_orders_table()
        
    def show_delivery_orders(self):
        """عرض طلبات الديلفيري في نافذة جديدة"""
        if self.delivery_orders_window and self.delivery_orders_window.winfo_exists():
            # إذا كانت النافذة مفتوحة بالفعل، إحضارها إلى المقدمة
            self.delivery_orders_window.lift()
            return
    
        # إنشاء النافذة الجديدة
        self.delivery_orders_window = tk.Toplevel(self.root)
        self.delivery_orders_window.title("طلبات الديلفيري")
        
        # جدول طلبات الديلفيري
        delivery_orders_table = ttk.Treeview(
            self.delivery_orders_window,
            columns=("ID","shift_id", "order_number",  "Name",  "Phone", "Address", "Total", "Status"),
            show="headings",
        )
        delivery_orders_table.heading("ID", text="ID")
        delivery_orders_table.heading("shift_id", text="الوردية")
        delivery_orders_table.heading("order_number", text="رقم الطلب")
        delivery_orders_table.heading("Name", text="اسم العميل")
        delivery_orders_table.heading("Phone", text="رقم الهاتف")
        delivery_orders_table.heading("Address", text="العنوان")
        delivery_orders_table.heading("Total", text="الإجمالي")
        delivery_orders_table.heading("Status", text="الحالة")
        delivery_orders_table.pack(fill="both", expand=True, pady=10)
    
        # تحديد عرض الأعمدة
        delivery_orders_table.column("ID", width=50, anchor="center")  # عرض عمود ID
        delivery_orders_table.column("shift_id",width=50, anchor="center")
        delivery_orders_table.column("order_number",width=80, anchor="center")
        delivery_orders_table.column("Name", width=130, anchor="center")  # عرض عمود اسم العميل
        delivery_orders_table.column("Phone", width=100, anchor="center")  # عرض عمود رقم الهاتف
        delivery_orders_table.column("Address", width=220, anchor="center")  # عرض عمود العنوان
        delivery_orders_table.column("Total", width=80, anchor="center")  # عرض عمود الإجمالي
        delivery_orders_table.column("Status", width=80, anchor="center")  # عرض عمود الحالة
    
        # جلب طلبات الديلفيري من قاعدة البيانات
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM delivery_orders WHERE shift_id = ? AND status = 'pending'", (self.current_shift_id,))
        orders = cursor.fetchall()
    
        # إضافة الطلبات إلى الجدول
        for order in orders:
            delivery_orders_table.insert("", "end", values=order)
    
        # إطار لتحديد الموصل
        assign_frame = ttkb.Frame(self.delivery_orders_window)
        assign_frame.pack(fill="x", pady=10)
      
       # قائمة الموصلين باستخدام OptionMenu
        self.selected_delivery_person = tk.StringVar(value="اختر طيار")  # القيمة الافتراضية
        self.delivery_person_menu = ttk.OptionMenu(
            assign_frame,
            self.selected_delivery_person,
            "اختر طيار",  # النص الافتراضي
            *self.load_delivery_persons(return_names_only=True),  # تحميل أسماء الموصلين
            command=self.update_delivery_person  # وظيفة التحديث
        )
        self.delivery_person_menu.pack(side="left", padx=5)
    
        # زر تأكيد التوصيل
        confirm_button = ttkb.Button(
            assign_frame,
            text="تأكيد التوصيل",
            bootstyle="success",
            command=lambda: self.assign_delivery_order(delivery_orders_table)
        )
        confirm_button.pack(side="left", padx=5)

    def assign_delivery_order(self, delivery_orders_table):
        """تحديد الطلب للتوصيل وتحديث الجدول"""
        selected_item = delivery_orders_table.selection()
        if not selected_item:
            messagebox.showwarning("خطأ", "يرجى تحديد طلب أولاً!")
            return
    
        order_id = delivery_orders_table.item(selected_item, "values")[0]
        delivery_person = self.selected_delivery_person.get()  # الحصول على القيمة المختارة
    
        # التحقق من أن المستخدم قد اختار طيارًا وليس القيمة الافتراضية
        if not delivery_person or delivery_person == "اختر طيار":
            messagebox.showwarning("خطأ", "يرجى اختيار طيار!")
            return
    
        # تحديث حالة الطلب في قاعدة البيانات
        cursor = self.db_connection.cursor()
        cursor.execute("""
            UPDATE delivery_orders
            SET status = ?, delivery_person = ?
            WHERE id = ?
        """, ("delivered", delivery_person, order_id))
        self.db_connection.commit()
    
        # عرض رسالة نجاح
        messagebox.showinfo("نجاح", "تم تعيين الطيار وتأكيد التوصيل بنجاح!")
    
        # تحديث الجدول مباشرة من قاعدة البيانات (فقط الطلبات المعلقة للوردية الحالية)
        self.update_delivery_orders_table(delivery_orders_table)
    
    def update_delivery_orders_table(self, delivery_orders_table):
         """تحديث جدول طلبات الديلفيري (فقط الطلبات المعلقة للوردية الحالية)"""
         # مسح الجدول الحالي
         for row in delivery_orders_table.get_children():
             delivery_orders_table.delete(row)
     
         # جلب طلبات الديلفيري المعلقة للوردية الحالية
         cursor = self.db_connection.cursor()
         cursor.execute("""
             SELECT id, order_number, customer_name, customer_phone, customer_address, total
             FROM delivery_orders
             WHERE shift_id = ? AND status = 'pending'
         """, (self.current_shift_id,))  # <-- تصفية الطلبات بناءً على shift_id الحالي
         orders = cursor.fetchall()
     
         # إضافة الطلبات إلى الجدول
         for order in orders:
             delivery_orders_table.insert("", "end", values=order)

#5. دوال إدارة العملاء  
    def search_customer_by_phone(self, event):
        """البحث عن العميل باستخدام رقم الهاتف"""
        phone = self.customer_phone_entry.get().strip()

        # التحقق من أن رقم الهاتف يتكون من 11 رقمًا
        if len(phone) != 11 or not phone.isdigit():
            self.customer_info_frame.pack_forget()  # إخفاء إطار بيانات العميل
            return

        # البحث عن العميل في قاعدة البيانات
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT name, address FROM customers WHERE phone = ?", (phone,))
        customer = cursor.fetchone()

        if customer:
            # إذا وجد العميل، عرض بياناته في الإطار
            self.customer_name_label.config(text=f"اسم العميل: {customer[0]}")
            self.customer_address_label.config(text=f"العنوان: {customer[1]}")
            self.customer_info_frame.pack(fill="x", pady=5)  # إظهار إطار بيانات العميل
        else:
            # إذا لم يتم العثور على العميل، إخفاء الإطار
            self.customer_info_frame.pack_forget()
 
    def save_new_customer(self):
        """حفظ بيانات العميل الجديد في قاعدة البيانات"""
        phone = self.customer_phone_entry.get().strip()
        name = self.new_customer_name_entry.get().strip()
        address = self.new_customer_address_entry.get().strip()
    
        # التحقق من أن رقم الهاتف يتكون من 11 رقمًا
        if len(phone) != 11 or not phone.isdigit():
            messagebox.showwarning("خطأ", "رقم الهاتف يجب أن يتكون من 11 رقمًا!")
            return  # إيقاف العملية إذا كان الرقم غير صالح
    
        if not name or not address:
            messagebox.showwarning("خطأ", "يرجى إدخال جميع البيانات!")
            return
    
        # التحقق مما إذا كان العميل موجودًا بالفعل (قبل الحفظ)
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
        if cursor.fetchone():
            messagebox.showwarning("خطأ", "رقم الهاتف موجود بالفعل!")
            return  # إيقاف العملية إذا كان العميل موجودًا
    
        # حفظ البيانات في قاعدة البيانات
        cursor.execute("""
            INSERT INTO customers (name, phone, address)
            VALUES (?, ?, ?)
        """, (name, phone, address))
        self.db_connection.commit()
    
        # عرض رسالة نجاح
        messagebox.showinfo("نجاح", "تم حفظ العميل الجديد بنجاح!")
    
        # تفريغ حقول الإدخال بعد الحفظ
        self.new_customer_name_entry.delete(0, tk.END)  # مسح حقل اسم العميل
        self.new_customer_address_entry.delete(0, tk.END)  # مسح حقل العنوان
    
        # إخفاء إطار إضافة العميل
        self.add_customer_frame.pack_forget()
    
        # تحديث بيانات العميل في الواجهة الرئيسية
        self.update_customer_info(name, address)
    
    def update_customer_info(self, name, address):
        """تحديث بيانات العميل في الواجهة الرئيسية"""
        # تحديث تسميات بيانات العميل
        self.customer_name_label.config(text=f"اسم العميل: {name}")
        self.customer_address_label.config(text=f"العنوان: {address}")
    
        # إظهار إطار بيانات العميل (إذا كان مخفيًا)
        self.customer_info_frame.pack(fill="x", pady=5)


#6. دوال إدارة الموصلين
    def manage_delivery_persons(self):
         """فتح نافذة إدارة الموصلين"""
         if self.delivery_persons_window and self.delivery_persons_window.winfo_exists():
             # إذا كانت النافذة مفتوحة بالفعل، إحضارها إلى المقدمة
             self.delivery_persons_window.lift()
             return
     
         # إنشاء النافذة الجديدة
         self.delivery_persons_window = tk.Toplevel(self.root)
         self.delivery_persons_window.title("إدارة الموصلين")
     
         # إطار لإضافة موصل جديد
         add_delivery_person_frame = ttkb.Frame(self.delivery_persons_window)
         add_delivery_person_frame.pack(fill="x", pady=10)
     
         ttkb.Label(add_delivery_person_frame, text="اسم الموصل:").pack(side="left", padx=5)
         self.new_delivery_person_entry = ttkb.Entry(add_delivery_person_frame, width=30)
         self.new_delivery_person_entry.pack(side="left", padx=5)
     
         # زر إضافة موصل جديد
         add_button = ttkb.Button(
             add_delivery_person_frame,
             text="إضافة",
             bootstyle="success",
             command=self.add_delivery_person
         )
         add_button.pack(side="left", padx=5)
     
         # جدول الموصلين
         self.delivery_persons_table = ttk.Treeview(
             self.delivery_persons_window, columns=("ID", "Name", "Edit", "Delete"), show="headings"
         )
         self.delivery_persons_table.heading("ID", text="ID")
         self.delivery_persons_table.heading("Name", text="اسم الموصل")
         self.delivery_persons_table.heading("Edit", text="تعديل")
         self.delivery_persons_table.heading("Delete", text="حذف")
         self.delivery_persons_table.pack(fill="both", expand=True, pady=10)
     
         # جلب الموصلين من قاعدة البيانات
         self.load_delivery_persons()
  
    def load_delivery_persons(self, return_names_only=False):
        """تحميل الموصلين من قاعدة البيانات وعرضهم في الجدول أو إرجاع قائمة بأسمائهم"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM delivery_persons")
        delivery_persons = cursor.fetchall()
    
        if return_names_only:
            # إرجاع قائمة بأسماء الموصلين فقط
            return [person[1] for person in delivery_persons]
    
        # مسح الجدول الحالي
        for row in self.delivery_persons_table.get_children():
            self.delivery_persons_table.delete(row)
    
        # إضافة الموصلين إلى الجدول
        for person in delivery_persons:
            person_id, name = person
            self.delivery_persons_table.insert("", "end", values=(person_id, name, "تعديل", "حذف"))
    
        # إضافة أحداث لأزرار التعديل والحذف
        self.delivery_persons_table.bind("<Button-1>", self.on_delivery_person_click)
     
    def update_delivery_person(self, selected_person):
        """تحديث الموصل المختار"""
        self.selected_delivery_person.set(selected_person)

    def on_delivery_person_click(self, event):
        """التعامل مع النقر على أزرار التعديل والحذف"""
        region = self.delivery_persons_table.identify_region(event.x, event.y)
        if region == "cell":
            column = self.delivery_persons_table.identify_column(event.x)
            row_id = self.delivery_persons_table.identify_row(event.y)
            if column == "#3":  # عمود التعديل
                self.edit_delivery_person(row_id)
            elif column == "#4":  # عمود الحذف
                self.delete_delivery_person(row_id)
    
    def edit_delivery_person(self, row_id):
        """فتح نافذة تعديل اسم الموصل"""
        person_id = self.delivery_persons_table.item(row_id, "values")[0]
        current_name = self.delivery_persons_table.item(row_id, "values")[1]
    
        edit_window = tk.Toplevel(self.root)
        edit_window.title("تعديل الموصل")
    
        ttkb.Label(edit_window, text="اسم الموصل:").pack(pady=10)
        self.edit_delivery_person_entry = ttkb.Entry(edit_window, width=30)
        self.edit_delivery_person_entry.pack(pady=10)
        self.edit_delivery_person_entry.insert(0, current_name)
    
        save_button = ttkb.Button(
            edit_window,
            text="حفظ",
            bootstyle="success",
            command=lambda: self.save_edited_delivery_person(person_id, edit_window)
        )
        save_button.pack(pady=10)
    
    def save_edited_delivery_person(self, person_id, edit_window):
        """حفظ التعديلات على اسم الموصل"""
        new_name = self.edit_delivery_person_entry.get().strip()
    
        if not new_name:
            messagebox.showwarning("خطأ", "يرجى إدخال اسم الموصل!")
            return
    
        cursor = self.db_connection.cursor()
        cursor.execute("""
            UPDATE delivery_persons
            SET name = ?
            WHERE id = ?
        """, (new_name, person_id))
        self.db_connection.commit()
    
        messagebox.showinfo("نجاح", "تم تعديل اسم الموصل بنجاح!")
        edit_window.destroy()
        self.load_delivery_persons()
    
    def delete_delivery_person(self, row_id):
        """حذف الموصل من قاعدة البيانات"""
        person_id = self.delivery_persons_table.item(row_id, "values")[0]
        person_name = self.delivery_persons_table.item(row_id, "values")[1]
    
        confirm = messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف الموصل {person_name}؟")
        if confirm:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                DELETE FROM delivery_persons
                WHERE id = ?
            """, (person_id,))
            self.db_connection.commit()
    
            messagebox.showinfo("نجاح", "تم حذف الموصل بنجاح!")
            self.load_delivery_persons()
   
    def add_delivery_person(self):
       """إضافة موصل جديد إلى قاعدة البيانات"""
       name = self.new_delivery_person_entry.get().strip()
   
       if not name:
           messagebox.showwarning("خطأ", "يرجى إدخال اسم الموصل!")
           return
   
       # التحقق مما إذا كان الموصل موجودًا بالفعل
       cursor = self.db_connection.cursor()
       cursor.execute("SELECT * FROM delivery_persons WHERE name = ?", (name,))
       if cursor.fetchone():
           messagebox.showwarning("خطأ", "الموصل موجود بالفعل!")
           return
   
       # إضافة الموصل إلى قاعدة البيانات
       cursor.execute("""
           INSERT INTO delivery_persons (name)
           VALUES (?)
       """, (name,))
       self.db_connection.commit()
   
       # مسح حقل الإدخال
       self.new_delivery_person_entry.delete(0, tk.END)
   
       # تحديث الجدول مباشرة
       self.load_delivery_persons()
 

#7. دوال إدارة الورديات
    def check_active_shift(self):
        """التحقق من وجود وردية نشطة"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id FROM shifts WHERE end_time IS NULL")
        active_shift = cursor.fetchone()

        if active_shift:
            self.current_shift_id = active_shift[0]  # تعيين معرف الوردية النشطة
        else:
            self.current_shift_id = None  # إذا لم تكن هناك وردية نشطة
            messagebox.showwarning("خطأ", "يجب بدء وردية أولاً!")
            self.return_callback()  # العودة إلى القائمة الرئيسية

    def end_shift(self):
         """إنهاء الوردية الحالية وعرض ملخص الطلبات"""
         if not self.current_shift_id:
             messagebox.showwarning("خطأ", "لا يوجد وردية نشطة!")
             return
    
         # تأكيد إنهاء الوردية
         confirm = messagebox.askyesno("تأكيد", "هل أنت متأكد من إنهاء الوردية الحالية؟")
         if not confirm:
             return
    
         # حساب ملخص الطلبات
         takeaway_count, delivery_count, total_revenue = self.calculate_orders_summary()
    
         # إنهاء الوردية
         end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         cursor = self.db_connection.cursor()
         cursor.execute("""
             UPDATE shifts
             SET end_time = ?, total_hours = ROUND((JULIANDAY(?) - JULIANDAY(start_time)) * 24, 2)
             WHERE id = ?
         """, (end_time, end_time, self.current_shift_id))
         self.db_connection.commit()
    
         # عرض ملخص الطلبات
         summary_message = (
             f"تم إنهاء الوردية بنجاح!\n\n"
             f"عدد طلبات التيك أواي: {takeaway_count}\n"
             f"عدد طلبات الديلفيري: {delivery_count}\n"
             f"إجمالي السعر النهائي: {total_revenue:.2f} جنيه"
         )
         messagebox.showinfo("ملخص الطلبات", summary_message)
    
         # إعادة تعيين الوردية النشطة
         self.current_shift_id = None
    
         # العودة إلى الصفحة الرئيسية
         self.return_callback()

    def return_to_shifts(self):
       """العودة إلى صفحة إدارة الورديات"""
       self.clear_frame()
       self.return_to_shifts_callback()  # تأكد من أن الاسم مطابقفحة الورديات

    def calculate_orders_summary(self):
         """حساب عدد طلبات التيك أواي وطلبات الديلفيري وإجمالي السعر النهائي للوردية الحالية"""
         cursor = self.db_connection.cursor()
     
         # جلب طلبات التيك أواي للوردية الحالية
         cursor.execute("""
             SELECT order_number, total 
             FROM takeaway_orders 
             WHERE shift_id = ?
         """, (self.current_shift_id,))
         takeaway_orders = cursor.fetchall()
         takeaway_count = len(takeaway_orders)
         takeaway_total = sum(order[1] for order in takeaway_orders)
     
         # جلب طلبات الديلفيري للوردية الحالية
         cursor.execute("""
             SELECT order_number, total 
             FROM delivery_orders 
             WHERE shift_id = ? AND status != 'pending'
         """, (self.current_shift_id,))
         delivery_orders = cursor.fetchall()
         delivery_count = len(delivery_orders)
         delivery_total = sum(order[1] for order in delivery_orders)
     
         # إجمالي السعر النهائي
         total_revenue = takeaway_total + delivery_total
     
         return takeaway_count, delivery_count, total_revenue
    
#8. دوال البحث والتصفية
    def dynamic_search(self, event):
        """بحث ديناميكي عند الكتابة في حقل البحث"""
        search_term = self.search_entry.get().strip()
        if search_term == "ابحث عن منتج...":
            return

        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT products.id, products.name 
            FROM products 
            WHERE products.name LIKE ?
        """, (f"%{search_term}%",))
        products = cursor.fetchall()

        # مسح الإطار الحالي
        for widget in self.products_buttons_frame.winfo_children():
            widget.destroy()

        # عرض نتائج البحث
        row, col = 0, 0
        for product in products:
            product_frame = ttkb.Frame(self.products_buttons_frame)
            product_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # زر المنتج
            product_button = ttkb.Button(
                product_frame,
                text=product[1],
                bootstyle="info-outline",
                command=lambda prod=product, frame=product_frame: self.toggle_sizes(prod, frame),
                style="Large.TButton"
            )
            product_button.pack(fill="both", expand=True)

            # إطار الأحجام
            sizes_frame = ttkb.Frame(product_frame)
            sizes_frame.pack(fill="x", pady=5)
            sizes_frame.pack_forget()
            product_frame.sizes_frame = sizes_frame

            # تحديث الصف والعمود
            col += 1
            if col == 2:
                col = 0
                row += 1

        # ضبط توسيع الأعمدة والصفوف
        self.products_buttons_frame.grid_columnconfigure(0, weight=1)
        self.products_buttons_frame.grid_columnconfigure(1, weight=1)
        for r in range(row + 1):
            self.products_buttons_frame.grid_rowconfigure(r, weight=1)

        # تحديث منطقة التمرير في Canvas
        self.update_scrollregion()

#9. دالة للطباعة 
    def print_receipt(self, receipt_text):
        """طباعة البون باستخدام الطابعة المحددة"""
        try:
            # جلب اسم الطابعة من الإعدادات
            printer_name = self.load_printer_settings()
            if not printer_name:
                messagebox.showwarning("خطأ", "لم يتم تحديد طابعة!")
                return
    
            # فتح الطابعة
            hprinter = win32print.OpenPrinter(printer_name)
    
            # بدء مهمة طباعة
            win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
    
            # إرسال النص إلى الطابعة
            win32print.WritePrinter(hprinter, receipt_text.encode('utf-8'))
    
            # إنهاء الطباعة
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
    
            # إغلاق الطابعة
            win32print.ClosePrinter(hprinter)
    
            print("تمت الطباعة بنجاح!")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء الطباعة: {e}")

    def load_printer_settings(self):
         """تحميل الطابعة المحددة من ملف"""
         try:
             with open("settings.json", "r", encoding="utf-8") as f:
                 settings = json.load(f)
                 return settings.get("printer", "")
         except FileNotFoundError:
             return ""

    def generate_receipt_text(self, order_type, total, order_number, customer_name=None, customer_address=None):
         """Generate receipt text based on order type"""
         receipt_lines = [
             "=" * 40,
             "           Your Favorite Store",
             "=" * 40,
             f"Order Type: {order_type}",
             f"Order Number: {order_number}",
             f"Total: {total:.2f} EGP",
             "=" * 40,
         ]
     
         # If the order is delivery, add customer details
         if order_type == "delivery":
             receipt_lines.extend([
                 f"Customer Name: {customer_name}",
                 f"Address: {customer_address}",
                 "=" * 40,
             ])
     
         # Add product details
         receipt_lines.append("Products:")
         for item in self.selected_items:
             receipt_lines.append(
                 f"{item['name']} ({item['size']}) - {item['quantity']} x {item['price']:.2f} = {item['total']:.2f}"
             )
     
         receipt_lines.extend([
             "=" * 40,
             "Thank you for your visit!",
             "=" * 40,
         ])
     
         return "\n".join(receipt_lines)

    
if __name__ == "__main__":
    root = ttkb.Window(themename="cosmo")
    root.title("نظام إدارة المبيعات")
    root.geometry("1200x600")

    def return_to_main():
        print("العودة إلى القائمة الرئيسية")

    def return_to_shifts_callback():
        print("العودة إلى صفحة الورديات")

    # تهيئة قاعدة البيانات
    db_connection = sqlite3.connect("products.db")
    initialize_database(db_connection)
    db_connection.close()

    sales_page = SalesPage(root, return_to_main, return_to_shifts_callback)  # تمرير جميع المعاملات
    root.mainloop()