import ujson
import uos
import urandom
import machine
import network
import binascii

# Constants
CONFIG_FILE = "wifi_config.json"
VERSION_FILE = "version.json"

# Character sets for generating references
ASCII_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGITS = '0123456789'
CHARS = ASCII_LETTERS + DIGITS


def load_config():
    """Load configuration from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return ujson.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}


def save_config(config):
    """Save configuration to the config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            ujson.dump(config, f)
        print("Configuration file updated.")
    except Exception as e:
        print(f"Error writing configuration file: {e}")


def check_free_space():
    """Check and print the total and free space on the device."""
    try:
        stats = uos.statvfs('/')
        block_size = stats[0]
        total_blocks = stats[2]
        free_blocks = stats[3]
        total_space = block_size * total_blocks
        free_space = block_size * free_blocks
        print(f"Total space: {total_space / (1024 * 1024):.2f} MB")
        print(f"Free space: {free_space / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"Error checking free space: {e}")


def reset_mother():
    """
    Resets the 'ring' status of all mother alarms to False without clearing the list.
    """
    config = load_config()
    if not config:
        print("Failed to load configuration file.")
        return False

    if 'mother_alarms' in config and isinstance(config['mother_alarms'], list):
        updated = False
        for alarm in config['mother_alarms']:
            if isinstance(alarm, dict):
                alarm['ring'] = False
                updated = True

        if not updated:
            print("No 'ring' keys found in 'mother_alarms'. No changes made.")
    else:
        print("'mother_alarms' not found in configuration or is not a list.")
        return False

    try:
        save_config(config)
        print("'mother_alarms' have been successfully updated.")
        return True
    except Exception as e:
        print(f"Error updating configuration file: {e}")
        return False


def gen_reference(length=8):
    """Generate a random reference string."""
    return ''.join([CHARS[urandom.getrandbits(8) % len(CHARS)] for _ in range(length)])


def read_internal_temp():
    """
    Attempt to read the internal temperature (if supported).
    """
    try:
        raw_temp = machine.temperature()  # Not officially in MicroPython docs
        temp_c = (raw_temp - 32) / 1.8  # Convert from Fahrenheit to Celsius
        return temp_c
    except AttributeError:
        print("This ESP32 model does not support internal temperature sensing.")
        return None


def get_mac_address():
    """Get the MAC address of the device."""
    try:
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        mac = ap_if.config('mac')
        return binascii.hexlify(mac, ':').decode()
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return None


def device_mode():
    """Get the current device mode (Production or Maintenance)."""
    config = load_config()
    return "Production" if not config.get('test_mode', False) else "Maintenance"


def load_version():
    """Load version information from the version file."""
    try:
        with open(VERSION_FILE, 'r') as f:
            return ujson.load(f)
    except Exception as e:
        print(f"Error loading version file: {e}")
        return {}


def firmware_version():
    """Get the firmware version from the version file."""
    version_info = load_version()
    return version_info.get('version', "Unknown")