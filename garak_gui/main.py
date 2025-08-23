import customtkinter
from garak_connector import GarakProcess, get_plugins
from tkinter import filedialog
from tooltip import ToolTip
import queue
import threading
import os
import time
import json

class GarakGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Garak GUI")
        self.geometry("1200x800")

        self.garak_process = GarakProcess()

        # --- Create and store control variables ---
        self._create_control_variables()

        # --- Main Layout ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)

        self.config_tab = self.tab_view.add("Scan Configuration")
        self.output_tab = self.tab_view.add("Scan Output")
        self.reports_tab = self.tab_view.add("Reports")
        self.advanced_tab = self.tab_view.add("Advanced")

        self.config_tab.grid_columnconfigure(0, weight=1)
        self.config_tab.grid_rowconfigure(2, weight=1)

        # --- Create UI Frames ---
        self._create_system_settings_frame()
        self._create_run_settings_frame()
        self._create_plugin_settings_frame()
        self._create_execution_frame()
        self._create_output_tab_widgets()
        self._create_reports_tab_widgets()
        self._create_advanced_tab_widgets()

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
        self.plugin_options = [] # List of tuples (type_var, key_var, val_var)

    def _create_system_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="System Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")

        cb_verbose = customtkinter.CTkCheckBox(frame, text="Verbose Output (-v)", variable=self.verbose_var)
        cb_verbose.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ToolTip(cb_verbose, "Show verbose output. Use -vv for even more.")

        cb_narrow = customtkinter.CTkCheckBox(frame, text="Narrow Output", variable=self.narrow_output_var)
        cb_narrow.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        ToolTip(cb_narrow, "Limit run to probes marked as narrow.")

        cb_skip = customtkinter.CTkCheckBox(frame, text="Skip Unknown Plugins", variable=self.skip_unknown_var)
        cb_skip.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        ToolTip(cb_skip, "Skip unknown plugins instead of erroring.")

        lbl_prefix = customtkinter.CTkLabel(frame, text="Report Prefix")
        lbl_prefix.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_prefix = customtkinter.CTkEntry(frame, textvariable=self.report_prefix_var)
        entry_prefix.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_prefix, "Prefix for report filenames.")
        ToolTip(entry_prefix, "Prefix for report filenames.")

        lbl_reqs = customtkinter.CTkLabel(frame, text="Parallel Requests")
        lbl_reqs.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_reqs = customtkinter.CTkEntry(frame, textvariable=self.parallel_requests_var)
        entry_reqs.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_reqs, "Number of parallel requests to make to the model.")
        ToolTip(entry_reqs, "Number of parallel requests to make to the model.")

        lbl_attempts = customtkinter.CTkLabel(frame, text="Parallel Attempts")
        lbl_attempts.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_attempts = customtkinter.CTkEntry(frame, textvariable=self.parallel_attempts_var)
        entry_attempts.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_attempts, "Number of parallel attempts to run.")
        ToolTip(entry_attempts, "Number of parallel attempts to run.")


    def _create_run_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="Run Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w")

        cb_deprefix = customtkinter.CTkCheckBox(frame, text="Deprefix Output", variable=self.deprefix_var)
        cb_deprefix.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ToolTip(cb_deprefix, "Remove prompt from model output before evaluation.")

        lbl_seed = customtkinter.CTkLabel(frame, text="Random Seed")
        lbl_seed.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_seed = customtkinter.CTkEntry(frame, textvariable=self.seed_var)
        entry_seed.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_seed, "Seed for random number generator.")
        ToolTip(entry_seed, "Seed for random number generator.")

        lbl_thresh = customtkinter.CTkLabel(frame, text="Eval Threshold")
        lbl_thresh.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_thresh = customtkinter.CTkEntry(frame, textvariable=self.eval_threshold_var)
        entry_thresh.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_thresh, "Threshold for detector evaluation.")
        ToolTip(entry_thresh, "Threshold for detector evaluation.")

        lbl_gens = customtkinter.CTkLabel(frame, text="Generations (-g)")
        lbl_gens.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_gens = customtkinter.CTkEntry(frame, textvariable=self.generations_var)
        entry_gens.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_gens, "Number of generations per prompt.")
        ToolTip(entry_gens, "Number of generations per prompt.")

        lbl_config = customtkinter.CTkLabel(frame, text="Config File")
        lbl_config.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_config = customtkinter.CTkEntry(frame, textvariable=self.config_var)
        entry_config.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(lbl_config, "Path to a YAML config file.")
        ToolTip(entry_config, "Path to a YAML config file.")

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

        # Detectors, Buffs, and Options
        plugin_tabs = customtkinter.CTkTabview(frame)
        plugin_tabs.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        detectors_tab = plugin_tabs.add("Detectors")
        detectors_tab.grid_columnconfigure(0, weight=1)
        detectors_tab.grid_rowconfigure(0, weight=1)
        detectors_frame = self._create_plugin_selection_frame(detectors_tab, "detectors", self.detector_vars)
        detectors_frame.grid(row=0, column=0, sticky="nsew")

        buffs_tab = plugin_tabs.add("Buffs")
        buffs_tab.grid_columnconfigure(0, weight=1)
        buffs_tab.grid_rowconfigure(0, weight=1)
        buffs_frame = self._create_plugin_selection_frame(buffs_tab, "buffs", self.buff_vars)
        buffs_frame.grid(row=0, column=0, sticky="nsew")

        options_tab = plugin_tabs.add("Options")
        options_tab.grid_columnconfigure(0, weight=1)
        options_tab.grid_rowconfigure(0, weight=1)
        options_frame = self._create_plugin_options_frame(options_tab)
        options_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)


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

    def _create_plugin_options_frame(self, parent):
        frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(frame, text="Plugin Options", font=customtkinter.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=(5,0), sticky="w")
        customtkinter.CTkLabel(frame, text="Use --[type]_options [key]=[value]", text_color="gray").grid(row=1, column=0, pady=(0,10), sticky="w")

        self.options_scroll_frame = customtkinter.CTkScrollableFrame(frame)
        self.options_scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.options_scroll_frame.grid_columnconfigure([1,2], weight=1)

        add_button = customtkinter.CTkButton(frame, text="Add Option", command=self._add_plugin_option_row)
        add_button.grid(row=3, column=0, pady=10, sticky="w")

        # Add a header row
        header_frame = customtkinter.CTkFrame(self.options_scroll_frame)
        header_frame.pack(fill="x", pady=2)
        header_frame.grid_columnconfigure([1,2,3], weight=1)
        customtkinter.CTkLabel(header_frame, text="Type").grid(row=0, column=0, padx=5)
        customtkinter.CTkLabel(header_frame, text="Key").grid(row=0, column=1, padx=5)
        customtkinter.CTkLabel(header_frame, text="Value").grid(row=0, column=2, padx=5)

        self._add_plugin_option_row() # Start with one empty row

        return frame

    def _add_plugin_option_row(self):
        row_frame = customtkinter.CTkFrame(self.options_scroll_frame)
        row_frame.pack(fill="x", pady=2)
        row_frame.grid_columnconfigure([1,2], weight=1)

        option_type_var = customtkinter.StringVar(value="probe")
        option_key_var = customtkinter.StringVar()
        option_val_var = customtkinter.StringVar()

        self.plugin_options.append((option_type_var, option_key_var, option_val_var))

        customtkinter.CTkOptionMenu(row_frame, variable=option_type_var, values=["probe", "detector", "buff", "generator"]).grid(row=0, column=0, padx=5, pady=2)
        customtkinter.CTkEntry(row_frame, textvariable=option_key_var).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        customtkinter.CTkEntry(row_frame, textvariable=option_val_var).grid(row=0, column=2, padx=5, pady=2, sticky="ew")

        # Ideally, we'd have a remove button here too, but keeping it simple for now.

    def _create_execution_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        frame.grid_columnconfigure([0,1], weight=1)

        self.start_button = customtkinter.CTkButton(frame, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=0, column=0, pady=10, padx=5, sticky="ew")

        self.stop_button = customtkinter.CTkButton(frame, text="Stop Scan", command=self.stop_scan, state="disabled")
        self.stop_button.grid(row=0, column=1, pady=10, padx=5, sticky="ew")

        self.save_button = customtkinter.CTkButton(frame, text="Save Config", command=self.save_config)
        self.save_button.grid(row=1, column=0, pady=10, padx=5, sticky="ew")

        self.load_button = customtkinter.CTkButton(frame, text="Load Config", command=self.load_config)
        self.load_button.grid(row=1, column=1, pady=10, padx=5, sticky="ew")


    def _create_output_tab_widgets(self):
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_reports_tab_widgets(self):
        self.reports_tab.grid_columnconfigure(1, weight=1)
        self.reports_tab.grid_rowconfigure(0, weight=1)

        # Frame for the list of reports
        self.report_list_frame = customtkinter.CTkScrollableFrame(self.reports_tab, width=250)
        self.report_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        customtkinter.CTkLabel(self.report_list_frame, text="Reports", font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=5)


        # Frame for displaying the selected report content
        self.report_content_frame = customtkinter.CTkFrame(self.reports_tab)
        self.report_content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.report_content_frame.grid_rowconfigure(1, weight=1)
        self.report_content_frame.grid_columnconfigure(0, weight=1)

        self.selected_report_label = customtkinter.CTkLabel(self.report_content_frame, text="Select a report to view", font=customtkinter.CTkFont(size=16))
        self.selected_report_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.report_textbox = customtkinter.CTkTextbox(self.report_content_frame)
        self.report_textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,10), sticky="nsew")

        # Buttons frame
        buttons_frame = customtkinter.CTkFrame(self.report_content_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.rerun_button = customtkinter.CTkButton(buttons_frame, text="Re-run Scan", state="disabled", command=self.rerun_scan)
        self.rerun_button.pack(side="left", padx=(0,10))

        self.delete_button = customtkinter.CTkButton(buttons_frame, text="Delete Report", state="disabled", command=self.delete_report)
        self.delete_button.pack(side="left")

        self.selected_report_path = None

        self._start_report_watcher()

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

        # Plugin Options
        for type_var, key_var, val_var in self.plugin_options:
            key = key_var.get()
            val = val_var.get()
            if key and val:
                option_type = type_var.get()
                args.extend([f"--{option_type}_options", f"{key}={val}"])

        return args

    def start_scan(self):
        """Builds arguments from the UI and starts the Garak scan."""
        self.output_textbox.delete("1.0", "end")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

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
        self.garak_thread = threading.Thread(
            target=self.garak_process.run, args=(garak_args, self.output_queue)
        )
        self.garak_thread.daemon = True
        self.garak_thread.start()
        self.after(100, self.process_queue)

    def stop_scan(self):
        """Stops the currently running Garak scan."""
        self.garak_process.stop()
        self.output_textbox.insert("end", "\n\n--- SCAN STOPPED BY USER ---\n")
        self.stop_button.configure(state="disabled")

    def process_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line is None:
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    return
                self.output_textbox.insert("end", line)
                self.output_textbox.see("end")
        except queue.Empty:
            self.after(100, self.process_queue)

    def _start_report_watcher(self):
        self.report_watcher_thread = threading.Thread(target=self._watch_reports)
        self.report_watcher_thread.daemon = True
        self.report_watcher_thread.start()

    def _watch_reports(self):
        runs_dir = "garak_runs"
        if not os.path.exists(runs_dir):
            os.makedirs(runs_dir)

        # Initial population of the list
        for filename in sorted(os.listdir(runs_dir), reverse=True):
             if filename.endswith(".jsonl"):
                filepath = os.path.join(runs_dir, filename)
                self.after(0, self._add_report_to_list, filepath)

        processed_files = set(os.listdir(runs_dir))

        while True:
            try:
                current_files = set(os.listdir(runs_dir))
                new_files = current_files - processed_files
                if new_files:
                    # Clear and rebuild the list to ensure correct order
                    for widget in self.report_list_frame.winfo_children():
                        if isinstance(widget, customtkinter.CTkButton):
                            widget.destroy()
                    for filename in sorted(os.listdir(runs_dir), reverse=True):
                        if filename.endswith(".jsonl"):
                            filepath = os.path.join(runs_dir, filename)
                            self._add_report_to_list(filepath)

                processed_files = current_files
            except Exception as e:
                print(f"Error in report watcher: {e}")
            time.sleep(2)

    def _add_report_to_list(self, filepath):
        filename = os.path.basename(filepath)
        # Using a lambda with a default argument to capture the correct filepath
        report_button = customtkinter.CTkButton(self.report_list_frame, text=filename,
                                                command=lambda fp=filepath: self._display_report(fp))
        report_button.pack(fill="x", padx=5, pady=2)

    def _display_report(self, filepath):
        self.report_textbox.delete("1.0", "end")
        self.selected_report_path = filepath
        self.selected_report_label.configure(text=os.path.basename(filepath))

        try:
            with open(filepath, "r") as f:
                report_data = [json.loads(line) for line in f]
            self.report_textbox.insert("end", json.dumps(report_data, indent=2))
            self.rerun_button.configure(state="normal")
            self.delete_button.configure(state="normal")

        except (IOError, json.JSONDecodeError) as e:
            self.report_textbox.insert("end", f"Error reading report:\n{e}")
            self.rerun_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

    def rerun_scan(self):
        if not self.selected_report_path:
            return

        # This is a simplified re-run. A real implementation would parse the report
        # to extract the original command used. For now, we'll just show a message.
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("end", f"Re-running scan from {os.path.basename(self.selected_report_path)}...\n"
                                          f"(This feature is not fully implemented yet).\n")
        self.tab_view.set("Scan Output")


    def delete_report(self):
        if not self.selected_report_path:
            return

        try:
            os.remove(self.selected_report_path)
            self.report_textbox.delete("1.0", "end")
            self.selected_report_label.configure(text="Select a report to view")
            self.rerun_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            # Refresh the list
            for widget in self.report_list_frame.winfo_children():
                if isinstance(widget, customtkinter.CTkButton) and widget.cget("text") == os.path.basename(self.selected_report_path):
                    widget.destroy()
            self.selected_report_path = None
        except OSError as e:
            self.report_textbox.delete("1.0", "end")
            self.report_textbox.insert("end", f"Error deleting report:\n{e}")


    def _create_advanced_tab_widgets(self):
        self.advanced_tab.grid_columnconfigure(0, weight=1)
        self.advanced_tab.grid_rowconfigure(1, weight=1)

        # --- Plugin Info ---
        plugin_info_frame = customtkinter.CTkFrame(self.advanced_tab)
        plugin_info_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        customtkinter.CTkLabel(plugin_info_frame, text="Plugin Info", font=customtkinter.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.plugin_info_entry = customtkinter.CTkEntry(plugin_info_frame, placeholder_text="e.g., probes.all")
        self.plugin_info_entry.pack(fill="x", padx=10, pady=5)
        customtkinter.CTkButton(plugin_info_frame, text="Get Info", command=self.run_plugin_info).pack(anchor="e", padx=10, pady=5)

        # --- Other Commands ---
        commands_frame = customtkinter.CTkFrame(self.advanced_tab)
        commands_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        customtkinter.CTkButton(commands_frame, text="List Config", command=self.run_list_config).pack(side="left", padx=10, pady=5)
        customtkinter.CTkButton(commands_frame, text="Suggest Fixes", command=self.run_fix).pack(side="left", padx=10, pady=5)

        # --- Output Textbox ---
        self.advanced_output_textbox = customtkinter.CTkTextbox(self.advanced_tab)
        self.advanced_output_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")


    def run_plugin_info(self):
        plugin_name = self.plugin_info_entry.get()
        if not plugin_name:
            self.advanced_output_textbox.delete("1.0", "end")
            self.advanced_output_textbox.insert("end", "Please enter a plugin name.")
            return

        self.advanced_output_textbox.delete("1.0", "end")
        self.advanced_output_textbox.insert("end", f"Getting info for {plugin_name}...\n\n")

        args = ["--plugin_info", plugin_name]
        # We can reuse the garak_process runner, but we need a separate queue
        output_queue = queue.Queue()
        threading.Thread(target=self.garak_process.run, args=(args, output_queue)).start()
        self.after(100, self.process_advanced_queue, output_queue, self.advanced_output_textbox)

    def process_advanced_queue(self, q, textbox):
        try:
            while True:
                line = q.get_nowait()
                if line is None:
                    return
                textbox.insert("end", line)
                textbox.see("end")
        except queue.Empty:
            self.after(100, self.process_advanced_queue, q, textbox)

    def run_list_config(self):
        self.advanced_output_textbox.delete("1.0", "end")
        self.advanced_output_textbox.insert("end", "Listing current config...\n\n")
        args = ["--list_config"]
        output_queue = queue.Queue()
        threading.Thread(target=self.garak_process.run, args=(args, output_queue)).start()
        self.after(100, self.process_advanced_queue, output_queue, self.advanced_output_textbox)

    def run_fix(self):
        self.advanced_output_textbox.delete("1.0", "end")
        self.advanced_output_textbox.insert("end", "Running fix suggestions...\n\n")
        args = ["--fix"]
        output_queue = queue.Queue()
        threading.Thread(target=self.garak_process.run, args=(args, output_queue)).start()
        self.after(100, self.process_advanced_queue, output_queue, self.advanced_output_textbox)


    def save_config(self):
        config_data = {
            # System Settings
            "verbose": self.verbose_var.get(),
            "report_prefix": self.report_prefix_var.get(),
            "narrow_output": self.narrow_output_var.get(),
            "parallel_requests": self.parallel_requests_var.get(),
            "parallel_attempts": self.parallel_attempts_var.get(),
            "skip_unknown": self.skip_unknown_var.get(),
            # Run Settings
            "seed": self.seed_var.get(),
            "deprefix": self.deprefix_var.get(),
            "eval_threshold": self.eval_threshold_var.get(),
            "generations": self.generations_var.get(),
            "config": self.config_var.get(),
            # Plugin Settings
            "model_type": self.model_type_var.get(),
            "model_name": self.model_name_var.get(),
            "probes": [name for name, var in self.probe_vars.items() if var.get()],
            "detectors": [name for name, var in self.detector_vars.items() if var.get()],
            "buffs": [name for name, var in self.buff_vars.items() if var.get()],
            "plugin_options": [(t.get(), k.get(), v.get()) for t,k,v in self.plugin_options if k.get() and v.get()]
        }

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Garak Configuration"
        )
        if not filepath:
            return

        with open(filepath, "w") as f:
            json.dump(config_data, f, indent=2)

    def load_config(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Garak Configuration"
        )
        if not filepath:
            return

        with open(filepath, "r") as f:
            config_data = json.load(f)

        # System Settings
        self.verbose_var.set(config_data.get("verbose", False))
        self.report_prefix_var.set(config_data.get("report_prefix", ""))
        self.narrow_output_var.set(config_data.get("narrow_output", False))
        self.parallel_requests_var.set(config_data.get("parallel_requests", ""))
        self.parallel_attempts_var.set(config_data.get("parallel_attempts", ""))
        self.skip_unknown_var.set(config_data.get("skip_unknown", False))
        # Run Settings
        self.seed_var.set(config_data.get("seed", ""))
        self.deprefix_var.set(config_data.get("deprefix", True))
        self.eval_threshold_var.set(config_data.get("eval_threshold", "0.5"))
        self.generations_var.set(config_data.get("generations", "10"))
        self.config_var.set(config_data.get("config", ""))
        # Plugin Settings
        self.model_type_var.set(config_data.get("model_type", ""))
        self.model_name_var.set(config_data.get("model_name", ""))

        for name, var in self.probe_vars.items():
            var.set(name in config_data.get("probes", []))
        for name, var in self.detector_vars.items():
            var.set(name in config_data.get("detectors", []))
        for name, var in self.buff_vars.items():
            var.set(name in config_data.get("buffs", []))

        # Clear existing option rows
        for widget in self.options_scroll_frame.winfo_children():
            if isinstance(widget, customtkinter.CTkFrame):
                widget.destroy()
        self.plugin_options.clear()

        # Add loaded options
        for t, k, v in config_data.get("plugin_options", []):
            self._add_plugin_option_row()
            type_var, key_var, val_var = self.plugin_options[-1]
            type_var.set(t)
            key_var.set(k)
            val_var.set(v)


if __name__ == "__main__":
    app = GarakGUI()
    app.mainloop()
