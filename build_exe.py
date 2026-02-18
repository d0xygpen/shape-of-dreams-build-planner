"""
PyInstaller build script for Shape of Dreams Build Planner.

Usage:
    python build_exe.py

Output:
    dist/SODBuildPlanner/  - folder with .exe and all dependencies
    Zip this folder for distribution.
"""

import subprocess
import sys
from pathlib import Path


def build():
    project_root = Path(__file__).parent

    # PyInstaller args
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SODBuildPlanner",
        "--noconfirm",
        "--clean",
        # Onedir mode (faster startup, fewer AV false positives)
        "--onedir",
        # No console window
        "--windowed",
        # Add data directories
        "--add-data", f"{project_root / 'data'};data",
        "--add-data", f"{project_root / 'builds'};builds",
        # Hidden imports for ttkbootstrap themes
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "ttkbootstrap.themes",
        "--hidden-import", "ttkbootstrap.tableview",
        # Exclude unnecessary modules to reduce size
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "cv2",
        "--exclude-module", "pytest",
        "--exclude-module", "unittest",
        # Entry point
        str(project_root / "app.py"),
    ]

    print("Building SODBuildPlanner executable...")
    print(f"Command: {' '.join(args)}")
    print()

    result = subprocess.run(args, cwd=str(project_root))

    if result.returncode == 0:
        dist_path = project_root / "dist" / "SODBuildPlanner"
        print()
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Output: {dist_path}")
        print()
        print("To distribute:")
        print(f"  1. ZIP the folder: {dist_path}")
        print("  2. Share the ZIP file")
        print("  3. Recipients extract and run SODBuildPlanner.exe")
        print("  4. User-created builds are saved in custom_builds/ next to the exe")
        print("=" * 60)
    else:
        print()
        print("BUILD FAILED! Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    build()
