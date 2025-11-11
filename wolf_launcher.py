"""
Wolf CLI Launcher
Entry point for PyInstaller-bundled executable.
"""
import sys
import os

# Add the current directory to the path so we can import wolf as a package
if hasattr(sys, '_MEIPASS'):
    # PyInstaller temporary folder
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Now import and run the main CLI
from wolf.cli_wrapper import wolf

def main():
    """Entry point for the wolf CLI"""
    wolf()

if __name__ == '__main__':
    main()
