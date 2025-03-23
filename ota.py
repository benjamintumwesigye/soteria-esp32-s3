import urequests
import os
import ujson  # Import ujson for JSON handling
import machine  # Import machine module for resetting the ESP32

class OTAUpdater:
    def __init__(self, ssid, password, firmware_url):
        self.ssid = ssid
        self.password = password
        self.firmware_url = firmware_url

    def download_and_install_update_if_available(self):
        print("Checking for updates...")
        version_info = self._get_version_info()
        if not version_info:
            print("Failed to fetch version info.")
            return

        current_version = self._get_current_version()
        if version_info["version"] > current_version:
            print(f"New version available: {version_info['version']}")
            self._update_files(version_info["files"])
            self._set_current_version(version_info["version"])
            print("Update complete. Rebooting device...")
            machine.reset()  # Reboot the ESP32
        else:
            print("No updates available.")

    def _get_version_info(self):
        try:
            print(f"{self.firmware_url}/version.json")
            response = urequests.get(f"{self.firmware_url}/version.json")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch version.json: {response.status_code}")
        except Exception as e:
            print(f"Error fetching version.json: {e}")
        return None

    def _get_current_version(self):
        try:
            with open("version.json", "r") as f:
                local_version = ujson.load(f)
                return local_version.get("version", 0)
        except Exception:
            return 0

    def _set_current_version(self, version):
        try:
            with open("version.json", "w") as f:
                ujson.dump({"version": version}, f)
        except Exception as e:
            print(f"Error updating local version.json: {e}")

    def _update_files(self, files):
        for file in files:
            print(f"Updating {file}...")
            try:
                # Check if the file exists locally
                if not os.path.exists(file):
                    print(f"{file} does not exist locally. Creating it...")

                # Fetch the file from the repository
                response = urequests.get(f"{self.firmware_url}/{file}")
                if response.status_code == 200:
                    # Write the file contents to the local file system
                    with open(file, "w") as f:
                        f.write(response.text)
                    print(f"{file} updated successfully.")
                else:
                    print(f"Failed to download {file}: {response.status_code}")
            except Exception as e:
                print(f"Error updating {file}: {e}")