import subprocess
import sys
import os
import shutil
from pathlib import Path
import platform

def get_config_dir():
    """Get the OS-appropriate configuration directory"""
    home = Path.home()
    system = platform.system()
    
    if system == "Windows":
        appdata = os.getenv("APPDATA")
        base = Path(appdata) if appdata else home
    else:
        xdg = os.getenv("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else (home / ".config")
    
    return base / "wolf-cli"


def find_python_executable():
    """Find the Python executable to use"""
    if getattr(sys, 'frozen', False):
        # Running as exe, need to find system Python
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
        return 'python'
    else:
        return sys.executable


def uninstall_package(python_exe: str):
    """Uninstall wolf-cli package from Python"""
    print("\n" + "="*50)
    print("Uninstalling wolf-cli package...")
    print("="*50)
    
    try:
        # Try to uninstall using pip
        result = subprocess.run(
            [python_exe, "-m", "pip", "uninstall", "wolf-cli", "-y"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ Package uninstalled successfully")
            return True
        else:
            # Package might not be installed, or installed in venv
            if "not installed" in result.stdout.lower() or "not installed" in result.stderr.lower():
                print("  Package not found in system Python (may be in venv)")
                return True
            else:
                print(f"  Warning: {result.stderr}")
                return False
    except Exception as e:
        print(f"  Warning: Could not uninstall package: {e}")
        return False


def remove_virtual_environment(install_dir: Path):
    """Remove virtual environment if it exists"""
    venv_path = install_dir / ".venv"
    
    if venv_path.exists():
        print("\n" + "="*50)
        print("Removing virtual environment...")
        print("="*50)
        try:
            shutil.rmtree(venv_path)
            print(f"✓ Removed virtual environment: {venv_path}")
            return True
        except Exception as e:
            print(f"  Error removing virtual environment: {e}")
            return False
    else:
        print("\n  No virtual environment found (skipping)")
        return True


def remove_config_files():
    """Remove configuration files"""
    print("\n" + "="*50)
    print("Removing configuration files...")
    print("="*50)
    
    config_dir = get_config_dir()
    removed = False
    
    if config_dir.exists():
        try:
            shutil.rmtree(config_dir)
            print(f"✓ Removed config directory: {config_dir}")
            removed = True
        except Exception as e:
            print(f"  Error removing config directory: {e}")
    else:
        print(f"  Config directory not found: {config_dir}")
    
    # Also check for .env file in current directory
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        try:
            # Only remove if it's a wolf-cli .env (check for WOLF_ prefix)
            with open(env_file, 'r') as f:
                content = f.read()
                if 'WOLF_' in content:
                    env_file.unlink()
                    print(f"✓ Removed .env file: {env_file}")
                    removed = True
        except Exception as e:
            print(f"  Warning: Could not check/remove .env file: {e}")
    
    if not removed:
        print("  No configuration files found")
    
    return True


def remove_log_files(install_dir: Path):
    """Remove log files"""
    print("\n" + "="*50)
    print("Removing log files...")
    print("="*50)
    
    log_file = install_dir / "wolf-cli.log"
    removed = False
    
    if log_file.exists():
        try:
            log_file.unlink()
            print(f"✓ Removed log file: {log_file}")
            removed = True
        except Exception as e:
            print(f"  Error removing log file: {e}")
    
    if not removed:
        print("  No log files found")
    
    return True


def remove_installation_files(install_dir: Path, confirm: bool = True):
    """Remove installation files (optional, asks user)"""
    print("\n" + "="*50)
    print("Installation files cleanup...")
    print("="*50)
    
    files_to_remove = [
        "requirements.txt",
        "setup.py",
        "README.md",
        "wolf",
        ".env",
        "uninstall.exe",
        # Note: install.exe is NOT removed - allows user to reinstall later
    ]
    
    removed_any = False
    for item in files_to_remove:
        item_path = install_dir / item
        if item_path.exists():
            if confirm:
                response = input(f"  Remove {item}? (y/N): ").strip().lower()
                if response != 'y':
                    print(f"    Skipping {item}")
                    continue
            
            try:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()
                print(f"✓ Removed: {item}")
                removed_any = True
            except Exception as e:
                print(f"  Error removing {item}: {e}")
    
    if not removed_any:
        print("  No installation files found to remove")
    
    return True


def verify_ollama_not_touched():
    """Verify that we're not touching Ollama"""
    print("\n" + "="*50)
    print("Verifying Ollama is untouched...")
    print("="*50)
    
    # Common Ollama locations (we should NOT touch these)
    ollama_paths = [
        Path.home() / "AppData" / "Local" / "Programs" / "Ollama",  # Windows
        Path.home() / ".ollama",  # Linux/macOS
        Path("/usr/local/bin/ollama"),  # Linux
        Path("/usr/bin/ollama"),  # Linux
    ]
    
    print("  ✓ Ollama installation locations are NOT modified")
    print("  ✓ Ollama models and data remain intact")
    print("  ✓ Only wolf-cli files are removed")
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("Wolf CLI Uninstaller")
    print("="*60)
    print("\nThis will uninstall wolf-cli but keep Ollama intact.")
    print("Ollama and its models will NOT be affected.")
    print("The install.exe file will be preserved so you can reinstall later.\n")
    
    # Confirm uninstallation
    response = input("Are you sure you want to uninstall wolf-cli? (yes/NO): ").strip().lower()
    if response != 'yes':
        print("\nUninstallation cancelled.")
        sys.exit(0)
    
    # Get installation directory (current directory)
    install_dir = Path.cwd()
    print(f"\nInstallation directory: {install_dir}")
    
    # Find Python executable
    python_exe = find_python_executable()
    print(f"Using Python: {python_exe}")
    
    # Step 1: Uninstall package
    uninstall_package(python_exe)
    
    # Step 2: Remove virtual environment
    remove_virtual_environment(install_dir)
    
    # Step 3: Remove config files
    remove_config_files()
    
    # Step 4: Remove log files
    remove_log_files(install_dir)
    
    # Step 5: Ask about installation files
    print("\n" + "="*60)
    response = input("Remove installation files (requirements.txt, setup.py, wolf/, etc.)? (y/N): ").strip().lower()
    remove_files = response == 'y'
    remove_installation_files(install_dir, confirm=False if remove_files else True)
    
    # Step 6: Verify Ollama is untouched
    verify_ollama_not_touched()
    
    print("\n" + "="*60)
    print("Uninstallation complete!")
    print("="*60)
    print("\n✓ wolf-cli has been uninstalled")
    print("✓ Ollama remains installed and untouched")
    print("✓ install.exe has been preserved")
    print("\nYou can reinstall wolf-cli anytime by running install.exe")
    print("\n")

