import os
import subprocess
import platform


def open_file_with_default_program(file_path):
    if platform.system() == "Windows":
        os.startfile(file_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", file_path])
    elif platform.system() == "Linux":
        subprocess.run(["xdg-open", file_path])
    else:
        print(f"Unsupported operating system: {platform.system()}")
