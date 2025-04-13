import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

class ModernMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Menu App")
        self.root.geometry("1250x670")

        # استخدام سمة حديثة
        self.style = ttkb.Style("darkly")

        # إنشاء الإطار الرئيسي
        self.main_frame = ttkb.Frame(root, bootstyle="default")
        self.main_frame.pack(fill="both", expand=True)

        # إنشاء شريط القوائم العلوي
        self.navbar = ttkb.Frame(self.main_frame, bootstyle="secondary")
        self.navbar.pack(side="top", fill="x")

        # إضافة عنوان في الشريط العلوي
        self.title_label = ttkb.Label(self.navbar, text="Modern App", font=("Helvetica", 16), bootstyle="inverse-secondary")
        self.title_label.pack(side="left", padx=20, pady=10)

        # إنشاء قائمة أزرار في الشريط العلوي
        self.create_modern_menu()

        # إطار المحتوى الرئيسي
        self.content_frame = ttkb.Frame(self.main_frame, bootstyle="default")
        self.content_frame.pack(fill="both", expand=True)

        # عرض محتوى افتراضي
        self.show_default_content()

    def create_modern_menu(self):
        # قائمة الأزرار في الشريط العلوي
        menu_buttons = [
            {"text": "المبيعات", "command": self.show_sales},
            {"text": "الأصناف", "command": self.show_categories},
            {"text": "المخزون", "command": self.show_inventory},
            {"text": "التقارير", "command": self.show_reports},
            {"text": "الإعدادات", "command": self.show_settings},
        ]

        for button in menu_buttons:
            btn = ttkb.Button(
                self.navbar,
                text=button["text"],
                bootstyle="light-outline",
                command=button["command"],
            )
            btn.pack(side="left", padx=10, pady=5)

        # زر تبديل السمة في الشريط العلوي
        self.theme_toggle = ttkb.Button(
            self.navbar,
            text="🌙 Dark Mode",
            bootstyle="light-outline",
            command=self.toggle_theme,
        )
        self.theme_toggle.pack(side="right", padx=10, pady=5)

    def toggle_theme(self):
        # تبديل بين الوضع الداكن والفاتح
        if self.style.theme_use() == "darkly":
            self.style.theme_use("pulse")
            self.theme_toggle.config(text="☀️ Light Mode")
        else:
            self.style.theme_use("darkly")
            self.theme_toggle.config(text="🌙 Dark Mode")

    def show_default_content(self):
        # عرض محتوى افتراضي
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="مرحبًا بك في التطبيق الحديث", font=("Helvetica", 24))
        label.pack(pady=50)

    def show_sales(self):
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="نافذة المبيعات", font=("Helvetica", 24))
        label.pack(pady=50)

    def show_categories(self):
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="نافذة الأصناف", font=("Helvetica", 24))
        label.pack(pady=50)

    def show_inventory(self):
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="نافذة المخزون", font=("Helvetica", 24))
        label.pack(pady=50)

    def show_reports(self):
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="نافذة التقارير", font=("Helvetica", 24))
        label.pack(pady=50)

    def show_settings(self):
        self.clear_content()
        label = ttkb.Label(self.content_frame, text="نافذة الإعدادات", font=("Helvetica", 24))
        label.pack(pady=50)

    def clear_content(self):
        # مسح المحتوى الحالي
        for widget in self.content_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = ttkb.Window(themename="darkly")
    app = ModernMenuApp(root)
    root.mainloop()
