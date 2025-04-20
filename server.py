import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import time
import json
import ssl
from datetime import datetime

# Server Configuration
HOST = '0.0.0.0'
PORT = 9000

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
        
        # Server controls could go here in future versions
        
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
        
        # Display humidity
        self.humidity_frame = ttk.Frame(self.summary_frame)
        self.humidity_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.humidity_var = tk.StringVar(value="--%")
        self.humidity_label = ttk.Label(self.humidity_frame, textvariable=self.humidity_var, 
                                       style="SummaryValue.TLabel")
        self.humidity_label.pack()
        
        self.humidity_desc_label = ttk.Label(self.humidity_frame, text="Humidity", 
                                            style="ValueDescription.TLabel")
        self.humidity_desc_label.pack()
        
        # Display pressure
        self.pressure_frame = ttk.Frame(self.summary_frame)
        self.pressure_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.pressure_var = tk.StringVar(value="-- hPa")
        self.pressure_label = ttk.Label(self.pressure_frame, textvariable=self.pressure_var, 
                                       style="SummaryValue.TLabel")
        self.pressure_label.pack()
        
        self.pressure_desc_label = ttk.Label(self.pressure_frame, text="Pressure", 
                                            style="ValueDescription.TLabel")
        self.pressure_desc_label.pack()
        
        # Display wind
        self.wind_frame = ttk.Frame(self.summary_frame)
        self.wind_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.wind_var = tk.StringVar(value="-- m/s")
        self.wind_label = ttk.Label(self.wind_frame, textvariable=self.wind_var, 
                                   style="SummaryValue.TLabel")
        self.wind_label.pack()
        
        self.wind_desc_label = ttk.Label(self.wind_frame, text="Wind Speed", 
                                        style="ValueDescription.TLabel")
        self.wind_desc_label.pack()
        
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

    def setup_styles(self):
        style = ttk.Style()
        
        # Frame styles
        style.configure("Main.TFrame", background="#f0f5fa")
        style.configure("Header.TFrame", background="#e0ebf5")
        style.configure("Station.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Summary.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Status.TFrame", background="#f0f5fa")
        
        # Label styles
        style.configure("Title.TLabel", font=("Helvetica", 18, "bold"), foreground="#2c3e50", background="#e0ebf5")
        style.configure("Subtitle.TLabel", font=("Helvetica", 12), foreground="#7f8c8d", background="#e0ebf5")
        style.configure("Time.TLabel", font=("Helvetica", 10), foreground="#7f8c8d", background="#f0f5fa")
        style.configure("StationTitle.TLabel", font=("Helvetica", 14, "bold"), foreground="#2980b9", background="#ffffff")
        style.configure("StationDetail.TLabel", font=("Helvetica", 12), foreground="#34495e", background="#ffffff")
        style.configure("Temperature.TLabel", font=("Helvetica", 24, "bold"), foreground="#e74c3c", background="#ffffff")
        style.configure("SummaryValue.TLabel", font=("Helvetica", 18, "bold"), foreground="#3498db", background="#ffffff")
        style.configure("ValueDescription.TLabel", font=("Helvetica", 10), foreground="#7f8c8d", background="#ffffff")
        style.configure("Status.TLabel", font=("Helvetica", 9), foreground="#95a5a6", background="#f0f5fa")
        style.configure("DataKey.TLabel", font=("Helvetica", 11, "bold"), foreground="#2c3e50", background="#ffffff")
        style.configure("DataValue.TLabel", font=("Helvetica", 11), foreground="#34495e", background="#ffffff")

    def update_time(self):
        current_time = datetime.now().strftime("%B %d, %Y %H:%M:%S")
        self.time_var.set(f"Current Time: {current_time}")
    
    def clock_tick(self):
        self.update_time()
        self.window.after(1000, self.clock_tick)
    
    def update_data(self, data_dict):
        # Update the last update time
        self.last_update_time = datetime.now()
        self.status_var.set(f"Last updated: {self.last_update_time.strftime('%H:%M:%S')}")
        
        # Update station info if available
        if "station_name" in data_dict:
            self.station_label.config(text=data_dict["station_name"])
        if "location" in data_dict:
            self.location_var.set(f"Location: {data_dict['location']}")
        if "station_id" in data_dict:
            self.id_var.set(f"Station ID: {data_dict['station_id']}")
        
        # Update summary values
        if "temperature" in data_dict:
            temp_value = data_dict["temperature"]
            if isinstance(temp_value, (int, float)):
                self.temp_var.set(f"{temp_value:.1f}°C")
            else:
                self.temp_var.set(f"{temp_value}")
        
        if "humidity" in data_dict:
            humidity_value = data_dict["humidity"]
            if isinstance(humidity_value, (int, float)):
                self.humidity_var.set(f"{humidity_value:.1f}%")
            else:
                self.humidity_var.set(f"{humidity_value}")
        
        if "pressure" in data_dict:
            pressure_value = data_dict["pressure"]
            if isinstance(pressure_value, (int, float)):
                self.pressure_var.set(f"{pressure_value:.1f} hPa")
            else:
                self.pressure_var.set(f"{pressure_value}")
        
        if "wind_speed" in data_dict:
            wind_value = data_dict["wind_speed"]
            if isinstance(wind_value, (int, float)):
                self.wind_var.set(f"{wind_value:.1f} m/s")
            else:
                self.wind_var.set(f"{wind_value}")
        
        # Clear old data in the detailed section
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        
        # Re-create labels for all data
        row = 0
        for key, value in data_dict.items():
            # Skip the ones we've already handled in the summary
            if key in ["temperature", "humidity", "pressure", "wind_speed", "station_name", "location", "station_id"]:
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
            
            # Value label
            label_value = ttk.Label(pair_frame, text=str(value), style="DataValue.TLabel", wraplength=400)
            label_value.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
            
            row += 1

# Server Thread
def start_server(gui, display_panel):
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

                client_thread = threading.Thread(target=handle_client, args=(ssl_client_socket, gui, display_panel))
                client_thread.daemon = True
                client_thread.start()
            except ssl.SSLError as ssl_err:
                gui.log(f"SSL error with client {client_addr}: {str(ssl_err)}", "ERROR")
                client_socket.close()
        except Exception as e:
            gui.log(f"Error accepting client: {str(e)}", "ERROR")

# Client Handler
def handle_client(client_socket, gui, display_panel):
    try:
        data = client_socket.recv(4096).decode()
        if data:
            gui.log("Weather Data Received:", "DATA")
            gui.log(data, "DATA")
            try:
                data_dict = json.loads(data)
                display_panel.update_data(data_dict)
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
    display_panel = WeatherDataDisplay(root)
    server_thread = threading.Thread(target=start_server, args=(gui, display_panel))
    server_thread.daemon = True
    server_thread.start()
    root.mainloop()