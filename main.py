from machine import Pin
from lcd_utils import display_message
import ure as re
from wifi_connect import *
from wifi_monitor import wifi_monitor
from api_calls import *
import uasyncio as asyncio
from messages import *
import server
from access_point import *
from utils import *
import gc

gc.collect()
print("Free memory:", gc.mem_free())

ALARM_ON = False
connect_to_wifi()
asyncio.run(welcome())
srv = server.start_server()

# Initialize the Siren pin
SIREN_PIN = Pin(3, Pin.OUT)

# Initialize the Button pin
BTN_PIN = Pin(43, Pin.IN, Pin.PULL_UP)

# Define the list of button pins and their corresponding room names
BUTTON_PINS = [
    (18, "Room 01"),
    (16, "Room 02"),
    (15, "Room 03"),
    (7, "Room 04"),
    (6, "Room 05"),
    (4, "Room 06"),
    (5, "Room 07"),
    (47, "Room 08"),
    (48, "Room 09"),
    (38, "Room 10"),
    (39, "Room 11"),
    (40, "Room 12"),
    (41, "Room 13"),
    (42, "Room 14"),
    (44, "Room 15"),
]

# Queue to store button press events
button_press_queue = []

# Initialize buttons and set up interrupts
buttons = {}
# Debouncing variables
last_press_times = {}  # Track the last press time for each pin
DEBOUNCE_INTERVAL = 500  # 500ms debounce interval

def button_handler(pin_num):
    """Interrupt handler for button presses with debouncing."""
    import utime
    current_time = utime.ticks_ms()
    
    # Initialize last press time for this pin if not set
    if pin_num not in last_press_times:
        last_press_times[pin_num] = 0
    
    # Check if enough time has passed since the last press
    if utime.ticks_diff(current_time, last_press_times[pin_num]) < DEBOUNCE_INTERVAL:
        return  # Ignore the press (debouncing)
    
    # Update the last press time
    last_press_times[pin_num] = current_time
    
    # Find the corresponding room name
    for p, room in BUTTON_PINS:
        if p == pin_num:
            # Add the event to the queue (pin number and timestamp)
            button_press_queue.append((pin_num, room))
            break

def btn_pin_handler(pin):
    """Interrupt handler for BTN_PIN with debouncing."""
    import utime
    current_time = utime.ticks_ms()
    
    # Use a special key for BTN_PIN
    pin_key = "BTN_PIN"
    if pin_key not in last_press_times:
        last_press_times[pin_key] = 0
    
    if utime.ticks_diff(current_time, last_press_times[pin_key]) < DEBOUNCE_INTERVAL:
        return
    
    last_press_times[pin_key] = current_time
    button_press_queue.append(("BTN_PIN", None))

# Factory function to create an interrupt handler for a specific pin
def make_button_handler(pin_num):
    return lambda p: button_handler(pin_num)

# Set up buttons with interrupts
for pin_num, _ in BUTTON_PINS:
    try:
        pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        buttons[pin_num] = pin
        # Attach interrupt on falling edge (button press, active low)
        pin.irq(trigger=Pin.IRQ_FALLING, handler=make_button_handler(pin_num))
    except ValueError as e:
        print(f"Error initializing pin {pin_num}: {e}")

# Set up interrupt for BTN_PIN
BTN_PIN.irq(trigger=Pin.IRQ_FALLING, handler=btn_pin_handler)

async def wifi():
    connected = is_connected()
    if not connected:
        print("Cannot proceed without Wi-Fi connection.")
        return
    asyncio.create_task(wifi_monitor())

async def set_alarm(room):
    config = load_config()
    if not config:
        print("Cannot load Wi-Fi credentials from config file.")
        return

    TEST_MODE = config.get('test_mode', False)
    print(f"Alarm is ON for {room}")
    global ALARM_ON
    ALARM_ON = True
    SIREN_PIN.value(1)  # Turn the Siren on
    await alarm_msg(room)
    if not TEST_MODE:
        await send_alarm_to_mother(room)
    else:
        await asyncio.sleep(2)
        SIREN_PIN.value(0)
        ALARM_ON = False
        await send_alarm_to_mother(room)
        await defaultDisplay()

async def set_mother_alarm():
    config = load_config()
    if config is None:
        print("Failed to load configuration file.")
        return False
    if config.get('isMother') == True:
        mother_alarms = config.get('mother_alarms', [])
        for alarm in mother_alarms:
            mode = alarm.get('mode')
            test_ring = True if mode == "Maintenance" else False
            if alarm.get('ring') == True:
                global ALARM_ON
                ALARM_ON = True
                SIREN_PIN.value(1)  # Turn the Siren on
                if test_ring == True:
                    await asyncio.sleep(0.1)
                    SIREN_PIN.value(0)
                    reset()
                await mother_alarm_msg(alarm.get('block_name'), alarm.get('room'))
                break  

def server_check():
    if srv is None:
        print("Server failed to start.")
        return

def reset():
    global ALARM_ON
    ALARM_ON = False
    reset_mother()
    asyncio.create_task(defaultDisplay())

async def set_mother_alarm_loop():
    while True:
        if BTN_PIN.value() == 0:
            SIREN_PIN.value(0)
            print(ALARM_ON)
            if not ALARM_ON:
                await view_connection()
            else:
                await defaultDisplay()
                reset()
        await set_mother_alarm()
        await asyncio.sleep(0.5)

async def start_socket_server():
    global ap_ip
    if ap_ip is None:
        print("AP IP is not available. Starting AP...")
        ap_obj, ap_ip = await start_access_point()
    
    try:
        server = await asyncio.start_server(handle_client, host=ap_ip, port=80)
        print('Socket Listening on port 80')
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        print("Failed to start socket server:", e)
        
async def handle_button_press(pin_num, room):
    config = load_config()
    number_of_rooms_str = config.get('number_of_rooms', '')
    number_of_rooms = number_of_rooms_str.split(',')
    room_index = None
    for index, (pin, _) in enumerate(BUTTON_PINS):
        if pin == pin_num:
            room_index = index
            break
    
    if room_index is not None:
        if room_index < len(number_of_rooms):
            dynamic_room_label = number_of_rooms[room_index]
            display_message_str = f"Room {dynamic_room_label}"
        else:
            display_message_str = "Room Unknown"
    else:
        display_message_str = room or "Room Unknown"
    
    print(f"Final display_message_str: {display_message_str}")
    asyncio.create_task(set_alarm(display_message_str))

async def main():
    await wifi()
    check_free_space()
    connect_to_wifi()
    
    srv = server.start_server()
    asyncio.create_task(defaultDisplay())

    global ap, ap_ip
    ap, ap_ip = await start_access_point()
    
    asyncio.create_task(start_socket_server())
    
    config = load_config()
    if config is None:
        print("Failed to load configuration file.")
        return False
    is_mother = config.get('isMother',False)
    if is_mother:
        asyncio.create_task(set_mother_alarm_loop())
    
    asyncio.create_task(periodic_ping())
    
    print("Waiting for button press events...")
    while True:
        # Process queued button press events
        if button_press_queue:
            event = button_press_queue.pop(0)  # Get the oldest event
            pin_num, room = event
            if pin_num == "BTN_PIN":
                SIREN_PIN.value(0)
                print(ALARM_ON)
                if not ALARM_ON:
                    asyncio.create_task(view_connection())
                else:
                    reset()
            else:
                if not is_mother:
                    await handle_button_press(pin_num, room)
            await asyncio.sleep(1)  # Debounce delay
        
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting program")
        server.stop_server(srv)