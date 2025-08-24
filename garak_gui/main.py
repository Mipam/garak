import customtkinter
from garak_connector import run_garak_command, get_plugins
from PIL import Image, ImageTk
import queue
import threading
import tkinter
from tkinter import filedialog
import os
import glob
import json

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tkinter.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tkinter.Label(self.tooltip_window, text=self.text, justify='left',
                              background="#2b2b2b", relief='solid', borderwidth=1,
                              wraplength=200, fg="white", font=("Arial", 10))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

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

        self.refresh_reports()

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
        self.garak_process = None
        self.generator_options_var = customtkinter.StringVar()
        self.probe_options_var = customtkinter.StringVar()
        self.detector_options_var = customtkinter.StringVar()
        self.buff_options_var = customtkinter.StringVar()

    def _create_system_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="System Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")

        verbose_cb = customtkinter.CTkCheckBox(frame, text="Verbose Output (-v)", variable=self.verbose_var)
        verbose_cb.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        Tooltip(verbose_cb, "Print verbose output. Use -vv for even more.")

        narrow_cb = customtkinter.CTkCheckBox(frame, text="Narrow Output", variable=self.narrow_output_var)
        narrow_cb.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        Tooltip(narrow_cb, "Don't show successful probes in the report.")

        skip_cb = customtkinter.CTkCheckBox(frame, text="Skip Unknown Plugins", variable=self.skip_unknown_var)
        skip_cb.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        Tooltip(skip_cb, "Skip plugins that garak doesn't know about.")

        customtkinter.CTkLabel(frame, text="Report Prefix").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        report_prefix_entry = customtkinter.CTkEntry(frame, textvariable=self.report_prefix_var)
        report_prefix_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        Tooltip(report_prefix_entry, "Specify a prefix for the report filename.")

        customtkinter.CTkLabel(frame, text="Parallel Requests").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        parallel_requests_entry = customtkinter.CTkEntry(frame, textvariable=self.parallel_requests_var)
        parallel_requests_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        Tooltip(parallel_requests_entry, "Number of parallel requests to make to the generator (default 10).")

        customtkinter.CTkLabel(frame, text="Parallel Attempts").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        parallel_attempts_entry = customtkinter.CTkEntry(frame, textvariable=self.parallel_attempts_var)
        parallel_attempts_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        Tooltip(parallel_attempts_entry, "Number of parallel attempts to make per probe (default 1).")

        customtkinter.CTkLabel(frame, text="Report File").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.report_file_var = customtkinter.StringVar()
        report_file_entry = customtkinter.CTkEntry(frame, textvariable=self.report_file_var)
        report_file_entry.grid(row=5, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        Tooltip(report_file_entry, "Specify a file to write the report to (e.g. report.avid.json).")

        customtkinter.CTkLabel(frame, text="Taxonomy").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.taxonomy_var = customtkinter.StringVar()
        taxonomy_entry = customtkinter.CTkEntry(frame, textvariable=self.taxonomy_var)
        taxonomy_entry.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        Tooltip(taxonomy_entry, "Specify the MISP taxonomy to use for the report.")

    def _create_run_settings_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(frame, text="Run Settings", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w")

        deprefix_cb = customtkinter.CTkCheckBox(frame, text="Deprefix Output", variable=self.deprefix_var)
        deprefix_cb.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        Tooltip(deprefix_cb, "Deprefix model output. Default is True. Use --no-deprefix to disable.")

        customtkinter.CTkLabel(frame, text="Random Seed").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        seed_entry = customtkinter.CTkEntry(frame, textvariable=self.seed_var)
        seed_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        Tooltip(seed_entry, "Set the random seed for the run.")

        customtkinter.CTkLabel(frame, text="Eval Threshold").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        eval_threshold_entry = customtkinter.CTkEntry(frame, textvariable=self.eval_threshold_var)
        eval_threshold_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        Tooltip(eval_threshold_entry, "The threshold for detectors to pass (default 0.5).")

        customtkinter.CTkLabel(frame, text="Generations (-g)").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        generations_entry = customtkinter.CTkEntry(frame, textvariable=self.generations_var)
        generations_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        Tooltip(generations_entry, "The number of generations to run for each probe (default 10).")

        customtkinter.CTkLabel(frame, text="Config File").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        config_entry = customtkinter.CTkEntry(frame, textvariable=self.config_var)
        config_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        Tooltip(config_entry, "Load a YAML config file.")

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
        model_type_menu = customtkinter.CTkOptionMenu(model_frame, variable=self.model_type_var, values=generators)
        model_type_menu.pack(fill="x")
        Tooltip(model_type_menu, "The type of model to test (e.g. openai, huggingface).")
        customtkinter.CTkLabel(model_frame, text="Model Name:").pack(anchor="w", pady=(10,0))
        model_name_entry = customtkinter.CTkEntry(model_frame, textvariable=self.model_name_var)
        model_name_entry.pack(fill="x")
        Tooltip(model_name_entry, "The name of the model to test (e.g. gpt-4, meta-llama/Llama-2-7b-chat-hf).")

        # Probes
        probes_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        probes_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        probes_frame.grid_rowconfigure(1, weight=1)
        probes_frame.grid_columnconfigure(0, weight=1)

        probes_sub_frame = customtkinter.CTkFrame(probes_frame)
        probes_sub_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        probes_sub_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(probes_sub_frame, text="Filter by Tags:").grid(row=0, column=0, padx=5, pady=5)
        self.probe_tags_var = customtkinter.StringVar()
        probe_tags_entry = customtkinter.CTkEntry(probes_sub_frame, textvariable=self.probe_tags_var)
        probe_tags_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        Tooltip(probe_tags_entry, "Filter probes by tags, comma-separated.")

        probes_selection_frame = self._create_plugin_selection_frame(probes_frame, "probes", self.probe_vars)
        probes_selection_frame.grid(row=1, column=0, padx=0, pady=5, sticky="nsew")


        # Detectors & Buffs
        sub_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
        sub_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        sub_frame.grid_columnconfigure(0, weight=1)
        sub_frame.grid_rowconfigure([0,2], weight=1)

        detectors_frame = self._create_plugin_selection_frame(sub_frame, "detectors", self.detector_vars)
        detectors_frame.grid(row=0, column=0, sticky="nsew")

        self.extended_detectors_var = customtkinter.BooleanVar()
        extended_detectors_cb = customtkinter.CTkCheckBox(sub_frame, text="Extended Detectors", variable=self.extended_detectors_var)
        extended_detectors_cb.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        Tooltip(extended_detectors_cb, "Use extended detectors.")

        buffs_frame = self._create_plugin_selection_frame(sub_frame, "buffs", self.buff_vars)
        buffs_frame.grid(row=1, column=0, sticky="nsew", pady=(10,0))

        # Plugin Options
        options_frame = customtkinter.CTkFrame(frame)
        options_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        customtkinter.CTkLabel(options_frame, text="Plugin Options (key=value, space-separated)", font=customtkinter.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        self._create_option_file_picker(options_frame, "Generator", self.generator_options_var)
        self._create_option_file_picker(options_frame, "Probe", self.probe_options_var)
        self._create_option_file_picker(options_frame, "Detector", self.detector_options_var)
        self._create_option_file_picker(options_frame, "Buff", self.buff_options_var)

    def _create_option_file_picker(self, parent, name, var):
        frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(frame, text=f"{name} Options:").grid(row=0, column=0, sticky="w")
        entry = customtkinter.CTkEntry(frame, textvariable=var)
        entry.grid(row=1, column=0, sticky="ew")
        Tooltip(entry, f"Options for {name.lower()}s, in key=value format, separated by spaces.")

        button = customtkinter.CTkButton(frame, text="Load File...", width=100, command=lambda: self.load_option_file(var))
        button.grid(row=1, column=1, padx=(10,0))


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
        frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        frame.grid_columnconfigure([0,1], weight=1)

        self.start_button = customtkinter.CTkButton(frame, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.stop_button = customtkinter.CTkButton(frame, text="Stop Scan", command=self.stop_scan, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(frame, orientation="horizontal")
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        self.progress_bar.set(0)


        # Config Preset Buttons
        preset_frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        preset_frame.grid(row=4, column=0, pady=10, padx=10, sticky="ew")
        preset_frame.grid_columnconfigure([0,1], weight=1)
        self.load_button = customtkinter.CTkButton(preset_frame, text="Load Config", command=self.load_config)
        self.load_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.save_button = customtkinter.CTkButton(preset_frame, text="Save Config", command=self.save_config)
        self.save_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _create_output_tab_widgets(self):
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_reports_tab_widgets(self):
        self.reports_tab.grid_columnconfigure(0, weight=1)
        self.reports_tab.grid_rowconfigure(1, weight=1)

        # Top frame for controls
        top_frame = customtkinter.CTkFrame(self.reports_tab)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.refresh_reports_button = customtkinter.CTkButton(top_frame, text="Refresh Reports", command=self.refresh_reports)
        self.refresh_reports_button.pack(side="left", padx=(0, 10))
        self.delete_report_button = customtkinter.CTkButton(top_frame, text="Delete Report", command=self.delete_report, state="disabled")
        self.delete_report_button.pack(side="left", padx=(0, 10))
        self.rerun_scan_button = customtkinter.CTkButton(top_frame, text="Re-run Scan", command=self.rerun_scan, state="disabled")
        self.rerun_scan_button.pack(side="left")


        # Main frame with two panes
        main_frame = customtkinter.CTkFrame(self.reports_tab, fg_color="transparent")
        main_frame.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left pane for report list
        report_list_frame = customtkinter.CTkFrame(main_frame)
        report_list_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        report_list_frame.grid_rowconfigure(0, weight=1)
        report_list_frame.grid_columnconfigure(0, weight=1)
        self.report_listbox = tkinter.Listbox(report_list_frame, bg="#2b2b2b", fg="white", highlightthickness=0, selectbackground="#1f6aa5")
        self.report_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.report_listbox.bind("<<ListboxSelect>>", self.on_report_selected)
        self.report_listbox.bind("<FocusOut>", self.on_report_deselected)


        # Right pane for report content
        report_content_frame = customtkinter.CTkFrame(main_frame)
        report_content_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        report_content_frame.grid_rowconfigure(0, weight=1)
        report_content_frame.grid_columnconfigure(0, weight=1)
        self.report_content_textbox = customtkinter.CTkTextbox(report_content_frame)
        self.report_content_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.report_content_textbox.configure(state="disabled")

    def build_garak_args(self):
        """Builds a list of command-line arguments from all UI settings."""
        args = []
        # System Settings
        if self.verbose_var.get(): args.append("-v")
        if self.report_prefix_var.get(): args.extend(["--report_prefix", self.report_prefix_var.get()])
        if self.report_file_var.get(): args.extend(["--report", self.report_file_var.get()])
        if self.taxonomy_var.get(): args.extend(["--taxonomy", self.taxonomy_var.get()])
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

        if self.probe_tags_var.get():
            args.extend(["--probe_tags", self.probe_tags_var.get()])

        selected_detectors = [name for name, var in self.detector_vars.items() if var.get()]
        if selected_detectors: args.extend(["--detectors", ",".join(selected_detectors)])
        if self.extended_detectors_var.get(): args.append("--extended_detectors")

        selected_buffs = [name for name, var in self.buff_vars.items() if var.get()]
        if selected_buffs: args.extend(["--buffs", ",".join(selected_buffs)])

        # Plugin Options
        self._add_plugin_options_args(args, "generator", self.generator_options_var)
        self._add_plugin_options_args(args, "probe", self.probe_options_var)
        self._add_plugin_options_args(args, "detector", self.detector_options_var)
        self._add_plugin_options_args(args, "buff", self.buff_options_var)

        return args

    def _add_plugin_options_args(self, args, name, var):
        value = var.get()
        if not value:
            return

        # Check if the value is a file path
        if os.path.isfile(value):
            args.extend([f"--{name}_option_file", value])
        else:
            args.extend([f"--{name}_options", value])

    def start_scan(self):
        """Builds arguments from the UI and starts the Garak scan."""
        self.output_textbox.delete("1.0", "end")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        garak_args = self.build_garak_args()

        if not garak_args:
            self.output_textbox.insert("end", "No settings or plugins selected. Please configure a scan.\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return

        # A model must be selected to run a scan
        if "--model_type" not in garak_args:
            self.output_textbox.insert("end", "Please select a Model Type to run a scan.\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return

        self.output_textbox.insert("end", f"Running Garak with command:\npython -m garak {' '.join(garak_args)}\n\n")
        self.progress_bar.start()
        self.output_queue = queue.Queue()
        self.garak_thread = threading.Thread(target=self.run_garak_thread, args=(garak_args, self.output_queue))
        self.garak_thread.daemon = True
        self.garak_thread.start()
        self.after(100, self.process_queue)

    def run_garak_thread(self, args, q):
        self.garak_process = run_garak_command(args, q)

    def stop_scan(self):
        """Stops the currently running Garak scan."""
        if self.garak_process and self.garak_process.poll() is None:
            self.garak_process.terminate()
            self.output_queue.put("\n\n--- SCAN TERMINATED BY USER ---\n")
        self.stop_button.configure(state="disabled")


    def process_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line is None: # Sentinel value
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.garak_process = None
                    self.progress_bar.stop()
                    self.progress_bar.set(0)
                    return
                self.output_textbox.insert("end", line)
                self.output_textbox.see("end")
        except queue.Empty:
            if self.garak_thread.is_alive():
                self.after(100, self.process_queue)
            else: # Thread finished, but sentinel not yet received
                self.after(100, self.process_queue)


    def refresh_reports(self):
        self.report_listbox.delete(0, "end")
        self.report_content_textbox.configure(state="normal")
        self.report_content_textbox.delete("1.0", "end")
        self.report_content_textbox.configure(state="disabled")

        report_files = glob.glob("garak_*.jsonl")
        for report_file in sorted(report_files, key=os.path.getmtime, reverse=True):
            self.report_listbox.insert("end", report_file)

    def on_report_selected(self, event):
        selection = event.widget.curselection()
        if not selection:
            return

        self.delete_report_button.configure(state="normal")
        self.rerun_scan_button.configure(state="normal")

        selected_report = event.widget.get(selection[0])

        self.report_content_textbox.configure(state="normal")
        self.report_content_textbox.delete("1.0", "end")

        try:
            with open(selected_report, "r") as f:
                # Read and pretty-print each JSON object line by line
                for line in f:
                    try:
                        json_obj = json.loads(line)
                        pretty_json = json.dumps(json_obj, indent=4)
                        self.report_content_textbox.insert("end", pretty_json + "\n")
                    except json.JSONDecodeError:
                        self.report_content_textbox.insert("end", line) # Insert as is if not valid JSON
        except Exception as e:
            self.report_content_textbox.insert("end", f"Error reading report file: {e}")

        self.report_content_textbox.configure(state="disabled")

    def on_report_deselected(self, event):
        self.report_listbox.selection_clear(0, "end")
        self.delete_report_button.configure(state="disabled")
        self.rerun_scan_button.configure(state="disabled")

    def delete_report(self):
        selection = self.report_listbox.curselection()
        if not selection:
            return

        selected_report = self.report_listbox.get(selection[0])
        try:
            os.remove(selected_report)
            self.refresh_reports()
        except Exception as e:
            self.output_textbox.insert("end", f"Error deleting report file: {e}\n")

    def rerun_scan(self):
        selection = self.report_listbox.curselection()
        if not selection:
            return

        selected_report = self.report_listbox.get(selection[0])
        try:
            with open(selected_report, "r") as f:
                first_line = f.readline()
                report_data = json.loads(first_line)
                config = report_data.get("config")
                if not config:
                    self.output_textbox.insert("end", "Could not find config in report file.\n")
                    return

                # This is a bit of a simplification. We should ideally load the config
                # into the UI, but for now, we'll just build the args and run the scan.
                self.load_config_from_dict(config)
                self.start_scan()
                self.tab_view.set("Scan Output")

        except Exception as e:
            self.output_textbox.insert("end", f"Error re-running scan: {e}\n")

    def _create_advanced_tab_widgets(self):
        self.advanced_tab.grid_columnconfigure(0, weight=1)

        frame = customtkinter.CTkFrame(self.advanced_tab)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(frame, text="Advanced Commands", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")

        # Plugin Info
        customtkinter.CTkButton(frame, text="Plugin Info", command=lambda: self.run_advanced_command("--plugin_info")).grid(row=1, column=0, padx=10, pady=5)

        # List Config
        customtkinter.CTkButton(frame, text="List Config", command=lambda: self.run_advanced_command("--list_config")).grid(row=2, column=0, padx=10, pady=5)

        # Fix
        customtkinter.CTkButton(frame, text="Fix", command=lambda: self.run_advanced_command("--fix")).grid(row=3, column=0, padx=10, pady=5)

        self.advanced_args_var = customtkinter.StringVar()
        customtkinter.CTkEntry(frame, textvariable=self.advanced_args_var, placeholder_text="Enter arguments for command...").grid(row=1, column=1, rowspan=3, padx=10, pady=5, sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)

    def run_advanced_command(self, command):
        """Runs an advanced garak command."""
        self.output_textbox.delete("1.0", "end")
        self.tab_view.set("Scan Output")

        args = [command]
        if self.advanced_args_var.get():
            args.extend(self.advanced_args_var.get().split())

        self.output_textbox.insert("end", f"Running Garak with command:\npython -m garak {' '.join(args)}\n\n")

        # Since these are usually quick, we can run them in a simple thread
        # and not worry about stopping them. A more robust implementation
        # might reuse the main scan infrastructure.
        def command_thread():
            try:
                output = subprocess.check_output(["python", "-m", "garak"] + args, text=True, stderr=subprocess.STDOUT)
                self.output_textbox.insert("end", output)
            except subprocess.CalledProcessError as e:
                self.output_textbox.insert("end", e.output)
            except Exception as e:
                self.output_textbox.insert("end", f"An error occurred: {str(e)}")

        thread = threading.Thread(target=command_thread)
        thread.daemon = True
        thread.start()


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
            "config_file": self.config_var.get(),
            # Plugin Settings
            "model_type": self.model_type_var.get(),
            "model_name": self.model_name_var.get(),
            "probes": [name for name, var in self.probe_vars.items() if var.get()],
            "detectors": [name for name, var in self.detector_vars.items() if var.get()],
            "buffs": [name for name, var in self.buff_vars.items() if var.get()],
            # Plugin Options
            "generator_options": self.generator_options_var.get(),
            "probe_options": self.probe_options_var.get(),
            "detector_options": self.detector_options_var.get(),
            "buff_options": self.buff_options_var.get(),
        }

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Garak Configuration"
        )
        if not filepath:
            return

        with open(filepath, "w") as f:
            json.dump(config_data, f, indent=4)

    def load_config(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Garak Configuration"
        )
        if not filepath:
            return

        with open(filepath, "r") as f:
            config_data = json.load(f)

        self.load_config_from_dict(config_data)

    def load_config_from_dict(self, config_data):
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
        self.config_var.set(config_data.get("config_file", ""))
        # Plugin Settings
        self.model_type_var.set(config_data.get("model_type", ""))
        self.model_name_var.set(config_data.get("model_name", ""))

        for name, var in self.probe_vars.items():
            var.set(name in config_data.get("probes", []))
        for name, var in self.detector_vars.items():
            var.set(name in config_data.get("detectors", []))
        for name, var in self.buff_vars.items():
            var.set(name in config_data.get("buffs", []))

        # Plugin Options
        self.generator_options_var.set(config_data.get("generator_options", ""))
        self.probe_options_var.set(config_data.get("probe_options", ""))
        self.detector_options_var.set(config_data.get("detector_options", ""))
        self.buff_options_var.set(config_data.get("buff_options", ""))

    def load_option_file(self, var):
        filepath = filedialog.askopenfilename(
            title="Select an option file",
            filetypes=[("All files", "*.*")]
        )
        if filepath:
            var.set(filepath)


if __name__ == "__main__":
    app = GarakGUI()
    app.mainloop()
