import customtkinter

class ToolTip(customtkinter.CTkToplevel):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.widget = widget
        self.text = text

        self.withdraw() # Hide window initially
        self.overrideredirect(True) # No window decorations

        self.label = customtkinter.CTkLabel(self, text=self.text, background="#FFFFE0", corner_radius=3, text_color="black")
        self.label.pack(ipadx=5, ipady=2)

        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def hide_tip(self, event=None):
        self.withdraw()
