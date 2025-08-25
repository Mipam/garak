import customtkinter
from garak_connector import run_garak_command, get_plugins, start_interactive_process
from PIL import Image, ImageTk
import queue
import threading
import tkinter
from tkinter import filedialog, messagebox
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
        self.interactive_tab = self.tab_view.add("Interactive")
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
        self._create_interactive_tab_widgets()
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
        self.interactive_process = None
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

        # Plugin Options
        options_frame = customtkinter.CTkFrame(frame)
        options_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        customtkinter.CTkLabel(options_frame, text="Plugin Options (key=value, space-separated)", font=customtkinter.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        customtkinter.CTkLabel(options_frame, text="Generator Options:").pack(anchor="w", padx=10)
        generator_options_entry = customtkinter.CTkEntry(options_frame, textvariable=self.generator_options_var)
        generator_options_entry.pack(fill="x", padx=10, pady=(0,5))
        Tooltip(generator_options_entry, "Options for the generator, in key=value format, separated by spaces.")

        customtkinter.CTkLabel(options_frame, text="Probe Options:").pack(anchor="w", padx=10)
        probe_options_entry = customtkinter.CTkEntry(options_frame, textvariable=self.probe_options_var)
        probe_options_entry.pack(fill="x", padx=10, pady=(0,5))
        Tooltip(probe_options_entry, "Options for probes, in key=value format, separated by spaces.")

        customtkinter.CTkLabel(options_frame, text="Detector Options:").pack(anchor="w", padx=10)
        detector_options_entry = customtkinter.CTkEntry(options_frame, textvariable=self.detector_options_var)
        detector_options_entry.pack(fill="x", padx=10, pady=(0,5))
        Tooltip(detector_options_entry, "Options for detectors, in key=value format, separated by spaces.")

        customtkinter.CTkLabel(options_frame, text="Buff Options:").pack(anchor="w", padx=10)
        buff_options_entry = customtkinter.CTkEntry(options_frame, textvariable=self.buff_options_var)
        buff_options_entry.pack(fill="x", padx=10, pady=(0,10))
        Tooltip(buff_options_entry, "Options for buffs, in key=value format, separated by spaces.")


    def _create_plugin_selection_frame(self, parent, plugin_type, var_dict):
        frame = customtkinter.CTkFrame(parent)
        frame.pack_propagate(False)
        customtkinter.CTkLabel(frame, text=plugin_type.title(), font=customtkinter.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        search_entry = customtkinter.CTkEntry(frame, placeholder_text=f"Search {plugin_type}...")
        search_entry.pack(fill="x", padx=10, pady=(0, 5))

        scroll_frame = customtkinter.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        plugin_list = get_plugins(plugin_type)

        checkboxes = []
        if not plugin_list:
            customtkinter.CTkLabel(scroll_frame, text=f"No {plugin_type} found.").pack()
        else:
            for plugin_name in plugin_list:
                var = customtkinter.BooleanVar()
                cb = customtkinter.CTkCheckBox(scroll_frame, text=plugin_name, variable=var)
                cb.pack(anchor="w", padx=5)
                var_dict[plugin_name] = var
                checkboxes.append(cb)

        def filter_plugins(event=None):
            search_term = search_entry.get().lower()
            for cb in checkboxes:
                if search_term in cb.cget("text").lower():
                    cb.pack(anchor="w", padx=5)
                else:
                    cb.pack_forget()

        search_entry.bind("<KeyRelease>", filter_plugins)

        return frame

    def _create_execution_frame(self):
        frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        frame.grid_columnconfigure([0,1], weight=1)

        self.start_button = customtkinter.CTkButton(frame, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        Tooltip(self.start_button, "Start the scan with the current configuration.")

        self.stop_button = customtkinter.CTkButton(frame, text="Stop Scan", command=self.stop_scan, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        Tooltip(self.stop_button, "Stop the currently running scan.")

        # Config Preset Buttons
        preset_frame = customtkinter.CTkFrame(self.config_tab, fg_color="transparent")
        preset_frame.grid(row=4, column=0, pady=10, padx=10, sticky="ew")
        preset_frame.grid_columnconfigure([0,1], weight=1)
        self.load_button = customtkinter.CTkButton(preset_frame, text="Load Config", command=self.load_config)
        self.load_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        Tooltip(self.load_button, "Load a scan configuration from a JSON file.")
        self.save_button = customtkinter.CTkButton(preset_frame, text="Save Config", command=self.save_config)
        self.save_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        Tooltip(self.save_button, "Save the current scan configuration to a JSON file.")

    def _create_output_tab_widgets(self):
        self.output_textbox = customtkinter.CTkTextbox(self.output_tab)
        self.output_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    def _create_reports_tab_widgets(self):
        self.reports_tab.grid_columnconfigure(0, weight=1)
        self.reports_tab.grid_rowconfigure(1, weight=1)

        # Top frame for controls
        top_frame = customtkinter.CTkFrame(self.reports_tab)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.refresh_reports_button = customtkinter.CTkButton(top_frame, text="Refresh", command=self.refresh_reports)
        self.refresh_reports_button.pack(side="left", padx=(0, 10))
        Tooltip(self.refresh_reports_button, "Refresh the list of reports.")
        self.load_rerun_button = customtkinter.CTkButton(top_frame, text="Load for Re-run", command=self.load_report_for_rerun)
        self.load_rerun_button.pack(side="left", padx=(0, 10))
        Tooltip(self.load_rerun_button, "Load the configuration from the selected report.")
        self.delete_report_button = customtkinter.CTkButton(top_frame, text="Delete Report", command=self.delete_report, fg_color="dark red", hover_color="red")
        self.delete_report_button.pack(side="left", padx=(0, 10))
        Tooltip(self.delete_report_button, "Delete the selected report.")

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
        if self.generator_options_var.get(): args.extend(["--generator_options", self.generator_options_var.get()])
        if self.probe_options_var.get(): args.extend(["--probe_options", self.probe_options_var.get()])
        if self.detector_options_var.get(): args.extend(["--detector_options", self.detector_options_var.get()])
        if self.buff_options_var.get(): args.extend(["--buff_options", self.buff_options_var.get()])

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
            self.stop_button.configure(state="disabled")
            return

        # A model must be selected to run a scan
        if "--model_type" not in garak_args:
            self.output_textbox.insert("end", "Please select a Model Type to run a scan.\n")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return

        self.output_textbox.insert("end", f"Running Garak with command:\npython -m garak {' '.join(garak_args)}\n\n")
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

    def delete_report(self):
        selection = self.report_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Report Selected", "Please select a report to delete.")
            return

        selected_report = self.report_listbox.get(selection[0])

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {selected_report}?"):
            try:
                os.remove(selected_report)
                self.refresh_reports()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete report: {e}")

    def load_report_for_rerun(self):
        selection = self.report_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Report Selected", "Please select a report to load.")
            return

        selected_report = self.report_listbox.get(selection[0])

        try:
            with open(selected_report, "r") as f:
                first_line = f.readline()
                if not first_line:
                    raise ValueError("Report file is empty.")
                config_data = json.loads(first_line)
                if config_data.get("entry_type") != "config":
                    raise ValueError("The first line of the report is not a config entry.")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Report file not found: {selected_report}")
            return
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Failed to parse JSON from report config: {selected_report}")
            return
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid report file: {e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while reading the report: {e}")
            return

        # System Settings
        self.verbose_var.set(config_data.get("_config.system.verbose", False))
        self.report_prefix_var.set(config_data.get("_config.reporting.report_prefix", ""))
        self.narrow_output_var.set(config_data.get("_config.system.narrow_output", False))
        self.parallel_requests_var.set(str(config_data.get("_config.system.parallel_requests", "")))
        self.parallel_attempts_var.set(str(config_data.get("_config.system.parallel_attempts", "")))
        self.skip_unknown_var.set(config_data.get("_config.system.skip_unknown", False))

        # Run Settings
        self.seed_var.set(str(config_data.get("_config.run.seed", "")))
        self.deprefix_var.set(config_data.get("_config.run.deprefix", True))
        self.eval_threshold_var.set(str(config_data.get("_config.run.eval_threshold", "0.5")))
        self.generations_var.set(str(config_data.get("_config.run.generations", "10")))
        self.config_var.set(config_data.get("_config.run.config", ""))

        # Plugin Settings
        self.model_type_var.set(config_data.get("_config.plugins.model_type", ""))
        self.model_name_var.set(config_data.get("_config.plugins.model_name", ""))

        probes = config_data.get("_config.plugins.probe_spec", "").split(',')
        for name, var in self.probe_vars.items():
            var.set(name in probes)

        detectors = config_data.get("_config.plugins.detector_spec", "").split(',')
        for name, var in self.detector_vars.items():
            var.set(name in detectors)

        buffs = config_data.get("_config.plugins.buff_spec", "").split(',')
        for name, var in self.buff_vars.items():
            var.set(name in buffs)

        # Plugin Options - These aren't stored in the config entry, so we clear them
        self.generator_options_var.set("")
        self.probe_options_var.set("")
        self.detector_options_var.set("")
        self.buff_options_var.set("")

        messagebox.showinfo("Config Loaded", "Report configuration loaded. Check the 'Scan Configuration' tab.")
        self.tab_view.set("Scan Configuration")

    def _create_interactive_tab_widgets(self):
        self.interactive_tab.grid_columnconfigure(0, weight=1)
        self.interactive_tab.grid_rowconfigure(0, weight=1)

        self.interactive_textbox = customtkinter.CTkTextbox(self.interactive_tab)
        self.interactive_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.interactive_textbox.configure(state="disabled")

        self.interactive_entry = customtkinter.CTkEntry(self.interactive_tab, placeholder_text="Enter command...")
        self.interactive_entry.grid(row=1, column=0, padx=(10, 0), pady=10, sticky="ew")
        self.interactive_entry.bind("<Return>", self.send_interactive_command)
        Tooltip(self.interactive_entry, "Enter a command to send to the interactive garak session.")

        self.interactive_send_button = customtkinter.CTkButton(self.interactive_tab, text="Send", command=self.send_interactive_command, state="disabled")
        self.interactive_send_button.grid(row=1, column=1, padx=(10, 10), pady=10, sticky="e")
        Tooltip(self.interactive_send_button, "Send the command to the interactive garak session.")

        self.start_interactive_button = customtkinter.CTkButton(self.interactive_tab, text="Start Interactive Session", command=self.start_interactive_session)
        self.start_interactive_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        Tooltip(self.start_interactive_button, "Start a new interactive garak session.")

    def start_interactive_session(self):
        self.interactive_textbox.configure(state="normal")
        self.interactive_textbox.delete("1.0", "end")
        self.start_interactive_button.configure(state="disabled")
        self.interactive_send_button.configure(state="normal")

        self.interactive_queue = queue.Queue()
        self.interactive_process = start_interactive_process(self.interactive_queue)

        if self.interactive_process:
            self.after(100, self.process_interactive_queue)
        else:
            self.start_interactive_button.configure(state="normal")
            self.interactive_send_button.configure(state="disabled")

    def send_interactive_command(self, event=None):
        command = self.interactive_entry.get()
        if command and self.interactive_process and self.interactive_process.poll() is None:
            self.interactive_process.stdin.write(command + "\n")
            self.interactive_process.stdin.flush()
            self.interactive_entry.delete(0, "end")

    def process_interactive_queue(self):
        try:
            while True:
                line = self.interactive_queue.get_nowait()
                if line is None: # Sentinel value
                    self.interactive_textbox.insert("end", "\n--- INTERACTIVE SESSION ENDED ---\n")
                    self.start_interactive_button.configure(state="normal")
                    self.interactive_send_button.configure(state="disabled")
                    self.interactive_process = None
                    return
                self.interactive_textbox.insert("end", line)
                self.interactive_textbox.see("end")
        except queue.Empty:
            if self.interactive_process and self.interactive_process.poll() is None:
                self.after(100, self.process_interactive_queue)
            else: # Process died
                self.after(100, self.process_interactive_queue) # one last check

    def _create_advanced_tab_widgets(self):
        self.advanced_tab.grid_columnconfigure(0, weight=1)

        frame = customtkinter.CTkFrame(self.advanced_tab)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(frame, text="Advanced Commands", font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(5, 10), sticky="w")

        # Plugin Info
        plugin_info_button = customtkinter.CTkButton(frame, text="Plugin Info", command=lambda: self.run_advanced_command("--plugin_info"))
        plugin_info_button.grid(row=1, column=0, padx=10, pady=5)
        Tooltip(plugin_info_button, "Get information about a specific plugin.")

        # List Config
        list_config_button = customtkinter.CTkButton(frame, text="List Config", command=lambda: self.run_advanced_command("--list_config"))
        list_config_button.grid(row=2, column=0, padx=10, pady=5)
        Tooltip(list_config_button, "Print the current configuration.")

        # Fix
        fix_button = customtkinter.CTkButton(frame, text="Fix", command=lambda: self.run_advanced_command("--fix"))
        fix_button.grid(row=3, column=0, padx=10, pady=5)
        Tooltip(fix_button, "Try to fix a misconfigured plugin.")

        self.advanced_args_var = customtkinter.StringVar()
        advanced_args_entry = customtkinter.CTkEntry(frame, textvariable=self.advanced_args_var, placeholder_text="Enter arguments for command...")
        advanced_args_entry.grid(row=1, column=1, rowspan=3, padx=10, pady=5, sticky="nsew")
        Tooltip(advanced_args_entry, "Enter any additional arguments for the selected advanced command.")
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


def main():
    app = GarakGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
