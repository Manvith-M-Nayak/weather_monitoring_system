import tkinter as tk
from tkinter import messagebox, ttk
import requests
import threading
import time
from datetime import datetime
import os
import json
from PIL import Image, ImageTk, ImageDraw
import sv_ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg")

def get_location():
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return data["lat"], data["lon"], data["city"]
            else:
                return fallback_location()
        else:
            return fallback_location()
    except Exception as e:
        print(f"Location error: {e}")
        return fallback_location()

def fallback_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "loc" in data:
                lat, lon = data["loc"].split(",")
                city = data.get("city", "Unknown")
                return float(lat), float(lon), city
        return 40.7128, -74.0060, "New York"
    except Exception as e:
        print(f"Fallback location error: {e}")
        return 40.7128, -74.0060, "New York"

def get_weather_condition(code):
    weather_conditions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle",
        53: "Moderate drizzle", 55: "Heavy drizzle", 61: "Light rain",
        63: "Moderate rain", 65: "Heavy rain", 71: "Light snow",
        73: "Moderate snow", 75: "Heavy snow", 80: "Light showers",
        81: "Moderate showers", 82: "Heavy showers", 95: "Thunderstorms",
        96: "Thunderstorms with slight hail", 99: "Thunderstorms with heavy hail"
    }
    return weather_conditions.get(code, "Unknown")

def get_weather_icon(code, is_day):
    if code == 0:
        return "sun.png" if is_day else "moon.png"
    elif code in [1, 2]:
        return "partly_cloudy.png" if is_day else "night_cloudy.png"
    elif code == 3:
        return "cloudy.png"
    elif code in [45, 48]:
        return "fog.png"
    elif code in [51, 53, 55]:
        return "drizzle.png"
    elif code in [61, 63, 65]:
        return "rain.png"
    elif code in [71, 73, 75]:
        return "snow.png"
    elif code in [80, 81, 82]:
        return "shower.png"
    elif code in [95, 96, 99]:
        return "thunderstorm.png"
    else:
        return "unknown.png"

def create_default_icons():
    icons_dir = "icons"
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    icon_names = ["sun.png", "moon.png", "partly_cloudy.png", "night_cloudy.png", 
                  "cloudy.png", "fog.png", "drizzle.png", "rain.png", "snow.png", 
                  "shower.png", "thunderstorm.png", "unknown.png"]
    
    colors = {
        "sun.png": "#FFD700", "moon.png": "#E6E6FA", "partly_cloudy.png": "#87CEEB",
        "night_cloudy.png": "#483D8B", "cloudy.png": "#A9A9A9", "fog.png": "#D3D3D3",
        "drizzle.png": "#B0E0E6", "rain.png": "#4682B4", "snow.png": "#FFFAFA",
        "shower.png": "#1E90FF", "thunderstorm.png": "#8A2BE2", "unknown.png": "#C0C0C0"
    }
    
    for icon_name in icon_names:
        icon_path = os.path.join(icons_dir, icon_name)
        if not os.path.exists(icon_path):
            img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((10, 10, 90, 90), fill=colors.get(icon_name, "#808080"))
            
            if "sun" in icon_name:
                for angle in range(0, 360, 45):
                    x1 = 50 + 40 * float(f"{angle:0.1f}".replace(',', '.')) / 180.0
                    y1 = 50 + 40 * float(f"{angle:0.1f}".replace(',', '.')) / 180.0
                    x2 = 50 + 45 * float(f"{angle:0.1f}".replace(',', '.')) / 180.0
                    y2 = 50 + 45 * float(f"{angle:0.1f}".replace(',', '.')) / 180.0
                    draw.line((x1, y1, x2, y2), fill="#FFD700", width=3)
            
            elif "cloud" in icon_name:
                draw.ellipse((20, 40, 60, 80), fill="#FFFFFF")
                draw.ellipse((40, 35, 80, 75), fill="#FFFFFF")
                draw.ellipse((30, 30, 70, 70), fill="#FFFFFF")
            
            elif "rain" in icon_name or "drizzle" in icon_name or "shower" in icon_name:
                for i in range(5):
                    draw.line((30+i*10, 60, 25+i*10, 80), fill="#4682B4", width=2)
            
            elif "snow" in icon_name:
                for i in range(5):
                    draw.rectangle((20+i*15, 60, 25+i*15, 65), fill="#FFFFFF")
            
            elif "thunder" in icon_name:
                draw.polygon([(40, 30), (60, 50), (45, 50), (60, 80), (35, 55), (50, 55)], fill="#FFFF00")
            
            img.save(icon_path)
            print(f"Created placeholder icon: {icon_name}")

def get_weather(latitude, longitude):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
           f"&current_weather=true&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weathercode,visibility,windspeed_10m,winddirection_10m"
           f"&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_hours,weathercode,sunrise,sunset&timezone=auto")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch weather data: {e}")
        return None

def rounded_image(img, radius=30):
    circle = Image.new('L', (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)
    
    w, h = img.size
    
    alpha = Image.new('L', img.size, 255)
    
    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))
    
    img.putalpha(alpha)
    return img

def update_weather():
    global monitoring, temp_data, precip_data, hourly_labels, chart_canvas
    if not monitoring:
        return
        
    status_var.set("Updating weather data...")
    progress["value"] = 30
    
    def fetch_data():
        try:
            if manual_lat is not None and manual_lon is not None and manual_city is not None:
                latitude, longitude, city = manual_lat, manual_lon, manual_city
            else:
                latitude, longitude, city = get_location()
            
            location_var.set(city)
            coord_var.set(f"({latitude:.4f}, {longitude:.4f})")
            
            weather_data = get_weather(latitude, longitude)
            
            if weather_data and "current_weather" in weather_data:
                current = weather_data["current_weather"]
                
                temp_var.set(f"{current['temperature']}°")
                
                weather_condition = get_weather_condition(current['weathercode'])
                condition_var.set(weather_condition)
                
                wind_speed_var.set(f"{current['windspeed']} km/h")
                
                direction = current['winddirection']
                wind_dir_text = get_wind_direction_text(direction)
                wind_direction_var.set(f"{direction}° {wind_dir_text}")
                
                weather_time = datetime.fromisoformat(current['time'].replace('Z', '+00:00'))
                time_var.set(f"Last Updated: {weather_time.strftime('%Y-%m-%d %H:%M')}")
                
                if "hourly" in weather_data:
                    hourly = weather_data["hourly"]
                    current_hour_index = get_current_hour_index(hourly["time"], current['time'])
                    
                    if current_hour_index is not None:
                        humidity = hourly["relative_humidity_2m"][current_hour_index]
                        feels_like = hourly["apparent_temperature"][current_hour_index]
                        visibility = hourly["visibility"][current_hour_index] / 1000
                        
                        humidity_var.set(f"{humidity}%")
                        feels_like_var.set(f"{feels_like}°")
                        visibility_var.set(f"{visibility:.1f} km")
                        
                        update_hourly_forecast(hourly, current_hour_index)
                
                is_day = current.get('is_day', 1) == 1
                icon_name = get_weather_icon(current['weathercode'], is_day)
                
                if not os.path.exists("icons"):
                    os.makedirs("icons")
                    
                try:
                    img = Image.open(f"icons/{icon_name}")
                    img = img.resize((120, 120), Image.LANCZOS)
                    weather_icon_img = ImageTk.PhotoImage(img)
                    weather_icon.config(image=weather_icon_img)
                    weather_icon.image = weather_icon_img
                except Exception as e:
                    print(f"Icon error: {e}")
                    weather_icon.config(image="")
                
                if "daily" in weather_data:
                    update_daily_forecast(weather_data["daily"])
                
                if "hourly" in weather_data and current_hour_index is not None:
                    end_index = min(current_hour_index + 24, len(hourly["time"]))
                    temp_data = hourly["temperature_2m"][current_hour_index:end_index]
                    precip_data = hourly["precipitation"][current_hour_index:end_index]
                    times = [datetime.fromisoformat(t.replace('Z', '+00:00')).strftime('%H:%M') 
                             for t in hourly["time"][current_hour_index:end_index]]
                    update_charts(temp_data, precip_data, times)
                
                if "daily" in weather_data:
                    daily = weather_data["daily"]
                    today_index = 0
                    
                    if today_index < len(daily["sunrise"]):
                        sunrise_time = datetime.fromisoformat(daily["sunrise"][today_index].replace('Z', '+00:00'))
                        sunset_time = datetime.fromisoformat(daily["sunset"][today_index].replace('Z', '+00:00'))
                        
                        sunrise_var.set(f"{sunrise_time.strftime('%H:%M')}")
                        sunset_var.set(f"{sunset_time.strftime('%H:%M')}")
                
                status_var.set("Weather data updated successfully")
                progress["value"] = 100
            else:
                status_var.set("Failed to retrieve weather data")
                progress["value"] = 0
        except Exception as e:
            print(f"Update error: {e}")
            status_var.set(f"Error: {str(e)}")
            progress["value"] = 0
    
    threading.Thread(target=fetch_data, daemon=True).start()
    
    current_time = time.strftime('%H:%M:%S')
    current_date = time.strftime('%A, %d %B %Y')
    time_now_var.set(current_time)
    date_now_var.set(current_date)
    
    if monitoring:
        def reset_progress_gradually():
            current = progress["value"]
            if current > 0:
                progress["value"] = max(0, current - 1)
                root.after(600, reset_progress_gradually)
                
        root.after(5000, reset_progress_gradually)
        root.after(60000, update_weather)

def get_wind_direction_text(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

def get_current_hour_index(time_list, current_time):
    try:
        current_time_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        
        for i, time_str in enumerate(time_list):
            time_dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            if time_dt >= current_time_dt:
                return i
        
        return None
    except Exception as e:
        print(f"Hour index error: {e}")
        return None

def update_hourly_forecast(hourly_data, start_index):
    hours_to_show = 5
    
    for i in range(hours_to_show):
        if start_index + i < len(hourly_data["time"]):
            hour_index = start_index + i
            time_str = hourly_data["time"][hour_index]
            hour_dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            hour_str = hour_dt.strftime("%H:%M")
            
            temp = hourly_data["temperature_2m"][hour_index]
            weather_code = hourly_data["weathercode"][hour_index]
            precip_prob = hourly_data["precipitation_probability"][hour_index]
            
            hourly_labels[i]["time"].config(text=hour_str)
            hourly_labels[i]["temp"].config(text=f"{temp}°")
            hourly_labels[i]["precip"].config(text=f"{precip_prob}%")
            
            is_day = 1 if 6 <= hour_dt.hour <= 18 else 0
            icon_name = get_weather_icon(weather_code, is_day)
            
            try:
                img = Image.open(f"icons/{icon_name}")
                img = img.resize((40, 40), Image.LANCZOS)
                hourly_icon = ImageTk.PhotoImage(img)
                hourly_labels[i]["icon"].config(image=hourly_icon)
                hourly_labels[i]["icon"].image = hourly_icon
            except Exception as e:
                print(f"Hourly icon error: {e}")
                hourly_labels[i]["icon"].config(image="")

def update_daily_forecast(daily_data):
    for i in range(min(7, len(daily_data["time"]))):
        if i < len(daily_data["time"]):
            day_dt = datetime.fromisoformat(daily_data["time"][i])
            day = day_dt.strftime("%a")
            date = day_dt.strftime("%d")
            max_temp = daily_data["temperature_2m_max"][i]
            min_temp = daily_data["temperature_2m_min"][i]
            precip = daily_data["precipitation_sum"][i]
            weather_code = daily_data["weathercode"][i]
            
            forecast_frames[i].day_label.config(text=day)
            forecast_frames[i].date_label.config(text=date)
            forecast_frames[i].temp_label.config(text=f"{min_temp:0.1f}° / {max_temp:0.1f}°")
            forecast_frames[i].precip_label.config(text=f"{precip:0.1f} mm")
            
            icon_name = get_weather_icon(weather_code, True)
            
            try:
                img = Image.open(f"icons/{icon_name}")
                img = img.resize((40, 40), Image.LANCZOS)
                forecast_icon = ImageTk.PhotoImage(img)
                forecast_frames[i].icon_label.config(image=forecast_icon)
                forecast_frames[i].icon_label.image = forecast_icon
            except:
                forecast_frames[i].icon_label.config(image="")

def update_charts(temps, precips, times):
    global chart_canvas, chart_figure
    
    if chart_canvas:
        chart_canvas.get_tk_widget().destroy()
    
    chart_figure = plt.Figure(figsize=(8, 4), dpi=80)
    chart_figure.subplots_adjust(hspace=0.3)
    
    temp_ax = chart_figure.add_subplot(211)
    temp_ax.plot(range(len(temps)), temps, color='#FFA500', marker='o', linestyle='-', linewidth=2)
    temp_ax.set_title('Temperature Forecast (°C)')
    temp_ax.set_xticks(range(0, len(temps), 3))
    temp_ax.set_xticklabels([times[i] for i in range(0, len(times), 3)])
    temp_ax.grid(True, linestyle='--', alpha=0.7)
    
    precip_ax = chart_figure.add_subplot(212)
    precip_ax.bar(range(len(precips)), precips, color='#4682B4', alpha=0.7)
    precip_ax.set_title('Precipitation Forecast (mm)')
    precip_ax.set_xticks(range(0, len(precips), 3))
    precip_ax.set_xticklabels([times[i] for i in range(0, len(temps), 3)])
    precip_ax.grid(True, linestyle='--', alpha=0.7)
    
    chart_canvas = FigureCanvasTkAgg(chart_figure, master=chart_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def toggle_monitoring():
    global monitoring
    monitoring = not monitoring
    
    if monitoring:
        start_button.config(text="Stop Monitoring")
        status_var.set("Starting weather monitoring...")
        progress["value"] = 50
        update_weather()
    else:
        start_button.config(text="Start Monitoring")
        status_var.set("Monitoring stopped")

class ForecastFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.day_label = ttk.Label(self, text="--", font=("Segoe UI", 11, "bold"))
        self.day_label.pack(pady=1)
        
        self.date_label = ttk.Label(self, text="--", font=("Segoe UI", 10))
        self.date_label.pack(pady=1)
        
        self.icon_label = ttk.Label(self)
        self.icon_label.pack(pady=2)
        
        self.temp_label = ttk.Label(self, text="--° / --°", font=("Segoe UI", 10))
        self.temp_label.pack(pady=1)
        
        self.precip_label = ttk.Label(self, text="-- mm", font=("Segoe UI", 9))
        self.precip_label.pack(pady=1)

def toggle_theme():
    current_theme = theme_var.get()
    if current_theme == "dark":
        sv_ttk.use_light_theme()
        theme_var.set("light")
        theme_button.config(text="🌙")
    else:
        sv_ttk.use_dark_theme()
        theme_var.set("dark")
        theme_button.config(text="☀️")

def change_location():
    global manual_lat, manual_lon, manual_city
    
    location_window = tk.Toplevel(root)
    location_window.title("Change Location")
    location_window.geometry("300x200")
    location_window.transient(root)
    location_window.resizable(False, False)
    
    if theme_var.get() == "dark":
        location_window.configure(bg="#2d3436")
    else:
        location_window.configure(bg="#f5f5f5")
    
    ttk.Label(location_window, text="City Name:").pack(pady=(20, 5))
    city_entry = ttk.Entry(location_window, width=30)
    city_entry.pack(pady=5)
    city_entry.insert(0, location_var.get())
    
    ttk.Label(location_window, text="Latitude:").pack(pady=(10, 5))
    lat_entry = ttk.Entry(location_window, width=30)
    lat_entry.pack(pady=5)
    
    coords = coord_var.get().strip("()")
    try:
        lat, lon = coords.split(",")
        lat_entry.insert(0, lat.strip())
        manual_lat = float(lat.strip())
    except:
        lat_entry.insert(0, "40.7128")
        manual_lat = 40.7128
    
    ttk.Label(location_window, text="Longitude:").pack(pady=(10, 5))
    lon_entry = ttk.Entry(location_window, width=30)
    lon_entry.pack(pady=5)
    
    try:
        lon_entry.insert(0, lon.strip())
        manual_lon = float(lon.strip())
    except:
        lon_entry.insert(0, "-74.0060")
        manual_lon = -74.0060
    
    def save_location():
        global manual_lat, manual_lon, manual_city
        
        try:
            manual_lat = float(lat_entry.get())
            manual_lon = float(lon_entry.get())
            manual_city = city_entry.get()
            
            location_var.set(manual_city)
            coord_var.set(f"({manual_lat:.4f}, {manual_lon:.4f})")
            
            if monitoring:
                update_weather()
                
            location_window.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for latitude and longitude.")
    
    ttk.Button(location_window, text="Save", command=save_location).pack(pady=20)
    
    location_window.focus_set()

def update_clock():
    current_time = time.strftime('%H:%M:%S')
    time_now_var.set(current_time)
    root.after(1000, update_clock)

def save_settings():
    settings = {
        "theme": theme_var.get(),
        "manual_lat": manual_lat,
        "manual_lon": manual_lon,
        "manual_city": manual_city
    }
    
    try:
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        status_var.set("Settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    global manual_lat, manual_lon, manual_city
    
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
            
            if "theme" in settings:
                if settings["theme"] == "dark":
                    sv_ttk.use_dark_theme()
                    theme_var.set("dark")
                    theme_button.config(text="☀️")
                else:
                    sv_ttk.use_light_theme()
                    theme_var.set("light")
                    theme_button.config(text="🌙")
            
            if "manual_lat" in settings and settings["manual_lat"] is not None:
                manual_lat = settings["manual_lat"]
            
            if "manual_lon" in settings and settings["manual_lon"] is not None:
                manual_lon = settings["manual_lon"]
            
            if "manual_city" in settings and settings["manual_city"] is not None:
                manual_city = settings["manual_city"]
                location_var.set(manual_city)
                coord_var.set(f"({manual_lat:.4f}, {manual_lon:.4f})")
    except Exception as e:
        print(f"Error loading settings: {e}")

def on_closing():
    save_settings()
    root.destroy()

root = tk.Tk()
root.title("Weather Monitor Pro")
root.geometry("950x750")

monitoring = False
temp_data = []
precip_data = []
forecast_frames = []
hourly_labels = []
chart_canvas = None
chart_figure = None
manual_lat = None
manual_lon = None
manual_city = None

create_default_icons()

from PIL import ImageDraw

sv_ttk.set_theme("dark")
theme_var = tk.StringVar(value="dark")

style = ttk.Style()
style.configure("TFrame", borderwidth=0)
style.configure("Card.TFrame", borderwidth=1, relief="solid")
style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"))
style.configure("Subheading.TLabel", font=("Segoe UI", 18, "bold"))
style.configure("Large.TLabel", font=("Segoe UI", 36, "bold"))
style.configure("Medium.TLabel", font=("Segoe UI", 16))
style.configure("Small.TLabel", font=("Segoe UI", 12))
style.configure("Info.TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=10)

location_var = tk.StringVar(value="Location")
coord_var = tk.StringVar(value="(-, -)")
temp_var = tk.StringVar(value="--°")
condition_var = tk.StringVar(value="--")
wind_speed_var = tk.StringVar(value="-- km/h")
wind_direction_var = tk.StringVar(value="--°")
humidity_var = tk.StringVar(value="--%")
feels_like_var = tk.StringVar(value="--°")
visibility_var = tk.StringVar(value="-- km")
time_var = tk.StringVar(value="Last Updated: --")
time_now_var = tk.StringVar(value="--:--:--")
date_now_var = tk.StringVar(value="----/--/--")
status_var = tk.StringVar(value="Ready")
sunrise_var = tk.StringVar(value="--:--")
sunset_var = tk.StringVar(value="--:--")

main_container = ttk.Frame(root)
main_container.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(main_container)
scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

main_frame = ttk.Frame(scrollable_frame)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

header_frame = ttk.Frame(main_frame)
header_frame.pack(fill=tk.X, pady=(0, 20))

title_label = ttk.Label(header_frame, text="Weather Monitor Pro", style="Header.TLabel")
title_label.pack(side=tk.LEFT)

theme_button = ttk.Button(header_frame, text="🌙", width=3, command=toggle_theme)
theme_button.pack(side=tk.RIGHT, padx=5)

location_button = ttk.Button(header_frame, text="📍", width=3, command=change_location)
location_button.pack(side=tk.RIGHT, padx=5)

time_frame = ttk.Frame(header_frame)
time_frame.pack(side=tk.RIGHT, padx=20)

time_now_label = ttk.Label(time_frame, textvariable=time_now_var, font=("Segoe UI", 20, "bold"))
time_now_label.pack(anchor=tk.E)

date_now_label = ttk.Label(time_frame, textvariable=date_now_var, font=("Segoe UI", 12))
date_now_label.pack(anchor=tk.E)

# Current weather section
current_weather_frame = ttk.Frame(main_frame)
current_weather_frame.pack(fill=tk.X, pady=10)

location_frame = ttk.Frame(current_weather_frame)
location_frame.pack(side=tk.TOP, fill=tk.X)

location_label = ttk.Label(location_frame, textvariable=location_var, style="Subheading.TLabel")
location_label.pack(side=tk.LEFT)

coordinates_label = ttk.Label(location_frame, textvariable=coord_var, style="Info.TLabel")
coordinates_label.pack(side=tk.LEFT, padx=(10, 0))

update_time_label = ttk.Label(location_frame, textvariable=time_var, style="Info.TLabel")
update_time_label.pack(side=tk.RIGHT)

# Weather display
weather_content_frame = ttk.Frame(current_weather_frame)
weather_content_frame.pack(fill=tk.X, pady=10)

# Left side - Weather icon and temperature
weather_left_frame = ttk.Frame(weather_content_frame)
weather_left_frame.pack(side=tk.LEFT, padx=(0, 20))

weather_icon = ttk.Label(weather_left_frame)
weather_icon.pack(side=tk.LEFT, padx=(0, 20))

temp_condition_frame = ttk.Frame(weather_left_frame)
temp_condition_frame.pack(side=tk.LEFT)

temp_label = ttk.Label(temp_condition_frame, textvariable=temp_var, style="Large.TLabel")
temp_label.pack(anchor=tk.W)

condition_label = ttk.Label(temp_condition_frame, textvariable=condition_var, style="Medium.TLabel")
condition_label.pack(anchor=tk.W)

# Right side - Weather details
weather_right_frame = ttk.Frame(weather_content_frame)
weather_right_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Create weather details in grid layout
details_frame = ttk.Frame(weather_right_frame)
details_frame.pack(pady=10)

# Row 1
ttk.Label(details_frame, text="Feels Like:", style="Medium.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
ttk.Label(details_frame, textvariable=feels_like_var, style="Medium.TLabel").grid(row=0, column=1, sticky=tk.E, padx=(20, 0), pady=5)

ttk.Label(details_frame, text="Wind:", style="Medium.TLabel").grid(row=0, column=2, sticky=tk.W, padx=(40, 0), pady=5)
ttk.Label(details_frame, textvariable=wind_speed_var, style="Medium.TLabel").grid(row=0, column=3, sticky=tk.E, padx=(20, 0), pady=5)

# Row 2
ttk.Label(details_frame, text="Humidity:", style="Medium.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
ttk.Label(details_frame, textvariable=humidity_var, style="Medium.TLabel").grid(row=1, column=1, sticky=tk.E, padx=(20, 0), pady=5)

ttk.Label(details_frame, text="Direction:", style="Medium.TLabel").grid(row=1, column=2, sticky=tk.W, padx=(40, 0), pady=5)
ttk.Label(details_frame, textvariable=wind_direction_var, style="Medium.TLabel").grid(row=1, column=3, sticky=tk.E, padx=(20, 0), pady=5)

# Row 3
ttk.Label(details_frame, text="Visibility:", style="Medium.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
ttk.Label(details_frame, textvariable=visibility_var, style="Medium.TLabel").grid(row=2, column=1, sticky=tk.E, padx=(20, 0), pady=5)

ttk.Label(details_frame, text="Sunrise:", style="Medium.TLabel").grid(row=2, column=2, sticky=tk.W, padx=(40, 0), pady=5)
ttk.Label(details_frame, textvariable=sunrise_var, style="Medium.TLabel").grid(row=2, column=3, sticky=tk.E, padx=(20, 0), pady=5)

# Row 4 (optional for more data)
ttk.Label(details_frame, text="", style="Medium.TLabel").grid(row=3, column=0, sticky=tk.W, pady=5)
ttk.Label(details_frame, text="", style="Medium.TLabel").grid(row=3, column=1, sticky=tk.E, padx=(20, 0), pady=5)

ttk.Label(details_frame, text="Sunset:", style="Medium.TLabel").grid(row=3, column=2, sticky=tk.W, padx=(40, 0), pady=5)
ttk.Label(details_frame, textvariable=sunset_var, style="Medium.TLabel").grid(row=3, column=3, sticky=tk.E, padx=(20, 0), pady=5)

# Hourly forecast section
hourly_frame = ttk.Frame(main_frame, style="Card.TFrame")
hourly_frame.pack(fill=tk.X, pady=20, padx=5)

hourly_title = ttk.Label(hourly_frame, text="Hourly Forecast", style="Subheading.TLabel")
hourly_title.pack(anchor=tk.W, padx=15, pady=10)

hourly_forecast_frame = ttk.Frame(hourly_frame)
hourly_forecast_frame.pack(padx=15, pady=(0, 15), fill=tk.X)

# Create hourly forecast blocks
for i in range(5):
    hour_frame = ttk.Frame(hourly_forecast_frame)
    hour_frame.pack(side=tk.LEFT, expand=True)
    
    time_label = ttk.Label(hour_frame, text="--:--", font=("Segoe UI", 12))
    time_label.pack(pady=2)
    
    icon_label = ttk.Label(hour_frame)
    icon_label.pack(pady=2)
    
    temp_label = ttk.Label(hour_frame, text="--°", font=("Segoe UI", 12, "bold"))
    temp_label.pack(pady=2)
    
    precip_label = ttk.Label(hour_frame, text="--%", font=("Segoe UI", 10))
    precip_label.pack(pady=2)
    
    hourly_labels.append({
        "time": time_label,
        "icon": icon_label,
        "temp": temp_label,
        "precip": precip_label
    })

# Daily forecast section
daily_frame = ttk.Frame(main_frame, style="Card.TFrame")
daily_frame.pack(fill=tk.X, pady=20, padx=5)

daily_title = ttk.Label(daily_frame, text="7-Day Forecast", style="Subheading.TLabel")
daily_title.pack(anchor=tk.W, padx=15, pady=10)

daily_forecast_frame = ttk.Frame(daily_frame)
daily_forecast_frame.pack(padx=15, pady=(0, 15), fill=tk.X)

# Create daily forecast blocks
for i in range(7):
    forecast_frame = ForecastFrame(daily_forecast_frame)
    forecast_frame.pack(side=tk.LEFT, expand=True)
    forecast_frames.append(forecast_frame)

# Charts section
chart_section = ttk.Frame(main_frame, style="Card.TFrame")
chart_section.pack(fill=tk.X, pady=20, padx=5)

chart_title = ttk.Label(chart_section, text="Weather Forecasts", style="Subheading.TLabel")
chart_title.pack(anchor=tk.W, padx=15, pady=10)

chart_frame = ttk.Frame(chart_section)
chart_frame.pack(padx=15, pady=(0, 15), fill=tk.BOTH)

# Status bar and controls
status_frame = ttk.Frame(main_frame)
status_frame.pack(fill=tk.X, pady=10)

progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=200, mode="determinate")
progress.pack(side=tk.LEFT, padx=(0, 10))

status_label = ttk.Label(status_frame, textvariable=status_var)
status_label.pack(side=tk.LEFT)

start_button = ttk.Button(status_frame, text="Start Monitoring", command=toggle_monitoring)
start_button.pack(side=tk.RIGHT)

# Initialize the clock
update_clock()

# Load saved settings
load_settings()

# Configure the window closing event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main loop
root.mainloop()