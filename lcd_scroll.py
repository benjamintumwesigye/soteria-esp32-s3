from machine import I2C, Pin
from time import sleep
from i2c_lcd import I2cLcd

# Define LCD parameters
I2C_ADDR = 0x27      # Replace with your I2C address
I2C_ROWS = 2         # Rows of your LCD (e.g., 2 for 16x2 LCD)
I2C_COLS = 16        # Columns of your LCD (e.g., 16 for 16x2 LCD)

# Initialize I2C and LCD
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)  # Use GPIO 21 and 22
lcd = I2cLcd(i2c, I2C_ADDR, I2C_ROWS, I2C_COLS)

def scroll_text(lcd, text, row=0, delay=0.3):
    """
    Scroll text on the LCD.
    
    Args:
        lcd: The LCD object.
        text: The text to scroll.
        row: The row on the LCD to scroll the text.
        delay: Time delay between each scroll step.
    """
    # Padding the text with spaces for smooth scrolling
    padded_text = text + " " * I2C_COLS
    display_length = len(text) + I2C_COLS
    
    for i in range(display_length):
        lcd.move_to(0, row)  # Move cursor to the beginning of the row
        lcd.putstr(padded_text[i:i+I2C_COLS])
        sleep(delay)

# Example usage
try:
    while True:
        lcd.clear()
        scroll_text(lcd, "Hello from ESP32!", row=0, delay=0.3)
        scroll_text(lcd, "MicroPython Rocks!", row=1, delay=0.3)
except KeyboardInterrupt:
    lcd.clear()  # Clear the display on exit
