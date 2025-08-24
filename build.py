import PyInstaller.__main__
import os

def build():
    # Get the absolute path to the garak_gui directory
    gui_dir = os.path.abspath('garak_gui')
    main_script = os.path.join(gui_dir, 'main.py')

    # Get the absolute path to the garak library directory
    garak_lib_dir = os.path.abspath('garak')

    pyinstaller_args = [
        main_script,
        '--name', 'GarakGUI',
        '--onefile',
        '--windowed',
        f'--add-data={garak_lib_dir}{os.pathsep}garak',
        '--hidden-import', 'customtkinter',
        '--clean',
    ]

    print(f"Running PyInstaller with args: {pyinstaller_args}")

    PyInstaller.__main__.run(pyinstaller_args)

if __name__ == '__main__':
    build()
