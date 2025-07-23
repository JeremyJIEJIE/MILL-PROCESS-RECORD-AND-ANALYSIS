import PyInstaller.__main__
import os
import shutil

# Define paths
project_root = os.path.dirname(os.path.abspath(__file__))
dist_path = os.path.join(project_root, 'dist')
build_path = os.path.join(project_root, 'build')
streamlit_app_path = os.path.join(project_root, 'app.py')
data_csv_path = os.path.join(project_root, 'data.csv')
icon_path = os.path.join(project_root, 'icon.ico') # Optional: if you have an icon file

# Clean up previous build directories
if os.path.exists(dist_path):
    shutil.rmtree(dist_path)
if os.path.exists(build_path):
    shutil.rmtree(build_path)
print(f"Cleaned up old 'dist' and 'build' directories.")

# PyInstaller arguments
# --name: Name of the executable and folder
# --onefile: Create a single executable file (can be slow to start)
# --noconsole: Do not show a console window (Streamlit runs in browser)
# --add-data: Add additional files (like data.csv) to the executable
# --icon: Add an icon to the executable (e.g., 'icon.ico')
# --collect-all: Include all submodules of specified packages (e.g., 'streamlit')
# --hidden-import: Explicitly include modules that PyInstaller might miss
# --specpath: Directory to store the .spec file
# --distpath: Directory to store the bundled app
# --workpath: Directory to store all temporary work files

pyinstaller_args = [
    f'--name=DataManagementApp',
    f'--onefile', # This will create a single EXE file. If you prefer a folder with many files, remove this line.
    f'--windowed', # This is typically for GUI apps without a console. For Streamlit, it prevents a console from popping up.
    # '--noconfirm', # Overwrite previous output without asking
    # f'--icon={icon_path}' if os.path.exists(icon_path) else '', # Uncomment and provide icon.ico if you have one
    f'--add-data={data_csv_path}{os.pathsep}.', # Add data.csv to the root of the bundled app
    # Add any other static files (images, CSS, etc.) here if app.py uses them
    # f'--add-data=path/to/your/image.png{os.pathsep}images', # Example for adding an image to a 'images' subfolder

    # PyInstaller often misses internal Streamlit dependencies, collect them
    '--collect-all=streamlit',
    '--collect-all=pandas',
    '--collect-all=matplotlib',
    # '--collect-all=numpy', # If you use numpy directly
    # '--collect-all=scipy', # If you use scipy directly

    # Explicitly include hidden imports that PyInstaller sometimes misses
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=matplotlib.pyplot',
    '--hidden-import=matplotlib.font_manager',
    '--hidden-import=pandas._libs.tslibs.timedeltas', # Common pandas issue
    '--hidden-import=pandas._libs.tslibs.timestamps', # Common pandas issue
    '--hidden-import=pandas._libs.interval', # Common pandas issue
    '--hidden-import=pandas._libs.arrays', # Common pandas issue
    '--hidden-import=streamlit.vendor.watchdog.observers.fsevents', # For macOS, harmless on Windows
    '--hidden-import=streamlit.vendor.toml', # Streamlit dependency
    '--hidden-import=streamlit.vendor.protobuf', # Streamlit dependency

    f'--specpath={project_root}', # Store .spec file in project root
    f'--distpath={dist_path}',   # Output to dist folder
    f'--workpath={build_path}',  # Use build folder for temporary files
    streamlit_app_path # Your main Streamlit application script
]

# Filter out empty arguments (e.g., if icon_path doesn't exist)
pyinstaller_args = [arg for arg in pyinstaller_args if arg]

print(f"Starting PyInstaller with arguments: {' '.join(pyinstaller_args)}")

try:
    PyInstaller.__main__.run(pyinstaller_args)
    print("\nPyInstaller finished successfully!")
    print(f"Your executable should be in: {dist_path}")
    print("Please test the .exe file on the target computer.")
except Exception as e:
    print(f"\nPyInstaller failed: {e}")
