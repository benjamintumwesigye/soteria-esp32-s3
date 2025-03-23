import uasyncio as asyncio
import ntptime
import time
from machine import Pin, SoftI2C, SPI
from utils import load_config
from ds3231 import DS3231

i2c = SoftI2C(scl=Pin(9), sda=Pin(8), freq=400000)
devices = i2c.scan()
if devices:
    for device in devices:
        print("I2C device found at address:", hex(device))
else:
    print("No I2C device found")
ds = DS3231(i2c)

last_sync = 0
sync_interval = 3600  # Sync every hour (3600 seconds)

def synchronize_time():
    global last_sync
    try:
        ntptime.settime()
        last_sync = time.time()
        print("Time synchronized with NTP server.")
    except Exception as e:
        print("Failed to synchronize time:", e)

async def periodic_time_sync():
    while True:
        current_time = time.time()
        if current_time - last_sync > sync_interval:
            synchronize_time()
        await asyncio.sleep(60)  # Check every minute

def get_current_datetime_string():
    config = load_config()
    if config is None:
        print("Failed to load configuration file.")
        current_time = time.localtime()
        datetime_str = f"{current_time[0]}-{current_time[1]:02}-{current_time[2]:02} {current_time[3]:02}:{current_time[4]:02}:{current_time[5]:02}"
        return datetime_str
    if config.get('rtc_on') == True:
        return loadRtc()
        
    else:
        current_time = time.localtime()
        datetime_str = f"{current_time[0]}-{current_time[1]:02}-{current_time[2]:02} {current_time[3]:02}:{current_time[4]:02}:{current_time[5]:02}"
        return datetime_str


def loadRtc():
        ds.save_time()
            
        t = ds.get_time()
        time_str = '{:02d}:{:02d}:{:02d}'.format(t[3], t[4], t[5])
        date = '{:04d}-{:02d}-{:02d}'.format(t[0], t[1], t[2])
        return f"{date} {time_str}"
           