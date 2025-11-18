import subprocess
import sys
import os
import shutil
from pathlib import Path

# Windows-specific imports
if sys.platform == "win32":
    import winreg
    import ctypes

def get_base_path():
    """Get the base path for installation files.
    If running as PyInstaller exe, extract bundled files to current directory.
    Otherwise, use current directory.
    """
    base_path = Path.cwd()
    
    if getattr(sys, 'frozen', False):
        # Running as compiled exe (PyInstaller)
        print(f"Extracting installation files to: {base_path}")
        
        # Get the directory where PyInstaller extracted files
        if hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
        else:
            meipass = Path(sys.executable).parent
        
        # Copy bundled files
        bundled_files = [
            'requirements.txt',
            'setup.py',
            'README.md',
            'wolf',
            'cursor_api',  # Include Cursor API server
            'uninstall.py',  # Include uninstall script
            'uninstall.spec',  # Include uninstall spec file
            '.env'  # Include .env file with model configurations
        ]
        
        for item in bundled_files:
            src = meipass / item
            if src.exists():
                dst = base_path / item
                # Check if destination exists and warn
                if dst.exists():
                    if dst.is_dir():
                        print(f"  Warning: Directory '{item}' already exists, skipping extraction")
                        continue
                    else:
                        print(f"  Warning: File '{item}' already exists, will be overwritten")
                
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                print(f"  Extracted: {item}")
            else:
                print(f"  Warning: {item} not found in bundle")
        
        # Special handling for cursor_api: ensure directory structure exists
        # PyInstaller may bundle files individually, so we need to ensure the directory exists
        cursor_api_src = meipass / 'cursor_api'
        cursor_api_dst = base_path / 'cursor_api'
        if cursor_api_src.exists() and cursor_api_src.is_dir():
            # Directory exists, already extracted above
            pass
        elif not cursor_api_dst.exists():
            # Check if individual cursor_api files exist in bundle
            cursor_api_files = ['cursor_api.py', 'requirements.txt', '__init__.py']
            found_files = []
            for file in cursor_api_files:
                if (meipass / 'cursor_api' / file).exists():
                    found_files.append(file)
            
            if found_files:
                # Create cursor_api directory and copy files
                cursor_api_dst.mkdir(exist_ok=True)
                print("  Creating cursor_api directory...")
                for file in found_files:
                    src_file = meipass / 'cursor_api' / file
                    dst_file = cursor_api_dst / file
                    shutil.copy2(src_file, dst_file)
                    print(f"  Extracted: cursor_api/{file}")
    
    return base_path

def find_python_executable():
    """Find the Python executable to use for creating venv."""
    if getattr(sys, 'frozen', False):
        # Running as exe, need to find system Python
        # Try common Python executable names
        python_names = ['python', 'python3', 'py']
        for name in python_names:
            try:
                result = subprocess.run(
                    [name, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return name
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        # If not found, try to use 'python' and let it fail with a clear error
        return 'python'
    else:
        # Running as script, use current interpreter
        return sys.executable

def run_command(command, cwd=None):
    """Runs a command and prints its output."""
    process = subprocess.Popen(
        command, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        shell=True, 
        text=True,
        cwd=cwd
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        sys.exit(1)

if __name__ == "__main__":
    # Get installation directory
    install_dir = get_base_path()
    print(f"Installation directory: {install_dir}")
    
    # Change to installation directory
    os.chdir(install_dir)
    
    # Verify required files exist
    required_files = ['requirements.txt', 'setup.py', 'wolf']
    missing = [f for f in required_files if not Path(f).exists()]
    if missing:
        print(f"Error: Missing required files: {missing}")
        sys.exit(1)
    
    # Verify cursor_api was extracted (required for full functionality)
    cursor_api_path = install_dir / 'cursor_api'
    if not cursor_api_path.exists():
        print("\n" + "="*50)
        print("ERROR: cursor_api directory not found after extraction!")
        print("="*50)
        print("The installer should have extracted cursor_api from the bundle.")
        print("Cursor API features will not be available.")
        print("Please ensure you're using the latest install.exe file.")
        sys.exit(1)
    
    # Verify cursor_api has required files
    required_cursor_files = ['cursor_api.py', 'requirements.txt', '__init__.py']
    missing_cursor_files = [f for f in required_cursor_files if not (cursor_api_path / f).exists()]
    if missing_cursor_files:
        print(f"\nWarning: Missing cursor_api files: {missing_cursor_files}")
        print("Cursor API installation may fail.")
    
    # Find Python executable
    python_exe = find_python_executable()
    print(f"Using Python: {python_exe}")
    
    # Create virtual environment
    print("\nCreating virtual environment...")
    run_command([python_exe, "-m", "venv", ".venv"], cwd=install_dir)

    # Activate virtual environment and install requirements
    print("\nInstalling requirements...")
    if sys.platform == "win32":
        pip_executable = os.path.join(".venv", "Scripts", "pip.exe")
    else:
        pip_executable = os.path.join(".venv", "bin", "pip")
    
    requirements_path = install_dir / "requirements.txt"
    run_command([pip_executable, "install", "-r", str(requirements_path)], cwd=install_dir)

    # Run setup.py
    print("\nInstalling wolf-cli package...")
    if sys.platform == "win32":
        python_executable = os.path.join(".venv", "Scripts", "python.exe")
    else:
        python_executable = os.path.join(".venv", "bin", "python")
    
    setup_path = install_dir / "setup.py"
    run_command([python_executable, str(setup_path), "install"], cwd=install_dir)

    # Install Cursor API server (required - should have been extracted)
    print("\n" + "="*50)
    print("Installing Cursor API server...")
    print("="*50)
    
    cursor_api_requirements = cursor_api_path / "requirements.txt"
    if not cursor_api_requirements.exists():
        print("ERROR: cursor_api/requirements.txt not found!")
        print("Cursor API installation failed.")
        sys.exit(1)
    
    print("Installing Cursor API dependencies...")
    run_command([pip_executable, "install", "-r", str(cursor_api_requirements)], cwd=install_dir)
    print("[OK] Cursor API dependencies installed")
    
    # Create a startup script for Cursor API
    if sys.platform == "win32":
        cursor_api_script = install_dir / "start_cursor_api.bat"
        with open(cursor_api_script, 'w') as f:
            f.write("@echo off\n")
            f.write("echo Starting Cursor API Server...\n")
            f.write("echo.\n")
            f.write(f"cd /d \"{install_dir}\"\n")
            f.write(f'"{python_executable}" -m uvicorn cursor_api.cursor_api:app --host 127.0.0.1 --port 5005\n')
            f.write("pause\n")
        print(f"[OK] Created startup script: {cursor_api_script}")
    else:
        cursor_api_script = install_dir / "start_cursor_api.sh"
        with open(cursor_api_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("echo 'Starting Cursor API Server...'\n")
            f.write(f"cd \"{install_dir}\"\n")
            f.write(f'"{python_executable}" -m uvicorn cursor_api.cursor_api:app --host 127.0.0.1 --port 5005\n')
        os.chmod(cursor_api_script, 0o755)
        print(f"[OK] Created startup script: {cursor_api_script}")

    # Generate uninstall.exe
    print("\n" + "="*50)
    print("Generating uninstall.exe...")
    print("="*50)
    
    uninstall_py = install_dir / "uninstall.py"
    uninstall_spec = install_dir / "uninstall.spec"
    
    # Check if files exist and provide diagnostics
    if not uninstall_py.exists():
        print(f"Error: uninstall.py not found at {uninstall_py}")
        print("  This file should have been extracted from the installer bundle.")
        print("  Skipping uninstall.exe generation.")
    elif not uninstall_spec.exists():
        print(f"Error: uninstall.spec not found at {uninstall_spec}")
        print("  This file should have been extracted from the installer bundle.")
        print("  Skipping uninstall.exe generation.")
    else:
        print(f"[OK] Found uninstall.py at: {uninstall_py}")
        print(f"[OK] Found uninstall.spec at: {uninstall_spec}")
        
        # Install PyInstaller if not already installed
        print("\nInstalling PyInstaller (required for uninstall.exe)...")
        pyinstaller_installed = False
        try:
            # Check if PyInstaller is already installed
            result = subprocess.run(
                [pip_executable, "show", "pyinstaller"],
                capture_output=True,
                text=True,
                cwd=install_dir,
                timeout=30
            )
            if result.returncode != 0:
                # PyInstaller not installed, install it
                print("PyInstaller not found, installing...")
                install_result = subprocess.run(
                    [pip_executable, "install", "pyinstaller"],
                    capture_output=True,
                    text=True,
                    cwd=install_dir,
                    timeout=300
                )
                if install_result.returncode == 0:
                    print("[OK] PyInstaller installed successfully")
                    pyinstaller_installed = True
                else:
                    print(f"Error installing PyInstaller:")
                    print(install_result.stdout)
                    print(install_result.stderr)
            else:
                print("[OK] PyInstaller already installed")
                pyinstaller_installed = True
        except subprocess.TimeoutExpired:
            print("Error: PyInstaller installation timed out")
        except Exception as e:
            print(f"Error: Could not install PyInstaller: {e}")
            import traceback
            traceback.print_exc()
        
        if pyinstaller_installed:
            # Verify PyInstaller executable exists
            if sys.platform == "win32":
                pyinstaller_exe = install_dir / ".venv" / "Scripts" / "pyinstaller.exe"
            else:
                pyinstaller_exe = install_dir / ".venv" / "bin" / "pyinstaller"
            
            if not pyinstaller_exe.exists():
                print(f"Error: PyInstaller executable not found at: {pyinstaller_exe}")
                print("  PyInstaller may not have installed correctly.")
            else:
                print(f"[OK] Found PyInstaller at: {pyinstaller_exe}")
                
                # Build uninstall.exe using PyInstaller
                print("\nBuilding uninstall.exe...")
                try:
                    # Run PyInstaller
                    build_result = subprocess.run(
                        [str(pyinstaller_exe), "--clean", "--noconfirm", str(uninstall_spec)],
                        cwd=install_dir,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if build_result.returncode != 0:
                        print("Error: PyInstaller build failed:")
                        print(build_result.stdout)
                        print(build_result.stderr)
                    else:
                        # Copy uninstall.exe from dist to installation directory
                        uninstall_exe_src = install_dir / "dist" / "uninstall.exe"
                        uninstall_exe_dst = install_dir / "uninstall.exe"
                        
                        if uninstall_exe_src.exists():
                            shutil.copy2(uninstall_exe_src, uninstall_exe_dst)
                            print(f"[OK] Created uninstall.exe at: {uninstall_exe_dst}")
                            
                            # Verify the file was copied successfully
                            if uninstall_exe_dst.exists() and uninstall_exe_dst.stat().st_size > 0:
                                print(f"[OK] Verified uninstall.exe (size: {uninstall_exe_dst.stat().st_size} bytes)")
                                
                                # Clean up build artifacts
                                build_dir = install_dir / "build"
                                dist_dir = install_dir / "dist"
                                if build_dir.exists():
                                    shutil.rmtree(build_dir)
                                if dist_dir.exists():
                                    shutil.rmtree(dist_dir)
                                print("[OK] Cleaned up build artifacts")
                            else:
                                print("Warning: uninstall.exe was copied but appears to be invalid")
                        else:
                            print(f"Error: uninstall.exe was not generated in dist directory")
                            print(f"  Expected location: {uninstall_exe_src}")
                            print("  PyInstaller output:")
                            print(build_result.stdout)
                            if build_result.stderr:
                                print("  Errors:")
                                print(build_result.stderr)
                            
                except subprocess.TimeoutExpired:
                    print("Error: PyInstaller build timed out after 5 minutes")
                except Exception as e:
                    print(f"Error: Could not build uninstall.exe: {e}")
                    import traceback
                    traceback.print_exc()
                    print("\nYou can manually build it later using:")
                    print(f"  cd {install_dir}")
                    print(f"  {pyinstaller_exe} --clean --noconfirm uninstall.spec")
        else:
            print("\nSkipping uninstall.exe build (PyInstaller not available)")

    # Install wolf commands to Windows PATH (Windows 11 compatible)
    if sys.platform == "win32":
        print("\n" + "="*50)
        print("Installing wolf commands to Windows PATH...")
        print("="*50)
        
        try:
            venv_scripts = install_dir / '.venv' / 'Scripts'
            
            # Check if console scripts exist
            if not (venv_scripts / 'wolf.exe').exists():
                print("Warning: Console scripts not found. Commands may not work properly.")
                print(f"Expected location: {venv_scripts}")
            else:
                print(f"[OK] Found console scripts at: {venv_scripts}")
            
            # Create a bin directory for wolf commands in user's local directory
            # This is a standard location that won't conflict with system directories
            user_bin = Path.home() / "AppData" / "Local" / "wolf-cli" / "bin"
            user_bin.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created command directory: {user_bin}")
            
            # Create batch file wrappers for each command
            commands = {
                'wolf': 'wolf.exe',
                'wolfv': 'wolfv.exe',
                'wolfc': 'wolfc.exe',
                'wolfcamera': 'wolfcamera.exe',
                'wolfw': 'wolfw.exe',
                'wolfem': 'wolfem.exe'
            }
            
            created_commands = []
            for cmd_name, exe_name in commands.items():
                exe_path = venv_scripts / exe_name
                if exe_path.exists():
                    # Create a .cmd file that calls the .exe
                    # Use absolute path to ensure it works from any directory
                    exe_path_absolute = exe_path.resolve()
                    cmd_file = user_bin / f"{cmd_name}.cmd"
                    with open(cmd_file, 'w', encoding='utf-8') as f:
                        f.write(f"""@echo off
"{exe_path_absolute}" %*
""")
                    created_commands.append(cmd_name)
                    print(f"  [OK] Created {cmd_name}.cmd")
                else:
                    print(f"  [WARN] Skipped {cmd_name} (executable not found)")
            
            if not created_commands:
                print("Error: No commands were created. Installation may have failed.")
            else:
                # Add the bin directory to user PATH
                print(f"\nAdding {user_bin} to Windows PATH...")
                
                # Get current user PATH
                try:
                    # Open the user environment variables registry key
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Environment",
                        0,
                        winreg.KEY_READ | winreg.KEY_WRITE
                    )
                    
                    try:
                        current_path, _ = winreg.QueryValueEx(key, "Path")
                    except FileNotFoundError:
                        current_path = ""
                    
                    # Check if already in PATH
                    path_entries = [p.strip() for p in current_path.split(os.pathsep) if p.strip()]
                    user_bin_str = str(user_bin)
                    
                    if user_bin_str not in path_entries:
                        # Add to PATH
                        if current_path:
                            new_path = current_path + os.pathsep + user_bin_str
                        else:
                            new_path = user_bin_str
                        
                        # Update PATH in registry
                        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                        winreg.CloseKey(key)
                        
                        # Broadcast environment change to all windows
                        HWND_BROADCAST = 0xFFFF
                        WM_SETTINGCHANGE = 0x001A
                        SendMessageW = ctypes.windll.user32.SendMessageW
                        SendMessageW(
                            HWND_BROADCAST,
                            WM_SETTINGCHANGE,
                            0,
                            "Environment"
                        )
                        
                        print(f"[OK] Added {user_bin} to Windows PATH")
                        print("[OK] Environment variables updated")
                        print("\n" + "="*50)
                        print("Installation Complete!")
                        print("="*50)
                        print(f"\nWolf commands are now available system-wide:")
                        for cmd in created_commands:
                            print(f"  - {cmd}")
                        print("\nYou can use these commands in:")
                        print("  - Command Prompt (CMD)")
                        print("  - PowerShell")
                        print("  - Windows Terminal")
                        print("  - Any terminal application")
                        print("\nNote: You may need to restart your terminal for the PATH changes to take effect.")
                        print("      Or open a new terminal window.")
                        print("="*50)
                    else:
                        winreg.CloseKey(key)
                        print(f"[OK] {user_bin} is already in PATH")
                        print("\n" + "="*50)
                        print("Installation Complete!")
                        print("="*50)
                        print(f"\nWolf commands are available:")
                        for cmd in created_commands:
                            print(f"  - {cmd}")
                        print("\nCommands should work immediately in new terminal windows.")
                        print("="*50)
                        
                except PermissionError:
                    print("Warning: Could not modify PATH (permission denied)")
                    print("You may need to run the installer as administrator.")
                    print(f"\nManual installation:")
                    print(f"1. Add this directory to your PATH: {user_bin}")
                    print("2. Open System Properties > Environment Variables")
                    print("3. Add the directory to User PATH variable")
                except Exception as e:
                    print(f"Warning: Could not modify PATH: {e}")
                    print(f"\nManual installation:")
                    print(f"1. Add this directory to your PATH: {user_bin}")
                    print("2. Open System Properties > Environment Variables")
                    print("3. Add the directory to User PATH variable")
                    
        except Exception as e:
            print(f"Error installing wolf commands: {e}")
            import traceback
            traceback.print_exc()
            print("\nYou may need to manually add the commands to your PATH.")

    print("\n" + "="*50)
    print("Installation complete!")
    print("="*50)
    print(f"\nVirtual environment created at: {install_dir / '.venv'}")
    if sys.platform == "win32":
        print(f"\nTo activate the virtual environment, run:")
        print(f"  {install_dir / '.venv' / 'Scripts' / 'Activate.ps1'}")
    else:
        print(f"\nTo activate the virtual environment, run:")
        print(f"  source {install_dir / '.venv' / 'bin' / 'activate'}")
    print(f"\nThen you can use the 'wolf' command.")
    print(f"\nTo start the Cursor API server, run:")
    if sys.platform == "win32":
        print(f"  {install_dir / 'start_cursor_api.bat'}")
    else:
        print(f"  {install_dir / 'start_cursor_api.sh'}")
    print("  (The server will run on http://127.0.0.1:5005)")
    
    uninstall_exe = install_dir / "uninstall.exe"
    if uninstall_exe.exists():
        print(f"\n[OK] Uninstaller created: {uninstall_exe}")
        print("  Run this file to uninstall Wolf CLI (preserves Ollama)")
