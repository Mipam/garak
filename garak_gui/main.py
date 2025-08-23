import customtkinter
from garak_connector import run_garak_command
import queue
import threading

class GarakGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Garak GUI")
        self.geometry("1024x768")

        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(padx=20, pady=20, fill="both", expand=True)

        self.config_tab = self.tab_view.add("Scan Configuration")
        self.output_tab = self.tab_view.add("Scan Output")
        self.reports_tab = self.tab_view.add("Reports")

        # --- Scan Configuration Tab ---
        self.start_button = customtkinter.CTkButton(self.config_tab, text="Start Scan", command=self.start_scan)
        self.start_button.pack(pady=20, padx=20)

        # --- Scan Output Tab ---
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Reports Tab ---
        self.reports_label = customtkinter.CTkLabel(self.reports_tab, text="Scan reports will be shown here.")
        self.reports_label.pack(padx=20, pady=20)

    def start_scan(self):
        """Called when the 'Start Scan' button is clicked."""
        self.output_textbox.delete("1.0", "end")
        self.start_button.configure(state="disabled")
        self.output_textbox.insert("end", "Starting Garak scan...\n\n")

        test_args = ["--version"]

        self.output_queue = queue.Queue()

        self.garak_thread = threading.Thread(
            target=run_garak_command,
            args=(test_args, self.output_queue)
        )
        self.garak_thread.daemon = True
        self.garak_thread.start()

        self.after(100, self.process_queue)

    def process_queue(self):
        """Process messages from the output queue."""
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line is None:
                    self.start_button.configure(state="normal")
                    return
                self.output_textbox.insert("end", line)
                self.output_textbox.see("end")
        except queue.Empty:
            self.after(100, self.process_queue)

if __name__ == "__main__":
    app = GarakGUI()
    app.mainloop()
