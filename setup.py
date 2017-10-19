from cx_Freeze import setup, Executable
import sys, os
import matplotlib
import tkinter

#base = 'Win32GUI' if sys.platform == 'win32' else None
base = 'Console'

os.environ['TCL_LIBRARY'] = r'C:\Users\florian.hofmaier\AppData\Local\Programs\Python\Python36-32\tcl\tcl8.6'

os.environ['TK_LIBRARY'] = r'C:\Users\florian.hofmaier\AppData\Local\Programs\Python\Python36-32\tcl\tk8.6'



executables = [Executable("serplot.py", base=base)]

packages = ["tkinter", "idna"]
include_files = [(matplotlib.get_data_path(), "mpl-data"),
                 r"C:\Users\florian.hofmaier\AppData\Local\Programs\Python\Python36-32\DLLs\tcl86t.dll",
                 r"C:\Users\florian.hofmaier\AppData\Local\Programs\Python\Python36-32\DLLs\tk86t.dll"]

includes = ['numpy.core._methods', 'numpy.lib.format', "matplotlib.backends.backend_tkagg"]

options = {"build_exe": {"includes": includes, "include_files": include_files}}


setup(
    name = "<any name>",
    options = options,
    version = "<any number>",
    description = '<any description>',
    executables = executables
)