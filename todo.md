# Garak GUI Development To-Do List

This document outlines the tasks for developing the Garak GUI, based on the Product Requirements Document.

## Phase 1: Project Setup & Core Functionality

- [x] **Project Initialization:**
    - [x] Set up a new Git repository for the GUI project.
    - [x] Create a Python 3.13 virtual environment.
    - [x] Add `garak` as a dependency.

- [x] **GUI Framework Selection:**
    - [x] Research and choose a suitable cross-platform Python GUI framework (e.g., PyQt, PySide, CustomTkinter, Flet).
    - [x] Implement a basic main window with a tabbed layout for "Scan Configuration", "Scan Output", and "Reports".

- [x] **Garak Integration:**
    - [x] Create a Python module to act as a wrapper around the `garak` command-line tool. This module will be responsible for:
        - Building command-line arguments based on UI settings.
        - Executing `garak` as a subprocess.
        - Capturing its standard output and error streams.
    - [x] Implement a basic "Start Scan" button that executes a default `garak` scan (e.g., `garak --probes all`).

- [x] **Real-time Output:**
    - [x] Implement a text area or terminal-like widget in the "Scan Output" tab.
    - [x] Stream the output from the `garak` subprocess to this widget in real-time.
    - [x] Implement a "Stop Scan" button that terminates the `garak` subprocess.

## Phase 2: Scan Configuration UI

- [x] **Implement System & Run Settings UI:**
    - [x] Create UI elements (checkboxes, text fields, sliders) for all options under "System Settings" and "Run Settings" as defined in the PRD.
    - [x] Link these UI elements to the Garak command builder.

- [x] **Implement Plugin Listing:**
    - [x] Implement functions in the `garak` wrapper to call `--list_probes`, `--list_detectors`, `--list_buffs`, and `--list_generators` and parse the output.
    - [x] Populate searchable and filterable lists in the UI with the available plugins.

- [x] **Implement Plugin Selection UI:**
    - [x] Create UI for selecting the model type and name.
    - [x] Create UI for selecting one or more probes, detectors, and buffs (e.g., using checkbox lists).
    - [x] Implement the text input for filtering probes by tags.

- [x] **Implement Plugin Options UI:**
    - [x] Create a dynamic key-value editor component for users to add custom options for each plugin type (`--generator_options`, `--probe_options`, etc.).
    - [x] Alternatively, provide a file picker for the `_option_file` arguments.

## Phase 3: Reporting & Advanced Features

- [x] **Report Viewer:**
    - [x] Implement a file watcher that detects when a new report file is created in the `garak_runs` directory.
    - [x] Parse the generated `.jsonl` report file.
    - [x] Create a user-friendly view to display the report data in the "Reports" tab, with clear summaries and details of the findings.

- [x] **Historical Reports:**
    - [x] Implement a view that lists all past reports.
    - [x] Add functionality to view, delete, or re-run a scan based on a past report's configuration.

- [x] **Advanced Commands:**
    - [x] Implement UI for the other Garak commands: `--plugin_info`, `--list_config`, `--fix`.
    - [x] Implement the "Interactive Mode" tab, which should open a terminal or a dedicated UI that simulates Garak's interactive console.

- [x] **Configuration Presets:**
    - [x] Implement functionality to save the current scan configuration to a file.
    - [x] Implement functionality to load a scan configuration from a file.

## Phase 4: Polishing & Packaging

- [x] **UI/UX Refinements:**
    - [x] Add tooltips and help text to all settings.
    - [x] Implement comprehensive error handling for invalid user input and scan failures.
    - [x] Ensure the UI is responsive and looks good on different screen sizes.

- [x] **Testing:**
    - [x] Thoroughly test all UI components and their interaction with the `garak` backend.
    - [x] Test the application on all target platforms: Windows, macOS, and Linux.

- [x] **Packaging and Distribution:**
    - [x] Create build scripts to package the application into standalone executables for each platform (e.g., using PyInstaller or cx_Freeze).
    - [ ] Write documentation on how to install and use the Garak GUI.
