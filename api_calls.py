import urequests
import uasyncio as asyncio
import json
from wifi_connect import connect_to_wifi
from utils import *
from time_sync import get_current_datetime_string

# Constants
BASE_URL = "https://erp.arxcess.com/arxcess-erp-api"
PING_URL = f"{BASE_URL}/open-accommodation-machines/ping"
EMERGENCIES_URL = f"{BASE_URL}/open-accommodation-machines/sync-emergencies"
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version'
}

async def send_alarm_to_mother(room):
    """
    Asynchronously sends an alarm to mother devices for a specific room.
    """
    config = load_config()
    if not config:
        print("Failed to load configuration.")
        return

    block_name = config.get('block_name')
    mother_ips_str = config.get('mothers')  # Get the mother IPs as a string

    if not block_name or not room:
        print("Block name or room number not found in configuration.")
        return

    if not mother_ips_str:
        print("Mother IPs not found in configuration.")
        return

    # Connect to Wi-Fi
    connected = connect_to_wifi()
    if not connected:
        print("Cannot proceed without Wi-Fi connection.")
        

    # Split mother IPs into a list
    mother_ips = [ip.strip() for ip in mother_ips_str.split(',')]

    # Send alarm to mother servers
    await send_alarm_to_mothers(block_name, room, mother_ips)

async def send_alarm_to_mothers(block_name, room, mother_ips, retries=2, delay=1):
    """
    Asynchronously sends alarms to multiple mother devices and updates the configuration.
    """
    datetime_str = get_current_datetime_string()

    for ip in mother_ips:
        url = f"http://{ip}/api/mother/alarm"
        reference = gen_reference()
        payload = {
            "block_name": block_name,
            "room": room,
            "date": datetime_str,
            "reference": reference,
            "mode": device_mode()
        }

        isSent = False  # Default to False

        for attempt in range(1, retries + 1):
            try:
                print(f"Attempt {attempt}: Sending alarm to mother server at {ip}...")
                response = urequests.put(url, data=json.dumps(payload), headers=HEADERS)
                if response.status_code == 200:
                    isSent = True
                    print(f"Successfully sent alarm to {ip}: {response.status_code} - {response.text}")
                    response.close()
                    break  # Exit the retry loop on success
                else:
                    print(f"Failed to send alarm to {ip}: {response.status_code} - {response.text}")
                response.close()
            except Exception as e:
                print(f"Error sending to {ip}: {e}")

            # Wait before the next retry
            await asyncio.sleep(delay)

        # Update 'last_alarm' in config regardless of success or failure
        await update_last_alarm(room, datetime_str, reference, isSent)
        
        # Yield control to the event loop
        await asyncio.sleep(0)

async def update_last_alarm(room, datetime_str, reference, isSent):
    """
    Asynchronously updates the 'last_alarm' key in the configuration file.
    """
    config = load_config()
    if config is None:
        print("Failed to load configuration for updating 'last_alarm'.")
        return

    # Ensure 'last_alarm' is a list
    if 'last_alarm' not in config or not isinstance(config['last_alarm'], list):
        config['last_alarm'] = []
        
    # Create the alarm entry
    alarm_entry = {
        "roomName": room,
        "alarmTime": datetime_str,
        "reference": reference,
        "isSent": isSent,
        "mode": device_mode(),
        "synced": False
    }

    # Append the new alarm entry
    config['last_alarm'].append(alarm_entry)
    print(f"Updated 'last_alarm' with: {alarm_entry}")

    # Save the updated configuration
    try:
        save_config(config)
    except Exception as e:
        print(f"Error updating 'last_alarm' in configuration: {e}")

async def ping_server_call(retries=1, backoff_factor=2):
    """
    Sends a ping to the server to check connectivity.
    """
    config = load_config()
    if not config:
        print("Failed to load configuration.")
        return False

    code = config.get('machine_code')
    token = config.get('machine_token')
    ipAddress = config.get('ip_address')
    mac_address = get_mac_address()
    rooms = config.get('number_of_rooms')
    firmware_version = get_firmware_version()

    if not code or not token or not ipAddress:
        print("Machine code or token missing in configuration.")
        return False

    payload = {
        "ipAddress": ipAddress,
        "mac_address": mac_address,
        "rooms": rooms,
        "firmware_version": firmware_version
    }
    full_url = f"{PING_URL}?code={code}&token={token}"

    print(f"Pinging server at: {full_url}")
    print(f"Payload: {json.dumps(payload)}")

    delay = 1  # Initial delay in seconds

    for attempt in range(1, retries + 1):
        try:
            response = urequests.put(full_url, data=json.dumps(payload), headers=HEADERS)
            if response.status_code == 200:
                print("Ping successful:", response.text)
                response.close()
                return True
            else:
                print(f"Ping failed with status {response.status_code}: {response.text}")
                response.close()
        except Exception as e:
            print(f"Error during ping (Attempt {attempt}): {e}")

        if attempt < retries:
            print(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay *= backoff_factor  # Exponential backoff

    print("All ping attempts failed.")
    send_alarms_to_cloud()
    return False

async def send_alarms_to_cloud(retries=1, backoff_factor=2):
    config = load_config()
    if not config:
        print("Failed to load configuration.")
        return False

    code = config.get('machine_code')
    token = config.get('machine_token')

    if not code or not token:
        print("Machine code or token missing in configuration.")
        return False

    # Filter unsynced alarms
    unsynced_alarms = [alarm for alarm in config.get('last_alarm', []) if not alarm.get('synced', False)]

    if not unsynced_alarms:
        print("No unsynced alarms to send.")
        return True

    # Convert booleans to strings to avoid serialization issues
    modified_alarms = []
    for alarm in unsynced_alarms:
        modified_alarm = {}
        for key, value in alarm.items():
            if isinstance(value, bool):
                modified_alarm[key] = str(value).lower()  # Convert True/False to "true"/"false"
            else:
                modified_alarm[key] = value
        modified_alarms.append(modified_alarm)

    # Serialize the payload
    payload_str = ujson.dumps(modified_alarms)
    # Convert to UTF-8 encoded bytes
    payload_bytes = payload_str.encode('utf-8')
    # Strip any trailing null bytes or whitespace
    payload_bytes = payload_bytes.rstrip(b'\x00').rstrip()

    # Explicitly set Content-Length in headers
    headers = HEADERS.copy()  # Copy the default headers
    headers['Content-Length'] = str(len(payload_bytes))

    full_url = f"{EMERGENCIES_URL}?code={code}&token={token}"

    delay = 1  # Initial delay in seconds

    for attempt in range(1, retries + 1):
        try:
            response = urequests.post(full_url, data=payload_bytes, headers=headers)
            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text}")

            if response.status_code == 200:
                print("Alarms sent successfully:", response.text)
                try:
                    synced_references = response.json()
                except Exception as e:
                    print(f"Failed to parse response as JSON: {e}")
                    synced_references = []

                for alarm in config['last_alarm']:
                    if alarm['reference'] in synced_references:
                        alarm['synced'] = True

                save_config(config)
                response.close()
                return True
            else:
                print(f"Failed to send alarms with status {response.status_code}: {response.text}")
                response.close()
        except Exception as e:
            print(f"Error during alarm sync (Attempt {attempt}): {e}")

        if attempt < retries:
            print(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay *= backoff_factor

    print("All attempts to send alarms failed.")
    return False

async def periodic_ping(interval=60):
    """
    Periodically pings the server and sends unsynced alarms to the cloud.
    """
    while True:
        print("Starting periodic ping...")
        success = await ping_server_call()
        if success:
            print("Periodic ping successful.")
            # Call send_alarms_to_cloud after a successful ping
            print("Sending unsynced alarms to the cloud...")
            alarms_sent = await send_alarms_to_cloud()
            if alarms_sent:
                print("Unsynced alarms sent successfully.")
            else:
                print("Failed to send unsynced alarms.")
        else:
            print("Periodic ping failed. Skipping alarm sync.")

        print(f"Waiting for {interval} seconds before next ping.")
        await asyncio.sleep(interval)