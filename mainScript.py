import os
import sys
import time
from scripts import globals
from scripts import display
from scripts import utilities
from scripts import processing
    """
    Counts all files in a given directory.
    Returns 0 if the directory does not exist.
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return 0

    return len([name for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))])

def show_main_menu():
    """
    Clears the screen and displays the main menu with current application status.
    """
    display.clear_screen()
    display.print_header(globals.APP_NAME)

    # Gather statistics for display
    original_count = count_files(globals.ORIGINAL_TEXTURES_DIR)
    processed_count = count_files(globals.PROCESSED_TEXTURES_DIR)

    # This is a simplification. The actual game textures are spread across many folders.
    # We will refine this logic later. For now, we point to the game's root /Data directory.
    game_data_dir = os.path.join(globals.bannerlord_game_path, 'Data') if globals.bannerlord_game_path else ''
    game_textures_count = count_files(game_data_dir)

    current_setting = globals.config.get('resizing_setting', 'Not Set')

    print("Status:")
    print(f"  - Original Textures Stored: {original_count}")
    print(f"  - Processed Textures Stored: {processed_count}")
    print(f"  - Loose Textures in Game Folder: {game_textures_count} (from {game_data_dir or 'N/A'})")
    print(f"  - Current Resize Setting: {current_setting}")
    print("")

    display.print_separator('-')
    print("Menu:")
    print("  1) Set Resize Option")
    print("  2) Process Textures")
    print("  3) Update Game Folder")
    print("  4) Revert to Original")
    print("  5) Re-Scan Textures & Build Database")
    print("  X) Exit")
    display.print_separator('-')

def show_resize_submenu():
    """Shows the menu for selecting a texture size limit."""
    display.clear_screen()
    display.print_header("Set Texture Resize Limit")

    options = {'1': 4096, '2': 2048, '3': 1024, '4': 512}

    print("Choose the maximum texture dimension (width or height):")
    for key, value in options.items():
        print(f"  {key}) Trim textures to {value}x{value}")
    print("  B) Back to Main Menu")

    while True:
        choice = input("Enter your choice: ").strip().upper()
        if choice in options:
            limit = options[choice]
            processing.save_resize_setting(limit)
            time.sleep(2)
            break
        elif choice == 'B':
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    """
    Main application function. Initializes data and runs the main menu loop.
    """
    # Initialize globals: load config, create dirs, etc.
    globals.initialize()

    # First-time check to ensure the installer has been run.
    if not globals.bannerlord_game_path:
        display.print_header(globals.APP_NAME)
        print("\nERROR: Bannerlord game path has not been configured.")
        print("Please run the installer (Option 2 from the batch launcher) first.")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    while True:
        show_main_menu()
        choice = input("Enter your choice: ").strip().upper()

        if choice == 'X':
            print("Exiting...")
            break
        elif choice == '1':
            show_resize_submenu()
        elif choice == '2':
            limit = globals.config.get('resizing_setting')
            if not limit:
                print("No resize setting selected. Please set one using Option 1 first.")
                time.sleep(3)
                continue

            try:
                default_workers = os.cpu_count()
                num_workers_str = input(f"Enter number of parallel workers (default: {default_workers}): ").strip()
                num_workers = int(num_workers_str) if num_workers_str else default_workers
            except (ValueError, TypeError):
                num_workers = default_workers

            processing.process_textures_parallel(limit, num_workers)
            input("\nProcessing complete. Press Enter to return to the main menu.")
        elif choice == '3':
            display.clear_screen()
            display.print_header("Update Game Folder")
            print("WARNING: This will copy processed textures into your game folder,")
            print("overwriting any existing modified textures.")
            confirm = input("Are you sure you want to continue? (y/n): ").strip().lower()
            if confirm == 'y':
                utilities.update_game_folder()
            else:
                print("Update cancelled.")
            input("\nPress Enter to return to the main menu.")
        elif choice == '4':
            display.clear_screen()
            display.print_header("Revert to Original")
            print("WARNING: This will revert any processed textures in your game folder")
            print("back to their original state, deleting new files or restoring backups.")
            confirm = input("Are you sure you want to continue? (y/n): ").strip().lower()
            if confirm == 'y':
                utilities.revert_to_original()
            else:
                print("Revert cancelled.")
            input("\nPress Enter to return to the main menu.")
        elif choice == '5':
            utilities.run_full_texture_scan()
            input("\nScan complete. Press Enter to return to the main menu.")
        else:
            print(f"'{choice}' is not a valid option. Please try again.")
            time.sleep(2)

if __name__ == "__main__":
    main()
