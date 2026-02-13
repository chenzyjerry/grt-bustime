#!/usr/bin/env python3
"""
Fetch the next two bus arrival times for GRT stop 2783.
Uses the GTFS Realtime API provided by Region of Waterloo.
"""

import requests
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import time
import sys
import os
from zoneinfo import ZoneInfo
try:
    from tm1637 import TM1637
    TM1637_AVAILABLE = True
except ImportError:
    TM1637_AVAILABLE = False
    print("Warning: raspberrypi-tm1637 library not found. Display functionality disabled.")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_URL = "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1"
STOP_ID = "2783"
LOCAL_TZ = ZoneInfo("America/Toronto")  # Eastern Time

# TM1637 Display Configuration
DISPLAY1_CLK = 11
DISPLAY1_DIO = 13
DISPLAY1_ROUTE = "12"  # Route to display on display 1
DISPLAY2_CLK = 11
DISPLAY2_DIO = 15
DISPLAY2_ROUTE = "19"  # Route to display on display 2


class DH_KeyAdapter(HTTPAdapter):
    """Custom adapter to allow weak DH keys for older servers"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


class TM1637DisplayManager:
    """Manages two TM1637 4-digit 7-segment displays"""
    def __init__(self):
        self.display1 = None
        self.display2 = None
        self.available = TM1637_AVAILABLE
        print(f"[INFO] TM1637_AVAILABLE: {TM1637_AVAILABLE}")
        
        if self.available:
            try:
                self.display1 = TM1637(clk=DISPLAY1_CLK, dio=DISPLAY1_DIO)
                self.display2 = TM1637(clk=DISPLAY2_CLK, dio=DISPLAY2_DIO)
                self.display1.brightness(7)  # 0-7 brightness levels
                self.display2.brightness(7)
                print("[INFO] TM1637 displays initialized on pins (CLK/DIO): ({}/{}), ({}/{}).".format(
                    DISPLAY1_CLK, DISPLAY1_DIO, DISPLAY2_CLK, DISPLAY2_DIO))
            except Exception as e:
                print(f"[ERROR] Failed to initialize displays: {e}")
                self.available = False
    
    def show_arrivals(self, arrival1=None, arrival2=None):
        """Display arrival times on the two displays.
        arrival1, arrival2: arrival dicts with 'time' and 'route_id' keys, or None if no bus.
        """
        if not self.available:
            return
        
        try:
            # Display 1: Show first arrival time as HHMM (no colon to avoid character errors)
            if arrival1:
                local_time = arrival1["time"].astimezone(LOCAL_TZ)
                time_str = local_time.strftime("%H%M")
                self.display1.show(time_str)
                print(f"[DEBUG] Display 1 showing: {time_str} (Route {arrival1['route_id']})")
            else:
                self.display1.show("----")  # Display dashes if no bus
                print(f"[DEBUG] Display 1 showing: ----")
            
            # Display 2: Show second arrival time as HHMM (no colon to avoid character errors)
            if arrival2:
                local_time = arrival2["time"].astimezone(LOCAL_TZ)
                time_str = local_time.strftime("%H%M")
                self.display2.show(time_str)
                print(f"[DEBUG] Display 2 showing: {time_str} (Route {arrival2['route_id']})")
            else:
                self.display2.show("----")  # Display dashes if no bus
                print(f"[DEBUG] Display 2 showing: ----")
        except Exception as e:
            print(f"[ERROR] Failed to update displays: {e}")


def fetch_bus_arrivals(debug=False):
    """
    Fetch and parse bus arrival times for the specified stop.
    Returns a list of tuples (arrival_time, route_id, trip_id).
    """
    try:
        # Create session with custom SSL adapter
        session = requests.Session()
        session.mount("https://", DH_KeyAdapter())
        
        # Download the protobuf file
        response = session.get(API_URL, timeout=10)
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

                        arrivals.append({
                            "time": arrival_time,
                            "route_id": route_id,
                            "trip_id": trip_id,
                            "timestamp": timestamp
                        })

        if debug:
            print(f"Total entities: {total_entities}, Matched stops for {STOP_ID}: {matched_stop_count}, Arrivals found: {len(arrivals)}")
            for arr in arrivals[:3]:  # Show first 3 arrivals
                local_time = arr["time"].astimezone(LOCAL_TZ)
                print(f"  Arrival time: {local_time} (UTC: {arr['time']}, timestamp: {arr['timestamp']})")

        # Sort by arrival time and get the next two
        arrivals.sort(key=lambda x: x["timestamp"])
        
        # Filter future arrivals only - use UTC-aware comparison
        now = datetime.now(timezone.utc)
        future_arrivals = [a for a in arrivals if a["time"] > now]
        
        if debug and len(arrivals) > 0:
            now_local = now.astimezone(LOCAL_TZ)
            print(f"Current time - UTC: {now}, Local: {now_local}")
            print(f"Future arrivals: {len(future_arrivals)}")
        
        return future_arrivals[:2]

    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []
    except Exception as e:
        print(f"Error parsing feed: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """Main entry point with continuous countdown and periodic refresh."""
    refresh_interval = 3 * 60  # 3 minutes in seconds
    last_fetch_time = 0
    arrivals = []
    debug_mode = "--debug" in sys.argv
    display_manager = TM1637DisplayManager()
    
    try:
        while True:
            current_time = time.time()
            
            # Fetch new arrivals every 3 minutes or on first run
            if current_time - last_fetch_time >= refresh_interval or last_fetch_time == 0:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Fetching bus arrivals for stop {STOP_ID}...")
                arrivals = fetch_bus_arrivals(debug=debug_mode)
                last_fetch_time = current_time
                
                if not arrivals:
                    print("No upcoming arrivals found.")
                    print("Retrying in 3 minutes...")
                    # Clear displays when no data
                    display_manager.show_arrivals(arrival1=None, arrival2=None)
                    time.sleep(30)  # Wait 30 seconds before next attempt if no data
                    continue
            
            # Display current arrivals with countdown
            now = datetime.now(timezone.utc)
            print(f"\r[{now.strftime('%H:%M:%S')}] Next bus arrivals for stop {STOP_ID}:", end="")
            
            # Check if any arrivals have passed
            future_arrivals = [a for a in arrivals if a["time"] > datetime.now(timezone.utc)]
            
            if not future_arrivals:
                print(" (No upcoming arrivals, refreshing...)")
                # Clear displays when no future arrivals
                display_manager.show_arrivals(arrival1=None, arrival2=None)
                last_fetch_time = 0
                time.sleep(1)
                continue
            
            # Display the next 2 arrivals with countdown
            display_text = ""
            arrival_list = future_arrivals[:2]
            
            # Find arrivals for specific routes
            arrival_route12 = None
            arrival_route19 = None
            
            for arrival in future_arrivals:
                if arrival["route_id"] == DISPLAY1_ROUTE and arrival_route12 is None:
                    arrival_route12 = arrival
                if arrival["route_id"] == DISPLAY2_ROUTE and arrival_route19 is None:
                    arrival_route19 = arrival
            
            for i, arrival in enumerate(arrival_list, 1):
                minutes_remaining = (arrival["time"] - now).total_seconds() / 60
                local_time = arrival["time"].astimezone(LOCAL_TZ)
                time_str = local_time.strftime("%I:%M %p")
                route_id = arrival["route_id"]
                
                if minutes_remaining < 1:
                    countdown_str = f"{int((arrival['time'] - now).total_seconds())}s"
                else:
                    countdown_str = f"{int(minutes_remaining)}m {int((arrival['time'] - now).total_seconds() % 60)}s"
                
                display_text += f" | Route {route_id}: {time_str} ({countdown_str})"
            
            # Update TM1637 displays with arrival times for specific routes
            display_manager.show_arrivals(
                arrival1=arrival_route12,
                arrival2=arrival_route19
            )
            
            print(display_text, end="", flush=True)
            
            # Update display every second
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nBus arrival monitor stopped.")


if __name__ == "__main__":
    main()
