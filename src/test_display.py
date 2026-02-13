#!/usr/bin/env python3
"""
Simple test script to verify TM1637 displays are working.
"""

import time
from tm1637 import TM1637

# Display pins
DISPLAY1_CLK = 11
DISPLAY1_DIO = 13
DISPLAY2_CLK = 12
DISPLAY2_DIO = 15

print("[TEST] Initializing displays...")
try:
    display1 = TM1637(clk=DISPLAY1_CLK, dio=DISPLAY1_DIO)
    display2 = TM1637(clk=DISPLAY2_CLK, dio=DISPLAY2_DIO)
    
    display1.brightness(7)
    display2.brightness(7)
    print("[SUCCESS] Displays initialized!")
except Exception as e:
    print(f"[ERROR] Failed to initialize: {e}")
    exit(1)

# Test sequence
test_sequence = [
    ("1234", "5678"),
    ("0000", "1111"),
    ("2222", "3333"),
    ("----", "----"),
    ("1234", "----"),
    ("HELP", "TEST"),
    ("1010", "1010"),
]

for d1_text, d2_text in test_sequence:
    print(f"\n[TEST] Displaying: Display1='{d1_text}', Display2='{d2_text}'")
    try:
        display1.show(d1_text)
        display2.show(d2_text)
        print(f"[SUCCESS] Displayed successfully")
    except Exception as e:
        print(f"[ERROR] Failed to display: {e}")
    
    time.sleep(2)

print("\n[TEST] Test complete!")
