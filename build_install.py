"""
Build script for creating install.exe using PyInstaller
Run this script to rebuild install.exe with the latest code changes
"""

import subprocess
import sys
import shutil
from pathlib import Path

def main():
    """Build install.exe using PyInstaller"""
    project_root = Path(__file__).parent
    install_spec = project_root / "install.spec"
    
    if not install_spec.exists():
        print(f"Error: install.spec not found at {install_spec}")
        sys.exit(1)
    
    print("="*60)
    print("Building install.exe with PyInstaller")
    print("="*60)
    print(f"Project root: {project_root}")
    print(f"Spec file: {install_spec}")
    print()
    
    # Check if PyInstaller is installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pyinstaller"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("PyInstaller not found. Installing...")
            install_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                cwd=project_root,
                timeout=300
            )
            if install_result.returncode != 0:
                print("Error: Failed to install PyInstaller")
                sys.exit(1)
            print("[OK] PyInstaller installed")
    except Exception as e:
        print(f"Error checking/installing PyInstaller: {e}")
        sys.exit(1)
    
    # Clean previous build artifacts
    print("\nCleaning previous build artifacts...")
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"  Removed: {build_dir}")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"  Removed: {dist_dir}")
    
    # Build with PyInstaller
    print("\nBuilding install.exe...")
    print("This may take a few minutes...")
    print()
    
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(install_spec)
            ],
            cwd=project_root,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode != 0:
            print("Error: PyInstaller build failed")
            print("Check the output above for details")
            sys.exit(1)
        
        # Check if install.exe was created
        install_exe = dist_dir / "install.exe"
        if install_exe.exists():
            # Copy to project root for convenience
            install_exe_dest = project_root / "install.exe"
            shutil.copy2(install_exe, install_exe_dest)
            
            file_size = install_exe_dest.stat().st_size
            print()
            print("="*60)
            print("Build successful!")
            print("="*60)
            print(f"install.exe created: {install_exe_dest}")
            print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print()
            print("The install.exe file includes:")
            print("  - Updated Ollama adapter with vision model fixes")
            print("  - All wolf CLI code")
            print("  - Installation scripts and dependencies")
            print()
            print("You can now distribute this install.exe file.")
            print("="*60)
        else:
            print(f"Error: install.exe not found in {dist_dir}")
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        print("Error: Build timed out after 10 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"Error during build: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

