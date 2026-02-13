#!/usr/bin/env python3
"""
Test script for TTP223 capacitive sensor on pin 4.
Run this to verify the sensor is working correctly.
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO not installed")
    sys.exit(1)

SENSOR_PIN = 4

def test_sensor():
    """Test the sensor by reading its state continuously"""
    try:
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_PIN, GPIO.IN)
        
        print(f"[INFO] Testing sensor on pin {SENSOR_PIN}")
        print("[INFO] Press Ctrl+C to exit")
        print("[INFO] Touch the sensor and watch for state changes below:\n")
        
        last_state = GPIO.input(SENSOR_PIN)
        print(f"Initial state: {last_state}")
        
        while True:
            current_state = GPIO.input(SENSOR_PIN)
            
            if current_state != last_state:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] State changed: {last_state} -> {current_state}")
                last_state = current_state
            
            time.sleep(0.05)  # Poll every 50ms
    
    except KeyboardInterrupt:
        print("\n\nSensor test stopped.")
    finally:
        GPIO.cleanup()
        print("[INFO] GPIO cleaned up.")

if __name__ == "__main__":
    test_sensor()
