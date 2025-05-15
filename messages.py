# messages.py

import uasyncio as asyncio
from lcd_utils import *
import ujson
from wifi_connect import is_connected

# Create a lock for the LCD to prevent concurrent access
lcd_lock = asyncio.Lock()


async def welcome():
    # Start both tasks concurrently
    task1 = asyncio.create_task(display_message("    ARXCESS    ", display_time=10))
    task2 = asyncio.create_task(display_message("Emergency Alarm System", line=1, scroll_time=0.4, display_time=10))

    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)
        
async def alarm_msg(room):
    clear_display()
    clear_display()
    # Start both tasks concurrently
    task1 = asyncio.create_task(display_message("!...EMERGENCY..!",clear_before=True))
    task2 = asyncio.create_task(display_message(room, line=1))

    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)

async def mother_alarm_msg(block, room):
    # Start both tasks concurrently
    task1 = asyncio.create_task(display_message("!...EMERGENCY..!", clear_before=True))
    task2 = asyncio.create_task(display_message(f"Block: {block} Room: {room}", line=1, display_time=10))

    # Wait for both tasks to complete
    await asyncio.gather(task1, task2)
        
async def view_connection():
    print("In display")
    try:
        # Read Wi-Fi configuration file
        with open('wifi_config.json', 'r') as f:
            credentials = ujson.load(f)
            ip_address = credentials.get('ip_address')
            ssid = credentials.get('ssid')
            password = credentials.get('password')

        # Create asynchronous tasks for the two messages
        dis_task1 = asyncio.create_task(display_message(f"IP: {ip_address}", scroll_time=0.5, display_time=15, clear_before=True))
        dis_task2 = asyncio.create_task(display_message(f"Wifi: {ssid} Pass: {password}", scroll_time=0.5, display_time=15, line=1))
        # Wait for both tasks to complete
        await asyncio.gather(dis_task1, dis_task2)
        await defaultDisplay()  # Changed from asyncio.run(defaultDisplay())
    
    except OSError as e:
        print("Error reading Wi-Fi credentials (file error):", str(e))
        return False
    except ValueError as e:
        print("Error parsing Wi-Fi credentials (invalid JSON):", str(e))
        return False

async def defaultDisplay():
    print("In display")
    try:
        # Read Wi-Fi configuration file
        with open('wifi_config.json', 'r') as f:
            credentials = ujson.load(f)
            block_name = credentials.get('block_name')
            number_of_rooms = credentials.get('number_of_rooms')
            isMother = credentials.get('isMother')
            center_name = credentials.get('center_name')
            ip_address = credentials.get('ip_address')
            conn_status = "ONLINE" if is_connected() else "OFFLINE"

        # Create asynchronous tasks for the two messages
        if not isMother:
            task1 = asyncio.create_task(display_message(block_name, clear_before=True))
            task2 = asyncio.create_task(display_message(f"R:{number_of_rooms}", allow_scroll=False, line=1))
            await asyncio.gather(task1, task2)
        else:
            dis_task1 = asyncio.create_task(display_message(center_name, clear_before=True))
            dis_task2 = asyncio.create_task(display_message(f"Status: {conn_status}", scroll_time=0.5, line=1))
            await asyncio.gather(dis_task1, dis_task2)
        # Wait for both tasks to complete
        
    except OSError as e:
        print("Error reading Wi-Fi credentials (file error):", str(e))
        return False
    except ValueError as e:
        print("Error parsing Wi-Fi credentials (invalid JSON):", str(e))
        return False

# Example usage (for testing purposes)
if __name__ == "__main__":
    asyncio.run(defaultDisplay())

