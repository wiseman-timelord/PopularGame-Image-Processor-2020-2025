import os
import xml.etree.ElementTree as ET
import subprocess
import shutil
from . import globals  # Use a relative import within the package

# --- Constants ---
EXTRACTION_TOOL_NAME = 'TpacToolCli.exe'
EXTRACTION_TOOL_PATH = os.path.join('data', EXTRACTION_TOOL_NAME)

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

    This is a placeholder function. The actual implementation would be complex.
    It returns a more detailed structure to allow for update/revert logic.
    """
    print("\nStarting texture database build (placeholder)...")
    if not os.path.exists(EXTRACTION_TOOL_PATH):
        print(f"CRITICAL: Extraction tool '{EXTRACTION_TOOL_NAME}' not found. Cannot build database.")
        return {}

    # This override directory is where we will place new loose files that were originally from a .tpac
    # It should be a module that loads last.
    override_dir = os.path.join(game_path, 'Modules', 'zzBannerlordTextureProcessorOverride')

    # --- More Detailed Placeholder Example ---
    texture_db = {
        # This texture was a loose file in a mod, so we'll overwrite it in place.
        'armors\\a_placeholder_armor.dds': {
            'source_type': 'loose',
            'source_path': os.path.join(game_path, 'Modules', 'SomeMod', 'Assets', 'armors', 'a_placeholder_armor.dds'),
            'destination_path': os.path.join(game_path, 'Modules', 'SomeMod', 'Assets', 'armors', 'a_placeholder_armor.dds')
        },
        # This texture was in a .tpac, so we create it as a new loose file in our override module.
        'items\\another_placeholder_item.dds': {
            'source_type': 'tpac',
            'source_path': os.path.join(game_path, 'Modules', 'Native', 'AssetPackages', 'core.tpac'),
            'destination_path': os.path.join(override_dir, 'Assets', 'items', 'another_placeholder_item.dds')
        }
    }
    print(f"Database build complete. Found {len(texture_db)} unique textures (placeholder).")
    # Save the DB to a file so other functions can use it without re-running the scan
    db_path = os.path.join('data', 'texture_database.json')
    with open(db_path, 'w') as f:
        json.dump(texture_db, f, indent=4)
    print(f"Texture database saved to {db_path}")
    return texture_db

def extract_textures(texture_db, output_dir):
    """
    Extracts textures from the database to the specified output directory.
    It will copy loose files and use the CLI tool for .tpac files.

    This is a placeholder function.
    """
    print(f"\nStarting texture extraction to '{output_dir}' (placeholder)...")
    if not texture_db:
        print("Texture database is empty. Nothing to extract.")
        return

    os.makedirs(output_dir, exist_ok=True)
    extracted_count = 0

    for texture_path, source_path in texture_db.items():
        # This is where the logic for calling TpacToolCli.exe would go.
        # Example command:
        # TpacToolCli.exe extract --package "C:\...\core.tpac" --files "textures\another_texture.dds" --output "C:\...\processed_textures"

        # Placeholder logic:
        print(f"  - Pretending to extract '{texture_path}' from '{source_path}'")
        extracted_count += 1

    print(f"\nExtraction complete. Processed {extracted_count} textures (placeholder).")

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
