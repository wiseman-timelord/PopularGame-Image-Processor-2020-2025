import os
import sys
import json
import subprocess
from tqdm import tqdm
from . import globals

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

def process_textures_parallel(limit):
    """
    Processes all textures from the original_textures directory in parallel
    by launching multiple instances of the instance.py worker script.

    Args:
        limit (int): The maximum dimension (width or height) for the textures.
    """
    source_dir = globals.ORIGINAL_TEXTURES_DIR
    output_dir = globals.PROCESSED_TEXTURES_DIR

    thread_count = globals.config.get('texconv_thread_count', 1)
    format_str = globals.config.get('format_setting', 'BC7_UNORM') # Default to BC7

    if not os.path.exists(source_dir):
        print(f"ERROR: Source directory not found: {source_dir}")
        return

    all_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.lower().endswith(('.dds', '.png', 'tga', '.jpg', '.jpeg'))]

    if not all_files:
        print("No textures found in the source directory to process.")
        return

    # Divide the work into chunks for each instance
    chunks = [all_files[i::thread_count] for i in range(thread_count)]

    print(f"\nStarting parallel processing of {len(all_files)} textures with {thread_count} instances...")

    processes = []
    for i in range(thread_count):
        instance_num = i + 1
        file_chunk = chunks[i]

        if not file_chunk:
            continue

        command = [
            sys.executable,
            os.path.join('scripts', 'instance.py'),
            '--instance-num', str(instance_num),
            '--limit', str(limit),
            '--format', format_str,
            '--output-dir', output_dir,
            '--files', *file_chunk
        ]

        # Launch the worker process
        # We can pipe the output to see real-time progress from workers
        processes.append(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))

    # Monitor the processes
    with tqdm(total=len(all_files), desc="Processing Textures") as pbar:
        for p in processes:
            # You can read stdout line by line for real-time feedback
            for line in iter(p.stdout.readline, ''):
                # print(line.strip()) # This would be too verbose, but good for debugging
                if "SUCCESS" in line or "ERROR" in line:
                    pbar.update(1)
            p.wait() # Wait for the process to finish

    print("\n--- Processing Complete ---")

    # Check for errors
    for p in processes:
        stderr = p.stderr.read()
        if stderr:
            print(f"--- Errors from Instance {p.pid} ---\n{stderr.strip()}\n--------------------")

    print("--- End of Summary ---")
