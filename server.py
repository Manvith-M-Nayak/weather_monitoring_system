import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import time

# Server Configuration
HOST = '0.0.0.0'
PORT = 9000

# Create GUI window using Tkinter
class WeatherServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌤️ Weather Monitoring Server")
        self.root.geometry("750x500")
        self.root.resizable(True, True)

        # Header
        self.header_label = ttk.Label(root, text="Weather Monitoring Server", font=("Helvetica", 18, "bold"), foreground="darkblue")
        self.header_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Log area with scrolled text
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=25, font=("Consolas", 11))
        self.text_area.grid(row=1, column=0, padx=10, pady=10)
        self.text_area.insert(tk.END, "Server initializing...\n")
        self.text_area.config(state=tk.DISABLED)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Waiting for connections...")
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Helvetica", 10), foreground="gray")
        self.status_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Tag setup for colored messages
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

# Socket server thread
def start_server(gui):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        gui.log(f"Listening on {HOST}:{PORT}", "INFO")
        gui.update_status(f"Listening on {HOST}:{PORT}")
    except Exception as e:
        gui.log(f"Failed to bind server socket: {str(e)}", "ERROR")
        return

    while True:
        try:
            client_socket, client_addr = server_socket.accept()
            gui.clients_connected += 1
            gui.log(f"Client connected: {client_addr}", "CONNECT")
            gui.update_status(f"{gui.clients_connected} client(s) connected")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, gui))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            gui.log(f"Error accepting client: {str(e)}", "ERROR")

# Handle each client
def handle_client(client_socket, gui):
    try:
        data = client_socket.recv(4096).decode()
        if data:
            gui.log("Weather Data Received:", "DATA")
            gui.log(data, "DATA")
    except Exception as e:
        gui.log(f"Client error: {str(e)}", "ERROR")
    finally:
        client_socket.close()
        gui.clients_connected = max(0, gui.clients_connected - 1)
        gui.update_status(f"{gui.clients_connected} client(s) connected")

# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    gui = WeatherServerGUI(root)
    server_thread = threading.Thread(target=start_server, args=(gui,))
    server_thread.daemon = True
    server_thread.start()
    root.mainloop()
