#!/usr/bin/env python3
"""
Fetch the next two bus arrival times for GRT stop 2783.
Uses the GTFS Realtime API provided by Region of Waterloo.
Direction information is obtained from the static GTFS data.
"""

import requests
from datetime import datetime, timezone, time as datetime_time
from google.transit import gtfs_realtime_pb2
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import time
import sys
import os
from zoneinfo import ZoneInfo
from pathlib import Path
import csv
import zipfile
import io
try:
    from astral import Observer
    from astral.sun import sun
    ASTRAL_AVAILABLE = True
except ImportError:
    ASTRAL_AVAILABLE = False
    print("Warning: astral library not found. Sunset dimming disabled.")
try:
    from tm1637 import TM1637
    TM1637_AVAILABLE = True
except ImportError:
    TM1637_AVAILABLE = False
    print("Warning: raspberrypi-tm1637 library not found. Display functionality disabled.")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO library not found. Capacitive sensor functionality disabled.")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config():
    """Load configuration from config.txt file.
    Returns a dictionary with all configuration values.
    Raises FileNotFoundError if config.txt doesn't exist.
    """
    config_path = Path(__file__).parent / "config.txt"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    config = {}
    
    with open(config_path, 'r') as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse key = value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Convert string values to appropriate types
                if value.lower() == 'true':
                    config[key] = True
                elif value.lower() == 'false':
                    config[key] = False
                else:
                    # Try to convert to number, otherwise keep as string
                    try:
                        if '.' in value:
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        config[key] = value
    
    return config


# Load configuration from file
try:
    CONFIG = load_config()
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Please create a config.txt file in the src directory.")
    sys.exit(1)

# Extract configuration values
API_URL = CONFIG.get("API_URL", "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1")
STATIC_GTFS_URL = CONFIG.get("STATIC_GTFS_URL", "https://webapps.regionofwaterloo.ca/api/grt-routes/api/staticfeeds/1")
STOP_ID = str(CONFIG.get("STOP_ID", "2783"))
LOCAL_TZ = ZoneInfo(CONFIG.get("LOCAL_TZ", "America/Toronto"))

# TM1637 Display Configuration
DISPLAY1_ROUTE = str(CONFIG.get("DISPLAY1_ROUTE", "12"))
DISPLAY1_HEADSIGN = CONFIG.get("DISPLAY1_HEADSIGN", "")
DISPLAY1_CLK = int(CONFIG.get("DISPLAY1_CLK", 27))
DISPLAY1_DIO = int(CONFIG.get("DISPLAY1_DIO", 17))

DISPLAY2_ROUTE = str(CONFIG.get("DISPLAY2_ROUTE", "19"))
DISPLAY2_HEADSIGN = CONFIG.get("DISPLAY2_HEADSIGN", "")
DISPLAY2_CLK = int(CONFIG.get("DISPLAY2_CLK", 24))
DISPLAY2_DIO = int(CONFIG.get("DISPLAY2_DIO", 23))

# Capacitive Sensor Configuration
SENSOR_PIN = int(CONFIG.get("SENSOR_PIN", 4))

# Sunset Dimming Configuration
ENABLE_SUNSET_DIMMING = CONFIG.get("ENABLE_SUNSET_DIMMING", True)
DAY_BRIGHTNESS = int(CONFIG.get("DAY_BRIGHTNESS", 7))
NIGHT_BRIGHTNESS = int(CONFIG.get("NIGHT_BRIGHTNESS", 2))

# Location for sunset calculation
LOCATION_LATITUDE = float(CONFIG.get("LOCATION_LATITUDE", 43.4516))
LOCATION_LONGITUDE = float(CONFIG.get("LOCATION_LONGITUDE", -80.4925))

# Refresh interval in seconds
REFRESH_INTERVAL = int(CONFIG.get("REFRESH_INTERVAL", 180))

# Store headsigns for filtering (empty string means accept all headsigns)
_display1_headsign = DISPLAY1_HEADSIGN.strip() if DISPLAY1_HEADSIGN else ""
_display2_headsign = DISPLAY2_HEADSIGN.strip() if DISPLAY2_HEADSIGN else ""

# Map routes to their desired headsigns (empty string means accept all headsigns)
ROUTE_HEADSIGNS = {
    DISPLAY1_ROUTE: _display1_headsign,
    DISPLAY2_ROUTE: _display2_headsign,
}

# Routes set for filtering (created once to avoid recreation on every fetch)
DESIRED_ROUTES = {DISPLAY1_ROUTE, DISPLAY2_ROUTE}

# Observer for sun calculations (cached to avoid recreation)
_OBSERVER = None
if ASTRAL_AVAILABLE and ENABLE_SUNSET_DIMMING:
    _OBSERVER = Observer(latitude=LOCATION_LATITUDE, longitude=LOCATION_LONGITUDE, elevation=0)

# HTTP session for API calls (reused across fetches)
_API_SESSION = None

# Log loaded configuration on startup
print("[INFO] Configuration loaded from config.txt:")
print(f"[INFO]   Stop ID: {STOP_ID}")
print(f"[INFO]   Route 1: {DISPLAY1_ROUTE}", end="")
if _display1_headsign:
    print(f" (headsign: {_display1_headsign})", end="")
print(f" (GPIO {DISPLAY1_CLK}/{DISPLAY1_DIO})")
print(f"[INFO]   Route 2: {DISPLAY2_ROUTE}", end="")
if _display2_headsign:
    print(f" (headsign: {_display2_headsign})", end="")
print(f" (GPIO {DISPLAY2_CLK}/{DISPLAY2_DIO})")
print(f"[INFO]   Refresh interval: {REFRESH_INTERVAL} seconds")
if ENABLE_SUNSET_DIMMING:
    print(f"[INFO]   Sunset dimming: enabled (day: {DAY_BRIGHTNESS}, night: {NIGHT_BRIGHTNESS})")
else:
    print(f"[INFO]   Sunset dimming: disabled")

def get_sunset_time(date=None):
    """Calculate sunset time for the location.
    Returns datetime object in LOCAL_TZ, or None if calculation fails.
    Uses cached observer instance.
    """
    if not ASTRAL_AVAILABLE or not ENABLE_SUNSET_DIMMING or _OBSERVER is None:
        return None
    
    try:
        if date is None:
            date = datetime.now(LOCAL_TZ).date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        sun_times = sun(_OBSERVER, date=date, tzinfo=LOCAL_TZ)
        return sun_times['sunset']
    except Exception as e:
        print(f"[ERROR] Failed to calculate sunset time: {e}")
        return None


def get_sunrise_time(date=None):
    """Calculate sunrise time for the location.
    Returns datetime object in LOCAL_TZ, or None if calculation fails.
    Uses cached observer instance.
    """
    if not ASTRAL_AVAILABLE or not ENABLE_SUNSET_DIMMING or _OBSERVER is None:
        return None
    
    try:
        if date is None:
            date = datetime.now(LOCAL_TZ).date()
        else:
            date = date.date() if isinstance(date, datetime) else date
        
        sun_times = sun(_OBSERVER, date=date, tzinfo=LOCAL_TZ)
        return sun_times['sunrise']
    except Exception as e:
        print(f"[ERROR] Failed to calculate sunrise time: {e}")
        return None


def load_static_gtfs_data():
    """
    Load and cache static GTFS data to build a mapping of trip_id to headsign.
    This is used to filter realtime arrivals by destination/direction.
    Returns a dictionary mapping trip_id to headsign.
    """
    trip_to_headsign = {}
    
    try:
        print("[INFO] Loading static GTFS data for headsign mapping...")
        session = requests.Session()
        session.mount("https://", DH_KeyAdapter())
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Download the static GTFS zip file
        response = session.get(STATIC_GTFS_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extract and parse the trips.txt file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Read trips.txt to get trip_id -> headsign mapping
            with zip_file.open('trips.txt') as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                for row in reader:
                    trip_id = row.get('trip_id')
                    headsign = row.get('trip_headsign', '')
                    if trip_id:
                        trip_to_headsign[trip_id] = headsign
        
        print(f"[INFO] Loaded {len(trip_to_headsign)} trip-headsign mappings from static GTFS data.")
        return trip_to_headsign
    
    except Exception as e:
        print(f"[ERROR] Failed to load static GTFS data: {e}")
        print("[WARNING] Headsign filtering will be disabled.")
        return {}


# Global cache for trip-to-headsign mapping
_TRIP_TO_HEADSIGN = None

def get_trip_headsign(trip_id):
    """
    Get the headsign for a given trip_id using cached static GTFS data.
    Returns the headsign (as string) or empty string if not found.
    Loads the data on first call.
    """
    global _TRIP_TO_HEADSIGN
    
    if _TRIP_TO_HEADSIGN is None:
        _TRIP_TO_HEADSIGN = load_static_gtfs_data()
    
    return _TRIP_TO_HEADSIGN.get(trip_id, "")


class DH_KeyAdapter(HTTPAdapter):
    """Custom adapter to allow weak DH keys for older servers"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def get_api_session():
    """Get or create the API session (reused across calls)."""
    global _API_SESSION
    if _API_SESSION is None:
        _API_SESSION = requests.Session()
        _API_SESSION.mount("https://", DH_KeyAdapter())
    return _API_SESSION


class CapacitiveSensorManager:
    """Manages TTP223 capacitive sensor for refresh trigger"""
    def __init__(self, callback=None, debug=False):
        self.available = GPIO_AVAILABLE
        self.callback = callback
        self.debug = debug
        self.last_state = 0
        self.state_change_count = 0
        
        if self.available:
            try:
                # Try to set GPIO mode, but don't fail if already set
                try:
                    GPIO.setmode(GPIO.BCM)
                except RuntimeError:
                    # GPIO mode already set, this is fine
                    pass
                
                GPIO.setup(SENSOR_PIN, GPIO.IN)
                
                # Try to remove any existing event detection on this pin first
                try:
                    GPIO.remove_event_detect(SENSOR_PIN)
                except RuntimeError:
                    pass  # No existing event, that's fine
                
                # Read initial state
                self.last_state = GPIO.input(SENSOR_PIN)
                
                # Use polling instead of event detection to avoid conflicts
                print(f"[INFO] Capacitive sensor initialized on pin {SENSOR_PIN} (polling mode).")
                print(f"[INFO] Initial sensor state: {self.last_state}")
            except Exception as e:
                print(f"[ERROR] Failed to initialize capacitive sensor: {e}")
                import traceback
                traceback.print_exc()
                self.available = False
    
    def check_sensor(self):
        """Poll the sensor and trigger callback if pressed (rising edge detected)"""
        if not self.available:
            return
        
        try:
            current_state = GPIO.input(SENSOR_PIN)
            
            # Log state changes in debug mode
            if self.debug and current_state != self.last_state:
                self.state_change_count += 1
                print(f"[DEBUG] Sensor state change #{self.state_change_count}: {self.last_state} -> {current_state}")
            
            # Detect rising edge (0 -> 1) - sensor goes HIGH when touched
            if current_state == 1 and self.last_state == 0:
                print("\n[INFO] Refresh button pressed!")
                if self.callback:
                    self.callback()
            
            # Also detect falling edge (1 -> 0) in case sensor is active-low
            elif current_state == 0 and self.last_state == 1 and self.debug:
                print("[DEBUG] Sensor falling edge detected (active-low test)")
            
            self.last_state = current_state
        except Exception as e:
            print(f"[ERROR] Error reading capacitive sensor: {e}")
            self.available = False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.available:
            try:
                # Don't call GPIO.cleanup() here as it conflicts with TM1637
                # Just let the system clean up when the program exits
                pass
            except Exception as e:
                print(f"[ERROR] Error cleaning up GPIO: {e}")

class TM1637DisplayManager:
    """Manages two TM1637 4-digit 7-segment displays"""
    def __init__(self):
        self.display1 = None
        self.display2 = None
        self.available = TM1637_AVAILABLE
        self.current_brightness = DAY_BRIGHTNESS
        print(f"[INFO] TM1637_AVAILABLE: {TM1637_AVAILABLE}")
        
        if self.available:
            try:
                self.display1 = TM1637(clk=DISPLAY1_CLK, dio=DISPLAY1_DIO)
                self.display2 = TM1637(clk=DISPLAY2_CLK, dio=DISPLAY2_DIO)
                self.display1.brightness(DAY_BRIGHTNESS)  # 0-7 brightness levels
                self.display2.brightness(DAY_BRIGHTNESS)
                print("[INFO] TM1637 displays initialized on pins (CLK/DIO): ({}/{}), ({}/{}).".format(
                    DISPLAY1_CLK, DISPLAY1_DIO, DISPLAY2_CLK, DISPLAY2_DIO))
                if ENABLE_SUNSET_DIMMING and ASTRAL_AVAILABLE:
                    sunset = get_sunset_time()
                    if sunset:
                        print(f"[INFO] Sunset dimming enabled. Sunset time: {sunset.strftime('%H:%M')} (day brightness: {DAY_BRIGHTNESS}, night brightness: {NIGHT_BRIGHTNESS})")
            except Exception as e:
                print(f"[ERROR] Failed to initialize displays: {e}")
                self.available = False
    
    def update_brightness_for_time(self):
        """Update display brightness based on current time relative to sunset.
        Returns True if brightness was changed, False otherwise.
        """
        print(f"[DEBUG] update_brightness_for_time called: available={self.available}, ENABLE_SUNSET_DIMMING={ENABLE_SUNSET_DIMMING}, ASTRAL_AVAILABLE={ASTRAL_AVAILABLE}")
        if not self.available or not ENABLE_SUNSET_DIMMING or not ASTRAL_AVAILABLE:
            print(f"[DEBUG] Skipping brightness update (available={self.available}, dimming_enabled={ENABLE_SUNSET_DIMMING}, astral_available={ASTRAL_AVAILABLE})")
            return False
        
        try:
            now = datetime.now(LOCAL_TZ)
            
            # Get sunrise and sunset for today
            sunrise_today = get_sunrise_time(now)
            sunset_today = get_sunset_time(now)
            
            if sunrise_today is None or sunset_today is None:
                print(f"[DEBUG] Sunrise/sunset calculation returned None")
                return False
            
            # Determine if it's night or day
            is_night = False
            
            if now >= sunset_today:
                # After today's sunset - it's night
                is_night = True
                print(f"[DEBUG] After sunset: {sunset_today.strftime('%H:%M:%S')}")
            elif now < sunrise_today:
                # Before today's sunrise - still night from yesterday
                is_night = True
                print(f"[DEBUG] Before sunrise: {sunrise_today.strftime('%H:%M:%S')}, still night from yesterday")
            else:
                # Between sunrise and sunset - it's day
                print(f"[DEBUG] Between sunrise ({sunrise_today.strftime('%H:%M:%S')}) and sunset ({sunset_today.strftime('%H:%M:%S')})")
            
            # Determine target brightness
            target_brightness = NIGHT_BRIGHTNESS if is_night else DAY_BRIGHTNESS
            
            # Debug output
            print(f"[DEBUG] Brightness check: now={now.strftime('%H:%M:%S')}, is_night={is_night}, target={target_brightness}, current={self.current_brightness}")
            
            # Update brightness if it changed
            if target_brightness != self.current_brightness:
                self.current_brightness = target_brightness
                self.display1.brightness(target_brightness)
                self.display2.brightness(target_brightness)
                time_str = now.strftime('%H:%M:%S')
                state = "night" if target_brightness == NIGHT_BRIGHTNESS else "day"
                print(f"[INFO] [{time_str}] Brightness updated to {target_brightness} ({state} mode)")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Failed to update brightness: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_arrivals(self, arrival1=None, arrival2=None):
        """Display arrival times on the two displays.
        arrival1, arrival2: arrival dicts with 'time' and 'route_id' keys, or None if no bus.
        """
        if not self.available:
            return
        
        try:
            # Display 1: Show first arrival time as HHMM
            if arrival1:
                local_time = arrival1["time"].astimezone(LOCAL_TZ)
                time_obj = local_time.time()
                self.display1.time(time_obj, colon=True, leading_zero=False)
            else:
                self.display1.show("----")
            
            # Display 2: Show second arrival time as HHMM
            if arrival2:
                local_time = arrival2["time"].astimezone(LOCAL_TZ)
                time_obj = local_time.time()
                self.display2.time(time_obj, colon=True, leading_zero=False)
            else:
                self.display2.show("----")
        except Exception as e:
            print(f"[ERROR] Failed to update displays: {e}")
            import traceback
            traceback.print_exc()


def fetch_bus_arrivals(debug=False):
    """
    Fetch and parse bus arrival times for the specified stop.
    Returns a list of tuples (arrival_time, route_id, trip_id).
    """
    max_retries = 3
    retry_delay = 1  # Start with 1 second delay
    
    for attempt in range(max_retries):
        try:
            # Get reusable API session
            session = get_api_session()
            
            # Add User-Agent header (required by many servers)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download the protobuf file
            response = session.get(API_URL, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse the protobuf message
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(response.content)

            # Collect arrival times for our stop
            arrivals = []
            total_entities = len(feed.entity)
            matched_stop_count = 0

            for entity in feed.entity:
                if entity.HasField("trip_update"):
                    trip_update = entity.trip_update
                    
                    # Check each stop time update
                    for stop_time_update in trip_update.stop_time_update:
                        if debug:
                            print(f"  Stop ID in data: '{stop_time_update.stop_id}' (type: {type(stop_time_update.stop_id).__name__})")
                        
                        if str(stop_time_update.stop_id) == STOP_ID:
                            matched_stop_count += 1
                            # Get arrival time (prefer arrival over departure)
                            if stop_time_update.HasField("arrival"):
                                timestamp = stop_time_update.arrival.time
                            elif stop_time_update.HasField("departure"):
                                timestamp = stop_time_update.departure.time
                            else:
                                continue

                            # Convert Unix timestamp to datetime (UTC-aware)
                            arrival_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                            route_id = trip_update.trip.route_id
                            trip_id = trip_update.trip.trip_id
                            
                            # Get headsign from static GTFS data using trip_id
                            headsign = get_trip_headsign(trip_id)

                            arrivals.append({
                                "time": arrival_time,
                                "route_id": route_id,
                                "trip_id": trip_id,
                                "headsign": headsign,
                                "timestamp": timestamp
                            })

            if debug:
                print(f"Total entities: {total_entities}, Matched stops for {STOP_ID}: {matched_stop_count}, Arrivals found: {len(arrivals)}")
                for arr in arrivals[:3]:  # Show first 3 arrivals
                    local_time = arr["time"].astimezone(LOCAL_TZ)
                    headsign_str = f", headsign: {arr['headsign']}" if arr['headsign'] else ""
                    print(f"  Route {arr['route_id']}: {local_time} (UTC: {arr['time']}, timestamp: {arr['timestamp']}{headsign_str})")

            # Sort by arrival time
            arrivals.sort(key=lambda x: x["timestamp"])
            
            # Filter future arrivals only - use timestamp comparison (faster)
            now_timestamp = datetime.now(timezone.utc).timestamp()
            future_arrivals = [a for a in arrivals if a["timestamp"] > now_timestamp]
            
            # Filter to only include arrivals for the desired routes and headsigns
            filtered_arrivals = []
            for a in future_arrivals:
                if a["route_id"] in DESIRED_ROUTES:
                    # Check if headsign filtering is required for this route
                    desired_headsign = ROUTE_HEADSIGNS.get(a["route_id"])
                    if not desired_headsign or a["headsign"] == desired_headsign:
                        filtered_arrivals.append(a)
            
            if debug and len(arrivals) > 0:
                now = datetime.now(timezone.utc)
                now_local = now.astimezone(LOCAL_TZ)
                print(f"Current time - UTC: {now}, Local: {now_local}")
                print(f"Future arrivals (all routes): {len(future_arrivals)}")
                print(f"Future arrivals (desired routes with headsign filtering): {len(filtered_arrivals)}")
            
            return filtered_arrivals
            
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                print(f"Failed to connect after {max_retries} attempts: {e}")
                return []
        except requests.RequestException as e:
            print(f"Error fetching data from API: {e}")
            return []
        except Exception as e:
            print(f"Error parsing feed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    return []


def main():
    """Main entry point with continuous countdown and periodic refresh."""
    refresh_interval = REFRESH_INTERVAL  # Read from config file
    last_fetch_time = 0
    last_brightness_check_time = 0  # Track when we last checked brightness
    arrivals = []
    debug_mode = "--debug" in sys.argv
    display_manager = TM1637DisplayManager()
    
    # Set up refresh trigger flag
    refresh_flag = {"triggered": False}
    
    def on_refresh_button():
        """Callback when refresh button is pressed"""
        refresh_flag["triggered"] = True
    
    # Initialize capacitive sensor with debug mode
    sensor_manager = CapacitiveSensorManager(callback=on_refresh_button, debug=debug_mode)
    
    try:
        while True:
            current_time = time.time()
            
            # Update brightness based on sunset time (check once per minute)
            # This runs early so it executes regardless of arrival status
            time_since_last_check = current_time - last_brightness_check_time
            if time_since_last_check >= 60:
                print(f"[DEBUG] Checking brightness (last check was {time_since_last_check:.1f}s ago)")
                display_manager.update_brightness_for_time()
                last_brightness_check_time = current_time
            
            # Fetch new arrivals every 3 minutes, on first run, or when button is pressed
            should_refresh = (
                current_time - last_fetch_time >= refresh_interval or 
                last_fetch_time == 0 or 
                refresh_flag["triggered"]
            )
            
            if should_refresh:
                if refresh_flag["triggered"]:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Manual refresh triggered by button press.")
                    refresh_flag["triggered"] = False
                else:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching bus arrivals for stop {STOP_ID}...")
                
                arrivals = fetch_bus_arrivals(debug=debug_mode)
                last_fetch_time = current_time
                
                if not arrivals:
                    print("No upcoming arrivals found.")
                    print("Retrying in 3 minutes...")
                    # Clear displays when no data
                    display_manager.show_arrivals(arrival1=None, arrival2=None)
                    
                    # Wait 30 seconds before next attempt, but poll sensor frequently
                    wait_time = 30
                    while wait_time > 0:
                        sensor_manager.check_sensor()
                        if refresh_flag["triggered"]:
                            break
                        time.sleep(1)
                        wait_time -= 1
                    continue
                else:
                    # Print the updated arrivals when successfully fetched
                    now = datetime.now(timezone.utc)
                    print(f"[{now.strftime('%H:%M:%S')}] Updated arrivals for stop {STOP_ID}:")
                    
                    # Find and print arrivals for specific routes
                    arrival_route12 = next((a for a in arrivals if a["route_id"] == DISPLAY1_ROUTE), None)
                    arrival_route19 = next((a for a in arrivals if a["route_id"] == DISPLAY2_ROUTE), None)
                    
                    # Print the next arrivals
                    for arrival in [a for a in [arrival_route12, arrival_route19] if a is not None]:
                        local_time = arrival["time"].astimezone(LOCAL_TZ)
                        time_str = local_time.strftime("%I:%M %p")
                        route_id = arrival["route_id"]
                        headsign_str = f" ({arrival['headsign']})" if arrival['headsign'] else ""
                        print(f"  Route {route_id}: {time_str}{headsign_str}")
            
            # Check if any arrivals have passed
            future_arrivals = [a for a in arrivals if a["time"] > datetime.now(timezone.utc)]
            
            if not future_arrivals:
                # Clear displays when no future arrivals
                display_manager.show_arrivals(arrival1=None, arrival2=None)
                last_fetch_time = 0
                sensor_manager.check_sensor()  # Poll sensor even when no arrivals
                time.sleep(1)
                continue
            
            # Find arrivals for specific routes
            arrival_route12 = next((a for a in future_arrivals if a["route_id"] == DISPLAY1_ROUTE), None)
            arrival_route19 = next((a for a in future_arrivals if a["route_id"] == DISPLAY2_ROUTE), None)
            
            # Update TM1637 displays with arrival times for specific routes
            display_manager.show_arrivals(
                arrival1=arrival_route12,
                arrival2=arrival_route19
            )
            
            # Check sensor for button press
            sensor_manager.check_sensor()
            
            # Sleep without printing every iteration
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\nBus arrival monitor stopped.")
    finally:
        sensor_manager.cleanup()


if __name__ == "__main__":
    main()
