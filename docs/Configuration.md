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

**STOP_ID**
- The GRT bus stop ID where you want to monitor arrivals
- Default: `2783`
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

## Example Configurations

### Two Bus Routes in Waterloo

```
API_URL = https://webapps.regionofwaterloo.ca/api/grt-routes/api/tripupdates/1
STOP_ID = 2783
LOCAL_TZ = America/Toronto

DISPLAY1_ROUTE = 12
DISPLAY1_CLK = 27
DISPLAY1_DIO = 17

DISPLAY2_ROUTE = 19
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
