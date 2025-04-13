import ctypes
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import glob  # لاستعماله في البحث عن الملفات
from cryptography.fernet import Fernet
import pygame  # type: ignore
from PIL import Image, ImageTk
import ttkbootstrap as ttkb  # Import ttkbootstrap

# تحديد مجلد AppData\Roaming بدلاً من Local
app_folder = os.path.join(os.getenv('APPDATA'), "Nassar")  # يستخدم Roaming بدلاً من Local

# التأكد من وجود المجلد، وإذا لم يكن موجودًا يتم إنشاؤه
if not os.path.exists(app_folder):
    os.makedirs(app_folder)

# تحديد مسار ملفات بيانات الاعتماد
credentials_file = os.path.join(app_folder, "credentials.enc")
key_file = os.path.join(app_folder, "secret.key")

# دالة لجعل الملف مخفيًا (Windows فقط)
def hide_file(file_path):
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)

# دالة لحفظ مفتاح التشفير في ملف
def save_key():
    key = Fernet.generate_key()
    with open(key_file, 'wb') as key_out:
        key_out.write(key)

# دالة لقراءة مفتاح التشفير من الملف
def load_key():
    if not os.path.exists(key_file):
        save_key()
    # حاول الوصول إلى الملف بدون إخفائه أولًا
    with open(key_file, 'rb') as key_in:
        key = key_in.read()
    
    # بعد تحميل المفتاح بنجاح، يمكنك إخفاءه
    hide_file(key_file)
    
    return key

# تحميل المفتاح
key = load_key()
cipher = Fernet(key)

# دالة لتشفير النصوص
def encrypt_data(data):
    return cipher.encrypt(data.encode())

# دالة لفك تشفير النصوص
def decrypt_data(data):
    decrypted_data = cipher.decrypt(data).decode()
    return decrypted_data

# دالة لحفظ اسم المستخدم وكلمة المرور المشفرة في ملف
def save_credentials(username, password):
    encrypted_username = encrypt_data(username)
    encrypted_password = encrypt_data(password)
    with open(credentials_file, 'wb') as file_out:
        file_out.write(encrypted_username + b'\n' + encrypted_password)
    hide_file(credentials_file)  # إخفاء ملف بيانات الاعتماد

# دالة لقراءة بيانات الاعتماد المشفرة والتحقق منها
def load_credentials():
    if os.path.exists(credentials_file):
        with open(credentials_file, 'rb') as file_in:
            encrypted_username = file_in.readline().strip()
            encrypted_password = file_in.readline().strip()
            return decrypt_data(encrypted_username), decrypt_data(encrypted_password)
    return None, None

# إخفاء المجلد الذي يحتوي على ملفات الاعتماد
hide_file(app_folder)

# دالة فتح نافذة المطور
def open_developer_window():
    developer_window = ttkb.Toplevel()  # استخدام Toplevel لإنشاء نافذة جديدة مستقلة
    developer_window.title("نافذة المطور")
    
    # استخدام المسار النسبي لتعيين الأيقونة
    base_path = Path(__file__).parent
    icon_path = base_path / "key.ico"
    
    if icon_path.exists():
        developer_window.iconbitmap(icon_path)
    else:
        print("Icon file not found")

    developer_window.geometry("400x300")

    label_title = ttkb.Label(developer_window, text="نافذة المطور", font=("Cairo", 16, "bold"))
    label_title.pack(pady=20)

class LoginWindow:
    def __init__(self, master, on_login_success):
        self.master = master
        self.on_login_success = on_login_success

        # تهيئة pygame
        pygame.mixer.init()
        # استخدام المسار النسبي لملف الصوت
        base_path = Path(__file__).parent
        sound_path = base_path / "success.wav"
        
        if sound_path.exists():
            self.success_sound = pygame.mixer.Sound(str(sound_path))  # تحويل المسار إلى نص لاستخدامه في pygame
        else:
            print("ملف الصوت غير موجود!")
    
        self.create_login_frame()

    def create_login_frame(self):
        self.clear_frame()

        # إعداد الخلفية - يتم تعيينه تلقائيًا مع سمة "superhero"
        ttkb.Label(self.master, text="تسجيل الدخول", font=("Helvetica", 18, "bold")).pack(padx=5,pady=40)

        # حقل إدخال اسم المستخدم
        ttkb.Label(self.master, text="اسم المستخدم:").pack(pady=0)
        self.username_entry = ttkb.Entry(self.master, width=15, font=("Arial", 16))
        self.username_entry.pack(pady=10)

        # التركيز تلقائيًا على حقل اسم المستخدم عند فتح النافذة
        self.username_entry.focus_set()

        ttkb.Label(self.master, text="كلمة المرور:").pack(pady=0)
        self.password_entry = ttkb.Entry(self.master, show="*", width=15, font=("Arial", 16))
        self.password_entry.pack(pady=10)

        # زر تسجيل الدخول  
        login_button = ttkb.Button(self.master, text="تسجيل الدخول", command=self.authenticate, 
                                    bootstyle="success", width=12)
        login_button.pack(pady=20)

        # زر "هل نسيت اسم المستخدم وكلمة المرور؟"
        forgot_credentials_button = ttkb.Button(self.master, text="تغيير اسم المستخدم وكلمة المرور", 
                                                 command=self.show_forgot_credentials_frame, 
                                                 bootstyle="info", width=30)
        forgot_credentials_button.pack(pady=20)

        self.add_developer_label()  # إضافة اسم المطور

        # ربط الضغط على Enter بالانتقال بين الحقول
        self.username_entry.bind('<Return>', lambda event: self.password_entry.focus_set())
        self.password_entry.bind('<Return>', lambda event: login_button.invoke())

        # ربط مفاتيح الأسهم للتنقل بين الحقول
        self.username_entry.bind('<Down>', lambda event: self.password_entry.focus_set())
        self.password_entry.bind('<Down>', lambda event: login_button.focus_set())
        login_button.bind('<Down>', lambda event: forgot_credentials_button.focus_set())
        
        forgot_credentials_button.bind('<Up>', lambda event: login_button.focus_set())
        login_button.bind('<Up>', lambda event: self.password_entry.focus_set())
        self.password_entry.bind('<Up>', lambda event: self.username_entry.focus_set())

    def clear_frame(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # تحميل بيانات الاعتماد من الملف
        saved_username, saved_password = load_credentials()

        # التحقق من اسم المستخدم وكلمة المرور
        if saved_username == username and saved_password == password:
            self.success_sound.play()  # تشغيل الصوت عند نجاح تسجيل الدخول
            self.on_login_success()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة!")

    def show_forgot_credentials_frame(self):
        self.clear_frame()

        ttkb.Label(self.master, text="تحديث بيانات الاعتماد", font=("Helvetica", 18, "bold")).pack(pady=20)

        ttkb.Label(self.master, text="اسم المستخدم القديم:").pack(pady=0)
        self.old_username_entry = ttkb.Entry(self.master, width=15, font=("Arial", 12))
        self.old_username_entry.pack(pady=5)

        # التركيز تلقائيًا على حقل اسم المستخدم القديم عند فتح النافذة
        self.old_username_entry.focus_set()

        ttkb.Label(self.master, text="كلمة المرور القديمة:").pack(pady=0)
        self.old_password_entry = ttkb.Entry(self.master, show="*", width=15, font=("Arial", 12))
        self.old_password_entry.pack(pady=5)

        ttkb.Label(self.master, text="اسم المستخدم الجديد:").pack(pady=0)
        self.new_username_entry = ttkb.Entry(self.master, width=15, font=("Arial", 12))
        self.new_username_entry.pack(pady=5)

        ttkb.Label(self.master, text="كلمة المرور الجديدة:").pack(pady=0)
        self.new_password_entry = ttkb.Entry(self.master, show="*", width=15, font=("Arial", 12))
        self.new_password_entry.pack(pady=5)

        # زر تحديث  
        update_button = ttkb.Button(self.master, text="تحديث", command=self.update_credentials, 
                                     bootstyle="success", width=12)
        update_button.pack(pady=10)

        # زر للعودة
        back_button = ttkb.Button(self.master, text="عودة", command=self.create_login_frame,
                                   bootstyle="danger", width=12)
        back_button.pack(pady=5)

        self.add_developer_label()  # إضافة اسم المطور
        # ربط الضغط على Enter بالانتقال بين الحقول
        self.old_username_entry.bind('<Return>', lambda event: self.old_password_entry.focus_set())
        self.old_password_entry.bind('<Return>', lambda event: self.new_username_entry.focus_set())
        self.new_username_entry.bind('<Return>', lambda event: self.new_password_entry.focus_set())
        self.new_password_entry.bind('<Return>', lambda event: update_button.invoke())
    
           # ربط مفاتيح الأسهم للتنقل بين الحقول
        self.old_username_entry.bind('<Down>', lambda event: self.old_password_entry.focus_set())
        self.old_password_entry.bind('<Down>', lambda event: self.new_username_entry.focus_set())
        self.new_username_entry.bind('<Down>', lambda event: self.new_password_entry.focus_set())
        self.new_password_entry.bind('<Down>', lambda event: update_button.focus_set())
        update_button.bind('<Down>', lambda event: back_button.focus_set())
        
        # زر العودة
        back_button.bind('<Up>', lambda event: update_button.focus_set())
        update_button.bind('<Up>', lambda event: self.new_password_entry.focus_set())
        self.new_password_entry.bind('<Up>', lambda event: self.new_username_entry.focus_set())
        self.new_username_entry.bind('<Up>', lambda event: self.old_password_entry.focus_set())
        self.old_password_entry.bind('<Up>', lambda event: self.old_username_entry.focus_set())

        
    def update_credentials(self):
        old_username = self.old_username_entry.get()
        old_password = self.old_password_entry.get()
        new_username = self.new_username_entry.get()
        new_password = self.new_password_entry.get()
    
        saved_username, saved_password = load_credentials()
    
        # تحقق من صحة اسم المستخدم وكلمة المرور القديمة
        if saved_username == old_username and saved_password == old_password:
            # تحقق من أن البيانات الجديدة ليست متطابقة مع البيانات القديمة
            if new_username == old_username and new_password == old_password:
                messagebox.showerror("خطأ", "اسم المستخدم وكلمة المرور الجديدة لا يجب أن تكون نفس القديمة!")
            elif new_username and new_password:
                # حذف ملفات التشفير والمفتاح إذا وجدت
                self.delete_old_credentials()
    
                # حفظ بيانات الاعتماد الجديدة بعد تشفيرها
                save_credentials(new_username, new_password)
                
                # عرض رسالة نجاح
                messagebox.showinfo("نجاح", "تم تحديث بيانات الاعتماد بنجاح!")
    
                # العودة إلى صفحة تسجيل الدخول بعد التحديث
                self.create_login_frame()
            else:
                messagebox.showerror("خطأ", "يرجى إدخال اسم المستخدم وكلمة المرور الجديدة!")
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور القديمة غير صحيحة!")
    
    def delete_old_credentials(self):
       # الحصول على مسار مجلد المستخدم
        user_home = os.path.expanduser("~")
        
        # حدد مسار ملفات التشفير والمفتاح
        credentials_file = os.path.join(user_home, "AppData", "Roaming", "Nassar", "credentials.enc")
        key_file = os.path.join(user_home, "AppData", "Roaming", "Nassar", "key.key")  # استبدل هذا بالمسار الصحيح
    
        # حذف الملفات إذا كانت موجودة
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
        
        if os.path.exists(key_file):
            os.remove(key_file)
    
        # إعادة إنشاء الملفات الجديدة وجعلها مخفية
        self.make_file_hidden(credentials_file)
        self.make_file_hidden(key_file)
    
    def make_file_hidden(self, file_path):
        # جعل الملف مخفيًا
        if os.path.exists(file_path):
            os.system(f'attrib +h "{file_path}"')
    

    def add_developer_label(self):
        base_path = Path(__file__).parent
    
        # إضافة أيقونة WhatsApp
        whatsapp_icon_path = base_path / "whatsapp.ico"
        if whatsapp_icon_path.exists():
            whatsapp_icon = Image.open(whatsapp_icon_path)  # استبدل هذا بمسار صورة الأيقونة
            whatsapp_icon = whatsapp_icon.resize((20, 20))
    
            # تحويل الصورة إلى تنسيق يمكن Tkinter استخدامه
            whatsapp_icon = ImageTk.PhotoImage(whatsapp_icon)
    
            # إضافة الرقم مع أيقونة WhatsApp
            whatsapp_frame = tk.Frame(self.master)
            whatsapp_frame.pack(side="bottom", pady=5)
    
            tk.Label(whatsapp_frame, image=whatsapp_icon).pack(side="left")
            tk.Label(whatsapp_frame, text="01500011785", font=("Cairo", 11, "bold")).pack(side="left", padx=5)
    
            # الاحتفاظ بالإشارة للأيقونة
            whatsapp_frame.whatsapp_icon = whatsapp_icon
        else:
            print("ملف أيقونة WhatsApp غير موجود!")
    
        # إضافة أيقونة Ahmed.ico
        ahmed_icon_path = base_path / "Ahmed.ico"
        if ahmed_icon_path.exists():
            ahmed_icon = Image.open(ahmed_icon_path)  # استبدل هذا بمسار أيقونة أحمد
            ahmed_icon = ahmed_icon.resize((120, 120))
    
            # تحويل الصورة إلى تنسيق يمكن Tkinter استخدامه
            ahmed_icon = ImageTk.PhotoImage(ahmed_icon)
    
            # إضافة النص مع أيقونة أحمد
            ahmed_frame = tk.Frame(self.master)
            ahmed_frame.pack(side="bottom", pady=5)
    
            tk.Label(ahmed_frame, image=ahmed_icon).pack(side="top")
            tk.Label(ahmed_frame, text="[Eng:Ahmed Mohsen Nassar]", font=("Cairo", 11, "bold")).pack(side="top", padx=5)
    
            # الاحتفاظ بالإشارة للأيقونة
            ahmed_frame.ahmed_icon = ahmed_icon
        else:
            print("ملف أيقونة أحمد غير موجود!")

class Application(ttkb.Window):  # استخدام ttkb.Window بدلاً من tk.Tk
    def __init__(self):
        super().__init__(themename="superhero")  # استخدام ttkbootstrap مع الثيم
        self.title("تسجيل الدخول")
        self.geometry("500x670")

        self.login_window = LoginWindow(self, self.on_login_success)

    def on_login_success(self):
        # هنا يمكن إضافة ما يجب القيام به بعد تسجيل الدخول الناجح
        self.destroy()  # إغلاق نافذة تسجيل الدخول

if __name__ == "__main__":
    app = Application()
    app.mainloop()
