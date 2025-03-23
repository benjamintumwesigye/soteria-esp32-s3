import ujson
import time
import uasyncio as asyncio
import uos
import urandom
import machine
import network
import binascii

# Define character sets manually
ASCII_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGITS = '0123456789'
CHARS = ASCII_LETTERS + DIGITS

CONFIG_FILE = "wifi_config.json"

def load_config():
    """Load Wi-Fi configuration from the config file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = ujson.load(f)
            return config
    except:
        return {}

def save_config(config):
    """Save Wi-Fi configuration to the config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            ujson.dump(config, f)
        print("Configuration file updated.")
    except Exception as e:
        print("Error writing configuration file:", e)

def check_free_space():
    stats = uos.statvfs('/')
    block_size = stats[0]
    total_blocks = stats[2]
    free_blocks = stats[3]
    total_space = block_size * total_blocks
    free_space = block_size * free_blocks
    print("Total space: {:.2f} MB".format(total_space / (1024 * 1024)))
    print("Free space: {:.2f} MB".format(free_space / (1024 * 1024)))

def reset_mother():
    """
    Resets the 'ring' status of all mother alarms to False without clearing the list.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Load the current configuration
    config = load_config()
    if config is None:
        print("Failed to load configuration file.")
        return False

    # Check if 'mother_alarms' exists and is a list
    if 'mother_alarms' in config and isinstance(config['mother_alarms'], list):
        # Flag to track if any 'ring' key was found and updated
        updated = False

        for idx, alarm in enumerate(config['mother_alarms']):
            if isinstance(alarm, dict):
                if 'ring' in alarm:
                    original_ring = alarm['ring']
                    alarm['ring'] = False
                    updated = True
                else:
                    # If 'ring' key doesn't exist, optionally handle it
                    alarm['ring'] = False
                    updated = True
        
        if not updated:
            print("No 'ring' keys found in 'mother_alarms'. No changes made.")
    else:
        print("'mother_alarms' not found in configuration or is not a list.")
        return False

    # Save the updated configuration back to the file
    try:
        save_config(config)
        print("'mother_alarms' have been successfully updated.")
        return True
    except Exception as e:
        print("Error updating configuration file:", e)
        return False



def gen_reference(length=8):
    return ''.join([CHARS[urandom.getrandbits(8) % len(CHARS)] for _ in range(length)])


# Attempt to read the internal temperature (if supported)
def read_internal_temp():
    # This uses an undocumented internal function; may not work on all ESP32 models
    try:
        raw_temp = machine.temperature()  # Not officially in MicroPython docs
        temp_c = (raw_temp - 32) / 1.8  # Convert from Fahrenheit to Celsius
        return temp_c
    except AttributeError:
        print("This ESP32 model does not support internal temperature sensing.")
        return None



def get_mac_address():
      # Get MAC address
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    mac = ap_if.config('mac')
    mac_str = binascii.hexlify(mac, ':').decode()
    return mac_str


def device_mode():
    mode = ""
    config = load_config()
    if config.get('test_mode') is False:
        mode = "Production"
    else:
        mode = "Maintenance"
    return mode     


