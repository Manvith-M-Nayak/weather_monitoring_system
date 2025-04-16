import socket
import requests
import json
import time

# ========== Configuration ==========

# IP address of the server
SERVER_IP = '127.0.0.1'  # CHANGE this to the actual server IP if on different machine

# Port number where server is listening
SERVER_PORT = 9000

# Coordinates for weather API (example: Bangalore)
LATITUDE = 28.61
LONGITUDE = 77.20

# ========== Utility Functions ==========

def debug_print(header, message):
    print(f"\n===== {header} =====")
    print(message)

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
        temperature = current.get("temperature", None)
        windspeed = current.get("windspeed", None)
        wind_direction = current.get("winddirection", None)
        weather_code = current.get("weathercode", None)
        time_value = current.get("time", None)

        # Prepare a dictionary in strict JSON-compatible format
        json_data = {
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

# ========== Socket Connection ==========

def send_to_server(json_dict, server_ip, server_port):
    """
    Sends a Python dictionary to the server as a JSON string over a TCP socket.
    """
    try:
        json_string = json.dumps(json_dict)  # Serialize the dictionary to JSON string
        debug_print("SOCKET", f"Connecting to server {server_ip}:{server_port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(10)
            client_socket.connect((server_ip, server_port))
            debug_print("SOCKET", "Connection established.")
            client_socket.sendall(json_string.encode('utf-8'))
            debug_print("SOCKET", "JSON data sent successfully.")
    except socket.timeout:
        debug_print("ERROR", "Socket connection timed out.")
    except ConnectionRefusedError:
        debug_print("ERROR", "Connection refused by the server. Is the server running?")
    except socket.gaierror:
        debug_print("ERROR", f"Invalid IP address or hostname: {server_ip}")
    except Exception as e:
        debug_print("ERROR", f"Unknown socket error: {str(e)}")

# ========== Main Execution ==========

def main():
    print("=== WEATHER CLIENT DEBUG MODE ===")

    # Step 1: Get weather data as a Python dictionary
    weather_data = get_weather_data(LATITUDE, LONGITUDE)

    if not weather_data:
        debug_print("EXIT", "Weather data could not be retrieved. Exiting client.")
        return

    # Step 2: Send JSON data to server
    send_to_server(weather_data, SERVER_IP, SERVER_PORT)

    debug_print("DONE", "Client execution completed.")

if __name__ == "__main__":
    main()
