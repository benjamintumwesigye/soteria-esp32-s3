
import machine
import time
import network
import socket
import ure as re
import ujson  # Import ujson for handling JSON data
import gc
import uasyncio as asyncio
from utils import *
from wifi_connect import *
from messages import defaultDisplay
from styles import *


gc.collect()


ap_ssid = 'SOTERIA-241'
ap_password = '123456789'

def url_decode(s, iterations=2):
    """Decode a URL-encoded string multiple times to handle double encoding."""
    for _ in range(iterations):
        prev = url_parse(s)
        s = s.replace('+', ' ')
        s = re.sub('%([0-9A-Fa-f]{2})', lambda m: chr(int(m.group(1), 16)), s)
        if s == prev:
            break
    return url_parse(s)

def url_parse(url):
    l = len(url)
    data = bytearray()
    i = 0
    while i < l:
        if url[i] != '%':
            d = ord(url[i])
            i += 1
        
        else:
            d = int(url[i+1:i+3], 16)
            i += 3
        
        data.append(d)
    
    return data.decode('utf8')

def web_page_wifi(status_messages, wifi_connected, wifi_ip):
    config = load_config()
    current_ssid = config.get('ssid', '')
    current_password = config.get('password', '')
    mac_address_string = get_mac_address()
    
    # Temperature
    temp = read_internal_temp()
    if temp is not None:
        print("Internal Temperature:", temp, "°C")
   
    status_html = ""
    for message in status_messages:
        status_html += f"<p>{message}</p>"

    connection_status = "Connected" if wifi_connected else "Not Connected"
    ip_info = f"IP Address: {wifi_ip}" if wifi_connected else ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ARX-RING Wi-Fi Configuration</title>
        {wifi_form_styles}
    </head>
    <body>
        <div class="container">
            <h2>Wi-Fi Configuration</h2>
            <div class="status">
                <h4>Status: {connection_status}</h4>
                <p>{ip_info}</p>
                {status_html}
            </div>
            <form action="/update_wifi" method="post">
            
                <h5>Mac Address: {mac_address_string}</h5>
                <h5>Internal Temperature: {temp} °C</h5>
            
                <label for="ssid">SSID:</label>
                <input type="text" id="ssid" name="ssid" value='""" + current_ssid + """' required>

                <label for="password">Password:</label>
                <input type="text" id="password" name="password" value='""" + current_password + """' required>

                <input type="submit" value="Update Wi-Fi">
            </form>
            <br>
            <a href="/config">Go to Additional Configuration</a>
        </div>
    </body>
    </html>
    """
    return html_content

def web_page_config(status_messages):
    # Load current configuration
    config = load_config()
    if config is None:
        print("Failed to load configuration file.")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ARX-RING Additional Configuration</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f2f2f2; }
                .container { width: 60%; margin: auto; background-color: #fff; padding: 20px; border-radius: 5px; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Additional Configuration</h2>
                <p class="error">Failed to load configuration file.</p>
                <br>
                <a href="/">Go to Wi-Fi Configuration</a>
            </div>
        </body>
        
        
        
        </html>
        """

    mothers = config.get('mothers', '')
    isMother = config.get('isMother', False)
    center_name = config.get('center_name', '')
    block_name = config.get('block_name', '')
    last_alarm = config.get('last_alarm', [])
    number_of_rooms = config.get('number_of_rooms', '')
    mother_alarms = config.get('mother_alarms', [])
    test_mode = config.get('test_mode', False)
    machine_code = config.get('machine_code', '')
    machine_token = config.get('machine_token', '')

    # Convert boolean to checked attribute
    isMother_checked = 'checked' if isMother else ''
    test_mode_checked = 'checked' if test_mode else ''

    # Generate status messages HTML
    status_html = ""
    for message in status_messages:
        status_html += f"<p>{message}</p>"

    # Generate mother_alarms HTML table
    if isinstance(mother_alarms, list) and mother_alarms:
        mother_alarms_html = """
        <h3>Mother Alarms</h3>
        <table>
            <tr>
                <th>Room</th>
                <th>Block Name</th>
                <th>Date</th>
                <th>Reference</th>
                <th>Ring</th>
            </tr>
        """
        for alarm in mother_alarms:
            if isinstance(alarm, dict):
                room = alarm.get('room', 'N/A')
                block = alarm.get('block_name', 'N/A')
                date = alarm.get('date', 'N/A')
                reference = alarm.get('reference','N/A')
                ring = 'Yes' if alarm.get('ring', False) else 'No'
                mother_alarms_html += f"""
                    <tr>
                        <td>{room}</td>
                        <td>{block}</td>
                         <td>{date}</td>
                         <td>{reference}</td>
                        <td>{ring}</td>
                    </tr>
                """
            else:
                # Handle non-dictionary entries gracefully
                mother_alarms_html += f"""
                    <tr>
                        <td colspan="3">Invalid alarm entry</td>
                    </tr>
                """
        mother_alarms_html += "</table>"
    else:
        mother_alarms_html = "<p>No mother alarms configured.</p>"
    
    # Generate last alarms HTML table
    if isinstance(last_alarm, list) and last_alarm:
        last_alarms_html = """
        <h3>Last Alarms</h3>
        <table>
            <tr>
                <th>Room</th>
                <th>Date</th>
                <th>Reference</th>
                <th>Mode</th>
                <th>Synced</th>
                <th>Sent to Mother</th>
            </tr>
        """
        for alarm in last_alarm:
            if isinstance(alarm, dict):
                room = alarm.get('roomName', 'N/A')
                date = alarm.get('alarmTime', 'N/A')
                reference = alarm.get('reference','N/A')
                mode = alarm.get('mode','N/A')
                synced = alarm.get('synced','N/A')
                status = 'Yes' if alarm.get('isSent', True) else 'No'
                last_alarms_html += f"""
                    <tr>
                        <td>{room}</td>
                         <td>{date}</td>
                         <td>{reference}</td>
                          <td>{mode}</td>
                          <td>{synced}</td>
                        <td>{status}</td>
                    </tr>
                """
            else:
                # Handle non-dictionary entries gracefully
                last_alarms_html += f"""
                    <tr>
                        <td colspan="3">Invalid alarm entry</td>
                    </tr>
                """
        last_alarms_html += "</table>"
    else:
        last_alarms_html = "<p>No last alarms configured.</p>"



    # Assemble the complete HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Additional Configuration</title>
        {table_style}
        {config_page_styles}
    </head>
    <body>
        <div class="container">
            <h2>Additional Configuration</h2>
            <div class="status">
                {status_html}
            </div>
            

            <br>
            <a href="/">Go to Wi-Fi Configuration</a>
        </div>
        
        <div class="layout">
  <input name="nav" type="radio" class="nav home-radio" id="home" checked="checked" />
  <div class="page home-page">
    <div class="page-contents">
     <div>
     <form action="/update_config" method="post">
                <span for="mothers">Mothers:</span>
                <input type="text" id="mothers" name="mothers" value="{mothers}" required>

                <span for="center_name">Center Name:</span>
                <input type="text" id="center_name" name="center_name" value="{center_name}" required>

                <span for="block_name">Block Name:</span>
                <input type="text" id="block_name" name="block_name" value="{block_name}" required>

                <span for="number_of_rooms">Number of Rooms:</span>
                <input type="text" id="number_of_rooms" name="number_of_rooms" value="{number_of_rooms}" required>
                
                <span for="machine_code">Machine Code:</span>
                <input type="text" id="machine_code" name="machine_code" value="{machine_code}" required>
                
                <span for="machine_token">Machine Token:</span>
                <input type="text" id="machine_token" name="machine_token" value="{machine_token}" required>

                <input type="checkbox" id="isMother" name="isMother" {isMother_checked}>
                <span for="isMother">Is Mother</span><br>

                <input type="checkbox" id="test_mode" name="test_mode" {test_mode_checked}>
                <span for="test_mode">Test Mode</span><br><br>

                <input type="submit" value="Update Configuration">
            </form>
     </div>
    </div>
  </div>
  <label class="nav" for="home">
    <span style="margin-right:4px">Settings</span>
  </label>

  <input name="nav" type="radio" class="about-radio" id="about" />
  <div class="page about-page">
    <div class="page-contents">
    {mother_alarms_html}
    </div>
  </div>
  <label class="nav" for="about">
   <span style="margin-right:4px">Mother Alarm History</span>
   </label>

  <input name="nav" type="radio" class="contact-radio" id="contact" />
  <div class="page contact-page">
    <div class="page-contents">
     {last_alarms_html}
     </div>
  </div>
  <label class="nav" for="contact">
    <span>
    <span style="margin-right:4px">
    Alarm History
    </span>
    
  </label>
</div>
        
    </body>
    </html>
    """
    return html_content




async def start_access_point():
    """
    Initializes and starts the Wi-Fi Access Point asynchronously.
    Returns the AP object and its IP address.
    """
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password)

    # Wait until the AP is active
    while not ap.active():
        await asyncio.sleep_ms(100)  # Non-blocking wait

    ap_ip = ap.ifconfig()[0]
    print('Access Point Active')
    print('AP SSID:', ap.config('essid'))
    print('AP IP Address:', ap_ip)

    return ap, ap_ip

async def stop_access_point(ap):
    """
    Stops the Wi-Fi Access Point asynchronously.
    """
    ap.active(False)
    print('Access Point Deactivated')
    
  
async def handle_client(reader, writer):
    try:
        request = await reader.read(1024)
        if not request:
            print("Empty request received.")
            writer.close()
            await writer.wait_closed()
            return

        request = request.decode('utf-8')
        print("Content =", str(request))
        
        # Parse HTTP request
        request_lines = request.split('\r\n')
        request_line = request_lines[0]
        parts = request_line.split(' ')
        if len(parts) < 2:
            method = 'GET'
            path = '/'
        else:
            method, path = parts[0], parts[1]
        
        status_messages = []
        
        # Handle different routes
        if method == 'GET' and path == '/':
            # Determine current Wi-Fi connection status
            wifi_connected = is_connected()
            wifi_ip = get_ip() if wifi_connected else ''
            
            # Serve the main Wi-Fi configuration page
            response = web_page_wifi(status_messages=status_messages, wifi_connected=wifi_connected, wifi_ip=wifi_ip)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        elif method == 'GET' and path == '/config':
            # Serve the additional configuration page
            response = web_page_config(status_messages=status_messages)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        elif method == 'POST' and path == '/update_wifi':
            print('/update_wifi')
            # Parse POST data
            body = request_lines[-1]
            # Extract form data
            params = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Decode URL-encoded characters using the helper function
                    key = url_decode(key)
                    value = url_decode(value)
                    params[key] = value
            
            new_ssid = params.get('ssid')
            new_password = params.get('password')
            
            if new_ssid and new_password:
                # Save the new Wi-Fi configuration
                config = load_config()
                if config:
                    config['ssid'] = new_ssid
                    config['password'] = new_password
                    save_config(config)
                    status_messages.append('Configuration updated: SSID and Password saved.')
                    
                    # Attempt to connect to the new Wi-Fi network
                    connected = connect_to_wifi()
                    if connected:
                        status_messages.append('Connected to new Wi-Fi network!')
                        print('Connected to new Wi-Fi network!')
                        print('IP Address:', get_ip())
                    else:
                        status_messages.append('Failed to connect to new Wi-Fi network.')
                        print('Failed to connect to new Wi-Fi network.')
                else:
                    status_messages.append('Failed to load existing configuration.')
                    print('Failed to load existing configuration.')
            else:
                status_messages.append('Invalid SSID or Password received.')
                print('Invalid SSID or Password received.')
            
            # Determine current Wi-Fi connection status
            wifi_connected = is_connected()
            wifi_ip = get_ip() if wifi_connected else ''
            
            # Serve the main Wi-Fi configuration page with status messages
            response = web_page_wifi(status_messages=status_messages, wifi_connected=wifi_connected, wifi_ip=wifi_ip)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        elif method == 'POST' and path == '/update_config':
            # Parse POST data
            body = request_lines[-1]
            # Extract form data
            params = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Decode URL-encoded characters using the helper function
                    key = url_decode(key)
                    value = url_decode(value)
                    params[key] = value
            
            # Handle checkboxes (presence means checked)
            isMother = 'isMother' in params
            test_mode = 'test_mode' in params
            
            # Retrieve other parameters
            mothers = params.get('mothers', '')
            center_name = params.get('center_name', '')
            block_name = params.get('block_name', '')
            number_of_rooms = params.get('number_of_rooms', '')
            machine_code = params.get('machine_code', '')
            machine_token = params.get('machine_token', '')
            
            # Debugging: Print the decoded 'number_of_rooms'
            print("Decoded 'number_of_rooms':", number_of_rooms)
            
            if number_of_rooms:
                status_messages.append(f"Number of Rooms: {number_of_rooms}")
            else:
                status_messages.append("Number of Rooms not provided.")
            
            # Update the configuration
            config = load_config()
            if config:
                config['mothers'] = mothers
                config['isMother'] = isMother
                config['center_name'] = center_name
                config['block_name'] = block_name
                config['number_of_rooms'] = number_of_rooms
                config['test_mode'] = test_mode
                config['machine_code'] = machine_code
                config['machine_token'] = machine_token
                save_config(config)
                status_messages.append('Additional configurations updated successfully.')
                asyncio.create_task(defaultDisplay())
            else:
                status_messages.append('Failed to load existing configuration.')
                print('Failed to load existing configuration.')
            
            # Serve the additional configuration page with status messages
            response = web_page_config(status_messages=status_messages)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
        else:
            # Handle unknown routes
            response = """<!DOCTYPE html>
                        <html>
                        <head>
                            <title>404 Not Found</title>
                        </head>
                        <body>
                            <h2>404 - Page Not Found</h2>
                            <p>The page you are looking for does not exist.</p>
                            <a href="/">Go to Home</a>
                        </body>
                        </html>"""
            writer.write('HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        
    except Exception as e:
            print("Failed to start socket server:", e)




