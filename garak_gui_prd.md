# Product Requirements Document: Garak GUI

## 1. Introduction

This document outlines the product requirements for a graphical user interface (GUI) for the Garak LLM vulnerability scanner. Garak is a powerful command-line tool for evaluating the security and safety of large language models (LLMs). A GUI will make Garak more accessible to a broader audience, including security professionals, researchers, and developers who may not be comfortable with a command-line interface. The GUI will provide a user-friendly way to configure and run Garak scans, view results, and manage reports.

## 2. Goals and Objectives

*   **Improve Usability:** Provide an intuitive and user-friendly interface for Garak, reducing the learning curve for new users.
*   **Full Feature Support:** Expose all of Garak's command-line functionality through the GUI.
*   **Streamline Workflow:** Simplify the process of configuring scans, selecting models, probes, detectors, and buffs.
*   **Visualize Results:** Present scan results in a clear, understandable, and visually appealing format.
*   **Centralized Management:** Allow users to manage their scan configurations and reports from a single interface.

## 3. Target Audience

*   **Security Professionals:** Pentesters and security auditors who need to assess the security of LLMs.
*   **LLM Developers:** Developers who want to integrate security testing into their development lifecycle.
*   **AI/ML Researchers:** Researchers who are studying the vulnerabilities of LLMs.
*   **Students and Educators:** Individuals who are learning about LLM security.

## 4. Functional Requirements

### 4.1. Scan Configuration

The GUI will provide a comprehensive interface for configuring Garak scans. This will include the following sections, based on the analysis of `garak/cli.py`, `garak/_config.py`, and `garak/resources/garak.core.yaml`:

#### 4.1.1. System Settings

*   **Verbosity:** A checkbox or dropdown to control the level of output verbosity (`-v`).
*   **Report Prefix:** A text input field for specifying a report prefix (`--report_prefix`).
*   **Output Format:** A toggle switch for narrow CLI output (`--narrow_output`).
*   **Parallelism:**
    *   An input field for the number of parallel requests (`--parallel_requests`).
    *   An input field for the number of parallel attempts (`--parallel_attempts`).
*   **Plugin Handling:** A checkbox to allow skipping of unknown plugins (`--skip_unknown`).

#### 4.1.2. Run Settings

*   **Random Seed:** An input field for the random seed (`-s`, `--seed`).
*   **Deprefix Output:** A checkbox to remove the prompt from the generator output (`--deprefix`).
*   **Evaluation Threshold:** A slider or input field for the evaluation threshold (`--eval_threshold`).
*   **Generations:** An input field for the number of generations per prompt (`-g`, `--generations`).
*   **Configuration File:** A file picker to select a YAML configuration file (`--config`).

#### 4.1.3. Plugin Selection and Configuration

This is a critical part of the GUI. It should allow users to easily select and configure generators, probes, detectors, and buffs.

*   **Model (Generator) Selection:**
    *   A dropdown menu to select the model type (`-m`, `--model_type`) from a list of available generators (obtained by running `garak --list_generators`).
    *   A text input field for the model name (`-n`, `--model_name`).
    *   A section for generator-specific options (`--generator_options` or `--generator_option_file`). This should be a dynamic key-value editor or a file picker.

*   **Probe Selection:**
    *   A searchable, filterable list of available probes (from `garak --list_probes`) with checkboxes for selection (`-p`, `--probes`).
    *   A text input for filtering probes by tags (`--probe_tags`).
    *   A section for probe-specific options (`--probe_options` or `--probe_option_file`).

*   **Detector Selection:**
    *   A searchable, filterable list of available detectors (from `garak --list_detectors`) with checkboxes for selection (`-d`, `--detectors`).
    *   A checkbox for enabling extended detectors (`--extended_detectors`).
    *   A section for detector-specific options (`--detector_options` or `--detector_option_file`).

*   **Buff Selection:**
    *   A searchable, filterable list of available buffs (from `garak --list_buffs`) with checkboxes for selection (`-b`, `--buffs`).
    *   A section for buff-specific options (`--buff_options` or `--buff_option_file`).

### 4.2. Running Scans

*   **Start/Stop:** A button to start the configured scan. It should be possible to stop a running scan.
*   **Real-time Output:** A terminal-like view to show the real-time output of the Garak scan.
*   **Progress Indicator:** A progress bar or other indicator to show the status of the scan.

### 4.3. Reporting

*   **Report Viewer:** A dedicated view to display the generated reports.
*   **Report Format:** The GUI should support the default Garak report format and provide an option to export reports (e.g., as AVID reports using `--report`).
*   **Taxonomy:** A dropdown or input field to specify the MISP taxonomy for reporting (`--taxonomy`).
*   **Historical Reports:** A list of past scan reports, with options to view, delete, or re-run them.

### 4.4. Other Commands

The GUI should provide access to the following Garak commands:

*   **List Plugins:** Buttons or menu items to display lists of available probes, detectors, generators, and buffs.
*   **Plugin Info:** A way to view detailed information about a specific plugin (`--plugin_info`).
*   **Interactive Mode:** A dedicated "Interactive" tab or window that launches Garak's interactive mode (`-I`, `--interactive`).
*   **Configuration Management:**
    *   An option to view the current configuration (`--list_config`).
    *   An option to run the configuration fixer (`--fix`).

## 5. User Interface (UI) and User Experience (UX) Requirements

*   **Intuitive Layout:** The GUI should be organized logically, with a clear separation between configuration, execution, and reporting. A tabbed interface might be suitable.
*   **Responsive Design:** The GUI should be responsive and work well on different screen sizes.
*   **Tooltips and Help Text:** Provide tooltips or help text for all configuration options to explain their purpose.
*   **Error Handling:** Display clear and helpful error messages if the user provides invalid input or if a scan fails.
*   **Configuration Presets:** Allow users to save and load scan configurations as presets.

## 6. Non-Functional Requirements

*   **Performance:** The GUI should be performant and not introduce significant overhead to the Garak scans.
*   **Cross-Platform Compatibility:** The GUI should be compatible with Windows, macOS, and Linux.
*   **Programming Language:** The GUI must be written in Python, version 3.13.
*   **Security:** The GUI should handle sensitive information like API keys securely (e.g., by using environment variables or a secure vault).
*   **Extensibility:** The GUI should be designed in a way that it can be easily updated to support new features and plugins in future versions of Garak.
