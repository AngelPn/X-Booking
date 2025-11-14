#!/usr/bin/env python3
"""
Simple CLI tool to test booking client functions
Usage: poetry run python test_booking.py
"""
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.booking_client import BookingClient


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def print_section(text: str):
    """Print a formatted section"""
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)


def main():
    """Main test function"""
    client = BookingClient()
    
    print_header("X Booking System - Test Client")
    
    # Get credentials
    username = input("\nEnter username/email: ").strip()
    password = input("Enter password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required")
        return
    
    # Test 1: Login
    print_section("1. Testing Login")
    result = client.login(username, password)
    
    if result["success"]:
        print(f"✅ Login successful!")
        print(f"   User: {result['user'].get('name', username)}")
        print(f"   User ID: {result['user'].get('user_id')}")
    else:
        print(f"❌ Login failed: {result['error']}")
        return
    
    # Test 2: Get current bookings
    print_section("2. Current Bookings")
    bookings = client.get_current_bookings()
    
    if bookings["success"]:
        if bookings["count"] > 0:
            print(f"Found {bookings['count']} booking(s):\n")
            for i, booking in enumerate(bookings["bookings"], 1):
                print(f"{i}. Booking ID: {booking['id']}")
                print(f"   Date: {booking['date']}")
                print(f"   Time: {booking['start_time']} - {booking['end_time']}")
                print(f"   Location: {booking['location']}", end="")
                if booking.get('sub_location'):
                    print(f" {booking['sub_location']}", end="")
                print()
                print(f"   Can Cancel: {'Yes' if booking['can_cancel'] else 'No'}")
                print()
        else:
            print("No current bookings found")
    else:
        print(f"❌ Failed to get bookings: {bookings['error']}")
    
    # Test 3: Available slots for Fitness (tomorrow)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print_section(f"3. Available Fitness Slots ({tomorrow})")
    
    fitness_slots = client.get_available_slots("Fitness", tomorrow)
    
    if fitness_slots["success"]:
        if fitness_slots["count"] > 0:
            print(f"Found {fitness_slots['count']} available slot(s):\n")
            for i, slot in enumerate(fitness_slots["slots"][:10], 1):  # Show first 10
                available = slot['available']
                total = slot['total']
                percentage = (available / total * 100) if total > 0 else 0
                status = "🟢" if available > 5 else "🟡" if available > 0 else "🔴"
                print(f"{i}. {slot['time']}-{slot['end_time']}: {status} {available}/{total} spots ({percentage:.0f}%)")
        else:
            print("No available slots found")
    else:
        print(f"❌ Failed to get slots: {fitness_slots['error']}")
    
    # Test 4: Available slots for X1-A (7 days ahead)
    week_ahead = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    print_section(f"4. Available X1-A Slots ({week_ahead})")
    
    x1_slots = client.get_available_slots("X1", week_ahead, sub_location="A")
    
    if x1_slots["success"]:
        if x1_slots["count"] > 0:
            print(f"Found {x1_slots['count']} available slot(s):\n")
            for i, slot in enumerate(x1_slots["slots"][:10], 1):
                available = slot['available']
                total = slot['total']
                status = "🟢" if available > 0 else "🔴"
                print(f"{i}. {slot['time']}-{slot['end_time']}: {status} {available}/{total} spots")
        else:
            print("No available slots (slots may not be unlocked yet)")
    else:
        print(f"❌ Failed to get slots: {x1_slots['error']}")
    
    # Test 5: Available slots for X3-A
    print_section(f"5. Available X3-A Slots ({week_ahead})")
    
    x3_slots = client.get_available_slots("X3", week_ahead, sub_location="A")
    
    if x3_slots["success"]:
        if x3_slots["count"] > 0:
            print(f"Found {x3_slots['count']} available slot(s):\n")
            for i, slot in enumerate(x3_slots["slots"][:10], 1):
                available = slot['available']
                total = slot['total']
                status = "🟢" if available > 0 else "🔴"
                print(f"{i}. {slot['time']}-{slot['end_time']}: {status} {available}/{total} spots")
        else:
            print("No available slots (slots may not be unlocked yet)")
    else:
        print(f"❌ Failed to get slots: {x3_slots['error']}")
    
    # Test 6: Cancel booking (optional)
    if bookings["success"] and bookings["count"] > 0:
        cancellable = [b for b in bookings["bookings"] if b["can_cancel"]]
        
        if cancellable:
            print_section("6. Cancel Booking (Optional)")
            print(f"\nFound {len(cancellable)} cancellable booking(s)")
            
            for i, booking in enumerate(cancellable, 1):
                print(f"{i}. Booking ID: {booking['id']} - {booking['location']} on {booking['date']} at {booking['start_time']}")
            
            choice = input("\nEnter booking number to cancel (or press Enter to skip): ").strip()
            
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(cancellable):
                    booking_to_cancel = cancellable[idx]
                    confirm = input(f"\nAre you sure you want to cancel booking {booking_to_cancel['id']}? (yes/no): ").strip().lower()
                    
                    if confirm == "yes":
                        cancel_result = client.cancel_booking(str(booking_to_cancel['id']))
                        if cancel_result["success"]:
                            print(f"✅ {cancel_result['message']}")
                        else:
                            print(f"❌ Failed to cancel: {cancel_result['error']}")
                    else:
                        print("Cancellation skipped")
                else:
                    print("Invalid booking number")
            else:
                print("Skipping cancellation test")
    
    # Logout
    print_section("7. Logout")
    if client.logout():
        print("✅ Logged out successfully")
    else:
        print("⚠️  Logout completed (with warnings)")
    
    print_header("Test Complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
