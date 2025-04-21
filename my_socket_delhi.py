import socket
import requests
import json
import ssl
import time
from datetime import datetime

# ========== Configuration ==========

# IP address of the server (must match certificate CN or SAN)
SERVER_IP = 'localhost'  # or 127.0.0.1 if your cert supports it

# Port number for the secure SSL socket
SERVER_PORT = 9000

# SSL certificate file from the server (self-signed or CA-signed)
CERT_FILE = 'server.crt'  # Must be trusted by this client

# Coordinates for weather API (e.g., Bangalore)
LATITUDE = 28.6139
LONGITUDE = 77.2090

# Station identification (added for enhanced display)
STATION_INFO = {
    "station_id": "WS-002",
    "station_name": "Weather Monitor Client"
}

# ========== Utility Functions ==========

def debug_print(header, message):
    """Print debug information with a formatted header"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n===== {header} [{timestamp}] =====")
    print(message)

def format_value(value, unit=""):
    """Format a value with its unit for display"""
    if value is None:
        return "N/A"
    return f"{value} {unit}".strip()

# ========== Weather API Fetching ==========

def get_weather_data(latitude, longitude):
    """
    Fetches current weather data from Open-Meteo API for the given latitude and longitude.
    Returns a Python dictionary ready to be converted into JSON.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&current_weather=true"
    )

    try:
        debug_print("API REQUEST", f"Requesting data from Open-Meteo API:\n{url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        debug_print("API RESPONSE", json.dumps(data, indent=4))

        current = data.get("current_weather", {})
        temperature = current.get("temperature")
        windspeed = current.get("windspeed")
        wind_direction = current.get("winddirection")
        weather_code = current.get("weathercode")
        time_value = current.get("time")

        # Enhance the data with station information
        json_data = {
            "station_id": STATION_INFO["station_id"],
            "station_name": STATION_INFO["station_name"],
            "location": [latitude, longitude],
            "time": time_value,
            "temperature": f"{temperature} °C" if temperature is not None else "N/A",
            "windspeed": f"{windspeed} km/h" if windspeed is not None else "N/A",
            "wind_direction": f"{wind_direction}°" if wind_direction is not None else "N/A",
            "weather_code": weather_code if weather_code is not None else "N/A"
        }

        debug_print("FORMATTED JSON DATA", json.dumps(json_data, indent=4))
        return json_data

    except requests.exceptions.Timeout:
        debug_print("ERROR", "API request timed out.")
    except requests.exceptions.ConnectionError:
        debug_print("ERROR", "Failed to connect to API server.")
    except requests.exceptions.HTTPError as err:
        debug_print("ERROR", f"HTTP error: {err}")
    except Exception as e:
        debug_print("ERROR", f"Unknown error fetching weather data: {str(e)}")

    return None

# ========== Secure Socket Connection ==========

def send_to_server_secure(json_dict, server_ip, server_port, certfile):
    """
    Sends a JSON-formatted dictionary to the server securely using SSL.
    Waits for an acknowledgment from the server.
    """
    try:
        json_string = json.dumps(json_dict)

        debug_print("SSL SETUP", f"Using certificate file: {certfile}")
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=certfile)

        debug_print("SOCKET", f"Connecting to SSL server {server_ip}:{server_port}...")
        with socket.create_connection((server_ip, server_port), timeout=10) as raw_sock:
            with context.wrap_socket(raw_sock, server_hostname=server_ip) as ssl_sock:
                debug_print("SSL CONNECTION", "SSL handshake successful. Secure connection established.")
                debug_print("CONNECTION INFO", f"Using cipher: {ssl_sock.cipher()}")
                
                # Send the JSON data
                ssl_sock.sendall(json_string.encode('utf-8'))
                debug_print("DATA SENT", "Secure JSON data sent successfully.")

                # Wait for server acknowledgment
                response = ssl_sock.recv(1024)
                if response:
                    debug_print("SERVER RESPONSE", response.decode())
                else:
                    debug_print("SERVER RESPONSE", "No response received from server.")

    except ssl.SSLError as ssl_err:
        debug_print("SSL ERROR", f"SSL error: {ssl_err}")
    except socket.timeout:
        debug_print("ERROR", "Socket connection timed out.")
    except ConnectionRefusedError:
        debug_print("ERROR", "Connection refused by the server. Is the server running?")
    except FileNotFoundError:
        debug_print("ERROR", f"Certificate file '{certfile}' not found.")
    except Exception as e:
        debug_print("ERROR", f"Unknown socket/SSL error: {str(e)}")

# ========== Periodic Data Sending ==========

def periodic_sender(interval=60):
    """
    Periodically fetches weather data and sends it to the server.
    
    Args:
        interval: Time in seconds between data transmissions
    """
    try:
        while True:
            debug_print("SCHEDULER", f"Fetching and sending weather data (interval: {interval}s)")
            
            # Step 1: Fetch weather data
            weather_data = get_weather_data(LATITUDE, LONGITUDE)
            
            if weather_data:
                # Step 2: Send data securely using SSL
                send_to_server_secure(weather_data, SERVER_IP, SERVER_PORT, CERT_FILE)
            else:
                debug_print("WARNING", "Weather data could not be retrieved. Skipping this update.")
            
            # Wait for next interval
            debug_print("SCHEDULER", f"Next update in {interval} seconds")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        debug_print("EXIT", "Client stopped by user (Ctrl+C).")
    except Exception as e:
        debug_print("CRITICAL ERROR", f"Unexpected error in periodic sender: {str(e)}")

# ========== Main Execution ==========

def main():
    print("\n" + "="*60)
    print(" WEATHER MONITORING CLIENT (SSL MODE) ".center(60, "="))
    print("="*60 + "\n")

    mode = input("Run mode [O]nce or [C]ontinuous (default: Once)? ").lower()
    
    if mode == 'c':
        interval = input("Update interval in seconds (default: 60): ")
        try:
            interval = int(interval) if interval.strip() else 60
        except ValueError:
            interval = 60
            print(f"Invalid input. Using default interval of {interval} seconds.")
        
        print(f"\nStarting continuous monitoring with {interval}s interval...")
        print("Press Ctrl+C to stop the client.")
        periodic_sender(interval)
    else:
        # Default mode: Run once
        debug_print("MODE", "Running in single-transmission mode")
        
        # Step 1: Fetch weather data
        weather_data = get_weather_data(LATITUDE, LONGITUDE)

        if not weather_data:
            debug_print("EXIT", "Weather data could not be retrieved. Exiting client.")
            return

        # Step 2: Send data securely using SSL
        send_to_server_secure(weather_data, SERVER_IP, SERVER_PORT, CERT_FILE)

        debug_print("DONE", "Client execution completed.")

if __name__ == "__main__":
    main()