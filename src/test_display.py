#!/usr/bin/env python3
"""
Simple test script to verify TM1637 displays are working.
"""

import time
import datetime
from tm1637 import TM1637

# Display pins
DISPLAY1_CLK = 17
DISPLAY1_DIO = 22
DISPLAY2_CLK = 18
DISPLAY2_DIO = 27

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

# Test time display with colons
print("\n[TEST] Testing time display with colons...")
time_tests = [
    (datetime.time(1, 30), datetime.time(2, 45)),
    (datetime.time(12, 34), datetime.time(10, 15)),
    (datetime.time(9, 59), datetime.time(11, 0)),
]

for t1, t2 in time_tests:
    print(f"\n[TEST] Displaying time: Display1='{t1}', Display2='{t2}'")
    try:
        display1.time(t1, colon=True, leading_zero=False)
        display2.time(t2, colon=True, leading_zero=False)
        print(f"[SUCCESS] Time displayed successfully")
    except Exception as e:
        print(f"[ERROR] Failed to display time: {e}")
    
    time.sleep(2)

print("\n[TEST] Test complete!")
