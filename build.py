import PyInstaller.__main__
import os
import shutil

def build():
    """Build the application using PyInstaller."""
    garak_path = os.path.abspath("garak")

    pyinstaller_args = [
        "garak_gui/main.py",
        "--name=garak-gui",
        "--onefile",
        "--windowed",
        f"--add-data={garak_path}{os.pathsep}garak",
    ]

    PyInstaller.__main__.run(pyinstaller_args)

if __name__ == "__main__":
    build()
