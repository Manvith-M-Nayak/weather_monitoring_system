import socket
import requests
import json
import time

# ========== Configuration ==========

# IP address of the server
SERVER_IP = '127.0.0.1'  # CHANGE this to the actual server IP if on different machine

# Port number where server is listening
SERVER_PORT = 9000

# Open-Meteo API endpoint (latitude and longitude for New Delhi as example)
LATITUDE = 28.61
LONGITUDE = 77.20

# ========== Utility Functions ==========

def debug_print(header, message):
    print(f"\n===== {header} =====")
    print(message)

# ========== Weather API Fetching ==========

def get_weather_data(latitude, longitude):
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
        temperature = current.get("temperature", "N/A")
        windspeed = current.get("windspeed", "N/A")
        winddir = current.get("winddirection", "N/A")
        weather_code = current.get("weathercode", "N/A")
        time_value = current.get("time", "N/A")

        formatted_data = (
            f"Location: ({latitude}, {longitude})\n"
            f"Time: {time_value}\n"
            f"Temperature: {temperature} °C\n"
            f"Windspeed: {windspeed} km/h\n"
            f"Wind Direction: {winddir}°\n"
            f"Weather Code: {weather_code}"
        )

        debug_print("FORMATTED WEATHER DATA", formatted_data)
        return formatted_data

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

def send_to_server(data, server_ip, server_port):
    try:
        debug_print("SOCKET", f"Attempting to connect to server {server_ip}:{server_port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(10)
            client_socket.connect((server_ip, server_port))
            debug_print("SOCKET", "Connection established.")
            client_socket.sendall(data.encode())
            debug_print("SOCKET", "Data sent successfully.")
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

    # Step 1: Get weather data
    weather_data = get_weather_data(LATITUDE, LONGITUDE)

    if not weather_data:
        debug_print("EXIT", "Weather data could not be retrieved. Exiting client.")
        return

    # Step 2: Send data to server
    send_to_server(weather_data, SERVER_IP, SERVER_PORT)

    debug_print("DONE", "Client execution completed.")

if __name__ == "__main__":
    main()
