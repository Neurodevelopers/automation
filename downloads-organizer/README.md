# Downloads Organizer Script

A simple Python script that organizes files in your **Downloads** folder into subfolders based on file extensions.  
Written by **Mustafa Yousry**.  


---

## Overview

- **Languages**: Python (3.6+)
- **Dependencies**: Standard library only (`os`, `shutil`, `pathlib`)
- **Platform**: Cross-platform (Windows, macOS, Linux)

---

## How It Works

1. Scans **all files** in your default **Downloads** directory.
2. Determines each file’s **extension** and **moves** it to a matching subfolder:
   - **Images**: (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, etc.)
   - **Documents**: (`.pdf`, `.doc`, `.docx`, `.txt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, etc.)
   - **Videos**: (`.mp4`, `.mkv`, `.avi`, `.mov`, etc.)
   - **Audio**: (`.mp3`, `.wav`, `.aac`, `.flac`, etc.)
   - **Archives**: (`.zip`, `.rar`, `.tar`, `.gz`, `.7z`, etc.)
   - **3D/CAD/Design**: (`.obj`, `.fbx`, `.stl`, `.dwg`, `.psd`, `.ai`, etc.)
   - **Web & Scripts**: (`.html`, `.css`, `.js`, `.php`, `.py`, etc.)
   - **Programs**: (`.exe`, `.msi`, `.dmg`, `.pkg`, `.apk`, etc.)
   - **Others**: Any extensions not covered above
3. **Creates** the corresponding subfolder automatically if it does not already exist.
4. **Prints** a message for each file it moves, and displays a **success banner** when finished.

---

## Getting Started

1. **Clone or Download** this repository.
2. **Navigate** to the directory containing `organizer.py`.
3. **Run** the script:

   ```bash
   python organizer.py



## Automating on Windows

To automate the script to run at regular intervals on Windows, you can use the Task Scheduler:

1. **Open Task Scheduler**: Press `Win + R`, type `taskschd.msc`, and press `Enter`.
2. **Create a Basic Task**:
    - Click on **Create Basic Task** in the right-hand Actions pane.
    - Name your task (e.g., "Downloads Organizer") and provide a description if desired.
3. **Set the Trigger**:
    - Choose when you want the task to start (e.g., daily, weekly).
    - Set the start date and time.
4. **Action**:
    - Select **Start a program**.
    - Browse to your Python executable (e.g., `C:\Python39\python.exe`).
    - Add the path to `organizer.py` in the **Add arguments** field (e.g., `D:\automation\downloads-organizer\organizer.py`).
5. **Finish**:
    - Review your settings and click **Finish** to create the task.
