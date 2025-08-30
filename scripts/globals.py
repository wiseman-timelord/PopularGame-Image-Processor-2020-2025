import json
import os

# --- Application Constants ---
APP_NAME = "Bannerlord2 Texture Processor"
CONFIG_FILE = os.path.join('data', 'persistent.json')
ORIGINAL_TEXTURES_DIR = os.path.join('data', 'original_textures')
PROCESSED_TEXTURES_DIR = os.path.join('processed_textures')

# --- Global Variables ---
# These will be populated by the load_configuration function
config = {}
bannerlord_game_path = None

def load_configuration():
    """
    Loads the configuration from the persistent JSON file into global variables.
    """
    global config, bannerlord_game_path
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                config = json.load(f)
                bannerlord_game_path = config.get('bannerlord_game_path')
            except json.JSONDecodeError:
                print(f"WARNING: Could not parse '{CONFIG_FILE}'. It might be corrupted.")
                config = {}
    else:
        print(f"WARNING: Configuration file not found. Please run the installer first.")

def initialize():
    """
    Initializes global data and ensures required directories exist.
    This should be called once at the start of the main script.
    """
    # Ensure data directories exist
    os.makedirs(ORIGINAL_TEXTURES_DIR, exist_ok=True)
    os.makedirs(PROCESSED_TEXTURES_DIR, exist_ok=True)

    # Load settings from file
    load_configuration()
