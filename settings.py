import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkb
import json
import win32print

class SettingsPage:
    def __init__(self, root, return_callback):
        self.root = root
        self.return_callback = return_callback
        self.create_page()

    def create_page(self):
        """إنشاء واجهة صفحة الإعدادات"""
        self.clear_frame()

        frame = ttkb.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ttkb.Label(frame, text="⚙️ الإعدادات", font=("Helvetica", 28, "bold"))
        title.pack(pady=20)

        # إضافة إعدادات الطابعة
        self.add_printer_settings(frame)

        # زر العودة للقائمة الرئيسية
        back_btn = ttkb.Button(frame, text="← العودة للقائمة الرئيسية",
                               bootstyle="light-outline", command=self.return_callback,
                               width=30, style="Large.TButton")
        back_btn.pack(pady=20)

    def add_printer_settings(self, parent):
        """إضافة إعدادات الطابعة باستخدام OptionMenu"""
        printer_frame = ttkb.Frame(parent)
        printer_frame.pack(fill="x", pady=10)

        ttkb.Label(printer_frame, text="الطابعة الافتراضية:", font=("Helvetica", 14)).pack(side="left", padx=10)

        # قائمة الطابعات المتاحة
        self.printer_var = tk.StringVar()
        self.printer_menu = ttkb.OptionMenu(
            printer_frame,
            self.printer_var,
            "اختر طابعة",  # النص الافتراضي
            *self.load_printers(),  # تحميل أسماء الطابعات
            command=self.on_printer_selected  # وظيفة التحديث
        )
        self.printer_menu.pack(side="left", padx=10, fill="x", expand=True)

        # تحميل الطابعة المحددة مسبقًا
        selected_printer = self.load_printer_settings()
        if selected_printer:
            self.printer_var.set(selected_printer)

        # زر تحديث الطابعات
        refresh_btn = ttkb.Button(printer_frame, text="تحديث", bootstyle="info",
                                  command=self.update_printer_menu)
        refresh_btn.pack(side="left", padx=10)

    def load_printers(self):
        """جلب الطابعات المتاحة"""
        printers = win32print.EnumPrinters(2)  # جلب الطابعات المتاحة
        printer_names = [printer[2] for printer in printers]  # استخراج أسماء الطابعات
        return printer_names if printer_names else ["لا توجد طابعات متاحة"]

    def update_printer_menu(self):
        """تحديث قائمة الطابعات في OptionMenu"""
        printers = self.load_printers()
        self.printer_menu.set_menu("اختر طابعة", *printers)

    def on_printer_selected(self, selected_printer):
        """تغيير لون الخانة المنسدلة عند اختيار الطابعة"""
        if selected_printer != "اختر طابعة":
            self.printer_menu.config(bootstyle="success")  # تغيير اللون إلى الأخضر
            self.save_printer_settings(selected_printer)  # حفظ الطابعة المحددة
            messagebox.showinfo("تم التحديد", f"تم اختيار الطابعة: {selected_printer}")

    def save_printer_settings(self, printer_name):
        """حفظ الطابعة المحددة في ملف"""
        settings = {"printer": printer_name}
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f)

    def load_printer_settings(self):
        """تحميل الطابعة المحددة من ملف"""
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("printer", "")
        except FileNotFoundError:
            return ""

    def clear_frame(self):
        """مسح جميع العناصر في الإطار"""
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = ttkb.Window(themename="cosmo")
    root.title("نظام الإعدادات")
    root.geometry("800x600")

    def return_to_main():
        print("العودة إلى القائمة الرئيسية")

    settings_page = SettingsPage(root, return_to_main)
    root.mainloop()