import os
import shutil
from pathlib import Path

# Map file extensions to folder names
# Customize these as needed
EXTENSION_MAP = {
    # IMAGES & RAW PHOTOS
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tif", ".tiff", 
        ".ico", ".webp"
    ],
    # RAW camera files (optional, or merge into "Images")
    "CameraRaw": [
        ".raw", ".cr2", ".cr3", ".nef", ".orf", ".raf", ".arw", ".dng"
    ],

    # DOCUMENTS, EBOOKS, SPREADSHEETS, PRESENTATIONS
    "Documents": [
        ".pdf", ".doc", ".docx", ".rtf", ".odt", ".txt", ".wpd", ".tex",
        ".md", ".pages"  # you can add more (like .docm if you wish)
    ],
    "Ebooks": [
        ".epub", ".mobi", ".azw", ".azw3", ".ibooks", ".fb2"
    ],
    "Spreadsheets": [
        ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".csv"
    ],
    "Presentations": [
        ".ppt", ".pptx", ".pps", ".ppsx", ".key", ".odp"
    ],

    # AUDIO & VIDEO
    "Audio": [
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".oga", ".wma", ".m4a", ".alac"
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg"
    ],

    # 3D, CAD, DESIGN, FONTS
    "3D": [
        ".obj", ".fbx", ".stl", ".blend", ".3ds", ".dae", ".gltf", ".glb"
    ],
    "CAD": [
        ".dwg", ".dxf", ".dwf"
    ],
    "Design": [
        ".psd", ".ai", ".eps", ".xd", ".fig", ".sketch"
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".fnt"
    ],

    # WEB & SCRIPTS
    "Web": [
        ".html", ".htm", ".css", ".js", ".ts", ".jsx", ".vue",
        ".php", ".aspx", ".asp", ".jsp", ".json", ".xml"
    ],
    "Scripts": [
        ".py", ".sh", ".bat", ".ps1", ".rb", ".pl", ".cmd"
    ],

    # PROGRAMS / EXECUTABLES
    "Programs": [
        ".exe", ".msi", ".dmg", ".pkg", ".app", ".apk", 
        ".deb", ".rpm", ".bin", ".run"
    ],

    # ARCHIVES & DISC IMAGES
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".lzma", ".tgz"
    ],
    "DiscImages": [
        ".iso", ".img", ".nrg", ".cue", ".bin"
    ],

    # DATABASE & VIRTUAL MACHINES (OPTIONAL)
    "Database": [
        ".sql", ".db", ".mdb", ".accdb", ".dbf", ".sqlite"
    ],
    "VirtualMachines": [
        ".vdi", ".vmdk", ".vhd", ".vhdx", ".ova", ".ovf"
    ],

    # SYSTEM FILES (OPTIONAL) - you may not want to move these often
    "SystemFiles": [
        ".dll", ".sys", ".drv", ".cpl", ".lnk"
    ],

    # CATCH-ALL FOR ANYTHING NOT MATCHED
    "Others": []
}


# Adjust this path if your Downloads folder is in a different location
DOWNLOADS_FOLDER = Path.home() / "Downloads"

def organize_downloads(download_folder: Path = DOWNLOADS_FOLDER):
    # Ensure the folder exists
    if not download_folder.exists():
        print(f"Downloads folder not found: {download_folder}")
        return

    # List all files in the folder
    for item in download_folder.iterdir():
        if item.is_file():
            file_extension = item.suffix.lower()
            moved = False

            # Match file extension to a category
            for folder_name, extensions in EXTENSION_MAP.items():
                if file_extension in extensions:
                    target_folder = download_folder / folder_name
                    target_folder.mkdir(exist_ok=True)
                    shutil.move(str(item), str(target_folder / item.name))
                    print(f"Moved {item.name} to {target_folder}")
                    moved = True
                    break
            
            # If not matched, move to 'Others' folder
            if not moved:
                others_folder = download_folder / "Others"
                others_folder.mkdir(exist_ok=True)
                shutil.move(str(item), str(others_folder / item.name))
                print(f"Moved {item.name} to {others_folder}")

if __name__ == "__main__":
    # Run the organizer
    organize_downloads()

    # Print a fancy ASCII banner when done
    print(r"""

    ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ 
    ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗
    ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║
    ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║
    ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝
    ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
        ~ Files Organized Successfully ~
            by Mustafa Yousry
    """)

