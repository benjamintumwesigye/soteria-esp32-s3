import network
import uasyncio as asyncio
from utils import *

wlan = network.WLAN(network.STA_IF)


async def wifi_monitor():
    """
    Monitors the Wi-Fi connection and attempts to reconnect if disconnected.
    If the maximum failure count is reached, it pauses for 2 hours before resuming attempts.
    """
    wlan.active(True)
    failure_count = 0
    max_failures = 2
    pause_duration = 2 * 60 * 60  # 2 hours in seconds

    while True:
        # Load current configuration
        config = load_config()
        if not config:
            print("Failed to load configuration. Waiting before retry...")
            await asyncio.sleep(5)
            continue

        # Get Wi-Fi credentials from config
        ssid = config.get('ssid')
        password = config.get('password')

        if not ssid or not password:
            print("Wi-Fi credentials not found in configuration. Waiting before retry...")
            await asyncio.sleep(5)
            continue

        if not wlan.isconnected():
            wlan.active(False)
            wlan.active(True)
            print("Wi-Fi connection lost. Attempting to reconnect...")

            # Update the config file with an empty IP address
            # Store old config for rollback
            old_config = config.copy()
            config['ip_address'] = ""
            
            # Save and verify configuration
            if save_config(config):
                if not verify_config():
                    # If verification fails, rollback
                    print("Configuration verification failed, rolling back")
                    if save_config(old_config):
                        verify_config()
                        print("Rolled back to previous configuration")
            else:
                print("Failed to save configuration")

            wlan.disconnect()
            wlan.connect(ssid, password)

            # Wait for reconnection
            max_wait = 15  # seconds
            while max_wait > 0:
                if wlan.isconnected():
                    # Store old config for rollback
                    old_config = config.copy()
                    config['ip_address'] = wlan.ifconfig()[0]
                    
                    # Save and verify configuration
                    if save_config(config):
                        if verify_config():
                            print("Updated IP address successfully")
                            failure_count = 0
                            print("Reconnected to Wi-Fi!")
                        else:
                            # If verification fails, rollback
                            print("Configuration verification failed, rolling back")
                            if save_config(old_config):
                                verify_config()
                                print("Rolled back to previous configuration")
                    else:
                        print("Failed to save configuration")
                    break
                await asyncio.sleep(1)
                max_wait -= 1
                print(f"Reconnecting... {max_wait} seconds remaining.")

            else:
                failure_count += 1
                print(f"Failed to reconnect to Wi-Fi. Failure count: {failure_count}")

                # Pause for 2 hours if the maximum failure count is reached
                if failure_count >= max_failures:
                    print(f"Maximum reconnection attempts reached. Pausing for {pause_duration // 3600} hours...")
                    await asyncio.sleep(pause_duration)  # Pause for 2 hours
                    failure_count = 0  # Reset failure count after the pause
        else:
            # Reset failure count if connected
            failure_count = 0

        await asyncio.sleep(5)  # Wait before checking again