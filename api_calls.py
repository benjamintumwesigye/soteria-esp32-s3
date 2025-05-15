import urequests
import uasyncio as asyncio
import ujson as json
from wifi_connect import connect_to_wifi
from utils import load_config, save_config, gen_reference, device_mode, get_mac_address, get_firmware_version, reset_last_alarms, verify_config
from time_sync import get_current_datetime_string
from firmware_updates import check_firmware

# Constants
BASE_URL = "https://erp.arxcess.com/arxcess-erp-api"
PING_URL = f"{BASE_URL}/open-accommodation-machines/ping"
EMERGENCIES_URL = f"{BASE_URL}/open-accommodation-machines/sync-emergencies"
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version'
}

async def send_alarm_to_mother(room: str) -> None:
    """Asynchronously sends an alarm to mother devices for a specific room.

    Args:
        room (str): The room identifier for the alarm.

    Returns:
        None
    """
    config = load_config()
    if not config:
        return

    if config.get("isMother", False):
        return

    block_name = config.get('block_name')
    mother_ips_str = config.get('mothers')

    if not block_name or not room:
        return

    if not mother_ips_str:
        return

    if not connect_to_wifi():
        return

    mother_ips = [ip.strip() for ip in mother_ips_str.split(',')]
    await send_alarm_to_mothers(block_name, room, mother_ips)

async def send_alarm_to_mothers(block_name: str, room: str, mother_ips: list, retries: int = 0, delay: int = 1) -> None:
    """Asynchronously sends alarms to multiple mother devices and updates the configuration.

    Args:
        block_name (str): The block name for the alarm.
        room (str): The room identifier for the alarm.
        mother_ips (list): List of mother device IP addresses.
        retries (int, optional): Not used, kept for backward compatibility.
        delay (int, optional): Not used, kept for backward compatibility.

    Returns:
        None
    """
    datetime_str = get_current_datetime_string()
    successful_mothers = []  # List to store machine_code of mothers that responded successfully

    for ip in mother_ips:
        url = f"http://{ip}/api/mother/alarm"
        headers = {'Content-Type': 'application/json'}
        reference = gen_reference()
        payload = {
            "block_name": block_name,
            "room": room,
            "date": datetime_str,
            "reference": reference,
            "mode": device_mode()
        }
        
        is_sent = False
        try:
            response = urequests.put(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    machine_code = response_data.get('machine_code', '')
                    if machine_code:
                        successful_mothers.append(machine_code)
                    is_sent = True
                except Exception:
                    is_sent = True
                finally:
                    response.close()
            else:
                response.close()
        except Exception:
            pass

    successful_mothers_str = ",".join(successful_mothers) if successful_mothers else ""
    await update_last_alarm(room, datetime_str, reference, is_sent, successful_mothers_str)
    await asyncio.sleep(0)

async def update_last_alarm(room: str, datetime_str: str, reference: str, is_sent: bool, successful_mothers: str) -> None:
    """Asynchronously updates the 'last_alarm' key in the configuration file.

    Args:
        room (str): The room identifier for the alarm.
        datetime_str (str): The timestamp of the alarm.
        reference (str): A unique reference for the alarm.
        is_sent (bool): Whether the alarm was successfully sent to at least one mother.
        successful_mothers (str): Comma-separated string of machine_codes from mothers that responded successfully.

    Returns:
        None
    """
    config = load_config()
    if not config:
        return

    old_config = config.copy()

    if 'last_alarm' not in config or not isinstance(config['last_alarm'], list):
        config['last_alarm'] = []

    alarm_entry = {
        "roomName": room,
        "alarmTime": datetime_str,
        "reference": reference,
        "isSent": is_sent,
        "mode": device_mode(),
        "synced": False,
        "successfulMothers": successful_mothers
    }
    config['last_alarm'].append(alarm_entry)

    if save_config(config):
        if not verify_config():
            if save_config(old_config):
                verify_config()

    if not connect_to_wifi():
        return

    await send_alarms_to_cloud()

async def ping_server_call() -> str | bool:
    """Sends a ping to the server to check connectivity.

    Returns:
        str | bool: The mother server IP if successful, False otherwise.
    """
    config = load_config()
    if not config:
        return False

    code = config.get('machine_code')
    token = config.get('machine_token')
    ip_address = config.get('ip_address')
    mac_address = get_mac_address()
    rooms = config.get('number_of_rooms')
    firmware_version = get_firmware_version()
    mode = config.get('test_mode')

    if not all([code, token, ip_address]):
        return False

    payload = {
        "ipAddress": ip_address,
        "macAddress": mac_address,
        "rooms": rooms,
        "firmwareVersion": firmware_version,
        "mode": "Maintenance" if mode else "Production",
        "deviceTime": get_current_datetime_string()
    }
    full_url = f"{PING_URL}?code={code}&token={token}"

    try:
        await asyncio.sleep(0)
        response = urequests.put(full_url, data=json.dumps(payload), headers=HEADERS)
        if response.status_code == 200:
            mother_server_ip = response.text.strip()
            old_config = config.copy()
            
            current_time = get_current_datetime_string()
            config['last_ping'] = f"Ping successful at {current_time}"
            
            if save_config(config):
                if verify_config():
                    response.close()
                    return mother_server_ip
                else:
                    if save_config(old_config):
                        verify_config()
            
            response.close()
            return mother_server_ip
            
        old_config = config.copy()
        
        current_time = get_current_datetime_string()
        config['last_ping'] = f"Ping failed with status {response.status_code} at {current_time}"
        
        if save_config(config):
            if not verify_config():
                if save_config(old_config):
                    verify_config()
            
        response.close()
    except Exception as e:
        current_time = get_current_datetime_string()
        config['last_ping'] = f"Ping failed with error: {str(e)} at {current_time}"
        
        if not save_config(config):
            if save_config(old_config):
                verify_config()

    await send_alarms_to_cloud()
    return False

async def send_alarms_to_cloud() -> bool:
    """Sends unsynced alarms to the cloud server.

    Returns:
        bool: True if alarms were sent successfully, False otherwise.
    """
    config = load_config()
    if not config or config.get("isMother", False):
        return False

    code = config.get('machine_code')
    token = config.get('machine_token')
    if not code or not token:
        return False

    unsynced_alarms = [alarm for alarm in config.get('last_alarm', []) if not alarm.get('synced', False)]
    if not unsynced_alarms:
        reset_last_alarms()
        return True

    modified_alarms = [
        {k: str(v).lower() if isinstance(v, bool) else v for k, v in alarm.items()}
        for alarm in unsynced_alarms
    ]

    payload_bytes = json.dumps(modified_alarms).encode('utf-8').rstrip(b'\x00').rstrip()
    headers = HEADERS.copy()
    headers['Content-Length'] = str(len(payload_bytes))

    full_url = f"{EMERGENCIES_URL}?code={code}&token={token}"

    try:
        response = urequests.post(full_url, data=payload_bytes, headers=headers)
        if response.status_code == 200:
            try:
                synced_references = response.json()
            except Exception:
                synced_references = []
            for alarm in config['last_alarm']:
                if alarm['reference'] in synced_references:
                    alarm['synced'] = True
            save_config(config)
            response.close()
            return True
        response.close()
    except Exception:
        pass

    return False

async def periodic_ping(interval: int = 120) -> None:
    """Periodically pings the server, updates the mother server IP in the configuration,
    and sends unsynced alarms to the cloud.

    Args:
        interval (int, optional): Interval between pings in seconds. Defaults to 120.

    Returns:
        None
    """
    while True:
        try:
            if not connect_to_wifi():
                await asyncio.sleep(interval)
                continue

            config = load_config()
            if not config:
                await asyncio.sleep(interval)
                continue
            
            mother_server_ip = await ping_server_call()
            
            config = load_config()
            if not config:
                await asyncio.sleep(interval)
                continue
            
            if mother_server_ip and not config.get('isMother', False):
                old_config = config.copy()
                config['mothers'] = mother_server_ip
                
                if save_config(config):
                    if not verify_config():
                        if save_config(old_config):
                            verify_config()
                
                await send_alarms_to_cloud()
            
            await asyncio.sleep(interval)
            
        except Exception:
            await asyncio.sleep(interval)