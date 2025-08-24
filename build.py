import PyInstaller.__main__
import os
import customtkinter
from PIL import Image, ImageTk

def build():
    # Get the absolute path to the garak_gui directory
    gui_dir = os.path.abspath('garak_gui')
    main_script = os.path.join(gui_dir, 'main.py')

    # Get the absolute path to the garak library directory
    garak_lib_dir = os.path.abspath('garak')

    # Get the path to the customtkinter library
    ctk_path = os.path.dirname(customtkinter.__file__)

    pyinstaller_args = [
        main_script,
        '--name', 'GarakGUI',
        '--onefile',
        '--windowed',
        f'--add-data={garak_lib_dir}{os.pathsep}garak',
        f'--add-data={ctk_path}{os.pathsep}customtkinter',
        '--hidden-import', 'customtkinter',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.ImageTk',
        '--clean',
    ]

    print(f"Running PyInstaller with args: {pyinstaller_args}")

    PyInstaller.__main__.run(pyinstaller_args)

if __name__ == '__main__':
    build()
