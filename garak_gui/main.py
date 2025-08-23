import customtkinter
from garak_connector import run_garak_command, get_plugins
import queue
import threading

class GarakGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Garak GUI")
        self.geometry("1200x800")

        # --- Create and store control variables ---
        self._create_control_variables()

        # --- Main Layout ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)

        self.config_tab = self.tab_view.add("Scan Configuration")
        self.output_tab = self.tab_view.add("Scan Output")
        self.reports_tab = self.tab_view.add("Reports")

        self.config_tab.grid_columnconfigure(0, weight=1)
        self.config_tab.grid_rowconfigure(2, weight=1)

        # --- Create UI Frames ---
        self._create_system_settings_frame()
        self._create_run_settings_frame()
        self._create_plugin_settings_frame()
        self._create_execution_frame()
        self._create_output_tab_widgets()
        self._create_reports_tab_widgets()

    def _create_control_variables(self):
        # System Settings
        self.verbose_var = customtkinter.BooleanVar()
        self.report_prefix_var = customtkinter.StringVar()
        self.narrow_output_var = customtkinter.BooleanVar()
        self.parallel_requests_var = customtkinter.StringVar()
        self.parallel_attempts_var = customtkinter.StringVar()
        self.skip_unknown_var = customtkinter.BooleanVar()
        # Run Settings
        self.seed_var = customtkinter.StringVar()
        self.deprefix_var = customtkinter.BooleanVar(value=True)
        self.eval_threshold_var = customtkinter.StringVar(value="0.5")
        self.generations_var = customtkinter.StringVar(value="10")
        self.config_var = customtkinter.StringVar()
        # Plugin Settings
        self.model_type_var = customtkinter.StringVar()
        self.model_name_var = customtkinter.StringVar()
        self.probe_vars = {}
        self.detector_vars = {}
        self.buff_vars = {}

    def _create_system_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="System Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")
        customtkinter.CTkCheckBox(frame, text="Verbose Output (-v)", variable=self.verbose_var).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkCheckBox(frame, text="Narrow Output", variable=self.narrow_output_var).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        customtkinter.CTkCheckBox(frame, text="Skip Unknown Plugins", variable=self.skip_unknown_var).grid(row=1, column=2, padx=10, pady=5, sticky="w")
        customtkinter.CTkLabel(frame, text="Report Prefix").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.report_prefix_var).grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(frame, text="Parallel Requests").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.parallel_requests_var).grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(frame, text="Parallel Attempts").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.parallel_attempts_var).grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

    def _create_run_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="Run Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w")
        customtkinter.CTkCheckBox(frame, text="Deprefix Output", variable=self.deprefix_var).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkLabel(frame, text="Random Seed").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.seed_var).grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(frame, text="Eval Threshold").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.eval_threshold_var).grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(frame, text="Generations (-g)").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.generations_var).grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(frame, text="Config File").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        customtkinter.CTkEntry(frame, textvariable=self.config_var).grid(row=5, column=1, padx=10, pady=5, sticky="ew")

    def _create_plugin_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        frame.grid_columnconfigure([0,1,2], weight=1)
        frame.grid_rowconfigure(1, weight=1)

        customtkinter.CTkLabel(frame, text="Plugin Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")

        # Model
        model_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        model_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        customtkinter.CTkLabel(model_frame, text="Model", font=customtkinter.CTkFont(weight="bold")).pack(anchor="w")
        customtkinter.CTkLabel(model_frame, text="Model Type:").pack(anchor="w", pady=(5,0))
        generators = get_plugins("generators")
        if not generators: generators = ["Not Found"]
        customtkinter.CTkOptionMenu(model_frame, variable=self.model_type_var, values=generators).pack(fill="x")
        customtkinter.CTkLabel(model_frame, text="Model Name:").pack(anchor="w", pady=(10,0))
        customtkinter.CTkEntry(model_frame, textvariable=self.model_name_var).pack(fill="x")

        # Probes
        probes_frame = self._create_plugin_selection_frame(frame, "probes", self.probe_vars)
        probes_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Detectors & Buffs
        sub_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        sub_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        sub_frame.grid_columnconfigure(0, weight=1)
        sub_frame.grid_rowconfigure([0,1], weight=1)
        detectors_frame = self._create_plugin_selection_frame(sub_frame, "detectors", self.detector_vars)
        detectors_frame.grid(row=0, column=0, sticky="nsew")
        buffs_frame = self._create_plugin_selection_frame(sub_frame, "buffs", self.buff_vars)
        buffs_frame.grid(row=1, column=0, sticky="nsew", pady=(10,0))

    def _create_plugin_selection_frame(self, parent, plugin_type, var_dict):
        frame = customtkinter.CTkFrame(parent)
        frame.pack_propagate(False)
        customtkinter.CTkLabel(frame, text=plugin_type.title(), font=customtkinter.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        scroll_frame = customtkinter.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        plugin_list = get_plugins(plugin_type)
        if not plugin_list:
            customtkinter.CTkLabel(scroll_frame, text=f"No {plugin_type} found.").pack()
        else:
            for plugin_name in plugin_list:
                var = customtkinter.BooleanVar()
                customtkinter.CTkCheckBox(scroll_frame, text=plugin_name, variable=var).pack(anchor="w", padx=5)
                var_dict[plugin_name] = var
        return frame

    def _create_execution_frame(self):
        self.start_button = customtkinter.CTkButton(self.config_tab, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

    def _create_output_tab_widgets(self):
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_reports_tab_widgets(self):
        self.reports_label = customtkinter.CTkLabel(self.reports_tab, text="Scan reports will be shown here.")
        self.reports_label.pack(padx=10, pady=10)

    def build_garak_args(self):
        """Builds a list of command-line arguments from all UI settings."""
        args = []
        # System Settings
        if self.verbose_var.get(): args.append("-v")
        if self.report_prefix_var.get(): args.extend(["--report_prefix", self.report_prefix_var.get()])
        if self.narrow_output_var.get(): args.append("--narrow_output")
        if self.parallel_requests_var.get(): args.extend(["--parallel_requests", self.parallel_requests_var.get()])
        if self.parallel_attempts_var.get(): args.extend(["--parallel_attempts", self.parallel_attempts_var.get()])
        if self.skip_unknown_var.get(): args.append("--skip_unknown")

        # Run Settings
        if self.seed_var.get(): args.extend(["--seed", self.seed_var.get()])
        if not self.deprefix_var.get(): args.append("--deprefix")
        if self.eval_threshold_var.get(): args.extend(["--eval_threshold", self.eval_threshold_var.get()])
        if self.generations_var.get(): args.extend(["-g", self.generations_var.get()])
        if self.config_var.get(): args.extend(["--config", self.config_var.get()])

        # Plugin Settings
        if self.model_type_var.get() and self.model_type_var.get() != "Not Found":
            args.extend(["--model_type", self.model_type_var.get()])
        if self.model_name_var.get():
            args.extend(["--model_name", self.model_name_var.get()])

        selected_probes = [name for name, var in self.probe_vars.items() if var.get()]
        if selected_probes: args.extend(["--probes", ",".join(selected_probes)])

        selected_detectors = [name for name, var in self.detector_vars.items() if var.get()]
        if selected_detectors: args.extend(["--detectors", ",".join(selected_detectors)])

        selected_buffs = [name for name, var in self.buff_vars.items() if var.get()]
        if selected_buffs: args.extend(["--buffs", ",".join(selected_buffs)])

        return args

    def start_scan(self):
        """Builds arguments from the UI and starts the Garak scan."""
        self.output_textbox.delete("1.0", "end")
        self.start_button.configure(state="disabled")

        garak_args = self.build_garak_args()

        if not garak_args:
            self.output_textbox.insert("end", "No settings or plugins selected. Please configure a scan.\n")
            self.start_button.configure(state="normal")
            return

        # A model must be selected to run a scan
        if "--model_type" not in garak_args:
            self.output_textbox.insert("end", "Please select a Model Type to run a scan.\n")
            self.start_button.configure(state="normal")
            return

        self.output_textbox.insert("end", f"Running Garak with command:\npython -m garak {' '.join(garak_args)}\n\n")
        self.output_queue = queue.Queue()
        self.garak_thread = threading.Thread(target=run_garak_command, args=(garak_args, self.output_queue))
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
