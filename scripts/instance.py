import os
import sys
import argparse
import subprocess
from PIL import Image

def process_file(instance_num, source_path, output_dir, limit, format_str):
    """
    Processes a single image file using the assigned texconv.exe instance.
    """
    try:
        # 1. Get image dimensions with Pillow to calculate new size
        with Image.open(source_path) as img:
            width, height = img.size

        new_width, new_height = width, height
        if width > limit or height > limit:
            ratio = min(limit / width, limit / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

        # 2. Construct the texconv command
        texconv_exe_path = os.path.join('data', f'texConv_{instance_num}', 'texconv.exe')

        # Ensure the output subdirectory exists
        # texconv can't create directory trees, so we do it first.
        # This assumes output_dir is the root of processed textures.
        # We need to construct the full output path including any subdirs from the source.
        relative_path = os.path.relpath(source_path, os.path.dirname(os.path.dirname(source_path))) # A bit tricky, assumes source is in a subdir of project root
        output_file_path = os.path.join(output_dir, os.path.splitext(os.path.basename(source_path))[0] + '.dds')

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        command = [
            texconv_exe_path,
            source_path,
            '-w', str(new_width),
            '-h', str(new_height),
            '-f', format_str,
            '-if', 'FANT', # Use Fant for high-quality resizing
            '-m', '0', # Generate all mipmaps
            '-o', output_dir, # texconv places it here
            '-y' # Overwrite existing
        ]

        # 3. Execute the command
        # Using DEVNULL to keep the console clean, but could be captured for logging.
        result = subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

        if result.stderr:
            # texconv sometimes prints warnings to stderr even on success
            print(f"INFO/WARNING [Instance {instance_num}]: {result.stderr.strip()}")

        return f"SUCCESS [Instance {instance_num}]: Processed {os.path.basename(source_path)}"

    except FileNotFoundError:
        return f"ERROR [Instance {instance_num}]: texconv.exe not found at {texconv_exe_path}. Please run the installer."
    except Exception as e:
        return f"ERROR [Instance {instance_num}] processing {os.path.basename(source_path)}: {e}"

def main():
    parser = argparse.ArgumentParser(description="Worker instance for texture processing.")
    parser.add_argument('--instance-num', required=True, type=int, help="The instance number of this worker.")
    parser.add_argument('--limit', required=True, type=int, help="The resize limit.")
    parser.add_argument('--format', required=True, help="The DDS format string.")
    parser.add_argument('--output-dir', required=True, help="The root output directory for processed files.")
    parser.add_argument('--files', nargs='+', required=True, help="List of source image files to process.")

    args = parser.parse_args()

    # This script will be called by the main processing orchestrator.
    # It will print its status to stdout, which can be monitored.
    for f in args.files:
        status = process_file(args.instance_num, f, args.output_dir, args.limit, args.format)
        print(status)

if __name__ == "__main__":
    main()
