import socket
import json
import time

def send_raw_socket_data(host, port, data):
    try:
        print(f"Connecting to {host}:{port}...")
        with socket.create_connection((host, port)) as sock:
            json_data = json.dumps(data)
            sock.sendall(json_data.encode())
            print("Data sent successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    weather_data = {
        "location": "(28.61, 77.20)",
        "temperature": 28,
        "windspeed": 10,
        "windindirection": 90,
        "weathercode": 1,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    send_raw_socket_data("serveo.net", 14500, weather_data)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()