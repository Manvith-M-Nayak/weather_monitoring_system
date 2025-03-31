import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading
import geocoder
import time
from datetime import datetime
import os
from PIL import Image, ImageTk

# Function to get real-time latitude and longitude
def get_location():
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng
    else:
        messagebox.showerror("Error", "Failed to retrieve location.")
        return None, None

# Function to determine weather condition based on weather code
def get_weather_condition(code):
    weather_conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Light showers",
        81: "Moderate showers",
        82: "Heavy showers",
        95: "Thunderstorms",
        96: "Thunderstorms with slight hail",
        99: "Thunderstorms with heavy hail"
    }
    return weather_conditions.get(code, "Unknown")

# Function to get weather icon based on weather code and time
def get_weather_icon(code, is_day):
    # Map weather codes to icon names
    if code == 0:  # Clear sky
        return "sun.png" if is_day else "moon.png"
    elif code in [1, 2]:  # Mainly clear, Partly cloudy
        return "partly_cloudy.png" if is_day else "night_cloudy.png"
    elif code == 3:  # Overcast
        return "cloudy.png"
    elif code in [45, 48]:  # Fog
        return "fog.png"
    elif code in [51, 53, 55]:  # Drizzle
        return "drizzle.png"
    elif code in [61, 63, 65]:  # Rain
        return "rain.png"
    elif code in [71, 73, 75]:  # Snow
        return "snow.png"
    elif code in [80, 81, 82]:  # Showers
        return "shower.png"
    elif code in [95, 96, 99]:  # Thunderstorm
        return "thunderstorm.png"
    else:
        return "unknown.png"

# Function to get weather data from Open-Meteo API
def get_weather(latitude, longitude):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
           f"&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch weather data: {e}")
        return None

# Function to get city name from coordinates
def get_city_name(latitude, longitude):
    try:
        g = geocoder.osm([latitude, longitude], method='reverse')
        if g.ok and g.city:
            return g.city
        else:
            return "Unknown Location"
    except Exception:
        return "Unknown Location"

# Function to update the weather display
def update_weather():
    global monitoring
    if not monitoring:
        return
        
    status_label.config(text="Updating weather data...")
    latitude, longitude = get_location()
    
    if latitude is not None and longitude is not None:
        # Update location info
        city_name = get_city_name(latitude, longitude)
        location_label.config(text=f"{city_name}")
        coord_label.config(text=f"({latitude:.4f}, {longitude:.4f})")
        
        # Get weather data
        weather_data = get_weather(latitude, longitude)
        
        if weather_data and "current_weather" in weather_data:
            current = weather_data["current_weather"]
            
            # Update current weather
            temp_display.config(text=f"{current['temperature']}°C")
            
            weather_condition = get_weather_condition(current['weathercode'])
            condition_label.config(text=f"{weather_condition}")
            
            wind_speed.config(text=f"{current['windspeed']} km/h")
            wind_direction.config(text=f"{current['winddirection']}°")
            
            # Format and display time
            weather_time = datetime.fromisoformat(current['time'].replace('Z', '+00:00'))
            time_label.config(text=f"Last Updated: {weather_time.strftime('%Y-%m-%d %H:%M')}")
            
            # Update icon
            is_day = current.get('is_day', 1) == 1
            icon_name = get_weather_icon(current['weathercode'], is_day)
            
            # Create icons directory if it doesn't exist
            if not os.path.exists("icons"):
                os.makedirs("icons")
                
            # Use a placeholder if icon file doesn't exist
            try:
                img = Image.open(f"icons/{icon_name}")
                img = img.resize((100, 100), Image.LANCZOS)
                weather_icon_img = ImageTk.PhotoImage(img)
                weather_icon.config(image=weather_icon_img)
                weather_icon.image = weather_icon_img
            except:
                # If icon doesn't exist, just show text
                weather_icon.config(image="")
                
            # Update progress bar to show successful update
            progress["value"] = 100
            status_label.config(text="Weather data updated successfully")
            
            # Update daily forecast if available
            if "daily" in weather_data:
                daily = weather_data["daily"]
                for i in range(min(3, len(daily["time"]))):
                    if i < len(daily["time"]):
                        day = datetime.fromisoformat(daily["time"][i]).strftime("%a")
                        max_temp = daily["temperature_2m_max"][i]
                        min_temp = daily["temperature_2m_min"][i]
                        precip = daily["precipitation_sum"][i]
                        
                        forecast_frames[i].day_label.config(text=day)
                        forecast_frames[i].temp_label.config(text=f"{min_temp}°C / {max_temp}°C")
                        forecast_frames[i].precip_label.config(text=f"Precip: {precip} mm")
        else:
            status_label.config(text="Failed to retrieve weather data")
            progress["value"] = 0
    else:
        status_label.config(text="Failed to retrieve location")
        progress["value"] = 0

    # Update current time
    current_time = time.strftime('%H:%M:%S')
    current_date = time.strftime('%Y-%m-%d')
    current_time_label.config(text=current_time)
    current_date_label.config(text=current_date)
    
    # Schedule the next update
    if monitoring:
        progress["value"] = 0
        root.after(60000, update_weather)  # Update every 60 seconds

# Toggle monitoring on/off
def toggle_monitoring():
    global monitoring
    monitoring = not monitoring
    
    if monitoring:
        start_button.config(text="Stop Monitoring", bg="#ff6b6b")
        status_label.config(text="Starting weather monitoring...")
        progress["value"] = 50
        update_weather()
    else:
        start_button.config(text="Start Monitoring", bg="#4ecdc4")
        status_label.config(text="Monitoring stopped")

# Create a forecast day frame
class ForecastFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#2d3436", padx=10, pady=5, relief=tk.RAISED, bd=1)
        self.day_label = tk.Label(self, text="--", font=("Arial", 12, "bold"), bg="#2d3436", fg="white")
        self.day_label.pack(pady=2)
        
        self.temp_label = tk.Label(self, text="--°C / --°C", font=("Arial", 10), bg="#2d3436", fg="white")
        self.temp_label.pack(pady=2)
        
        self.precip_label = tk.Label(self, text="Precip: -- mm", font=("Arial", 9), bg="#2d3436", fg="#dfe6e9")
        self.precip_label.pack(pady=2)

# GUI setup
root = tk.Tk()
root.title("Weather Monitor Pro")
root.geometry("750x600")
root.configure(bg="#2d3436")
root.resizable(False, False)

# Global variables
monitoring = False
forecast_frames = []

# Create main frames
header_frame = tk.Frame(root, bg="#1e272e", pady=15)
header_frame.pack(fill=tk.X)

content_frame = tk.Frame(root, bg="#2d3436", pady=10)
content_frame.pack(fill=tk.BOTH, expand=True)

left_frame = tk.Frame(content_frame, bg="#2d3436", padx=20, pady=10)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(content_frame, bg="#2d3436", padx=20, pady=10)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

footer_frame = tk.Frame(root, bg="#1e272e", pady=10)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

# Header
title_label = tk.Label(header_frame, text="Weather Monitor Pro", font=("Arial", 24, "bold"), bg="#1e272e", fg="white")
title_label.pack()

# Current Time Display in Header
time_frame = tk.Frame(header_frame, bg="#1e272e")
time_frame.pack(pady=5)

current_time_label = tk.Label(time_frame, text="--:--:--", font=("Arial", 18), bg="#1e272e", fg="#dfe6e9")
current_time_label.pack(side=tk.RIGHT, padx=10)

current_date_label = tk.Label(time_frame, text="----/--/--", font=("Arial", 14), bg="#1e272e", fg="#dfe6e9")
current_date_label.pack(side=tk.LEFT, padx=10)

# Left Panel - Current Weather
location_frame = tk.Frame(left_frame, bg="#2d3436")
location_frame.pack(fill=tk.X, pady=10)

location_label = tk.Label(location_frame, text="Location", font=("Arial", 18, "bold"), bg="#2d3436", fg="white")
location_label.pack()

coord_label = tk.Label(location_frame, text="(-, -)", font=("Arial", 10), bg="#2d3436", fg="#dfe6e9")
coord_label.pack()

# Current Weather Display
weather_display = tk.Frame(left_frame, bg="#34495e", padx=15, pady=15, relief=tk.RAISED, bd=1)
weather_display.pack(fill=tk.X, pady=10)

weather_icon = tk.Label(weather_display, bg="#34495e")
weather_icon.pack()

temp_display = tk.Label(weather_display, text="--°C", font=("Arial", 36, "bold"), bg="#34495e", fg="white")
temp_display.pack(pady=5)

condition_label = tk.Label(weather_display, text="--", font=("Arial", 16), bg="#34495e", fg="white")
condition_label.pack(pady=5)

# Wind Information
wind_frame = tk.Frame(weather_display, bg="#34495e")
wind_frame.pack(fill=tk.X, pady=10)

wind_label = tk.Label(wind_frame, text="Wind:", font=("Arial", 12, "bold"), bg="#34495e", fg="white")
wind_label.pack(side=tk.LEFT, padx=5)

wind_speed = tk.Label(wind_frame, text="-- km/h", font=("Arial", 12), bg="#34495e", fg="white")
wind_speed.pack(side=tk.LEFT, padx=5)

wind_direction = tk.Label(wind_frame, text="--°", font=("Arial", 12), bg="#34495e", fg="white")
wind_direction.pack(side=tk.LEFT, padx=5)

time_label = tk.Label(weather_display, text="Last Updated: --", font=("Arial", 10), bg="#34495e", fg="#dfe6e9")
time_label.pack(pady=5)

# Right Panel - Forecast
forecast_label = tk.Label(right_frame, text="Forecast", font=("Arial", 18, "bold"), bg="#2d3436", fg="white")
forecast_label.pack(pady=10)

forecast_container = tk.Frame(right_frame, bg="#2d3436")
forecast_container.pack(fill=tk.X, pady=5)

# Create 3-day forecast frames
for i in range(3):
    frame = ForecastFrame(forecast_container)
    frame.pack(fill=tk.X, pady=5)
    forecast_frames.append(frame)

# Controls
controls_frame = tk.Frame(right_frame, bg="#2d3436", pady=10)
controls_frame.pack(fill=tk.X, pady=10)

start_button = tk.Button(controls_frame, text="Start Monitoring", font=("Arial", 12, "bold"), 
                         bg="#4ecdc4", fg="white", padx=10, pady=5, command=toggle_monitoring)
start_button.pack(fill=tk.X, pady=10)

# Footer with status
status_frame = tk.Frame(footer_frame, bg="#1e272e")
status_frame.pack(fill=tk.X, padx=20)

status_label = tk.Label(status_frame, text="Ready", font=("Arial", 10), bg="#1e272e", fg="#dfe6e9")
status_label.pack(side=tk.LEFT, pady=5)

progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
progress.pack(side=tk.RIGHT, pady=5)

# Run the Tkinter main loop
root.mainloop()