import customtkinter
from garak_connector import run_garak_command
import queue
import threading

class GarakGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Garak GUI")
        self.geometry("1024x768")

        # --- Create and store control variables ---
        self.verbose_var = customtkinter.BooleanVar()
        self.report_prefix_var = customtkinter.StringVar()
        self.narrow_output_var = customtkinter.BooleanVar()
        self.parallel_requests_var = customtkinter.StringVar()
        self.parallel_attempts_var = customtkinter.StringVar()
        self.skip_unknown_var = customtkinter.BooleanVar()

        self.seed_var = customtkinter.StringVar()
        self.deprefix_var = customtkinter.BooleanVar(value=True)
        self.eval_threshold_var = customtkinter.StringVar(value="0.5")
        self.generations_var = customtkinter.StringVar(value="10")
        self.config_var = customtkinter.StringVar()

        # --- Main Layout ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(padx=20, pady=20, fill="both", expand=True)

        self.config_tab = self.tab_view.add("Scan Configuration")
        self.output_tab = self.tab_view.add("Scan Output")
        self.reports_tab = self.tab_view.add("Reports")

        self.config_tab.grid_columnconfigure(0, weight=1)

        # --- System Settings Frame ---
        self.system_frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        self.system_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.system_frame.grid_columnconfigure(1, weight=1)

        system_label = customtkinter.CTkLabel(self.system_frame, text="System Settings", font=customtkinter.CTkFont(size=16, weight="bold"))
        system_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        # Verbose
        customtkinter.CTkCheckBox(self.system_frame, text="Verbose Output (-v)", variable=self.verbose_var).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        # Narrow Output
        customtkinter.CTkCheckBox(self.system_frame, text="Narrow Output", variable=self.narrow_output_var).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        # Skip Unknown
        customtkinter.CTkCheckBox(self.system_frame, text="Skip Unknown Plugins", variable=self.skip_unknown_var).grid(row=1, column=2, padx=10, pady=5, sticky="w")

        # Report Prefix
        customtkinter.CTkLabel(self.system_frame, text="Report Prefix").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.system_frame, textvariable=self.report_prefix_var).grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Parallel Requests
        customtkinter.CTkLabel(self.system_frame, text="Parallel Requests").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.system_frame, textvariable=self.parallel_requests_var).grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Parallel Attempts
        customtkinter.CTkLabel(self.system_frame, text="Parallel Attempts").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.system_frame, textvariable=self.parallel_attempts_var).grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")


        # --- Run Settings Frame ---
        self.run_frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        self.run_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        self.run_frame.grid_columnconfigure(1, weight=1)

        run_label = customtkinter.CTkLabel(self.run_frame, text="Run Settings", font=customtkinter.CTkFont(size=16, weight="bold"))
        run_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        # Deprefix
        customtkinter.CTkCheckBox(self.run_frame, text="Deprefix Output", variable=self.deprefix_var).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # Seed
        customtkinter.CTkLabel(self.run_frame, text="Random Seed").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.run_frame, textvariable=self.seed_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Eval Threshold
        customtkinter.CTkLabel(self.run_frame, text="Eval Threshold").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.run_frame, textvariable=self.eval_threshold_var).grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Generations
        customtkinter.CTkLabel(self.run_frame, text="Generations (-g)").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(self.run_frame, textvariable=self.generations_var).grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # Config File
        customtkinter.CTkLabel(self.run_frame, text="Config File").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        # File picker would be better, but for now an entry box
        customtkinter.CTkEntry(self.run_frame, textvariable=self.config_var).grid(row=5, column=1, padx=10, pady=5, sticky="ew")


        # --- Scan Execution ---
        self.start_button = customtkinter.CTkButton(self.config_tab, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=2, column=0, pady=20, padx=20, sticky="ew")

        # --- Scan Output Tab ---
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Reports Tab ---
        self.reports_label = customtkinter.CTkLabel(self.reports_tab, text="Scan reports will be shown here.")
        self.reports_label.pack(padx=20, pady=20)

    def build_garak_args(self):
        """Builds a list of command-line arguments from the UI settings."""
        args = []
        # System Settings
        if self.verbose_var.get():
            args.append("-v")
        if self.report_prefix_var.get():
            args.extend(["--report_prefix", self.report_prefix_var.get()])
        if self.narrow_output_var.get():
            args.append("--narrow_output")
        if self.parallel_requests_var.get():
            args.extend(["--parallel_requests", self.parallel_requests_var.get()])
        if self.parallel_attempts_var.get():
            args.extend(["--parallel_attempts", self.parallel_attempts_var.get()])
        if self.skip_unknown_var.get():
            args.append("--skip_unknown")

        # Run Settings
        if self.seed_var.get():
            args.extend(["--seed", self.seed_var.get()])

        # The --deprefix flag in garak is a store_false action.
        # It's on by default (deprefix=True). Adding the flag makes it False.
        # Our checkbox is "Deprefix Output", default True.
        # So, we add the flag only if the box is unchecked.
        if not self.deprefix_var.get():
            args.append("--deprefix")

        if self.eval_threshold_var.get():
            args.extend(["--eval_threshold", self.eval_threshold_var.get()])
        if self.generations_var.get():
            args.extend(["-g", self.generations_var.get()])
        if self.config_var.get():
            args.extend(["--config", self.config_var.get()])

        return args

    def start_scan(self):
        """Builds arguments from the UI and starts the Garak scan."""
        self.output_textbox.delete("1.0", "end")
        self.start_button.configure(state="disabled")

        garak_args = self.build_garak_args()

        # Add a model and probe for testing if not specified, otherwise garak shows help
        if not any(arg.startswith('--model') for arg in garak_args):
             garak_args.extend(["-m", "test.Blank"])
        if not any(arg.startswith('--probes') for arg in garak_args):
            garak_args.extend(["-p", "test.Blank"])

        self.output_textbox.insert("end", f"Running Garak with command:\npython -m garak {' '.join(garak_args)}\n\n")

        self.output_queue = queue.Queue()

        self.garak_thread = threading.Thread(
            target=run_garak_command,
            args=(garak_args, self.output_queue)
        )
        self.garak_thread.daemon = True
        self.garak_thread.start()

        self.after(100, self.process_queue)

    def process_queue(self):
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
