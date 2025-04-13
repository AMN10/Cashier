import ctypes
import os
from pathlib import Path
import time
from cryptography.fernet import Fernet
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar
from datetime import datetime

# تحديد مجلد AppData\Roaming
app_folder = os.path.join(os.getenv('APPDATA'), "Nassar")

# تأكد من وجود المجلد
if not os.path.exists(app_folder):
    os.makedirs(app_folder)

# إخفاء المجلد
def hide_folder(folder_path):
    FOLDER_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW(folder_path, FOLDER_ATTRIBUTE_HIDDEN)


# تعديل مسارات ملفات التشفير والاعتمادات
LOG_FILE = os.path.join(app_folder, "access_log.txt")  # ملف السجلات
credentials_file = os.path.join(app_folder, "credentials.enc")  # ملف الاعتمادات المشفرة
key_file = os.path.join(app_folder, "secret.key")  # ملف مفتاح التشفير

# كلمة مرور المطور الثابتة للتحقق
DEVELOPER_PASSWORD = "1a2h3m4e5d"  # يمكنك تغيير كلمة المرور هنا

# متغيرات لقفل خانة كلمة المرور
lock_time = 0  # زمن القفل (بالثواني)
lock_duration = 300  # مدة القفل الأول (5 دقائق)
attempts = 0  # عدد المحاولات الخاطئة

# دالة لتسجيل الأحداث
def log_event(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as log_file:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"{timestamp} - {message}\n")

# دالة لجعل الملف مخفيًا (Windows فقط)
def hide_file(file_path):
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)

# دالة لإنشاء مفتاح تشفير جديد
def generate_key():
    return Fernet.generate_key()

# دالة لتشفير بيانات الاعتماد
def encrypt_credentials(username, password, key):
    fernet = Fernet(key)
    encrypted_username = fernet.encrypt(username.encode())
    encrypted_password = fernet.encrypt(password.encode())
    return encrypted_username, encrypted_password

# دالة لحفظ بيانات الاعتماد والمفتاح في الملفات
def save_credentials_to_files(credentials_file, key_file, encrypted_username, encrypted_password, key):
    # إذا كان الملف موجودًا، قم بمسحه
    if os.path.exists(credentials_file):
        os.remove(credentials_file)

    if os.path.exists(key_file):
        os.remove(key_file)

    # حفظ بيانات الاعتماد
    with open(credentials_file, 'wb') as cf:
        cf.write(encrypted_username + b'\n' + encrypted_password)

    # حفظ المفتاح
    with open(key_file, 'wb') as kf:
        kf.write(key)
    
    # إخفاء الملفات
    hide_file(credentials_file)
    hide_file(key_file)
# إخفاء المجلد الذي يحتوي على ملفات الاعتماد
hide_file(app_folder)

# دالة لتحديث بيانات الاعتماد من خلال الواجهة
def update_credentials():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        message_var.set("يرجى إدخال اسم المستخدم وكلمة المرور.")
        return

    # إنشاء مفتاح تشفير جديد
    key = generate_key()

    # تشفير بيانات الاعتماد
    encrypted_username, encrypted_password = encrypt_credentials(username, password, key)

    # حفظ البيانات في الملفات
    save_credentials_to_files(credentials_file, key_file, encrypted_username, encrypted_password, key)

    # تسجيل الحدث
    log_event(f"تم تحديث بيانات الاعتماد للمستخدم: {username}")

    # إظهار رسالة نجاح
    message_var.set("تم تحديث بيانات الاعتماد بنجاح.")
    
    # إغلاق التطبيق بعد التحديث
    root.destroy()

# دالة التحقق من كلمة مرور المطور
def check_developer_password(event=None):
    global lock_time, lock_duration, attempts

    # التحقق من الوقت الحالي
    current_time = time.time()

    # إذا كان هناك وقت قفل، تحقق مما إذا كان قد انتهى
    if lock_time > 0:
        if current_time < lock_time:
            remaining_time = int(lock_time - current_time)
            message_var.set(f"تم قفل خانة كلمة مرور المطور. يرجى الانتظار {remaining_time // 60 + 1} دقيقة.")
            return
        else:
            # إعادة تعيين الوقت القفل
            lock_time = 0
            attempts = 0  # إعادة تعيين عدد المحاولات
            entry_dev_password.config(state='normal')  # إعادة تمكين حقل الإدخال
            label_remaining_time.pack_forget()  # إخفاء Label الوقت المتبقي
            message_var.set("")  # مسح الرسالة
            return

    entered_password = entry_dev_password.get()

    if entered_password == DEVELOPER_PASSWORD:
        log_event("محاولة دخول ناجحة من المطور.")
        message_var.set("تم التحقق من كلمة مرور المطور بنجاح.")
        show_update_fields()  # إظهار حقول تحديث بيانات الاعتماد
    else:
        attempts += 1
        log_event("محاولة دخول فاشلة من المطور.")
        message_var.set(f"كلمة مرور المطور غير صحيحة. لديك {3 - attempts} محاولات متبقية.")
        
        # تعيين وقت القفل إذا تم الوصول إلى الحد الأقصى من المحاولات
        if attempts >= 3:
            lock_time = time.time() + lock_duration  # 5 دقائق
            entry_dev_password.config(state='disabled')  # قفل حقل الإدخال
            message_var.set("لقد تجاوزت عدد المحاولات المسموح بها. سيتم قفل الحقل لمدة 5 دقائق.")
            show_remaining_time()  # إظهار الوقت المتبقي
        else:
            entry_dev_password.delete(0, 'end')  # مسح حقل الإدخال بعد فشل الإدخال

# إظهار حقول تحديث بيانات الاعتماد بعد التحقق من كلمة مرور المطور
def show_update_fields():
    # إخفاء حقول كلمة مرور المطور
    label_dev_password.pack_forget()
    entry_dev_password.pack_forget()
    button_check_password.pack_forget()

    # إظهار حقول اسم المستخدم وكلمة المرور الجديدة
    label_username.pack(pady=5)
    entry_username.pack(pady=5, ipadx=10)
    entry_username.focus()  # تعيين التركيز على حقل اسم المستخدم
    label_password.pack(pady=5)
    entry_password.pack(pady=5, ipadx=10)
    button_update.pack(pady=20)

# إظهار الوقت المتبقي
def show_remaining_time():
    remaining_time = int(lock_time - time.time())
    if remaining_time > 0:
        label_remaining_time.config(text=f"الوقت المتبقي: {remaining_time // 60} دقيقة و {remaining_time % 60} ثانية")
        label_remaining_time.pack(pady=5)
        root.after(1000, show_remaining_time)  # تحديث الوقت المتبقي كل ثانية

# الانتقال إلى حقل كلمة المرور عند الضغط على Enter
def focus_password(event):
    entry_password.focus()

# التحديث عند الضغط على Enter في حقل كلمة المرور
def submit_on_enter(event):
    update_credentials()

# تصميم واجهة المستخدم باستخدام ttkbootstrap
root = ttk.Window(themename="superhero")
root.title("تحديث بيانات الاعتماد")

# تعيين الأيقونة للنافذة
icon_path = Path(__file__).parent / "key.ico"
if icon_path.exists():
    root.iconbitmap(str(icon_path))  # تأكد من وجود ملف key.ico في نفس المجلد
else:
    print("ملف أيقونة 'key.ico' غير موجود!")

# إعداد الحجم
root.geometry("700x500")

# العنوان
label_title = ttk.Label(root, text="تحديث بيانات الاعتماد", font=("Cairo", 16, "bold"))
label_title.pack(pady=20)

# حقل إدخال كلمة مرور المطور
label_dev_password = ttk.Label(root, text="كلمة مرور المطور:")
label_dev_password.pack(pady=5)
entry_dev_password = ttk.Entry(root, font=("Cairo", 12), show="*")
entry_dev_password.pack(pady=5, ipadx=10)

# تعيين التركيز على حقل كلمة مرور المطور عند بدء التطبيق
entry_dev_password.focus()

# ربط مفتاح Enter بحقل كلمة مرور المطور للتحقق
entry_dev_password.bind("<Return>", check_developer_password)

# زر التحقق من كلمة مرور المطور
button_check_password = ttk.Button(root, text="تحقق", bootstyle=INFO, command=check_developer_password)
button_check_password.pack(pady=20)

# حقل إدخال اسم المستخدم (يتم إخفاؤه في البداية)
label_username = ttk.Label(root, text="اسم المستخدم:")
entry_username = ttk.Entry(root, font=("Cairo", 12))

# حقل إدخال كلمة المرور الجديدة (يتم إخفاؤه في البداية)
label_password = ttk.Label(root, text="كلمة المرور الجديدة:")
entry_password = ttk.Entry(root, font=("Cairo", 12), show="*")

# زر تحديث (يتم إخفاؤه في البداية)
button_update = ttk.Button(root, text="تحديث", bootstyle=SUCCESS, command=update_credentials)

# Label لإظهار الوقت المتبقي (يتم إخفاؤه في البداية)
label_remaining_time = ttk.Label(root, text="", font=("Cairo", 12, "bold"))

# Label لإظهار الرسائل (يتم إخفاؤه في البداية)
message_var = StringVar()
message_label = ttk.Label(root, textvariable=message_var, font=("Cairo", 12, "bold"), foreground="red")
message_label.pack(pady=5)

# ربط مفتاح Enter بحقل اسم المستخدم للانتقال إلى حقل كلمة المرور
entry_username.bind("<Return>", focus_password)

# ربط مفتاح Enter بحقل كلمة المرور لتحديث بيانات الاعتماد
entry_password.bind("<Return>", submit_on_enter)

# بدء التطبيق
root.mainloop()
