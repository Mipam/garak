# Garak GUI

This is a graphical user interface (GUI) for the `garak` LLM vulnerability scanner. It provides a user-friendly way to configure and run `garak` scans, view results, and manage reports.

## Features

*   **Comprehensive Scan Configuration:** Configure all major `garak` settings, including system settings, run settings, and plugin selection, through an intuitive UI.
*   **Plugin Management:** Easily select from lists of available probes, detectors, buffs, and generators.
*   **Real-time Output:** View the output of a running `garak` scan in real-time.
*   **Report Viewer:** Browse and view generated `.jsonl` report files directly in the application.
*   **Report Management:** Delete and re-run scans from past reports.
*   **Interactive Mode:** Use `garak`'s interactive mode directly from a tab in the GUI.
*   **Configuration Presets:** Save and load your scan configurations to easily repeat experiments.

## Installation and Usage

There are two ways to run the Garak GUI: from source or as a standalone executable.

### Running from Source

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NVIDIA/garak.git
    cd garak
    ```

2.  **Install dependencies:**
    It is recommended to use a Python virtual environment. The GUI requires `customtkinter`.
    ```bash
    pip install -r requirements.txt
    pip install customtkinter
    ```

3.  **Run the application:**
    ```bash
    python -m garak_gui.main
    ```

### Using the Packaged Executable

A standalone executable can be built using the provided `build.py` script. This requires `PyInstaller`.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Run the build script:**
    ```bash
    python build.py
    ```

3.  **Run the executable:**
    The executable will be located in the `dist` directory. You can run it directly:
    ```bash
    ./dist/GarakGUI
    ```
    (The name and path may vary slightly depending on your operating system).
