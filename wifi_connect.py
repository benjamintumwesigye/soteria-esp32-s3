import network
import ujson
import time
import uasyncio as asyncio
from utils import load_config, save_config, verify_config

wlan = network.WLAN(network.STA_IF)

def connect_to_wifi():
    """
    Connects to Wi-Fi using credentials from configuration.
    """
    # Load configuration
    config = load_config()
    if not config:
        print("Error: Failed to load configuration.")
        return False

    # Print current configuration for debugging
    print("Current configuration:", config)

    ssid = config.get('ssid')
    password = config.get('password')

    if not ssid or not password:
        print("Error: SSID or password is missing in the configuration.")
        print("SSID present:", bool(ssid))
        print("Password present:", bool(password))
        return False
    
    wlan.active(True)

    # Check if already connected
    if wlan.isconnected():
        print("Already connected to Wi-Fi:", wlan.ifconfig())
        return True

    # Attempt to connect
    print(f"Connecting to Wi-Fi SSID='{ssid}'...")
    wlan.active(False)
    wlan.active(True)
    try:
        wlan.connect(ssid, password)
    except Exception as e:
        print("Wifi Error:", e)    

    # Wait for connection with timeout
    max_wait = 15  # seconds
    while max_wait > 0:
        if wlan.isconnected():
            print("Successfully connected to Wi-Fi!")
            print("Network configuration:", wlan.ifconfig())
            
            # Store old config for rollback
            old_config = config.copy()
            
            # Update IP address in configuration
            config['ip_address'] = wlan.ifconfig()[0]
            
            # Save and verify configuration
            if save_config(config):
                if verify_config():
                    print("Updated IP address successfully")
                else:
                    # If verification fails, rollback
                    print("Configuration verification failed, rolling back")
                    if save_config(old_config):
                        verify_config()
                        print("Rolled back to previous configuration")
            else:
                print("Failed to save configuration")
                
            return True
        time.sleep(1)
        max_wait -= 1
        print(f"Waiting for connection... {max_wait} seconds remaining.")

    print("Failed to connect to Wi-Fi.")
    return False

def is_connected():
    return wlan.isconnected()

def get_ip():
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    else:
        return None
