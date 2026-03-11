#!/usr/bin/env python3
"""
Test program to fetch and display all bus arrivals with their direction IDs.
This helps determine which direction_id to use in the config file.
"""

import requests
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import sys
import os
from zoneinfo import ZoneInfo
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_config():
    """Load configuration from config.txt file."""
    config_path = Path(__file__).parent / "config.txt"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    config = {}
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if value.lower() == 'true':
                    config[key] = True
                elif value.lower() == 'false':
                    config[key] = False
                else:
                    try:
                        if '.' in value:
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        config[key] = value
    
    return config


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
    """Get or create the API session."""
    session = requests.Session()
    session.mount("https://", DH_KeyAdapter())
    return session


def test_directions():
    """Fetch and display all bus arrivals with their direction IDs."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please create a config.txt file in the src directory.")
        sys.exit(1)
    
    # Extract configuration
    API_URL = config.get("API_URL", "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1")
    STOP_ID = str(config.get("STOP_ID", "2783"))
    LOCAL_TZ = ZoneInfo(config.get("LOCAL_TZ", "America/Toronto"))
    DISPLAY1_ROUTE = str(config.get("DISPLAY1_ROUTE", "12"))
    DISPLAY2_ROUTE = str(config.get("DISPLAY2_ROUTE", "19"))
    
    print(f"[INFO] Fetching bus data for stop {STOP_ID}...")
    print(f"[INFO] Looking for routes: {DISPLAY1_ROUTE}, {DISPLAY2_ROUTE}\n")
    
    try:
        session = get_api_session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = session.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the protobuf message
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        
        # Collect all arrival data
        all_arrivals = []
        
        for entity in feed.entity:
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update
                
                for stop_time_update in trip_update.stop_time_update:
                    if str(stop_time_update.stop_id) == STOP_ID:
                        # Get arrival time
                        if stop_time_update.HasField("arrival"):
                            timestamp = stop_time_update.arrival.time
                        elif stop_time_update.HasField("departure"):
                            timestamp = stop_time_update.departure.time
                        else:
                            continue
                        
                        arrival_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        route_id = trip_update.trip.route_id
                        trip_id = trip_update.trip.trip_id
                        direction_id = trip_update.trip.direction_id if trip_update.trip.HasField("direction_id") else None
                        
                        all_arrivals.append({
                            "time": arrival_time,
                            "route_id": route_id,
                            "trip_id": trip_id,
                            "direction_id": direction_id,
                            "timestamp": timestamp
                        })
        
        # Filter to future arrivals and sort
        now_timestamp = datetime.now(timezone.utc).timestamp()
        future_arrivals = [a for a in all_arrivals if a["timestamp"] > now_timestamp]
        future_arrivals.sort(key=lambda x: x["timestamp"])
        
        if not future_arrivals:
            print("No upcoming arrivals found.")
            return
        
        # Group by route
        routes = {}
        for arrival in future_arrivals:
            route = arrival["route_id"]
            if route not in routes:
                routes[route] = []
            routes[route].append(arrival)
        
        # Display results
        print(f"Found {len(future_arrivals)} upcoming arrivals\n")
        
        for route in sorted(routes.keys()):
            arrivals = routes[route]
            print(f"Route {route}:")
            print("-" * 80)
            
            # Group by direction
            directions = {}
            for arrival in arrivals:
                direction = arrival["direction_id"]
                if direction not in directions:
                    directions[direction] = []
                directions[direction].append(arrival)
            
            for direction in sorted(directions.keys(), key=lambda x: (x is None, x)):
                direction_arrivals = directions[direction]
                direction_str = f"Direction {direction}" if direction is not None else "Direction [NONE]"
                print(f"  {direction_str} ({len(direction_arrivals)} arrivals):")
                
                for arrival in direction_arrivals[:3]:  # Show first 3
                    local_time = arrival["time"].astimezone(LOCAL_TZ)
                    time_str = local_time.strftime("%I:%M %p")
                    print(f"    {time_str} (trip: {arrival['trip_id']})")
                
                if len(direction_arrivals) > 3:
                    print(f"    ... and {len(direction_arrivals) - 3} more")
            
            print()
        
        # Summary for config
        print("\n" + "=" * 80)
        print("SUMMARY FOR CONFIG.TXT:")
        print("=" * 80)
        
        if DISPLAY1_ROUTE in routes:
            route1_directions = set()
            for arrival in routes[DISPLAY1_ROUTE]:
                route1_directions.add(arrival["direction_id"])
            print(f"Route {DISPLAY1_ROUTE} has directions: {sorted(route1_directions)}")
            print(f"  Suggestion: Set DISPLAY1_DIRECTION = {min([d for d in route1_directions if d is not None], default=0)}")
        
        if DISPLAY2_ROUTE in routes:
            route2_directions = set()
            for arrival in routes[DISPLAY2_ROUTE]:
                route2_directions.add(arrival["direction_id"])
            print(f"Route {DISPLAY2_ROUTE} has directions: {sorted(route2_directions)}")
            print(f"  Suggestion: Set DISPLAY2_DIRECTION = {min([d for d in route2_directions if d is not None], default=0)}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing feed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_directions()
