import os
import sys
import json
import subprocess
import winreg
import shutil
import requests
from tqdm import tqdm

# --- UI Functions ---

def get_console_width():
    """Gets the width of the console."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80  # Default width

def print_separator(width):
    """Prints a separator line."""
    print("#" * width)

def print_header(title, width):
    """Prints a formatted header."""
    print_separator(width)
    print(title)
    print_separator(width)

# --- Core Installer Functions ---

def find_bannerlord_path():
    """
    Finds the Bannerlord 2 installation path in the Windows registry.
    It checks the common Steam uninstall key.
    """
    try:
        key_path = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 261550"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            install_path, _ = winreg.QueryValueEx(key, "InstallLocation")
            return install_path
    except FileNotFoundError:
        print("INFO: Bannerlord 2 registry key not found. This is normal if not installed via Steam.")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while reading the registry: {e}")
        return None

def save_config(data):
    """Saves the given data to the persistent JSON file."""
    if not os.path.exists('data'):
        os.makedirs('data')

    config_path = 'data/persistent.json'
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                existing_config = json.load(f)
            except json.JSONDecodeError:
                print("WARNING: Could not read existing config, it will be overwritten.")

    existing_config.update(data)

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=4)
    print(f"Configuration saved to {config_path}")

def install_dependencies():
    """Installs required Python packages using pip."""
    required_packages = {"Pillow", "Pillow-DDS-Plugin", "tqdm", "requests"}
    print(f"Checking and installing required packages: {', '.join(required_packages)}")
    try:
        # Using sys.executable to ensure we use the pip from the correct Python interpreter
        subprocess.check_call([sys.executable, "-m", "pip", "install", *required_packages],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Dependencies are up to date.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install Python packages. Please try running pip install manually.")
        print(f"Error details: {e}")
        return False
    except FileNotFoundError:
        print("ERROR: 'pip' command not found. Is Python installed and in your PATH?")
        return False

def download_file(url, target_path):
    """Downloads a file from a URL to a target path with a progress bar."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with open(target_path, 'wb') as f, tqdm(
            desc=os.path.basename(target_path),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
        return True
    except requests.exceptions.RequestException as e:
        print(f"\nERROR: Failed to download file from {url}. {e}")
        return False

def setup_texconv_instances():
    """Asks user for thread count and sets up texconv instances."""
    while True:
        try:
            thread_count_str = input("How many threads to install for the converter (1-6)? ")
            thread_count = int(thread_count_str)
            if 1 <= thread_count <= 6:
                break
            else:
                print("Please enter a number between 1 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    print(f"Setting up {thread_count} instances for texconv...")
    save_config({"texconv_thread_count": thread_count})

    default_converter_path = os.path.join('data', 'default_converter', 'texconv.exe')
    if not os.path.exists(default_converter_path):
        print("ERROR: texconv.exe not found in the default location. Cannot create instances.")
        return False

    for i in range(1, thread_count + 1):
        instance_dir = os.path.join('data', f'texConv_{i}')
        os.makedirs(instance_dir, exist_ok=True)
        shutil.copy2(default_converter_path, os.path.join(instance_dir, 'texconv.exe'))

    print("texconv instances created successfully.")
    return True

# --- Main Execution ---

def main():
    """Main function to run the installer steps."""
    width = get_console_width()
    print_header("Bannerlord2 Texture Processor: Installation", width)

    results = []

    # 1. Find Game Directory
    print("\nStep 1: Locating Bannerlord 2 Directory...")
    game_path = find_bannerlord_path()
    if game_path and os.path.exists(game_path):
        print(f"SUCCESS: Game found at: {game_path}")
        results.append(("Locate Game Directory", "PASS"))
        # Save path to config
        save_config({"bannerlord_game_path": game_path})
    else:
        print("CRITICAL: Bannerlord 2 installation directory not found.")
        print("The program may not function correctly without this path.")
        results.append(("Locate Game Directory", "FAIL"))

    # 2. Install Dependencies
    print("\nStep 2: Checking Python Dependencies...")
    if install_dependencies():
        results.append(("Install Python Packages", "PASS"))
    else:
        results.append(("Install Python Packages", "FAIL"))

    # 3. Check for Texture Extraction Tool
    print("\nStep 3: Checking for Texture Extraction Tool...")
    tool_path = os.path.join('data', 'TpacToolCli.exe')
    if os.path.exists(tool_path):
        print(f"SUCCESS: Found TpacToolCli.exe at: {tool_path}")
        results.append(("Find Extraction Tool", "PASS"))
    else:
        print("CRITICAL: The texture extraction tool was not found.")
        print(f"Please download 'TpacTool' from: https://github.com/szszss/TpacTool/releases")
        print(f"Then, find 'TpacToolCli.exe' in the downloaded archive and place it in the '{os.path.join(os.getcwd(), 'data')}' directory.")
        results.append(("Find Extraction Tool", "FAIL"))

    # 4. Download and Set Up Texture Converter (texconv)
    print("\nStep 4: Setting up Texture Converter (texconv.exe)...")
    texconv_url = "https://github.com/Microsoft/DirectXTex/releases/latest/download/texconv.exe"
    default_converter_dir = os.path.join('data', 'default_converter')
    os.makedirs(default_converter_dir, exist_ok=True)
    texconv_path = os.path.join(default_converter_dir, 'texconv.exe')

    if not os.path.exists(texconv_path):
        print(f"Downloading texconv.exe from {texconv_url}...")
        if download_file(texconv_url, texconv_path):
            print("Download successful.")
            if setup_texconv_instances():
                results.append(("Setup texconv.exe", "PASS"))
            else:
                results.append(("Setup texconv.exe", "FAIL"))
        else:
            print("CRITICAL: Failed to download texconv.exe.")
            results.append(("Setup texconv.exe", "FAIL"))
    else:
        print("texconv.exe already exists. Re-running setup for instances.")
        if setup_texconv_instances():
            results.append(("Setup texconv.exe", "PASS"))
        else:
            results.append(("Setup texconv.exe", "FAIL"))

    # 5. Final Results
    print("\n")
    print_header("Installation Results", width)

    overall_status = "PASS"
    for task, status in results:
        status_text = f"[{status}]"
        # Pad task name to align status to the right
        padding = width - len(task) - len(status_text)
        print(f"{task}{' ' * padding}{status_text}")
        if status == "FAIL":
            overall_status = "FAIL"

    print_separator(width)
    print(f"Overall Status: {overall_status}")
    if overall_status == "FAIL":
        print("One or more setup steps failed. Please review the output above.")
    else:
        print("Setup completed successfully.")
    print_separator(width)


if __name__ == "__main__":
    main()
