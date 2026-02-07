#!/usr/bin/env python3
"""
Fetch the next two bus arrival times for GRT stop 2783.
Uses the GTFS Realtime API provided by Region of Waterloo.
"""

import requests
from datetime import datetime
from google.transit_realtime import gtfs_realtime_pb2

# Configuration
API_URL = "https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates"
STOP_ID = "2783"


def fetch_bus_arrivals():
    """
    Fetch and parse bus arrival times for the specified stop.
    Returns a list of tuples (arrival_time, route_id, trip_id).
    """
    try:
        # Download the protobuf file
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()

        # Parse the protobuf message
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        # Collect arrival times for our stop
        arrivals = []

        for entity in feed.entity:
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update
                
                # Check each stop time update
                for stop_time_update in trip_update.stop_time_update:
                    if str(stop_time_update.stop_id) == STOP_ID:
                        # Get arrival time (prefer arrival over departure)
                        if stop_time_update.HasField("arrival"):
                            timestamp = stop_time_update.arrival.time
                        elif stop_time_update.HasField("departure"):
                            timestamp = stop_time_update.departure.time
                        else:
                            continue

                        # Convert Unix timestamp to datetime
                        arrival_time = datetime.fromtimestamp(timestamp)
                        route_id = trip_update.trip.route_id
                        trip_id = trip_update.trip.trip_id

                        arrivals.append({
                            "time": arrival_time,
                            "route_id": route_id,
                            "trip_id": trip_id,
                            "timestamp": timestamp
                        })

        # Sort by arrival time and get the next two
        arrivals.sort(key=lambda x: x["timestamp"])
        
        # Filter future arrivals only
        now = datetime.now()
        future_arrivals = [a for a in arrivals if a["time"] > now]
        
        return future_arrivals[:2]

    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []
    except Exception as e:
        print(f"Error parsing feed: {e}")
        return []


def main():
    """Main entry point."""
    print(f"Fetching next bus arrivals for stop {STOP_ID}...")
    arrivals = fetch_bus_arrivals()

    if not arrivals:
        print("No upcoming arrivals found.")
        return

    print(f"\nNext {len(arrivals)} bus arrivals for stop {STOP_ID}:")
    print("-" * 60)

    for i, arrival in enumerate(arrivals, 1):
        time_str = arrival["time"].strftime("%I:%M %p")
        route_id = arrival["route_id"]
        print(f"{i}. Route {route_id}: {time_str}")

    print("-" * 60)


if __name__ == "__main__":
    main()
