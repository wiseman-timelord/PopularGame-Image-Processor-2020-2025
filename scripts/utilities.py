import os
import xml.etree.ElementTree as ET
import subprocess
import shutil
import sys
import json
from . import globals  # Use a relative import within the package

# --- Constants ---
# Check for the simulator first, then the real tool.
if os.path.exists(os.path.join('data', 'TpacToolCli.py')):
    EXTRACTION_TOOL_CMD = [sys.executable, os.path.join('data', 'TpacToolCli.py')]
    print("INFO: Using 'TpacToolCli.py' simulator.")
else:
    EXTRACTION_TOOL_CMD = [os.path.join('data', 'TpacToolCli.exe')]

# --- Core Functions ---

def get_load_order_path():
    """
    Constructs the platform-independent path to the Bannerlord launcher config file.

    Returns:
        str: The full path to LauncherData.xml, or None if it can't be determined.
    """
    try:
        # User's documents folder is the most reliable place to find this
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
        return os.path.join(docs_path, 'Mount and Blade II Bannerlord', 'Configs', 'LauncherData.xml')
    except Exception as e:
        print(f"ERROR: Could not determine user's documents folder. {e}")
        return None

def parse_load_order(file_path):
    """
    Parses the LauncherData.xml to get the list of active mods in order.

    Args:
        file_path (str): The path to LauncherData.xml.

    Returns:
        list: An ordered list of mod IDs (strings). Returns an empty list on failure.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: Load order file not found at '{file_path}'")
        return []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # The modules are listed under the 'LoadOrder' element
        mod_nodes = root.findall('.//LoadOrder/Module')
        mod_ids = [mod.get('Id') for mod in mod_nodes if mod.get('Id')]
        print(f"Found {len(mod_ids)} mods in load order.")
        return mod_ids
    except ET.ParseError as e:
        print(f"ERROR: Failed to parse XML file '{file_path}'. It may be corrupt. {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while parsing the load order: {e}")
        return []

def build_texture_database(game_path, mod_order):
    """
    Scans game files and mods to build a database of the highest priority textures.
    """
    print("\nStarting texture database build...")

    # In a real scenario, we would check if the tool exists here.
    # The installer already does this, so we can assume it's present.

    texture_db = {}
    # This override directory is where we will place new loose files that were originally from a .tpac
    override_dir = os.path.join(game_path, 'Modules', 'zzBannerlordTextureProcessorOverride')

    # In a real implementation, we would iterate through each mod's AssetPackages folder.
    # For this simulation, we just call the tool once on the Native module path.
    native_assets_path = os.path.join(game_path, 'Modules', 'Native', 'AssetPackages')

    print(f"Scanning for assets in '{native_assets_path}'...")
    cmd = EXTRACTION_TOOL_CMD + ['list', '--asset_dir', native_assets_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        asset_list = result.stdout.strip().splitlines()
        print(f"Simulator found {len(asset_list)} assets.")

        for asset_path in asset_list:
            # For this simulation, we'll assume all found assets are from a .tpac
            # and their destination is our override module.
            texture_db[asset_path] = {
                'source_type': 'tpac',
                'source_path': os.path.join(native_assets_path, 'SIMULATED.tpac'), # Dummy source
                'destination_path': os.path.join(override_dir, 'Assets', asset_path)
            }

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR: Failed to run the texture extraction tool: {e}")
        print("Please ensure it is placed in the 'data' directory and is executable.")
        return {}

    print(f"Database build complete. Found {len(texture_db)} unique textures.")
    db_path = os.path.join('data', 'texture_database.json')
    with open(db_path, 'w') as f:
        json.dump(texture_db, f, indent=4)
    print(f"Texture database saved to {db_path}")
    return texture_db

def extract_textures(texture_db, output_dir):
    """
    Extracts textures from the database to the specified output directory.
    It will copy loose files and use the CLI tool for .tpac files.
    """
    print(f"\nStarting texture extraction to '{output_dir}'...")
    if not texture_db:
        print("Texture database is empty. Nothing to extract.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # We can extract files in batches.
    files_to_extract = [path for path, data in texture_db.items() if data['source_type'] == 'tpac']

    if not files_to_extract:
        print("No textures to extract from .tpac files.")
        return

    print(f"Extracting {len(files_to_extract)} textures...")
    # In a real scenario, we might need to chunk this for very long command lines.
    cmd = EXTRACTION_TOOL_CMD + [
        'extract',
        '--asset_dir', os.path.join(globals.bannerlord_game_path, 'Modules', 'Native', 'AssetPackages'),
        '--output', output_dir,
        '--files'
    ] + files_to_extract

    try:
        # The simulator will create dummy files in the output directory.
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Extraction complete.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR: Failed to run the texture extraction tool for extraction: {e}")


def update_game_folder():
    """
    Copies processed textures to the game directory, overwriting as needed.
    """
    print("\n--- Starting Game Folder Update ---")
    db_path = os.path.join('data', 'texture_database.json')
    processed_dir = globals.PROCESSED_TEXTURES_DIR

    if not os.path.exists(db_path):
        print("ERROR: Texture database not found. Please run a scan first (Option 5).")
        return

    with open(db_path, 'r') as f:
        texture_db = json.load(f)

    if not texture_db:
        print("Texture database is empty. Nothing to update.")
        return

    updated_count = 0
    for canonical_path, data in texture_db.items():
        processed_filename = os.path.basename(canonical_path)
        processed_path = os.path.join(processed_dir, processed_filename)
        destination_path = data['destination_path']

        if os.path.exists(processed_path):
            print(f"Copying '{processed_path}' to '{destination_path}'")
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(processed_path, destination_path)
            updated_count += 1
        else:
            print(f"WARNING: Processed file not found for '{canonical_path}', skipping.")

    print(f"\nUpdate complete. Copied {updated_count} files to game directory.")

def revert_to_original():
    """
    Reverts modified textures back to their original state.
    """
    print("\n--- Starting Revert to Original ---")
    db_path = os.path.join('data', 'texture_database.json')
    original_dir = globals.ORIGINAL_TEXTURES_DIR

    if not os.path.exists(db_path):
        print("ERROR: Texture database not found. Please run a scan first (Option 5).")
        return

    with open(db_path, 'r') as f:
        texture_db = json.load(f)

    if not texture_db:
        print("Texture database is empty. Nothing to revert.")
        return

    reverted_count = 0
    for canonical_path, data in texture_db.items():
        destination_path = data['destination_path']

        if data['source_type'] == 'tpac':
            # This file was created by us, so reverting means deleting it.
            if os.path.exists(destination_path):
                print(f"Deleting '{destination_path}' (was originally from .tpac)")
                os.remove(destination_path)
                reverted_count += 1

        elif data['source_type'] == 'loose':
            # This file was a loose file originally, so we copy our backup over it.
            original_filename = os.path.basename(canonical_path)
            original_path = os.path.join(original_dir, original_filename)
            if os.path.exists(original_path):
                print(f"Restoring '{original_path}' to '{destination_path}'")
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy2(original_path, destination_path)
                reverted_count += 1
            else:
                print(f"WARNING: Original texture backup not found for '{canonical_path}', skipping.")

    print(f"\nRevert complete. Restored/deleted {reverted_count} files.")

def run_full_texture_scan():
    """
    Orchestrates the entire process of scanning and building the database.
    """
    print("--- Starting Full Texture Scan ---")

    # 1. Get Load Order
    load_order_file = get_load_order_path()
    if not load_order_file:
        return

    mod_list = parse_load_order(load_order_file)
    if not mod_list:
        print("Could not establish mod load order. Aborting scan.")
        return

    # 2. Build Database (using placeholder)
    if not globals.bannerlord_game_path:
        print("Game path not set. Cannot build texture database.")
        return

    db = build_texture_database(globals.bannerlord_game_path, mod_list)

    # 3. Extract Textures (using placeholder)
    extract_textures(db, globals.ORIGINAL_TEXTURES_DIR)

    print("\n--- Full Texture Scan Finished ---")
