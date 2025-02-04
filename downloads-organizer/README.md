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

1. Scans all files in your default **Downloads** directory.
2. Checks each file's extension and **moves** the file to a corresponding subfolder:
   - **Images** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`)
   - **Documents** (`.pdf`, `.doc`, `.docx`, `.txt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`)
   - **Videos** (`.mp4`, `.mkv`, `.avi`, `.mov`)
   - **Music** (`.mp3`, `.wav`, `.aac`, `.flac`)
   - **Archives** (`.zip`, `.rar`, `.tar`, `.gz`, `.7z`)
   - **Executables** (`.exe`, `.msi`, `.app`, `.apk`)
   - **Others** (for any extensions not listed above)
3. If the corresponding subfolder does not exist, it automatically **creates** it.
4. Prints a message for each file it moves.

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
