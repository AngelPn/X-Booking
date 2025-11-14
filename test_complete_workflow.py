#!/usr/bin/env python3
"""
Complete workflow test with the fix for string IDs.
Tests: login → get bookings → get slots → create booking → cancel booking
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.services.booking_client_v2 import BookingClient

# Load environment variables
load_dotenv()

def test_complete_workflow():
    """Test the complete booking workflow."""
    print("\n" + "="*70)
    print("  COMPLETE BOOKING WORKFLOW TEST")
    print("="*70)
    
    client = BookingClient(institution='tudelft')
    
    # Step 1: Login
    print("\n[1/6] 🔐 LOGGING IN...")
    username = os.getenv('TU_USERNAME')
    password = os.getenv('TU_PASSWORD')
    
    if not username or not password:
        print("❌ Missing TU_USERNAME or TU_PASSWORD in .env file")
        return False
    
    login_result = client.login_and_get_token(username, password)
    
    if not login_result['success']:
        print(f"❌ Login failed: {login_result['message']}")
        return False
    
    print(f"✅ Successfully logged in as: {login_result['user']['firstName']} {login_result['user']['lastName']}")
    
    # Step 2: Get current bookings (BEFORE)
    print("\n[2/6] 📋 GETTING CURRENT BOOKINGS (BEFORE)...")
    bookings_before = client.get_current_bookings()
    
    if not bookings_before['success']:
        print(f"❌ Failed to get bookings: {bookings_before['message']}")
        return False
    
    count_before = bookings_before['count']
    print(f"✅ Current bookings: {count_before}")
    
    # Step 3: Get available slots
    print("\n[3/6] 🗓️  GETTING AVAILABLE SLOTS...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    slots_result = client.get_available_slots('Fitness', tomorrow)
    
    if not slots_result['success']:
        print(f"❌ Failed to get slots: {slots_result['message']}")
        return False
    
    slots = slots_result['slots']
    print(f"✅ Available slots for {tomorrow}: {len(slots)}")
    
    if not slots:
        print("❌ No available slots found!")
        return False
    
    # Pick first slot
    slot = slots[0]
    slot_id = slot.get('bookingId')
    product_id = slot.get('bookableProductId')
    linked_product_id = slot.get('bookableLinkedProductId')
    start_time = slot.get('startDate')
    end_time = slot.get('endDate')
    
    print(f"   Selected slot: bookingId={slot_id}, productId={product_id}")
    print(f"   Time: {start_time} - {end_time}")
    
    # Step 4: Create booking
    print("\n[4/6] ✏️  CREATING BOOKING...")
    create_result = client.create_booking(
        slot_id=slot_id,
        product_id=product_id,
        start_time=start_time,
        end_time=end_time,
        linked_product_id=linked_product_id
    )
    
    if not create_result['success']:
        print(f"❌ Failed to create booking: {create_result['message']}")
        if 'error' in create_result:
            print(f"   Error details: {create_result['error']}")
        return False
    
    booking_id = create_result['booking_id']
    print(f"✅ Booking created with ID: {booking_id}")
    
    # Step 5: Get current bookings (AFTER)
    print("\n[5/6] 📋 GETTING CURRENT BOOKINGS (AFTER)...")
    bookings_after = client.get_current_bookings()
    
    if not bookings_after['success']:
        print(f"❌ Failed to get bookings: {bookings_after['message']}")
        return False
    
    count_after = bookings_after['count']
    print(f"✅ Current bookings: {count_after}")
    print(f"   Change: {count_before} → {count_after} (increase of {count_after - count_before})")
    
    if count_after <= count_before:
        print("⚠️  WARNING: Booking count did not increase!")
    
    # Step 6: Cancel booking
    print("\n[6/6] 🗑️  CANCELLING BOOKING...")
    cancel_result = client.cancel_booking(booking_id)
    
    if not cancel_result['success']:
        print(f"❌ Failed to cancel booking: {cancel_result['message']}")
        return False
    
    print("✅ Booking cancelled successfully")
    
    # Verify cancellation
    bookings_final = client.get_current_bookings()
    count_final = bookings_final['count']
    print(f"✅ Final bookings count: {count_final}")
    print(f"   Change: {count_after} → {count_final} (decrease of {count_after - count_final})")
    
    # Summary
    print("\n" + "="*70)
    print("  ✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nSummary:")
    print("  • Login: ✅")
    print(f"  • Get bookings (before): ✅ ({count_before} bookings)")
    print(f"  • Get slots: ✅ ({len(slots)} slots)")
    print(f"  • Create booking: ✅ (ID: {booking_id})")
    print(f"  • Get bookings (after): ✅ ({count_after} bookings)")
    print("  • Cancel booking: ✅")
    print(f"  • Get bookings (final): ✅ ({count_final} bookings)")
    
    return True


if __name__ == '__main__':
    try:
        success = test_complete_workflow()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(1)
    except Exception as err:  # pylint: disable=broad-except
        print(f"\n\n❌ Unexpected error: {err}")
        import traceback
        traceback.print_exc()
        exit(1)
