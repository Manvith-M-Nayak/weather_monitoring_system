import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import time
import json
import ssl

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

        # Header
        self.header_label = ttk.Label(root, text="Weather Monitoring Server", font=("Helvetica", 18, "bold"), foreground="darkblue")
        self.header_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Scrolled text area for logs
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=25, font=("Consolas", 11))
        self.text_area.grid(row=1, column=0, padx=10, pady=10)
        self.text_area.insert(tk.END, "Server initializing...\n")
        self.text_area.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Waiting for connections...")
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Helvetica", 10), foreground="gray")
        self.status_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Color tag setup for styling
        self.text_area.tag_config("INFO", foreground="green")
        self.text_area.tag_config("ERROR", foreground="red")
        self.text_area.tag_config("DATA", foreground="blue")
        self.text_area.tag_config("CONNECT", foreground="orange")

        self.clients_connected = 0

    def log(self, message, tag="INFO"):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n", tag)
        self.text_area.yview(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def update_status(self, message):
        self.status_var.set(f"Status: {message}")

# GUI Class for Weather Data Display
class WeatherDataDisplay:
    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.title("📊 Live Weather Data Viewer")
        self.window.geometry("500x500")
        self.window.configure(bg="#f4f4f4")
        self.window.resizable(True, True)

        # Title
        self.title_label = ttk.Label(self.window, text="Latest Weather Data", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        # Frame for displaying key-value data
        self.data_frame = ttk.Frame(self.window)
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollable canvas
        self.canvas = tk.Canvas(self.data_frame, borderwidth=0, background="#ffffff")
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self.data_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self.scroll_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.labels = {}

    def update_data(self, data_dict):
        # Clear old labels
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Re-create labels
        for key, value in data_dict.items():
            label_key = ttk.Label(self.scroll_frame, text=f"{key}:", font=("Helvetica", 12, "bold"), foreground="darkblue")
            label_key.pack(anchor="w", pady=2, padx=5)

            label_value = ttk.Label(self.scroll_frame, text=str(value), font=("Helvetica", 12), wraplength=450)
            label_value.pack(anchor="w", pady=1, padx=20)

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
                