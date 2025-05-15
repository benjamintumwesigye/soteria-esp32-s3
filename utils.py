import ujson
import uos
import urandom
import machine
import network
import binascii
import gc
import time

# Constants
CONFIG_FILE = "wifi_config.json"
CONFIG_BACKUP = "wifi_config.bak"
DATABASE_FILE = "database.json"
VERSION_FILE = "version.json"

# Character sets for generating references
ASCII_LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGITS = '0123456789'
CHARS = ASCII_LETTERS + DIGITS


def load_config():
    gc.collect()
    """Load configuration from the config file with fallback to backup."""
    try:
        # Try to load from main config file
        with open(CONFIG_FILE, 'r') as f:
            config = ujson.load(f)
            return config
    except Exception:
        try:
            # If main config fails, try backup
            with open(CONFIG_BACKUP, 'r') as f:
                config = ujson.load(f)
                return config
        except Exception:
            return {}


def save_config(config):
    """Save configuration using a robust two-file approach."""
    try:
        # First, write to backup file
        with open(CONFIG_BACKUP, 'w') as f:
            ujson.dump(config, f)
            f.flush()
            uos.sync()
        
        # Verify backup file
        with open(CONFIG_BACKUP, 'r') as f:
            backup_config = ujson.load(f)
            if backup_config != config:
                raise ValueError("Backup verification failed")
        
        # If backup is good, write to main file
        with open(CONFIG_FILE, 'w') as f:
            ujson.dump(config, f)
            f.flush()
            uos.sync()
        
        # Verify main file
        with open(CONFIG_FILE, 'r') as f:
            main_config = ujson.load(f)
            if main_config != config:
                raise ValueError("Main file verification failed")
        
        return True
        
    except Exception:
        # If main file write failed, at least we have the backup
        return False


def check_free_space():
    """Check and print the total and free space on the device."""
    try:
        stats = uos.statvfs('/')
        block_size = stats[0]
        total_blocks = stats[2]
        free_blocks = stats[3]
        total_space = block_size * total_blocks
        free_space = block_size * free_blocks
        return total_space, free_space
    except Exception:
        return 0, 0


def reset_config():
    """Reset configuration to default values."""
    default_config = {
        'ssid': '',
        'password': '',
        'block_name': '',
        'center_name': '',
        'number_of_rooms': '',
        'isMother': False,
        'mothers': '',
        'test_mode': False,
        'machine_code': '',
        'machine_token': '',
        'last_alarm': [],
        'mother_alarms': [],
        'last_ping': 'Never pinged',
        'ip_address': ''
    }
    return save_config(default_config)


def verify_config():
    """Verify the integrity of the configuration files."""
    try:
        # Check if main config exists and is valid
        with open(CONFIG_FILE, 'r') as f:
            main_config = ujson.load(f)
        
        # Check if backup exists and is valid
        with open(CONFIG_BACKUP, 'r') as f:
            backup_config = ujson.load(f)
        
        # Compare configs
        if main_config != backup_config:
            # If they're different, use the most recently modified one
            main_stat = uos.stat(CONFIG_FILE)
            backup_stat = uos.stat(CONFIG_BACKUP)
            
            if main_stat[8] > backup_stat[8]:  # Compare modification times
                save_config(main_config)  # Update backup with main
            else:
                save_config(backup_config)  # Update main with backup
        
        return True
    except Exception:
        return False


def reset_mother():
    """
    Resets the 'mother_alarms' list in the configuration file.
    """
    config = load_config()
    if not config:
        return False

    # Check if 'last_alarm' exists and is a list
    if 'mother_alarms' in config and isinstance(config['mother_alarms'], list):
        config['mother_alarms'] = ''  # Clear the list
    else:
        return False

    # Save the updated configuration
    try:
        save_config(config)
        return True
    except Exception:
        return False


def reset_last_alarms():
    """
    Resets the 'last_alarm' list in the configuration file.
    """
    config = load_config()
    if not config:
        return False

    # Check if 'last_alarm' exists and is a list
    if 'last_alarm' in config and isinstance(config['last_alarm'], list):
        config['last_alarm'] = ''  # Clear the list
    else:
        return False

    # Save the updated configuration
    try:
        save_config(config)
        return True
    except Exception:
        return False


def gen_reference(length=10):
    """Generate a random reference string."""
    return ''.join([CHARS[urandom.getrandbits(8) % len(CHARS)] for _ in range(length)])


def get_mac_address():
    """Get the MAC address of the device."""
    try:
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        mac = ap_if.config('mac')
        return binascii.hexlify(mac, ':').decode()
    except Exception:
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
    except Exception:
        return {}


def get_firmware_version():
    """Get the firmware version from the version file."""
    version_info = load_version()
    return version_info.get('version', "Unknown")


def get_remaining_space():
    """
    Get the remaining free space on the ESP32 in MB.
    :return: Free space in MB as a float.
    """
    try:
        stats = uos.statvfs('/')
        block_size = stats[0]
        free_blocks = stats[3]
        free_space_mb = (block_size * free_blocks) / (1024 * 1024)  # Convert to MB
        return round(free_space_mb, 2)  # Round to 2 decimal places
    except Exception:
        return 0.0


verify_config()