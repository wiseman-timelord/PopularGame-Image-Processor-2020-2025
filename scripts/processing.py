import os
import shutil
import json
import concurrent.futures
from PIL import Image
from tqdm import tqdm
from . import globals

# This is necessary to enable DDS support in Pillow
try:
    from PIL import DdsImagePlugin
except ImportError:
    print("WARNING: Pillow-DDS-Plugin not found. DDS file support will be limited.")

def save_format_setting(format_str):
    """
    Saves the chosen DDS format to the persistent config file.
    """
    config_path = globals.CONFIG_FILE
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                existing_config = json.load(f)
            except json.JSONDecodeError:
                print(f"WARNING: Could not read existing config at {config_path}.")

    existing_config['format_setting'] = format_str

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=4)

    # Also update the currently loaded globals
    globals.config['format_setting'] = format_str
    print(f"Format setting saved: {format_str}")

def save_resize_setting(limit):
    """
    Saves the chosen resize limit to the persistent config file.
    """
    config_path = globals.CONFIG_FILE
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                existing_config = json.load(f)
            except json.JSONDecodeError:
                print(f"WARNING: Could not read existing config at {config_path}.")

    existing_config['resizing_setting'] = limit

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=4)

    # Also update the currently loaded globals
    globals.config['resizing_setting'] = limit
    print(f"Resize setting saved: {limit}px")

def resize_image(args):
    """
    Worker function to resize a single image. Designed to be called by a ProcessPoolExecutor.

    Args:
        args (tuple): A tuple containing (source_path, output_path, limit, format_str).

    Returns:
        str: A status message for the processed file.
    """
    source_path, output_path, limit, format_str = args
    try:
        # Ensure the output directory for the file exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with Image.open(source_path) as img:
            # Detect alpha channel
            has_alpha = img.mode in ('RGBA', 'LA')

            # Smart format selection
            # The user requested DXT5 (BC3) or BC7 for alpha textures.
            # BC2 also supports alpha, but BC3 is better for gradients.
            # We will auto-upgrade to BC3 if a non-alpha format is chosen for an alpha texture.
            effective_format = format_str
            if has_alpha and format_str in ['BC1']: # BC1 is DXT1, a common non-alpha format
                 print(f"INFO: Upgrading {os.path.basename(source_path)} to BC3 due to alpha channel.")
                 effective_format = 'BC3'

            width, height = img.size

            # Determine if resizing is needed
            if width > limit or height > limit:
                ratio = min(limit / width, limit / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)

                # Resize using a high-quality downsampling filter
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # If the source had no alpha but we are saving to a format that supports it,
                # we might need to convert the mode. Pillow usually handles this, but being explicit is safer.
                if not has_alpha and resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')

                resized_img.save(output_path, format=effective_format)
                return f"Resized {os.path.basename(source_path)} to {new_width}x{new_height} ({effective_format})"
            else:
                # If not resizing, we still might need to re-compress to the target format.
                img.save(output_path, format=effective_format)
                return f"Re-saved {os.path.basename(source_path)} with new format ({effective_format})"

    except Exception as e:
        return f"ERROR processing {os.path.basename(source_path)}: {e}"

def process_textures_parallel(limit, num_workers):
    """
    Processes all textures from the original_textures directory in parallel.

    Args:
        limit (int): The maximum dimension (width or height) for the textures.
        num_workers (int): The number of parallel processes to use.
    """
    source_dir = globals.ORIGINAL_TEXTURES_DIR
    output_dir = globals.PROCESSED_TEXTURES_DIR

    # Get the desired output format from the global config
    # Default to BC7 for highest quality if not set.
    format_str = globals.config.get('format_setting', 'BC7')

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory not found: {source_dir}")
        return

    # Get a list of all files to process
    tasks = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.dds', '.png', '.tga', '.jpg', '.jpeg')):
            source_path = os.path.join(source_dir, filename)
            # All output is .dds
            output_filename = os.path.splitext(filename)[0] + '.dds'
            output_path = os.path.join(output_dir, output_filename)
            tasks.append((source_path, output_path, limit, format_str))

    if not tasks:
        print("No textures found in the source directory to process.")
        return

    print(f"\nStarting parallel processing of {len(tasks)} textures with {num_workers} workers...")

    # Use ProcessPoolExecutor for true parallelism, bypassing the GIL
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Use tqdm to display a progress bar
        results = list(tqdm(executor.map(resize_image, tasks), total=len(tasks), desc="Processing Textures"))

    print("\n--- Processing Complete ---")
    # Optionally, print a summary of results
    success_count = sum(1 for r in results if not r.startswith("ERROR"))
    error_count = len(results) - success_count
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {error_count}")
    if error_count > 0:
        print("Failures (see details above):")
        for r in results:
            if r.startswith("ERROR"):
                print(f"  - {r}")
    print("--- End of Summary ---")
