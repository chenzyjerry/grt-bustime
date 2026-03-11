# Configuration Guide

This document explains how to configure the GRT Bus Time Display system using the `config.txt` file.

## Overview

All settings for the bus arrival time display are now stored in `config.txt` in the `src/` directory. You no longer need to edit Python code to change settings - simply modify `config.txt` and restart the program.

## Configuration File Location

```
src/config.txt
```

## How to Modify Settings

1. Open `src/config.txt` in any text editor
2. Change the values as needed (see below for details)
3. Save the file
4. Restart the program for changes to take effect

## Configuration Options

### API Configuration

**API_URL**
- The endpoint URL for the GRT real-time bus API
- Default: `https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1`
- Change this only if GRT updates their API endpoint

**STATIC_GTFS_URL**
- The endpoint URL for the static GTFS data (schedule information)
- Default: `https://webapps.regionofwaterloo.ca/api/grt-routes/api/staticfeeds/1`
- This is used to get destination/direction information (headsigns) for bus trips
- Change this only if GRT updates their API endpoint

**STOP_ID**
- The GRT bus stop ID where you want to monitor arrivals
- Default: `2673`
- To find your stop ID, visit the GRT website or check a transit app

**LOCAL_TZ**
- Your timezone (IANA timezone name)
- Default: `America/Toronto`
- Examples: `America/New_York`, `America/Denver`, `America/Los_Angeles`
- Find your timezone at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### Display 1 Configuration

**DISPLAY1_ROUTE**
- Route number displayed on the first TM1637 display
- Default: `12`
- Example: `12`, `19`, `5`

**DISPLAY1_HEADSIGN**
- Filter arrivals by destination/direction (headsign)
- Leave blank to show all directions for this route
- Example values: `Downtown`, `Fairway Station`, `Waterloo Station`, `University of Waterloo`
- To find available headsigns for your route, run: `python test_directions.py`
- The program will display all available destinations for your configured routes

**DISPLAY1_CLK**
- GPIO pin for the first display's clock signal
- Default: `27`
- Common values: `27`, `17`, `22`

**DISPLAY1_DIO**
- GPIO pin for the first display's data signal
- Default: `17`
- Common values: `17`, `23`, `24`

### Display 2 Configuration

**DISPLAY2_ROUTE**
- Route number displayed on the second TM1637 display
- Default: `19`
- Example: `12`, `19`, `5`

**DISPLAY2_HEADSIGN**
- Filter arrivals by destination/direction (headsign)
- Leave blank to show all directions for this route
- Example values: `Downtown`, `Fairway Station`, `Waterloo Station`, `University of Waterloo`
- To find available headsigns for your route, run: `python test_directions.py`
- The program will display all available destinations for your configured routes

**DISPLAY2_CLK**
- GPIO pin for the second display's clock signal
- Default: `24`
- Common values: `27`, `17`, `22`

**DISPLAY2_DIO**
- GPIO pin for the second display's data signal
- Default: `23`
- Common values: `17`, `23`, `24`

### Capacitive Sensor Configuration

**SENSOR_PIN**
- GPIO pin for the TTP223 capacitive touch sensor
- Default: `4`
- This button triggers a manual refresh of bus arrival times

### Sunset Dimming Configuration

**ENABLE_SUNSET_DIMMING**
- Enable automatic brightness dimming after sunset
- Options: `true` or `false`
- Default: `true`
- Requires the `astral` Python library; if not installed, dimming is disabled

**DAY_BRIGHTNESS**
- Display brightness level during daytime
- Range: `0-7` (0 = dimmest, 7 = brightest)
- Default: `7`

**NIGHT_BRIGHTNESS**
- Display brightness level after sunset
- Range: `0-7` (0 = dimmest, 7 = brightest)
- Default: `2`

### Location Configuration

**LOCATION_LATITUDE**
- Your latitude for sunset calculation
- Default: `43.4516` (Waterloo, ON)
- Example: `43.4516` for Waterloo
- Precision: 4 decimal places is sufficient

**LOCATION_LONGITUDE**
- Your longitude for sunset calculation
- Default: `-80.4925` (Waterloo, ON)
- Example: `-80.4925` for Waterloo
- Note: Western hemisphere is negative

### Refresh Interval

**REFRESH_INTERVAL**
- How often to fetch updated bus arrival times from the API
- Specified in seconds
- Default: `180` (3 minutes)
- Minimum recommended: `60` (1 minute)
- Set higher to reduce network usage, lower for more frequent updates

## Finding Your Headsigns

The headsign (also called trip_headsign or destination) is the destination name for a bus trip. To discover which headsigns are available for your routes:

1. Ensure your `STOP_ID`, `DISPLAY1_ROUTE`, and `DISPLAY2_ROUTE` are correctly configured
2. Run the test script:
   ```bash
   cd src/
   python test_directions.py
   ```
3. The script will display all upcoming arrivals grouped by route and destination
4. Copy the exact headsign text (e.g., "Downtown", "Fairway Station") into your config file
5. To show all destinations for a route, leave the headsign blank

## Example Configurations

### Two Bus Routes with Specific Destinations

```
API_URL = https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1
STATIC_GTFS_URL = https://webapps.regionofwaterloo.ca/api/grt-routes/api/staticfeeds/1
STOP_ID = 2673
LOCAL_TZ = America/Toronto

DISPLAY1_ROUTE = 12
DISPLAY1_HEADSIGN = Fairway Station
DISPLAY1_CLK = 27
DISPLAY1_DIO = 17

DISPLAY2_ROUTE = 19
DISPLAY2_HEADSIGN = University of Waterloo Station
DISPLAY2_CLK = 24
DISPLAY2_DIO = 23

SENSOR_PIN = 4

ENABLE_SUNSET_DIMMING = true
DAY_BRIGHTNESS = 7
NIGHT_BRIGHTNESS = 2

LOCATION_LATITUDE = 43.4516
LOCATION_LONGITUDE = -80.4925

REFRESH_INTERVAL = 180
```

### Two Bus Routes (All Destinations)

Leave `DISPLAY1_HEADSIGN` and `DISPLAY2_HEADSIGN` blank to show arrivals for all destinations:

```
API_URL = https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1
STATIC_GTFS_URL = https://webapps.regionofwaterloo.ca/api/grt-routes/api/staticfeeds/1
STOP_ID = 2673
LOCAL_TZ = America/Toronto

DISPLAY1_ROUTE = 12
DISPLAY1_HEADSIGN = 
DISPLAY1_CLK = 27
DISPLAY1_DIO = 17

DISPLAY2_ROUTE = 19
DISPLAY2_HEADSIGN = 
DISPLAY2_CLK = 24
DISPLAY2_DIO = 23

REFRESH_INTERVAL = 180
```

### Testing (No Dimming, Single Route)

```
ENABLE_SUNSET_DIMMING = false
DAY_BRIGHTNESS = 7

DISPLAY1_ROUTE = 12
DISPLAY2_ROUTE = 12

REFRESH_INTERVAL = 60
```

## Troubleshooting

### Configuration File Not Found

If you get an error like "Configuration file not found: /path/to/config.txt":
- Make sure `config.txt` exists in the `src/` directory
- Check file spelling and location
- The file must be named exactly `config.txt` (lowercase)

### Invalid Configuration Values

Common issues:
- **Brightness values**: Must be between 0 and 7
- **GPIO pins**: Must be valid Raspberry Pi GPIO pin numbers
- **Booleans**: Use `true` or `false` (lowercase)
- **Numbers**: Don't use quotes around numeric values
- **Timezone**: Must be a valid IANA timezone name
- **Headsign**: Must match exactly (check spelling, case, and spacing) - run `test_directions.py` to see exact values

### Headsign Not Working

If your filtered headsign shows no arrivals:
- Run `python test_directions.py` to verify the exact headsign text
- Copy the text exactly (including case and spacing)
- Some headsigns may have trailing or leading spaces - the config loader trims these
- If the headsign is not available at your stop, you may need to use a different stop or leave the headsign blank

### Program Doesn't Recognize Changes

Always restart the program after modifying `config.txt`. The configuration is loaded once when the program starts.

## Format Notes

- **Comments** start with `#` and are ignored
- **Empty lines** are ignored
- **Key = Value** format with `=` separator
- **Whitespace** around keys and values is trimmed automatically
- **Boolean values** must be lowercase: `true` or `false`
- **String values** do not need quotes
- **Numeric values** must not have quotes

## Advanced: Adding More Routes

To monitor additional routes beyond the default two displays, you would need to modify the Python code to add additional display objects and parsing logic. The configuration system is designed for the current two-display setup.

## About Headsigns vs Direction IDs

**Why use headsigns instead of direction IDs?**

Bus systems often use "direction IDs" (like 0 or 1) to indicate opposite directions of the same route. However, the GRT (Grand River Transit) system uses more meaningful descriptions called "headsigns" (e.g., "Downtown", "Waterloo Station", "Fairway Station") to indicate where the bus is heading.

Using headsigns is more user-friendly because:
- You can see exactly where each bus is going
- Configuration is more intuitive (e.g., "Downtown" vs "Direction 0")
- The same route can serve multiple destinations at different times

Use `test_directions.py` to explore available headsigns for your routes!
