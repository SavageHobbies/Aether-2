#!/usr/bin/env python3

"""
Super simple calendar test.
"""

# Test if we can create a simple class in a separate file
class SimpleCalendar:
    def __init__(self):
        print("SimpleCalendar created")

if __name__ == "__main__":
    cal = SimpleCalendar()
    print("✓ SimpleCalendar works")