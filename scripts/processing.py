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
        args (tuple): A tuple containing (source_path, output_path, limit).

    Returns:
        str: A status message for the processed file.
    """
    source_path, output_path, limit = args
    try:
        # Ensure the output directory for the file exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with Image.open(source_path) as img:
            width, height = img.size

            if width > limit or height > limit:
                # Calculate new dimensions while maintaining aspect ratio
                ratio = min(limit / width, limit / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)

                # Resize using a high-quality downsampling filter
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized_img.save(output_path)
                return f"Resized {os.path.basename(source_path)} to {new_width}x{new_height}"
            else:
                # If the image is smaller than the limit, just copy it
                shutil.copy2(source_path, output_path)
                return f"Copied {os.path.basename(source_path)} (already within limit)"

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

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory not found: {source_dir}")
        return

    # Get a list of all files to process
    tasks = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.dds', '.png', '.tga', '.jpg', '.jpeg')):
            source_path = os.path.join(source_dir, filename)
            output_path = os.path.join(output_dir, filename)
            tasks.append((source_path, output_path, limit))

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
