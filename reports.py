import tkinter as tk
import ttkbootstrap as ttkb

class ReportsPage:
    def __init__(self, root, return_callback):
        self.root = root
        self.return_callback = return_callback
        self.create_page()

    def create_page(self):
        self.clear_frame()

        frame = ttkb.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ttkb.Label(frame, text="📈 التقارير", font=("Helvetica", 28, "bold"))
        title.pack(pady=20)

        back_btn = ttkb.Button(frame, text="← العودة للقائمة الرئيسية",
                               bootstyle="light-outline", command=self.return_callback,
                               width=30, style="Large.TButton")
        back_btn.pack(pady=20)

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
