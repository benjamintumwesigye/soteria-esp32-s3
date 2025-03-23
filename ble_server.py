import ubluetooth
from machine import Pin
import time
import _thread
import ujson
from lcd_utils import display_message
from wifi_connect import connect_to_wifi

class BLEServer:
    def __init__(self, name="ESP32-BLE"):
        # Initialize BLE
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.config(mtu=256)  # Request a higher MTU size
        self.name = name
        self.ble.irq(self.ble_irq)
        self.register()
        self.advertise()
        
        # Initialize data buffer for receiving data
        self.data_buffer = ""  # Add this line to initialize data_buffer

        # Initialize variables to store received data
        self.received_ssid = ""
        self.received_password = ""
        self.received_block_name = ""
        self.received_number_of_rooms = ""

    def ble_irq(self, event, data):
        if event == 1:  # Central connected
            print("Central connected")
        elif event == 2:  # Central disconnected
            print("Central disconnected")
            self.advertise()  # Start advertising again
        elif event == 3:  # Write event
            # Read and decode the data, then append it to the buffer
            buffer = self.ble.gatts_read(self.write_handle)
            self.data_buffer += buffer.decode('utf-8').strip()
            
            # Check if the buffer contains a complete message (using '\n' as delimiter)
            if '\n' in self.data_buffer:
                # Split the buffer by the delimiter to process each message separately
                messages = self.data_buffer.split('\n')
                
                # Process each complete message in the buffer
                for message in messages[:-1]:
                    self.process_received_data(message.strip())
                
                # Keep the last partial message (if any) in the buffer
                self.data_buffer = messages[-1]

    def register(self):
        # Define a service with a unique identifier and characteristics
        service_uuid = ubluetooth.UUID(0x181A)  # Custom service UUID
        char_uuid = ubluetooth.UUID(0x2A6E)  # Characteristic UUID for data transmission

        self.service = (service_uuid, ((char_uuid, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_READ | ubluetooth.FLAG_NOTIFY),))
        ((self.write_handle,),) = self.ble.gatts_register_services((self.service,))

    def advertise(self):
        # Start advertising the BLE service
        name = bytes(self.name, 'utf-8')
        adv_data = b'\x02\x01\x06' + bytes([len(name) + 1]) + b'\x09' + name
        self.ble.gap_advertise(100, adv_data)

    def set_value(self, value):
        # Set a value for the characteristic
        self.ble.gatts_write(self.write_handle, value)

    def process_received_data(self, data):
        # Process the received data based on prefix
        try:
            prefix, value = data.split(';', 1)  # Split the data into prefix and value
            if prefix == '1':  # SSID
                self.received_ssid = value
                display_message(f"WF:{value}.", display_time=5, clear_after=True)
                print("Received SSID:", self.received_ssid)
            elif prefix == '2':  # Password
                self.received_password = value
                display_message(f"PW:{value}.", display_time=5, clear_after=True)
                print("Received Password:", self.received_password)
            elif prefix == '3':  # Block name
                self.received_block_name = value
                display_message(f"Name:{value}.", display_time=5, clear_after=True)
                print("Received Block Name:", self.received_block_name)
            elif prefix == '4':  # Number of rooms
                self.received_number_of_rooms = value
                display_message(f"  Rooms:  {self.received_number_of_rooms}.", display_time=5, clear_after=True)
                print("Received Number of Rooms:", str(self.received_number_of_rooms))
            else:
                display_message(f"  E:  {self.data}.")
                print("Unknown prefix received.")
            
            # Check if all data has been received to save
            if self.received_ssid and self.received_password and self.received_block_name and self.received_number_of_rooms:
                self.save_wifi_credentials()
        
        except ValueError:
            display_message(data,line=1, display_time=1, clear_after=True)
            print("Error: Received data format is incorrect. Expected format: Prefix;Value")

    def save_wifi_credentials(self):
        # Save all received data to a file
        try:
            # Store all received data in a file
            credentials = {
                'ssid': self.received_ssid,
                'password': self.received_password,
                'block_name': self.received_block_name,
                'number_of_rooms': self.received_number_of_rooms
            }
            with open('wifi_config.json', 'w') as f:
                ujson.dump(credentials, f)
            
            print("All data saved successfully.")
            connect_to_wifi()
        except Exception as e:
            print("Error saving data:", str(e))

# Initialize the BLE server
ble_server = BLEServer()

# Example usage of keeping the BLE server running
if __name__ == "__main__":
    try:
        while True:
            time.sleep(10)  # Main loop to keep the BLE server running
    except KeyboardInterrupt:
        ble_server.stop()
        print("BLE Server stopped")

