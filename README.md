# PopularGame-Image-Processor-2020-2025
Status: Planning

# Description
Its a Image Processor for PopularGames from 2020-2025, these game feature on nexus, and may at some point include: CyberPunk 2077, Baldurs Gate 3, Mount & Blade 2, Resident Evil 4, Resident Evil Village, Monster Hunter Rise, Witcher 3, Hogwards Legacy. Starting with Bannerlord 2, and possibly finishing wihtout doing them all, but I would likely do more if there is some kind of relating, sponsorship or high endorsement, response(s) (which was not the case with my previous ESP cleaner for Bethesda games, because done in powershell). 

# Features
- Batch Launcher: A simple Windows batch file provides a menu to run the installer or the main application.
- Automated Installer: A setup script handles all dependency installation and configuration for the user.
- Automatic Game Detection: The installer automatically finds the target game's installation path by reading the Windows registry.
- High-Speed Converter Setup: The installer downloads the industry-standard texconv.exe tool and configures it for multi-threaded use.
- Configurable Parallel Processing: Users can choose how many parallel processes (1-6) to use for converting textures.
- Texture Source Analysis: The application is designed to scan game archives and loose mod files to find all relevant textures.
- Mod Priority Handling: It reads the game's mod load order to ensure textures are processed with the correct override priority.
- Centralized Texture Database: A JSON database is created to track the source and destination of every texture.
- Non-Destructive Workflow: Original textures are backed up to a local data folder before any processing occurs.
- Advanced Resizing: Textures can be proportionally downscaled to user-selected size limits (e.g., 4096, 2048, 1024, 512).
- Selectable Compression Formats: Users can choose the output DDS format (e.g., BC3, BC7) for a balance of quality and file size.
- Smart Alpha Handling: The tool automatically uses an alpha-compatible compression format for textures that contain transparency.
- Game Folder Updating: Processed textures can be copied into the game's folders with a single command to apply the changes.
- Safe Revert Option: All changes made to the game's files can be safely and completely reverted to their original state.

## Development
- Progress - Project detailed in a prompt, and handed to Jules to speed up creation, it will upload to a cloned folder. It understands to put the individual tools in individual subfolders from the main github repository, ie ~/PopularGame-Image-Processor-2020-2025/**GameTitle**/.
- Here are the research notes...

| Game                                | Launch window   | Nexus mods footprint       | Compressed format(s)     | Extraction tool(s)              | Tool package       | Installed footprint | Kept for processor |
| ----------------------------------- | --------------- | -------------------------- | ------------------------ | ------------------------------- | ------------------ | ------------------- | ------------------ |
| Cyberpunk 2077                      | Dec 2020        | 5 000+ mods / 30 M+ DL     | `.archive` (REDengine 4) | WolvenKit CLI                   | zip (portable)     | ≈ 110 GB            | ✅                  |
| Baldur’s Gate 3                     | Aug 2023        | 4 000+ mods / rapid growth | `.pak` + `.lsf`          | ExportTool (LSLib)              | zip (portable)     | ≈ 150 GB            | ✅                  |
| Mount & Blade II: Bannerlord        | Oct 2022        | 3 600+ mods / 14 M+ DL     | `.tpac` / `.bfx`         | TaleWorlds Modding Tools        | zip (no installer) | ≈ 60 GB             | ✅                  |
| Resident Evil 4 (2023 remake)       | Mar 2023        | 2 000+ mods / 5 M+ DL      | `.pak` (RE Engine)       | REE.Unpacker                    | zip (single exe)   | ≈ 58 GB             | ✅                  |
| Resident Evil Village               | May 2021        | 1 500+ mods / 4 M+ DL      | `.pak` (RE Engine)       | REE.Unpacker                    | zip (single exe)   | ≈ 50 GB             | ✅                  |
| Monster Hunter Rise                 | Jan 2022        | 2 000+ mods / 7 M+ DL      | `.pak` + `.arc`          | MHRUnpack + Rise PAK Patch Tool | zip (portable)     | ≈ 36 GB             | ✅                  |
| The Witcher 3: Wild Hunt – Next-Gen | Dec 2022 update | 5 000+ mods / 60 M+ DL     | `.bundle` + `.cache`     | WolvenKit CLI                   | zip (portable)     | ≈ 100 GB            | ✅                  |
| Hogwarts Legacy                     | Feb 2023        | 2 500+ mods / 6 M+ DL      | `.pak` (Unreal Engine 4) | FModel + UE4SS                  | zip (portable)     | ≈ 85 GB             | ✅                  |

# Logic
LOGIC SUMMARY...
1. **Install**  
   - Auto-install Pillow, Requests, texconv.exe.  
   - Ask for thread count → create data/texConv_N folders with texconv.exe copies.  
   - Store game path & settings in data/persistent.json.
2. **Scan**  
   - Read mod load order.  
   - Extract every texture from game + mods (via TpacToolCli).  
   - Pick highest-priority version → save mapping to data/texture_database.json.  
   - Backup originals to data/original_textures.
3. **Process**  
   - User sets resize limit & format.  
   - Split backup list into chunks → spawn N instance.py workers (one per thread).  
   - Each worker uses its texconv.exe to resize/compress → output to processed_textures.
4. **Deploy / Revert**  
   - **Update:** copy processed .dds files to their game paths.  
   - **Revert:** restore from backup or delete loose override so game uses archived original.
