import network
import ure as re
import gc
import uasyncio as asyncio
from utils import *
from wifi_connect import *
from messages import defaultDisplay
from styles import *
from api_calls import ping_server_call
from time_sync import get_current_datetime_string,set_manual_time

gc.collect()

ap_ssid = 'SOTERIA-241'
ap_password = 'abcd@123'

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
    remaining_space = get_remaining_space()
    
    # Scan for available Wi-Fi networks
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        networks = wlan.scan()  # Returns a list of tuples: (ssid, bssid, channel, RSSI, authmode, hidden)
        # Extract unique SSIDs (filter out hidden networks and duplicates)
        available_ssids = sorted(set(net[0].decode('utf-8') for net in networks if net[0] and not net[5]))
    except Exception as e:
        print("Failed to scan Wi-Fi networks:", e)
        available_ssids = [current_ssid]  # Fallback to current SSID if scan fails
    finally:
        wlan.active(False)  # Deactivate STA mode after scanning

    # Generate the dropdown options for SSIDs
    ssid_options = ""
    for ssid in available_ssids:
        selected = 'selected' if ssid == current_ssid else ''
        ssid_options += f'<option value="{ssid}" {selected}>{ssid}</option>'

    status_html = ""
    for message in status_messages:
        status_html += f"<p>{message}</p>"

    connection_status = "Connected" if wifi_connected else "Not Connected"
    ip_info = f"IP Address: {wifi_ip}" if wifi_connected else ""

    # Add a status icon (using Unicode for simplicity; replace with an image if desired)
    status_icon = "✔" if wifi_connected else "✖"
    status_icon_class = "status-icon-connected" if wifi_connected else "status-icon-disconnected"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOTERIA Wi-Fi Configuration</title>
        {main_styles}
    </head>
    <body>
        <header>
            <div class="header-left">
                <div class="logo-icon">
                    <img src="/white-logo.png" alt="Logo" style="width: 50px; height: 50px;">
                </div>
                <div class="site-info">
                    <h1>Arxcess</h1>
                    <p>Soteria-241</p>
                </div>
            </div>
            <div class="header-right">
                <a href="/">Home</a>
                <a href="/config">Settings</a>
            </div>
        </header>
        <main>
            <div class="container">
                <h3>Wi-Fi Configuration</h3>
                <div class="status">
                    <h4><span class="{status_icon_class}">{status_icon}</span> Status: {connection_status}</h4>
                    <p>{ip_info}</p>
                    <p>Mac Address: {mac_address_string}</p>
                    <p>Remain Space: {remaining_space} MBz</p>
                    {status_html}
                </div>
                <form action="/update_wifi" method="post">
                    <label for="ssid">SSID:</label>
                    <select id="ssid" name="ssid" required>
                        {ssid_options}
                    </select>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" value="{current_password}" required>
                    <input type="submit" value="Update Wi-Fi">
                </form>
                <br>
            </div>
        </main>
        <footer>
            <p>© 2025 Arxcess Ltd. All rights reserved.</p>
        </footer>
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
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SOTERIA Additional Configuration</title>
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
    last_ping = config.get('last_ping','')
    date_string = get_current_datetime_string()

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
        <h2>Mother Alarms</h3>
        <table>
            <tr>
                <th>Room</th>
                <th>Block Name</th>
                <th>Date</th>
                <th>Reference</th>
                <th>Mode</th>
                <th>Ring</th>
            </tr>
        """
        for alarm in mother_alarms:
            if isinstance(alarm, dict):
                room = alarm.get('room', 'N/A')
                block = alarm.get('block_name', 'N/A')
                date = alarm.get('date', 'N/A')
                reference = alarm.get('reference','N/A')
                mode = alarm.get('mode','N/A')
                ring = 'Yes' if alarm.get('ring', False) else 'No'
                mother_alarms_html += f"""
                    <tr>
                        <td>{room}</td>
                        <td>{block}</td>
                         <td>{date}</td>
                         <td>{reference}</td>
                         <td>{mode}</td>
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
        <h2>Last Alarms</h3>
        <table>
            <tr>
                <th>Room</th>
                <th>Date</th>
                <th>Reference</th>
                <th>Mode</th>
                <th>Synced</th>
                <th>Sent to Mother</th>
                <th>Mothers</th>
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
                successful_mothers = alarm.get('successfulMothers','N/A')
                last_alarms_html += f"""
                    <tr>
                        <td>{room}</td>
                         <td>{date}</td>
                         <td>{reference}</td>
                          <td>{mode}</td>
                          <td>{synced}</td>
                          <td>{status}</td>
                          <td>{successful_mothers}</td>
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOTERIA Additional Configuration</title>
        {table_style}
        {main_styles}
    </head>
    <body>
        <header>
        <div class="header-left">
            <div class="logo-icon">
              <img src="/white-logo.png" alt="Logo" style="width: 50px; height: 50px;">
            </div> 
            <div class="site-info">
                <h1>Arxcess</h1>
                <p>Soteria-241</p>
            </div>
        </div>
        <div class="header-right">
            <a href="/">Home</a>
            <a href="/config">Settings</a>
        </div>
        
        </header>
        
        <main>
            <h2>Additional Configuration</h2>
            <div class="status">
                {status_html}
            </div>
             <div class="status">
                {last_ping}
            </div>
            <br>
       
            <form action="/update_config" method="post">
            
                <label for="date">Device Date: ( {date_string} )</label>
                <input id="date" type="datetime-local" name="date" value="" />
            
                <label for="mothers">Mothers:</label>
                <input type="text" id="mothers" name="mothers" value="{mothers}" required>

                <label for="center_name">Center Name:</label>
                <input type="text" id="center_name" name="center_name" value="{center_name}" required>

                <label for="block_name">Block Name:</label>
                <input type="text" id="block_name" name="block_name" value="{block_name}" required>

                <label for="number_of_rooms">Number of Rooms:</label>
                <input type="text" id="number_of_rooms" name="number_of_rooms" value="{number_of_rooms}" required>
                
                <label for="machine_code">Machine Code:</label>
                <input type="text" id="machine_code" name="machine_code" value="{machine_code}" required>
                
                <label for="machine_token">Machine Token:</label>
                <input type="text" id="machine_token" name="machine_token" value="{machine_token}" required>

                <div class="checkbox-group">
                    <input type="checkbox" id="isMother" name="isMother" {isMother_checked}>
                    <label for="isMother">Is Mother</label>
                </div>
                 <div class="checkbox-group">
                    <input type="checkbox" id="test_mode" name="test_mode" {test_mode_checked}>
                    <label for="test_mode">Maintenance Mode</label>
                </div>

                <input type="submit" value="Update Configuration">
            </form>
 
        <div class="table-container">
         {mother_alarms_html if isMother else ""}
        </div>
    
        <div class="table-container">
         {last_alarms_html if not isMother else ""}
        </div>
        
        </main>
        
        <footer>
        <p>&copy; 2025 Arxcess Ltd. All rights reserved.</p>
        </footer>
        
    </body>
    </html>
    """
    return html_content

async def start_access_point():
    config = load_config()
    block_name = config.get("block_name", "")
    """
    Initializes and starts the Wi-Fi Access Point asynchronously.
    Returns the AP object and its IP address.
    """
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=f"{ap_ssid} ({block_name})", password=ap_password, authmode=3)  # authmode=3 for WPA2

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
            gc.collect()  # Collect garbage after serving the page
            return
        
        elif path == '/white-logo.png':
            # Serve the image
            try:
                with open('/white-logo.png', 'rb') as f:
                    image_data = f.read()
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n')
                writer.write(image_data)
                await writer.drain()
            except OSError:
                writer.write(b'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n')
                writer.write(b'404: Image not found')
                await writer.drain()
            writer.close()
            await writer.wait_closed()
            gc.collect()  # Collect garbage after serving the image
            return
        
        elif method == 'GET' and path == '/config':
            # Serve the additional configuration page
            response = web_page_config(status_messages=status_messages)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            gc.collect()  # Collect garbage after serving the page
            return
        
        elif method == 'POST' and path == '/update_wifi':
            gc.collect()  # Collect garbage before processing POST
            print('/update_wifi')
            # Parse POST data
            body = request_lines[-1]
            print("Raw POST body:", body)  # Debug: Print the raw body
            
            # Extract form data
            params = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Decode URL-encoded characters using the helper function
                    key = url_decode(key)
                    value = url_decode(value)
                    params[key] = value
            
            print("Parsed params:", params)  # Debug: Print the parsed parameters
            
            new_ssid = params.get('ssid')
            new_password = params.get('password')
            
            print("New SSID:", new_ssid)  # Debug: Print the extracted SSID
            print("New Password:", new_password)  # Debug: Print the extracted password
            
            if new_ssid and new_password:
                # Load current configuration
                config = load_config()
                if not config:
                    print("Failed to load configuration, creating new config")
                    config = {}
                
                # Store old values for rollback if needed
                old_ssid = config.get('ssid', '')
                old_password = config.get('password', '')
                
                # Update configuration
                config['ssid'] = new_ssid
                config['password'] = new_password
                
                # Save configuration
                if save_config(config):
                    print("Configuration saved successfully")
                    
                    # Verify the save was successful
                    verify_config()
                    
                    # Attempt to connect to the new Wi-Fi network
                    connected = connect_to_wifi()
                    if connected:
                        status_messages.append('Connected to new Wi-Fi network!')
                        print('Connected to new Wi-Fi network!')
                        print('IP Address:', get_ip())
                    else:
                        # If connection fails, rollback to old configuration
                        print("Connection failed, rolling back to old configuration")
                        config['ssid'] = old_ssid
                        config['password'] = old_password
                        save_config(config)
                        verify_config()
                        status_messages.append('Failed to connect to new Wi-Fi network. Rolled back to previous configuration.')
                        print('Failed to connect to new Wi-Fi network.')
                else:
                    status_messages.append('Failed to save configuration.')
                    print('Failed to save configuration.')
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
            gc.collect()  # Collect garbage after processing POST
            return
        
        elif method == 'POST' and path == '/update_config':
            gc.collect()  # Collect garbage before processing POST
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
            date = params.get('date', '')
            
            # Handle date update if provided
            if date:
                try:
                    # Parse the datetime string (format: "YYYY-MM-DDTHH:mm")
                    dt = date.split('T')
                    date_parts = dt[0].split('-')
                    time_parts = dt[1].split(':')
                    
                    # Convert to integers
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = 0  # Default to 0 seconds
                    
                    # Set the time
                    if set_manual_time(year, month, day, hour, minute, second):
                        print(year, month, day, hour, minute, second)
                        status_messages.append('Time updated successfully')
                    else:
                        status_messages.append('Failed to update time')
                except Exception as e:
                    status_messages.append(f'Error updating time: {str(e)}')
            
            # Load current configuration
            config = load_config()
            if not config:
                print("Failed to load configuration, creating new config")
                config = {}
            
            # Store old values for potential rollback
            old_config = config.copy()
            
            # Update configuration with new values
            config['mothers'] = mothers
            config['isMother'] = isMother
            config['center_name'] = center_name
            config['block_name'] = block_name
            config['number_of_rooms'] = number_of_rooms
            config['test_mode'] = test_mode
            config['machine_code'] = machine_code
            config['machine_token'] = machine_token
            
            # Save and verify configuration
            if save_config(config):
                if verify_config():
                    print("Configuration verified successfully")
                    status_messages.append('Additional configurations updated successfully.')
                    
                    # Update display and ping server
                    asyncio.create_task(defaultDisplay())
                    await ping_server_call()
                else:
                    # If verification fails, rollback to old configuration
                    print("Configuration verification failed, rolling back")
                    if save_config(old_config):
                        if verify_config():
                            status_messages.append('Configuration update failed. Rolled back to previous settings.')
                        else:
                            status_messages.append('Critical error: Failed to verify rollback configuration.')
                    else:
                        status_messages.append('Critical error: Failed to rollback configuration.')
            else:
                status_messages.append('Failed to save configuration.')
                print('Failed to save configuration.')
            
            # Serve the additional configuration page with status messages
            response = web_page_config(status_messages=status_messages)
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            gc.collect()  # Collect garbage after processing POST
            return
        
        else:
            # Handle unknown routes
            response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>404 Not Found</title>
            </head>
            <body>
                <h2>404 - Page Not Found</h2>
                <p>The page you are looking for does not exist.</p>
                <a href="/">Go to Home</a>
            </body>
            </html>
            """
            writer.write('HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n' + response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            gc.collect()  # Collect garbage after serving 404
            return
        
    except Exception as e:
        print("Failed to start socket server:", e)
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
        gc.collect()  # Collect garbage after error