import os
import shutil
from pathlib import Path

# Map file extensions to folder names
# Feel free to customize these
EXTENSION_MAP = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Music": [".mp3", ".wav", ".aac", ".flac"],
    "Archives": [".zip", ".rar", ".tar", ".gz", ".7z"],
    "Executables": [".exe", ".msi", ".app", ".apk"],
    # Add or remove categories as needed
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
    organize_downloads()
