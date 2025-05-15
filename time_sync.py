from machine import Pin, SoftI2C, RTC
import utime
from ds3231 import DS3231
import gc

# Constants
I2C_SCL_PIN = 9
I2C_SDA_PIN = 8
I2C_FREQ = 400_000

# Initialize I2C and DS3231
i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
ds = DS3231(i2c)
rtc = RTC()

def set_manual_time(year: int, month: int, day: int, hour: int, minute: int, second: int) -> bool:
    """Manually set the time on both DS3231 and ESP32 RTC."""
    try:
        # Create time tuple
        time_tuple = (year, month, day, 0, hour, minute, second, 0)
        
        # Set ESP32 RTC
        rtc.datetime(time_tuple)
        
        # Set DS3231
        if hasattr(ds, 'set_time'):
            ds.set_time(time_tuple)
        else:
            ds.save_time()
        
        gc.collect()
        return True
    except Exception:
        return False

def get_current_datetime_string() -> str:
    """Get current datetime as formatted string in 12-hour format."""
    try:
        # Get time from DS3231
        t = ds.get_time()
        
        # Convert to 12-hour format
        hour = t[3]
        am_pm = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12
        hour_12 = 12 if hour_12 == 0 else hour_12  # Convert 0 to 12 for 12-hour format
        
        return (f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} "
                f"{hour_12:02d}:{t[4]:02d}:{t[5]:02d} {am_pm}")
    except Exception:
        # Fallback to ESP32 RTC
        try:
            current_time = utime.localtime()
            
            # Convert to 12-hour format
            hour = current_time[3]
            am_pm = "AM" if hour < 12 else "PM"
            hour_12 = hour % 12
            hour_12 = 12 if hour_12 == 0 else hour_12  # Convert 0 to 12 for 12-hour format
            
            return (f"{current_time[0]:04d}-{current_time[1]:02d}-{current_time[2]:02d} "
                    f"{hour_12:02d}:{current_time[4]:02d}:{current_time[5]:02d} {am_pm}")
        except Exception:
            return "2000-01-01 12:00:00 AM"

# Initial time sync on boot
try:
    # Get time from DS3231
    ds_time = ds.get_time()
    
    # Set ESP32 RTC with DS3231 time
    rtc.datetime(ds_time)
except Exception:
    pass