# server.py

import network
from time import sleep
import ujson  # Use ujson for MicroPython
from MicroWebSrv.microWebSrv import MicroWebSrv
import uasyncio as asyncio
from wifi_connect import get_ip
from utils import *
from machine import Pin
from messages import defaultDisplay
import uasyncio as asyncio

SIREN_PIN = Pin(3, Pin.OUT)

server_instance = None

# Define a GET route handler for the configuration
def alarm_off_handler(httpClient, httpResponse):
    try:
        SIREN_PIN.value(0)
        reset_mother()
        asyncio.create_task(defaultDisplay())
        with open('wifi_config.json', 'r') as f:
            config = f.read()
        # Return the config as JSON
        httpResponse.WriteResponseOk(
            headers=None,
            contentType="application/json",
            contentCharset="UTF-8",
            content=config
        )
    except Exception:
        httpResponse.WriteResponseInternalServerError()

# Define a GET route handler for the configuration
def config_get_handler(httpClient, httpResponse):
    try:
        with open('wifi_config.json', 'r') as f:
            config = f.read()
        # Return the config as JSON
        httpResponse.WriteResponseOk(
            headers=None,
            contentType="application/json",
            contentCharset="UTF-8",
            content=config
        )
    except Exception:
        httpResponse.WriteResponseInternalServerError()

# Define a PUT route handler to update the configuration
def config_put_handler(httpClient, httpResponse):
    # Get JSON payload from request
    content = httpClient.ReadRequestContentAsJSON()
    if content:
        try:
            # Load current config for rollback
            config = load_config()
            if not config:
                httpResponse.WriteResponseInternalServerError()
                return
                
            old_config = config.copy()
            
            # Update config with new values
            config.update(content)
            
            # Save and verify configuration
            if save_config(config):
                if verify_config():
                    httpResponse.WriteResponseOk(
                        headers=None,
                        contentType="application/json",
                        contentCharset="UTF-8",
                        content=ujson.dumps({"message": "Configuration updated successfully"})
                    )
                else:
                    # If verification fails, rollback
                    if save_config(old_config):
                        verify_config()
                    httpResponse.WriteResponseInternalServerError()
            else:
                httpResponse.WriteResponseInternalServerError()
        except Exception:
            httpResponse.WriteResponseInternalServerError()
    else:
        # Bad request
        httpResponse.WriteResponseBadRequest({"error": "Invalid JSON data in request."})
        

# Define the POST route handler for '/mother/alarm'
def mother_alarm_handler(httpClient, httpResponse):
    # Read the JSON data from the request
    data = httpClient.ReadRequestContentAsJSON()
    if data:
        block_name = data.get('block_name')
        room = data.get('room')
        if block_name and room:
            # Load current configuration
            config = load_config()
            if not config:
                response_data = {'error': 'Failed to load configuration file.'}
                httpResponse.WriteResponseInternalServerError(obj=response_data)
                return

            # Store old config for rollback
            old_config = config.copy()

            # Initialize mother_alarms if it doesn't exist
            if 'mother_alarms' not in config or not isinstance(config['mother_alarms'], list):
                config['mother_alarms'] = []

            # Create new alarm entry
            new_alarm = {
                'block_name': block_name,
                'room': room,
                'date': data.get('date', ''),
                'reference': data.get('reference', ''),
                'mode': data.get('mode', '')
            }

            # Add the new alarm to the list
            config['mother_alarms'].append(new_alarm)

            # Get machine code for response
            machine_code = config.get('machine_code', '')

            # Save and verify configuration
            if save_config(config):
                if verify_config():
                    # Send a success response
                    response_data = {'message': 'Alarm received and saved successfully', 'machine_code': machine_code}
                    httpResponse.WriteResponseJSONOk(obj=response_data)
                else:
                    # If verification fails, rollback
                    if save_config(old_config):
                        verify_config()
                    response_data = {'error': 'Failed to verify configuration.'}
                    httpResponse.WriteResponseInternalServerError(obj=response_data)
            else:
                response_data = {'error': 'Failed to update configuration file.'}
                httpResponse.WriteResponseInternalServerError(obj=response_data)
        else:
            # Missing 'block_name' or 'room' in the data
            response_data = {'error': 'Missing "block_name" or "room" in request data'}
            httpResponse.WriteResponseBadRequest(obj=response_data)
    else:
        # Invalid or missing JSON data
        response_data = {'error': 'Invalid or missing JSON data'}
        httpResponse.WriteResponseBadRequest(obj=response_data)
        
        
# Define the POST route handler for '/device/mode'
def device_mode_handler(httpClient, httpResponse):
    # Read the JSON data from the request
    data = httpClient.ReadRequestContentAsJSON()
    if data:
        test_mode = data.get('test_mode')
        # Load current configuration
        config = load_config()
        if not config:
            response_data = {'error': 'Failed to load configuration file.'}
            httpResponse.WriteResponseInternalServerError(obj=response_data)
            return

        # Store old config for rollback
        old_config = config.copy()

        # Update test mode
        config['test_mode'] = test_mode

        # Save and verify configuration
        if save_config(config):
            if verify_config():
                response_data = {'message': 'Mode saved successfully'}
                httpResponse.WriteResponseJSONOk(obj=response_data)
            else:
                # If verification fails, rollback
                if save_config(old_config):
                    verify_config()
                response_data = {'error': 'Failed to verify configuration.'}
                httpResponse.WriteResponseInternalServerError(obj=response_data)
        else:
            response_data = {'error': 'Failed to update configuration file.'}
            httpResponse.WriteResponseInternalServerError(obj=response_data)
    else:
        # Invalid or missing JSON data
        response_data = {'error': 'Invalid or missing JSON data'}
        httpResponse.WriteResponseBadRequest(obj=response_data)

# Function to start the server
def start_server():
    global server_instance
    config = load_config()
    
    if server_instance is not None:
        return server_instance

    # Connect to Wi-Fi
    ip_address = get_ip()
    if not ip_address:
        if config:
            # Store old config for rollback
            old_config = config.copy()
            config['ip_address'] = ""
            
            # Save and verify configuration
            if save_config(config):
                if not verify_config():
                    if save_config(old_config):
                        verify_config()
        return None

    # Update the config file with the ip_address
    if config:
        # Store old config for rollback
        old_config = config.copy()
        config['ip_address'] = ip_address
        
        # Save and verify configuration
        if save_config(config):
            if not verify_config():
                if save_config(old_config):
                    verify_config()

    # Initialize the server with route handlers
    routeHandlers = [
        ("/api/alarm/off", "GET", alarm_off_handler),
        ("/api/config", "GET", config_get_handler),
        ("/api/config", "PUT", config_put_handler),
        ("/api/mother/alarm", "PUT", mother_alarm_handler),
        ("/api/device/mode", "PUT", device_mode_handler)
    ]
    srv = MicroWebSrv(routeHandlers=routeHandlers)
    srv.Start(threaded=True)

    server_instance = srv  # Store the server instance
    return srv

# Optional: Function to stop the server
def stop_server(srv):
    srv.Stop()
