import os
import psutil
from win32api import GetVolumeInformation
import winreg
import json
from concurrent.futures import ThreadPoolExecutor
import string


class DriveManager:
    def __init__(self):
        self.drives = []
        self.config_file = 'last_location.json'

    def get_available_drives(self):
        """Optimized drive detection using parallel processing"""
        drives = []

        def check_drive(letter):
            drive_path = f"{letter}:\\"
            try:
                if os.path.exists(drive_path):
                    label = ""
                    try:
                        label = GetVolumeInformation(drive_path)[0]
                    except:
                        pass
                    return {
                        'path': drive_path,
                        'label': label or 'Local Disk',
                        'type': 'drive'
                    }
            except:
                pass
            return None

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                potential_drives = string.ascii_uppercase
                results = executor.map(check_drive, potential_drives)
                drives = [drive for drive in results if drive is not None]
        except Exception as e:
            print(f"Error getting drives: {e}")

        return drives

    def get_special_folders(self):
        """Get Windows special folders using registry."""
        special_folders = []

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                folders_to_check = {
                    "Desktop": "Desktop",
                    "Personal": "My Documents",
                    "Local AppData": "AppData"
                }

                for reg_name, display_name in folders_to_check.items():
                    try:
                        path = winreg.QueryValueEx(key, reg_name)[0]
                        if os.path.exists(path):
                            special_folders.append({
                                'path': path,
                                'label': display_name,
                                'type': 'special'
                            })
                    except WindowsError:
                        continue

                # Add Downloads folder
                downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
                if os.path.exists(downloads):
                    special_folders.append({
                        'path': downloads,
                        'label': 'Downloads',
                        'type': 'special'
                    })

        except Exception as e:
            print(f"Error getting special folders: {e}")

        return special_folders

    def save_last_location(self, location):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'last_location': location}, f)
        except Exception:
            pass

    def get_last_location(self):
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return data.get('last_location')
        except Exception:
            return None