"""
Test script for BookingClient
Run this to test the booking system integration
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.booking_client import BookingClient


def test_booking_flow():
    """Test the complete booking flow"""
    client = BookingClient()
    
    print("=" * 60)
    print("X Booking System - Test Script")
    print("=" * 60)
    
    # Get credentials from environment or user input
    username = os.getenv("X_USERNAME") or input("Enter username/email: ")
    password = os.getenv("X_PASSWORD") or input("Enter password: ")
    
    # Test 1: Login
    print("\n1. Testing Login...")
    print("-" * 60)
    login_result = client.login(username, password)
    print(f"Result: {login_result}")
    
    if not login_result["success"]:
        print("\n❌ Login failed. Cannot continue tests.")
        return
    
    print(f"✅ Logged in as: {login_result['user']['name']}")
    
    # Test 2: Get current bookings
    print("\n2. Testing Get Current Bookings...")
    print("-" * 60)
    bookings_result = client.get_current_bookings()
    print(f"Result: Found {bookings_result.get('count', 0)} bookings")
    
    if bookings_result["success"] and bookings_result["count"] > 0:
        print("\nCurrent Bookings:")
        for booking in bookings_result["bookings"][:5]:  # Show first 5
            print(f"  - ID: {booking['id']}")
            print(f"    Date: {booking['date']} at {booking['start_time']}-{booking['end_time']}")
            print(f"    Location: {booking['location']} {booking.get('sub_location', '')}")
            print(f"    Can Cancel: {booking['can_cancel']}")
            print()
    
    # Test 3: Get available slots for Fitness (tomorrow)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n3. Testing Get Available Slots (Fitness on {tomorrow})...")
    print("-" * 60)
    slots_result = client.get_available_slots("Fitness", tomorrow)
    print(f"Result: Found {slots_result.get('count', 0)} available slots")
    
    if slots_result["success"] and slots_result["count"] > 0:
        print("\nAvailable Slots:")
        for slot in slots_result["slots"][:10]:  # Show first 10
            print(f"  - {slot['time']}-{slot['end_time']}: {slot['available']}/{slot['total']} spots")
    
    # Test 4: Get available slots for X1 (7 days from now - typically unlocked)
    week_ahead = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"\n4. Testing Get Available Slots (X1 on {week_ahead})...")
    print("-" * 60)
    x1_slots = client.get_available_slots("X1", week_ahead, sub_location="A")
    print(f"Result: Found {x1_slots.get('count', 0)} available slots for X1-A")
    
    if x1_slots["success"] and x1_slots["count"] > 0:
        print("\nAvailable X1-A Slots:")
        for slot in x1_slots["slots"][:5]:  # Show first 5
            print(f"  - {slot['time']}-{slot['end_time']}: {slot['available']}/{slot['total']} spots")
    
    # Test 5: Get available slots for X3
    print(f"\n5. Testing Get Available Slots (X3 on {week_ahead})...")
    print("-" * 60)
    x3_slots = client.get_available_slots("X3", week_ahead, sub_location="A")
    print(f"Result: Found {x3_slots.get('count', 0)} available slots for X3-A")
    
    if x3_slots["success"] and x3_slots["count"] > 0:
        print("\nAvailable X3-A Slots:")
        for slot in x3_slots["slots"][:5]:  # Show first 5
            print(f"  - {slot['time']}-{slot['end_time']}: {slot['available']}/{slot['total']} spots")
    
    # Test 6: Cancel booking (if any cancellable bookings exist)
    print("\n6. Testing Cancel Booking...")
    print("-" * 60)
    if bookings_result["success"] and bookings_result["count"] > 0:
        cancellable = [b for b in bookings_result["bookings"] if b["can_cancel"]]
        if cancellable:
            booking_to_cancel = cancellable[0]
            print(f"Found cancellable booking: ID {booking_to_cancel['id']}")
            
            confirm = input("Do you want to test cancellation? (yes/no): ")
            if confirm.lower() == "yes":
                cancel_result = client.cancel_booking(booking_to_cancel["id"])
                print(f"Result: {cancel_result}")
                
                if cancel_result["success"]:
                    print("✅ Booking cancelled successfully")
                else:
                    print(f"❌ Failed to cancel: {cancel_result['error']}")
            else:
                print("⏭️  Skipping cancellation test")
        else:
            print("No cancellable bookings found")
    else:
        print("No bookings available to test cancellation")
    
    # Test 7: Logout
    print("\n7. Testing Logout...")
    print("-" * 60)
    logout_result = client.logout()
    print(f"Result: {'✅ Logged out successfully' if logout_result else '❌ Logout failed'}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_booking_flow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
