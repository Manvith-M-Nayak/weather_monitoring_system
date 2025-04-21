import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import time
import json
import ssl
from datetime import datetime
import requests

# Server Configuration
HOST = '0.0.0.0'
PORT = 9000

# Weather code translation dictionary
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

# Global dictionary to store data from all weather stations
stations_data = {}

# Function to get location name from coordinates
def get_location_name(lat, lon):
    """Get location name from coordinates using Nominatim API"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {
            "User-Agent": "WeatherMonitoringServer/1.0"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                address = data["address"]
                # Try to construct a sensible location name
                if "city" in address:
                    return address["city"]
                elif "town" in address:
                    return address["town"]
                elif "village" in address:
                    return address["village"]
                elif "suburb" in address:
                    return address["suburb"]
                elif "county" in address:
                    return address["county"]
                else:
                    return f"{address.get('state', '')}, {address.get('country', '')}"
        return "Unknown Location"
    except Exception:
        return "Unknown Location"

# GUI Class for Main Server Window
class WeatherServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌤️ Weather Monitoring Server")
        self.root.geometry("750x500")
        self.root.resizable(True, True)

        # Define styles
        self.setup_styles()

        # Header Frame
        header_frame = ttk.Frame(root)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Header
        self.header_label = ttk.Label(header_frame, text="Weather Monitoring Server", 
                                     style="Header.TLabel")
        self.header_label.pack(side=tk.LEFT)
        
        # View Data Button
        self.view_button = ttk.Button(header_frame, text="View Weather Data", 
                                     command=self.open_data_viewer)
        self.view_button.pack(side=tk.RIGHT, padx=10)
        
        # Scrolled text area for logs
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=25, 
                                                  font=("Consolas", 11))
        self.text_area.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.text_area.insert(tk.END, "Server initializing...\n")
        self.text_area.config(state=tk.DISABLED)

        # Status bar
        status_frame = ttk.Frame(root)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Waiting for connections...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # Connection count
        self.connection_var = tk.StringVar()
        self.connection_var.set("Connections: 0")
        self.connection_label = ttk.Label(status_frame, textvariable=self.connection_var, 
                                         style="Connection.TLabel")
        self.connection_label.pack(side=tk.RIGHT)

        # Make grid resizable
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Color tag setup for styling
        self.text_area.tag_config("INFO", foreground="green")
        self.text_area.tag_config("ERROR", foreground="red")
        self.text_area.tag_config("DATA", foreground="blue")
        self.text_area.tag_config("CONNECT", foreground="orange")

        self.clients_connected = 0
        self.data_viewer = None

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), foreground="darkblue")
        style.configure("Status.TLabel", font=("Helvetica", 10), foreground="gray")
        style.configure("Connection.TLabel", font=("Helvetica", 10), foreground="#007acc")

    def log(self, message, tag="INFO"):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n", tag)
        self.text_area.yview(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def update_status(self, message):
        self.status_var.set(f"Status: {message}")
        self.connection_var.set(f"Connections: {self.clients_connected}")
    
    def open_data_viewer(self):
        if self.data_viewer is None or not self.data_viewer.is_alive():
            self.data_viewer = WeatherDataDisplay(self.root)
        else:
            self.data_viewer.window.focus_set()
            self.data_viewer.window.lift()

# GUI Class for Weather Data Display
class WeatherDataDisplay:
    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.title("📊 Live Weather Data Viewer")
        self.window.geometry("600x650")
        self.window.configure(bg="#f0f5fa")
        self.window.resizable(True, True)
        
        # Setup styles
        self.setup_styles()
        
        # Main container
        main_frame = ttk.Frame(self.window, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header section with gradient effect
        header_frame = ttk.Frame(main_frame, style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ttk.Label(header_frame, text="Live Weather Monitoring", 
                                    style="Title.TLabel")
        self.title_label.pack(pady=10)
        
        self.subtitle_label = ttk.Label(header_frame, text="Real-time weather data from connected stations", 
                                       style="Subtitle.TLabel")
        self.subtitle_label.pack(pady=(0, 10))
        
        # Station selection dropdown
        self.station_selection_frame = ttk.Frame(main_frame)
        self.station_selection_frame.pack(fill=tk.X, pady=5)
        
        self.station_label = ttk.Label(self.station_selection_frame, text="Select Station:", 
                                      style="StationSelector.TLabel")
        self.station_label.pack(side=tk.LEFT, padx=10)
        
        self.station_var = tk.StringVar()
        self.station_dropdown = ttk.Combobox(self.station_selection_frame, 
                                           textvariable=self.station_var, 
                                           state="readonly")
        self.station_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.station_dropdown.bind("<<ComboboxSelected>>", self.on_station_selected)
        
        # Refresh button
        self.refresh_button = ttk.Button(self.station_selection_frame, text="Refresh", 
                                        command=self.refresh_station_list)
        self.refresh_button.pack(side=tk.RIGHT, padx=10)
        
        # Time display
        self.time_frame = ttk.Frame(main_frame)
        self.time_frame.pack(fill=tk.X, pady=5)
        
        self.time_var = tk.StringVar()
        self.update_time()
        self.time_label = ttk.Label(self.time_frame, textvariable=self.time_var, 
                                   style="Time.TLabel")
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
        # Station info frame
        self.station_frame = ttk.Frame(main_frame, style="Station.TFrame")
        self.station_frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.station_label = ttk.Label(self.station_frame, text="Weather Station", 
                                      style="StationTitle.TLabel")
        self.station_label.pack(anchor="w", padx=10, pady=5)
        
        self.location_var = tk.StringVar(value="Location: Unknown")
        self.location_label = ttk.Label(self.station_frame, textvariable=self.location_var, 
                                       style="StationDetail.TLabel")
        self.location_label.pack(anchor="w", padx=20, pady=2)
        
        self.id_var = tk.StringVar(value="Station ID: Unknown")
        self.id_label = ttk.Label(self.station_frame, textvariable=self.id_var, 
                                 style="StationDetail.TLabel")
        self.id_label.pack(anchor="w", padx=20, pady=2)
        
        # Current weather condition frame
        self.weather_frame = ttk.Frame(main_frame, style="Weather.TFrame")
        self.weather_frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.weather_condition_var = tk.StringVar(value="Weather: Unknown")
        self.weather_condition_label = ttk.Label(self.weather_frame, textvariable=self.weather_condition_var,
                                               style="WeatherCondition.TLabel")
        self.weather_condition_label.pack(anchor="center", pady=5)
        
        # Summary section
        self.summary_frame = ttk.Frame(main_frame, style="Summary.TFrame")
        self.summary_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Display current temperature prominently
        self.temp_frame = ttk.Frame(self.summary_frame)
        self.temp_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.temp_var = tk.StringVar(value="--°C")
        self.temp_label = ttk.Label(self.temp_frame, textvariable=self.temp_var, 
                                   style="Temperature.TLabel")
        self.temp_label.pack()
        
        self.temp_desc_label = ttk.Label(self.temp_frame, text="Temperature", 
                                        style="ValueDescription.TLabel")
        self.temp_desc_label.pack()
        
        # Display wind speed
        self.wind_frame = ttk.Frame(self.summary_frame)
        self.wind_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.wind_var = tk.StringVar(value="-- m/s")
        self.wind_label = ttk.Label(self.wind_frame, textvariable=self.wind_var, 
                                   style="SummaryValue.TLabel")
        self.wind_label.pack()
        
        self.wind_desc_label = ttk.Label(self.wind_frame, text="Wind Speed", 
                                        style="ValueDescription.TLabel")
        self.wind_desc_label.pack()
        
        # Display wind direction
        self.wind_dir_frame = ttk.Frame(self.summary_frame)
        self.wind_dir_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.wind_dir_var = tk.StringVar(value="--°")
        self.wind_dir_label = ttk.Label(self.wind_dir_frame, textvariable=self.wind_dir_var, 
                                      style="SummaryValue.TLabel")
        self.wind_dir_label.pack()
        
        self.wind_dir_desc_label = ttk.Label(self.wind_dir_frame, text="Wind Direction", 
                                           style="ValueDescription.TLabel")
        self.wind_dir_desc_label.pack()
        
        # Detailed data section with notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
        
        # All data tab
        self.all_data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.all_data_frame, text="All Data")
        
        # Create scrollable frame for all data
        self.data_canvas = tk.Canvas(self.all_data_frame, background="#ffffff")
        self.scrollbar = ttk.Scrollbar(self.all_data_frame, orient="vertical", command=self.data_canvas.yview)
        self.data_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.data_canvas.pack(side="left", fill="both", expand=True)
        
        self.data_frame = ttk.Frame(self.data_canvas)
        self.data_canvas.create_window((0, 0), window=self.data_frame, anchor="nw")
        
        self.data_frame.bind("<Configure>", 
                             lambda e: self.data_canvas.configure(scrollregion=self.data_canvas.bbox("all")))
        
        # Status frame
        self.status_frame = ttk.Frame(main_frame, style="Status.TFrame")
        self.status_frame.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Waiting for data...")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, 
                                     style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Start clock update
        self.clock_tick()
        
        # Placeholder for storing the last received data timestamp
        self.last_update_time = None
        
        # Refresh the station list initially
        self.refresh_station_list()

    def setup_styles(self):
        style = ttk.Style()
        
        # Frame styles
        style.configure("Main.TFrame", background="#f0f5fa")
        style.configure("Header.TFrame", background="#e0ebf5")
        style.configure("Station.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Weather.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Summary.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Status.TFrame", background="#f0f5fa")
        
        # Label styles
        style.configure("Title.TLabel", font=("Helvetica", 18, "bold"), foreground="#2c3e50", background="#e0ebf5")
        style.configure("Subtitle.TLabel", font=("Helvetica", 12), foreground="#7f8c8d", background="#e0ebf5")
        style.configure("Time.TLabel", font=("Helvetica", 10), foreground="#7f8c8d", background="#f0f5fa")
        style.configure("StationTitle.TLabel", font=("Helvetica", 14, "bold"), foreground="#2980b9", background="#ffffff")
        style.configure("StationDetail.TLabel", font=("Helvetica", 12), foreground="#34495e", background="#ffffff")
        style.configure("WeatherCondition.TLabel", font=("Helvetica", 16, "bold"), foreground="#16a085", background="#ffffff")
        style.configure("Temperature.TLabel", font=("Helvetica", 24, "bold"), foreground="#e74c3c", background="#ffffff")
        style.configure("SummaryValue.TLabel", font=("Helvetica", 18, "bold"), foreground="#3498db", background="#ffffff")
        style.configure("ValueDescription.TLabel", font=("Helvetica", 10), foreground="#7f8c8d", background="#ffffff")
        style.configure("Status.TLabel", font=("Helvetica", 9), foreground="#95a5a6", background="#f0f5fa")
        style.configure("DataKey.TLabel", font=("Helvetica", 11, "bold"), foreground="#2c3e50", background="#ffffff")
        style.configure("DataValue.TLabel", font=("Helvetica", 11), foreground="#34495e", background="#ffffff")
        style.configure("StationSelector.TLabel", font=("Helvetica", 12), foreground="#34495e", background="#f0f5fa")

    def update_time(self):
        current_time = datetime.now().strftime("%B %d, %Y %H:%M:%S")
        self.time_var.set(f"Current Time: {current_time}")
    
    def clock_tick(self):
        self.update_time()
        self.window.after(1000, self.clock_tick)
    
    def refresh_station_list(self):
        """Update the station dropdown with available stations"""
        current_selection = self.station_var.get()
        
        station_names = []
        for station_id, data in stations_data.items():
            station_name = data.get("station_name", "Unknown Station")
            station_names.append(f"{station_name} ({station_id})")
        
        if not station_names:
            station_names = ["No stations available"]
        
        self.station_dropdown['values'] = station_names
        
        # Try to keep the same selection if possible
        if current_selection in station_names:
            self.station_var.set(current_selection)
        else:
            self.station_var.set(station_names[0])
            # If we have a valid station, update the display
            if station_names[0] != "No stations available":
                self.on_station_selected(None)
    
    def on_station_selected(self, event):
        """Handle station selection from dropdown"""
        selection = self.station_var.get()
        if selection == "No stations available":
            return
        
        # Extract station ID from selection (format: "Station Name (ID)")
        station_id = selection.split("(")[-1].rstrip(")")
        
        if station_id in stations_data:
            self.update_data(stations_data[station_id])
    
    def update_data(self, data_dict):
        # Update the last update time
        self.last_update_time = datetime.now()
        self.status_var.set(f"Last updated: {self.last_update_time.strftime('%H:%M:%S')}")
        
        # Update station info if available
        if "station_name" in data_dict:
            self.station_label.config(text=data_dict["station_name"])
        if "location" in data_dict:
            if isinstance(data_dict["location"], list) and len(data_dict["location"]) >= 2:
                # We have coordinates, get location name
                lat, lon = data_dict["location"][0], data_dict["location"][1]
                location_name = data_dict.get("location_name", get_location_name(lat, lon))
                self.location_var.set(f"Location: {location_name} ({lat}, {lon})")
            else:
                self.location_var.set(f"Location: {data_dict['location']}")
        if "station_id" in data_dict:
            self.id_var.set(f"Station ID: {data_dict['station_id']}")
        
        # Update weather condition (translate code to description)
        if "weather_code" in data_dict:
            weather_code = data_dict["weather_code"]
            try:
                if isinstance(weather_code, (int, str)) and int(weather_code) in WEATHER_CODES:
                    weather_desc = WEATHER_CODES[int(weather_code)]
                    self.weather_condition_var.set(f"Weather Condition: {weather_desc} (Code: {weather_code})")
                else:
                    self.weather_condition_var.set(f"Weather Condition: Unknown (Code: {weather_code})")
            except (ValueError, TypeError):
                self.weather_condition_var.set(f"Weather Condition: {weather_code}")
        
        # Update summary values
        if "temperature" in data_dict:
            self.temp_var.set(f"{data_dict['temperature']}" if not isinstance(data_dict['temperature'], (int, float)) 
                             else f"{data_dict['temperature']:.1f}°C")
        
        # Update wind speed (from 'windspeed' or 'wind_speed')
        wind_key = "windspeed" if "windspeed" in data_dict else "wind_speed"
        if wind_key in data_dict:
            self.wind_var.set(f"{data_dict[wind_key]}" if not isinstance(data_dict[wind_key], (int, float)) 
                             else f"{data_dict[wind_key]:.1f} m/s")
        
        # Update wind direction
        if "wind_direction" in data_dict:
            self.wind_dir_var.set(f"{data_dict['wind_direction']}" if not isinstance(data_dict['wind_direction'], (int, float)) 
                                else f"{data_dict['wind_direction']}°")
        
        # Clear old data in the detailed section
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        
        # Re-create labels for all data
        row = 0
        for key, value in data_dict.items():
            # Skip the ones we've already handled in the summary
            if key in ["temperature", "humidity", "pressure", "station_name", "location", "station_id"]:
                continue
                
            # Create a frame for each data pair
            pair_frame = ttk.Frame(self.data_frame, style="Main.TFrame")
            pair_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            
            # Make the frame span the full width
            self.data_frame.columnconfigure(0, weight=1)
            
            # Key label
            formatted_key = key.replace("_", " ").title()
            label_key = ttk.Label(pair_frame, text=f"{formatted_key}:", style="DataKey.TLabel")
            label_key.pack(side=tk.LEFT, padx=10)
            
            # Value processing for special cases
            display_value = value
            if key == "weather_code" and isinstance(value, (int, str)):
                try:
                    code_int = int(value)
                    if code_int in WEATHER_CODES:
                        display_value = f"{value} ({WEATHER_CODES[code_int]})"
                except (ValueError, TypeError):
                    pass
            elif key == "time":
                # Format time if it's an ISO timestamp
                try:
                    if isinstance(value, str) and 'T' in value:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        display_value = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass
                    
            # Value label
            label_value = ttk.Label(pair_frame, text=str(display_value), style="DataValue.TLabel", wraplength=400)
            label_value.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
            
            row += 1
    
    def is_alive(self):
        """Check if window is still open"""
        try:
            return self.window.winfo_exists()
        except:
            return False

# Server Thread
def start_server(gui):
    # Create a basic TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Wrap the socket with SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        gui.log(f"Listening securely on {HOST}:{PORT}", "INFO")
        gui.update_status(f"Listening securely on {HOST}:{PORT}")
    except Exception as e:
        gui.log(f"Failed to bind server socket: {str(e)}", "ERROR")
        return

    while True:
        try:
            client_socket, client_addr = server_socket.accept()

            # Wrap client connection with SSL
            try:
                ssl_client_socket = context.wrap_socket(client_socket, server_side=True)
                gui.clients_connected += 1
                gui.log(f"Secure client connected: {client_addr}", "CONNECT")
                gui.update_status(f"{gui.clients_connected} client(s) connected")

                client_thread = threading.Thread(target=handle_client, args=(ssl_client_socket, gui, client_addr))
                client_thread.daemon = True
                client_thread.start()
            except ssl.SSLError as ssl_err:
                gui.log(f"SSL error with client {client_addr}: {str(ssl_err)}", "ERROR")
                client_socket.close()
        except Exception as e:
            gui.log(f"Error accepting client: {str(e)}", "ERROR")

# Client Handler
def handle_client(client_socket, gui, client_addr):
    try:
        data = client_socket.recv(4096).decode()
        if data:
            gui.log(f"Weather Data Received from {client_addr}:", "DATA")
            gui.log(data, "DATA")
            try:
                data_dict = json.loads(data)
                
                # Check if we have location coordinates and get location name if needed
                if "location" in data_dict and isinstance(data_dict["location"], list) and len(data_dict["location"]) >= 2:
                    lat, lon = data_dict["location"][0], data_dict["location"][1]
                    if "location_name" not in data_dict:
                        data_dict["location_name"] = get_location_name(lat, lon)
                        gui.log(f"Resolved location: {data_dict['location_name']}", "INFO")
                
                # Store data by station ID
                if "station_id" in data_dict:
                    station_id = data_dict["station_id"]
                    stations_data[station_id] = data_dict
                    gui.log(f"Updated data for station {station_id}", "INFO")
                else:
                    gui.log("Received data without station ID", "ERROR")
                
                # Update display if it's open
                if gui.data_viewer and gui.data_viewer.is_alive():
                    # Refresh the station list
                    gui.data_viewer.refresh_station_list()
                
                # Send acknowledgment back to client
                client_socket.sendall("Data received successfully!".encode())
                gui.log(f"Sent acknowledgment to {client_addr}", "INFO")
                
            except json.JSONDecodeError:
                gui.log("Invalid JSON format from client", "ERROR")
    except Exception as e:
        gui.log(f"Client error: {str(e)}", "ERROR")
    finally:
        client_socket.close()
        gui.clients_connected = max(0, gui.clients_connected - 1)
        gui.update_status(f"{gui.clients_connected} client(s) connected")

# Entry Point
if __name__ == "__main__":
    root = tk.Tk()
    gui = WeatherServerGUI(root)
    server_thread = threading.Thread(target=start_server, args=(gui,))
    server_thread.daemon = True
    server_thread.start()
    root.mainloop()