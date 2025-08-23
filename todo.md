# Garak GUI Development To-Do List

This document outlines the tasks for developing the Garak GUI, based on the Product Requirements Document.

## Phase 1: Project Setup & Core Functionality

- [ ] **Project Initialization:**
    - [ ] Set up a new Git repository for the GUI project.
    - [ ] Create a Python 3.13 virtual environment.
    - [ ] Add `garak` as a dependency.

- [ ] **GUI Framework Selection:**
    - [ ] Research and choose a suitable cross-platform Python GUI framework (e.g., PyQt, PySide, CustomTkinter, Flet).
    - [ ] Implement a basic main window with a tabbed layout for "Scan Configuration", "Scan Output", and "Reports".

- [ ] **Garak Integration:**
    - [ ] Create a Python module to act as a wrapper around the `garak` command-line tool. This module will be responsible for:
        - Building command-line arguments based on UI settings.
        - Executing `garak` as a subprocess.
        - Capturing its standard output and error streams.
    - [ ] Implement a basic "Start Scan" button that executes a default `garak` scan (e.g., `garak --probes all`).

- [ ] **Real-time Output:**
    - [ ] Implement a text area or terminal-like widget in the "Scan Output" tab.
    - [ ] Stream the output from the `garak` subprocess to this widget in real-time.
    - [ ] Implement a "Stop Scan" button that terminates the `garak` subprocess.

## Phase 2: Scan Configuration UI

- [ ] **Implement System & Run Settings UI:**
    - [ ] Create UI elements (checkboxes, text fields, sliders) for all options under "System Settings" and "Run Settings" as defined in the PRD.
    - [ ] Link these UI elements to the Garak command builder.

- [ ] **Implement Plugin Listing:**
    - [ ] Implement functions in the `garak` wrapper to call `--list_probes`, `--list_detectors`, `--list_buffs`, and `--list_generators` and parse the output.
    - [ ] Populate searchable and filterable lists in the UI with the available plugins.

- [ ] **Implement Plugin Selection UI:**
    - [ ] Create UI for selecting the model type and name.
    - [ ] Create UI for selecting one or more probes, detectors, and buffs (e.g., using checkbox lists).
    - [ ] Implement the text input for filtering probes by tags.

- [ ] **Implement Plugin Options UI:**
    - [ ] Create a dynamic key-value editor component for users to add custom options for each plugin type (`--generator_options`, `--probe_options`, etc.).
    - [ ] Alternatively, provide a file picker for the `_option_file` arguments.

## Phase 3: Reporting & Advanced Features

- [ ] **Report Viewer:**
    - [ ] Implement a file watcher that detects when a new report file is created in the `garak_runs` directory.
    - [ ] Parse the generated `.jsonl` report file.
    - [ ] Create a user-friendly view to display the report data in the "Reports" tab, with clear summaries and details of the findings.

- [ ] **Historical Reports:**
    - [ ] Implement a view that lists all past reports.
    - [ ] Add functionality to view, delete, or re-run a scan based on a past report's configuration.

- [ ] **Advanced Commands:**
    - [ ] Implement UI for the other Garak commands: `--plugin_info`, `--list_config`, `--fix`.
    - [ ] Implement the "Interactive Mode" tab, which should open a terminal or a dedicated UI that simulates Garak's interactive console.

- [ ] **Configuration Presets:**
    - [ ] Implement functionality to save the current scan configuration to a file.
    - [ ] Implement functionality to load a scan configuration from a file.

## Phase 4: Polishing & Packaging

- [ ] **UI/UX Refinements:**
    - [ ] Add tooltips and help text to all settings.
    - [ ] Implement comprehensive error handling for invalid user input and scan failures.
    - [ ] Ensure the UI is responsive and looks good on different screen sizes.

- [ ] **Testing:**
    - [ ] Thoroughly test all UI components and their interaction with the `garak` backend.
    - [ ] Test the application on all target platforms: Windows, macOS, and Linux.

- [ ] **Packaging and Distribution:**
    - [ ] Create build scripts to package the application into standalone executables for each platform (e.g., using PyInstaller or cx_Freeze).
    - [ ] Write documentation on how to install and use the Garak GUI.
