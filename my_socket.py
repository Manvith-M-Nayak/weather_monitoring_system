import socket
import json
import time
import ssl
import re

def extract_domain(url):
    """Extract domain from URL, removing protocol and path"""
    match = re.search(r'(?:https?://)?([^/]+)', url)
    return match.group(1) if match else url

def send_http_request_via_socket(host, data):
    """Send HTTP POST request directly via socket"""
    # Create socket and wrap with SSL
    context = ssl.create_default_context()
    
    print(f"Connecting to {host} on port 443...")
    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            print(f"SSL established. Peer: {ssock.getpeercert()}")
            
            # Prepare JSON data
            json_data = json.dumps(data)
            
            # Create HTTP request
            http_request = (
                f"POST / HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{json_data}"
            )
            
            # Send request
            print("Sending HTTP request via socket...")
            ssock.sendall(http_request.encode())
            
            # Receive response
            print("Receiving response...")
            response = b""
            while True:
                chunk = ssock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            return response.decode('utf-8')

def parse_http_response(response):
    """Parse HTTP response to extract status code and body"""
    # Split headers and body
    parts = response.split('\r\n\r\n', 1)
    if len(parts) < 2:
        return None, None, "Invalid HTTP response format"
    
    headers, body = parts
    
    # Extract status code
    status_line = headers.split('\r\n')[0]
    status_match = re.search(r'HTTP/\d\.\d (\d+)', status_line)
    status_code = int(status_match.group(1)) if status_match else None
    
    # Try to parse body as JSON
    try:
        json_body = json.loads(body)
        return status_code, json_body, None
    except json.JSONDecodeError:
        return status_code, body, None

def main():
    print("=== WEATHER CLIENT (SOCKET THROUGH TUNNEL) ===")
    
    # Create weather data
    weather_data = {
        "location": "(28.61, 77.20)",
        "temperature": 28,
        "windspeed": 10,
        "winddirection": 90,
        "weathercode": 1,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ask for the tunnel URL from the server logs
    print("\nPlease check your server logs for the LocalTunnel URL.")
    print("It should look something like: https://weather-monitoring.loca.lt")
    
    tunnel_url = "https://weather-monitoring.loca.lt"
    if not tunnel_url:
        tunnel_url = "weather-monitoring.loca.lt"  # Default
    
    # Extract domain from URL if needed
    host = extract_domain(tunnel_url)
    
    print(f"\nConnecting to tunnel at {host}")
    print("\nSending weather data:")
    print(json.dumps(weather_data, indent=2))
    
    try:
        # Send HTTP request via socket
        response = send_http_request_via_socket(host, weather_data)
        
        # Parse response
        status_code, body, error = parse_http_response(response)
        
        if error:
            print(f"Error parsing response: {error}")
            print(f"Raw response: {response[:200]}...")
        else:
            print(f"Received HTTP status code: {status_code}")
            
            if status_code == 200:
                if isinstance(body, dict):
                    print(f"Server response: {json.dumps(body, indent=2)}")
                    print("\nData transmission successful!")
                else:
                    print("Server responded but not with valid JSON.")
                    print(f"Response content: {body[:200]}...")
            else:
                print(f"Server responded with error status code: {status_code}")
                print(f"Response content: {body}")
                
    except socket.gaierror:
        print(f"Error: Could not resolve host '{host}'")
    except socket.timeout:
        print("Error: Connection timed out")
    except ConnectionRefusedError:
        print(f"Error: Connection refused by host {host}")
    except ssl.SSLError as e:
        print(f"SSL Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()