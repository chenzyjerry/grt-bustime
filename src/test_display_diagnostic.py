#!/usr/bin/env python3
"""
Diagnostic test for TM1637 displays - checks GPIO and power.
"""

import time

# First, check if GPIO library is available and set up
try:
    import RPi.GPIO as GPIO
    print("[INFO] RPi.GPIO available")
    
    # Check GPIO mode
    mode = GPIO.getmode()
    print(f"[INFO] Current GPIO mode: {mode}")
    
    # Set to BCM mode if not set
    if mode is None:
        GPIO.setmode(GPIO.BCM)
        print("[INFO] Set GPIO mode to BCM")
    
except ImportError:
    print("[WARNING] RPi.GPIO not available, some checks skipped")
    GPIO = None

# Now test the display
from tm1637 import TM1637

DISPLAY1_CLK = 11
DISPLAY1_DIO = 13
DISPLAY2_CLK = 12
DISPLAY2_DIO = 15

print("\n[INFO] Checking power and connections...")
print(f"[INFO] Display 1: CLK={DISPLAY1_CLK}, DIO={DISPLAY1_DIO}")
print(f"[INFO] Display 2: CLK={DISPLAY2_CLK}, DIO={DISPLAY2_DIO}")

print("\n[TEST] Initializing Display 1...")
try:
    display1 = TM1637(clk=DISPLAY1_CLK, dio=DISPLAY1_DIO)
    print("[SUCCESS] Display 1 initialized")
    
    # Try to set brightness
    display1.brightness(7)
    print("[INFO] Display 1 brightness set to 7")
    
    # Try to display something
    print("[TEST] Sending '1111' to Display 1...")
    display1.show("1111")
    print("[SUCCESS] Display 1 command sent (no errors)")
    time.sleep(2)
    
    # Try other values
    print("[TEST] Sending '8888' to Display 1...")
    display1.show("8888")
    print("[SUCCESS] Display 1 command sent (no errors)")
    time.sleep(2)
    
    # Try dashes
    print("[TEST] Sending '----' to Display 1...")
    display1.show("----")
    print("[SUCCESS] Display 1 command sent (no errors)")
    time.sleep(2)
    
except Exception as e:
    print(f"[ERROR] Display 1 failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[TEST] Initializing Display 2...")
try:
    display2 = TM1637(clk=DISPLAY2_CLK, dio=DISPLAY2_DIO)
    print("[SUCCESS] Display 2 initialized")
    
    display2.brightness(7)
    print("[INFO] Display 2 brightness set to 7")
    
    print("[TEST] Sending '2222' to Display 2...")
    display2.show("2222")
    print("[SUCCESS] Display 2 command sent (no errors)")
    time.sleep(2)
    
    print("[TEST] Sending '8888' to Display 2...")
    display2.show("8888")
    print("[SUCCESS] Display 2 command sent (no errors)")
    time.sleep(2)
    
except Exception as e:
    print(f"[ERROR] Display 2 failed: {e}")
    import traceback
    traceback.print_exc()

print("\n[INFO] Diagnostic test complete")
print("[INFO] If you still don't see anything:")
print("  1. Check if VCC (power) and GND (ground) are connected to the displays")
print("  2. Check if CLK and DIO pins are properly connected")
print("  3. Check if there are pull-up resistors on CLK and DIO (typically 10k)")
print("  4. Try using different GPIO pins if available")
print("  5. Check if the module needs different library (Adafruit, luma.display, etc.)")
