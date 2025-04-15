import socket
import threading
import time
import subprocess
import re
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import json
import sys

# Server Configuration
HOST = '0.0.0.0'
PORT = 443

class WeatherServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌤️ Weather Monitoring Server")
        self.root.geometry("750x550")
        self.root.resizable(True, True)

        # Header
        self.header_label = ttk.Label(root, text="Weather Monitoring Server", font=("Helvetica", 18, "bold"), foreground="darkblue")
        self.header_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Log area
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=25, font=("Consolas", 11))
        self.text_area.grid(row=1, column=0, padx=10, pady=10)
        self.text_area.insert(tk.END, "Server initializing...\n")
        self.text_area.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Waiting for connections...")
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Helvetica", 10), foreground="gray")
        self.status_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Text tags for coloring
        self.text_area.tag_config("INFO", foreground="green")
        self.text_area.tag_config("ERROR", foreground="red")
        self.text_area.tag_config("DATA", foreground="blue")
        self.text_area.tag_config("CONNECT", foreground="orange")
        self.text_area.tag_config("TUNNEL", foreground="purple")
        self.text_area.tag_config("RESPONSE", foreground="magenta")  # New tag for responses

        self.clients_connected = 0
        self.public_url = None
        self.server_socket = None

    def log(self, message, tag="INFO"):
        self.text_area.config(state=tk.NORMAL)
        timestamp = time.strftime('%H:%M:%S')
        self.text_area.insert(tk.END, f"{timestamp} - {message}\n", tag)
        self.text_area.yview(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def update_status(self, message):
        self.status_var.set(f"Status: {message}")

def start_server(gui):
    try:
        gui.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gui.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        gui.server_socket.bind((HOST, PORT))
        gui.server_socket.listen(5)
        gui.log(f"Server started on {HOST}:{PORT}", "INFO")
        gui.update_status(f"Listening on {HOST}:{PORT}")

        while True:
            try:
                client_socket, client_addr = gui.server_socket.accept()
                gui.clients_connected += 1
                gui.log(f"Client connected: {client_addr}", "CONNECT")
                gui.update_status(f"{gui.clients_connected} client(s) connected")
                
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_addr, gui)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if gui.server_socket:
                    gui.log(f"Error accepting client: {str(e)}", "ERROR")
    except Exception as e:
        gui.log(f"Failed to start server: {str(e)}", "ERROR")
        sys.exit(1)

def handle_client(client_socket, client_addr, gui):
    try:
        data = client_socket.recv(4096).decode()
        if data:
            try:
                # Parse HTTP request to extract JSON body
                if "HTTP" in data and "Content-Type:" in data:
                    parts = data.split('\r\n\r\n', 1)
                    if len(parts) > 1:
                        data = parts[1]

                json_data = json.loads(data)
                pretty_data = json.dumps(json_data, indent=2)
                gui.log(f"Data from {client_addr}:", "DATA")
                gui.log(pretty_data, "DATA")
                
                # Generate meaningful response based on weather data
                weather_feedback = generate_weather_feedback(json_data)
                
                response_data = {
                    "status": "success",
                    "message": "Weather data received successfully",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "weather_feedback": weather_feedback,
                    "data_received": json_data  # Echo back the data received
                }
                
                response_json = json.dumps(response_data)
                
                # If the request was HTTP, send HTTP response
                if "HTTP" in data:
                    http_response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        f"Content-Length: {len(response_json)}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{response_json}"
                    )
                    client_socket.send(http_response.encode())
                else:
                    # Otherwise just send the JSON
                    client_socket.send(response_json.encode())
                
                # Log the response
                gui.log("Sending response:", "RESPONSE")
                gui.log(json.dumps(response_data, indent=2), "RESPONSE")
                
            except json.JSONDecodeError:
                gui.log(f"Raw data from {client_addr}:", "DATA")
                gui.log(data, "DATA")
                
                # Send error response
                error_response = json.dumps({
                    "status": "error",
                    "message": "Invalid JSON data received",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
                if "HTTP" in data:
                    http_response = (
                        "HTTP/1.1 400 Bad Request\r\n"
                        "Content-Type: application/json\r\n"
                        f"Content-Length: {len(error_response)}\r\n"
                        "Connection: close\r\n"
                        "\r\n"
                        f"{error_response}"
                    )
                    client_socket.send(http_response.encode())
                else:
                    client_socket.send(error_response.encode())
                
                gui.log("Sending error response:", "ERROR")
                gui.log(error_response, "ERROR")
                
    except Exception as e:
        gui.log(f"Error with client {client_addr}: {str(e)}", "ERROR")
    finally:
        client_socket.close()
        gui.clients_connected = max(0, gui.clients_connected - 1)
        gui.update_status(f"{gui.clients_connected} client(s) connected")

def generate_weather_feedback(weather_data):
    """Generate meaningful feedback based on weather data"""
    feedback = []
    
    try:
        if "temperature" in weather_data:
            temp = weather_data["temperature"]
            if temp > 30:
                feedback.append(f"High temperature of {temp}°C detected. Heat advisory in effect.")
            elif temp < 5:
                feedback.append(f"Low temperature of {temp}°C detected. Cold weather alert.")
            else:
                feedback.append(f"Current temperature is {temp}°C. Normal range.")
        
        if "windspeed" in weather_data:
            wind = weather_data["windspeed"]
            if wind > 20:
                feedback.append(f"Strong winds at {wind} km/h. Exercise caution.")
            else:
                feedback.append(f"Wind speed at {wind} km/h.")
        
        if "weathercode" in weather_data:
            code = weather_data["weathercode"]
            conditions = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snow fall",
                73: "Moderate snow fall",
                75: "Heavy snow fall",
                95: "Thunderstorm"
            }
            condition = conditions.get(code, f"Unknown condition (code {code})")
            feedback.append(f"Weather condition: {condition}")
        
        if "location" in weather_data:
            feedback.append(f"Location: {weather_data['location']}")
            
        if "time" in weather_data:
            feedback.append(f"Time recorded: {weather_data['time']}")
            
    except Exception as e:
        feedback.append(f"Error analyzing weather data: {str(e)}")
    
    return feedback

def start_localtunnel(gui):
    try:
        gui.log("Starting LocalTunnel...", "TUNNEL")
        process = subprocess.Popen(
            ["lt", "--port", str(PORT), "--subdomain", "weather-monitoring"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        def monitor_output():
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                gui.log(f"LT: {line.strip()}", "TUNNEL")
                match = re.search(r"(https://[^\s]+)", line)
                if match:
                    gui.public_url = match.group(1)
                    gui.log(f"Public URL: {gui.public_url}", "TUNNEL")
                    gui.update_status(f"Tunnel: {gui.public_url}")
        
        threading.Thread(target=monitor_output, daemon=True).start()
    except Exception as e:
        gui.log(f"LocalTunnel error: {str(e)}", "ERROR")

if __name__ == "__main__":
    root = tk.Tk()
    gui = WeatherServerGUI(root)

    # Start server thread
    server_thread = threading.Thread(target=start_server, args=(gui,))
    server_thread.daemon = True
    server_thread.start()

    # Start LocalTunnel thread
    tunnel_thread = threading.Thread(target=start_localtunnel, args=(gui,))
    tunnel_thread.daemon = True
    tunnel_thread.start()

    # Handle window close
    def on_closing():
        if gui.server_socket:
            gui.server_socket.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()