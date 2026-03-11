#!/usr/bin/env python3
"""
Test program to fetch and display all bus arrivals with their direction IDs.
This helps determine which direction_id to use in the config file.
Uses static GTFS data to get direction information.
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
import csv
import zipfile
import io

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


def load_static_gtfs_directions(static_gtfs_url):
    """
    Load trip-to-direction mapping from static GTFS data.
    Returns a dictionary mapping trip_id to direction_id.
    """
    trip_to_direction = {}
    
    try:
        print("[INFO] Loading static GTFS data for direction mapping...")
        session = get_api_session()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Download the static GTFS zip file
        response = session.get(static_gtfs_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extract and parse the trips.txt file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Read trips.txt to get trip_id -> direction_id mapping
            with zip_file.open('trips.txt') as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                for row in reader:
                    trip_id = row.get('trip_id')
                    direction_id = row.get('direction_id')
                    if trip_id and direction_id is not None:
                        try:
                            trip_to_direction[trip_id] = int(direction_id)
                        except (ValueError, TypeError):
                            pass  # Skip invalid direction IDs
        
        print(f"[INFO] Loaded {len(trip_to_direction)} trip-direction mappings from static GTFS data.\n")
        return trip_to_direction
    
    except Exception as e:
        print(f"[ERROR] Failed to load static GTFS data: {e}")
        return {}


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
    STATIC_GTFS_URL = config.get("STATIC_GTFS_URL", "https://webapps.regionofwaterloo.ca/api/grt-routes/api/staticfeeds/1")
    STOP_ID = str(config.get("STOP_ID", "2783"))
    LOCAL_TZ = ZoneInfo(config.get("LOCAL_TZ", "America/Toronto"))
    DISPLAY1_ROUTE = str(config.get("DISPLAY1_ROUTE", "12"))
    DISPLAY2_ROUTE = str(config.get("DISPLAY2_ROUTE", "19"))
    
    # Load static GTFS data to get direction mappings
    trip_to_direction = load_static_gtfs_directions(STATIC_GTFS_URL)
    
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
                        # Get direction_id from static GTFS data mapping
                        direction_id = trip_to_direction.get(trip_id)
                        
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
            print(f"\n{'='*80}")
            print(f"ROUTE {route}")
            print(f"{'='*80}")
            
            # Group by direction
            directions = {}
            for arrival in arrivals:
                direction = arrival["direction_id"]
                if direction not in directions:
                    directions[direction] = []
                directions[direction].append(arrival)
            
            # Get all unique direction values (sorted)
            dir_list = sorted([d for d in directions.keys() if d is not None], default=[])
            
            if len(dir_list) == 2:
                dir0, dir1 = dir_list[0], dir_list[1]
                arrivals_dir0 = directions.get(dir0, [])
                arrivals_dir1 = directions.get(dir1, [])
                
                print(f"\nDirection {dir0}:".ljust(40) + f"Direction {dir1}:")
                print("-" * 40 + "-" * 40)
                
                max_arrivals = max(len(arrivals_dir0), len(arrivals_dir1))
                for i in range(max_arrivals):
                    left = ""
                    if i < len(arrivals_dir0):
                        local_time = arrivals_dir0[i]["time"].astimezone(LOCAL_TZ)
                        time_str = local_time.strftime("%I:%M %p")
                        left = f"  {time_str}"
                    
                    right = ""
                    if i < len(arrivals_dir1):
                        local_time = arrivals_dir1[i]["time"].astimezone(LOCAL_TZ)
                        time_str = local_time.strftime("%I:%M %p")
                        right = f"  {time_str}"
                    
                    print(left.ljust(40) + right)
                
                print(f"\nTotal arrivals: {len(arrivals_dir0)}".ljust(40) + f"Total arrivals: {len(arrivals_dir1)}")
            else:
                # Fallback to original display if not exactly 2 directions
                for direction in sorted(directions.keys(), key=lambda x: (x is None, x)):
                    direction_arrivals = directions[direction]
                    direction_str = f"Direction {direction}" if direction is not None else "Direction [NONE]"
                    print(f"\n{direction_str} ({len(direction_arrivals)} arrivals):")
                    
                    for arrival in direction_arrivals[:5]:
                        local_time = arrival["time"].astimezone(LOCAL_TZ)
                        time_str = local_time.strftime("%I:%M %p")
                        print(f"  {time_str} (trip: {arrival['trip_id']})")
                    
                    if len(direction_arrivals) > 5:
                        print(f"  ... and {len(direction_arrivals) - 5} more")
        
        # Summary for config
        print("\n" + "=" * 80)
        print("SUMMARY FOR CONFIG.TXT:")
        print("=" * 80)
        
        for route in sorted(routes.keys()):
            route_arrivals = routes[route]
            directions = {}
            for arrival in route_arrivals:
                direction = arrival["direction_id"]
                if direction not in directions:
                    directions[direction] = []
                directions[direction].append(arrival)
            
            dir_list = sorted([d for d in directions.keys() if d is not None], default=[])
            
            if route == DISPLAY1_ROUTE:
                print(f"\nRoute {DISPLAY1_ROUTE} (DISPLAY1):")
                print(f"  Available directions: {dir_list}")
                if len(dir_list) > 0:
                    print(f"  Set DISPLAY1_DIRECTION = {dir_list[0]} or {dir_list[1] if len(dir_list) > 1 else 'none'}")
                else:
                    print(f"  No direction data available")
            elif route == DISPLAY2_ROUTE:
                print(f"\nRoute {DISPLAY2_ROUTE} (DISPLAY2):")
                print(f"  Available directions: {dir_list}")
                if len(dir_list) > 0:
                    print(f"  Set DISPLAY2_DIRECTION = {dir_list[0]} or {dir_list[1] if len(dir_list) > 1 else 'none'}")
                else:
                    print(f"  No direction data available")
        
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
