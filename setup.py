from setuptools import setup, find_packages

setup(
    name="garak-gui",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "gui_scripts": [
            "garak-gui = garak_gui.main:main",
        ]
    },
    install_requires=[
        "customtkinter",
        "Pillow",
    ],
    python_requires=">=3.10",
)
