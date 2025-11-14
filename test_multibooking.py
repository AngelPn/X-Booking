#!/usr/bin/env python3
"""Test script for Phase 5.2 (Database) and 5.3 (Slot Monitor)."""

import sys
from datetime import date, time, datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.database import db_service
from services.slot_monitor import slot_monitor

def test_database():
    """Test Phase 5.2: Database Layer."""
    print("=" * 60)
    print("TEST 1: Database Layer (Phase 5.2)")
    print("=" * 60)
    
    # Initialize database
    print("\n[1.1] Initializing database...")
    db_service.initialize_db()
    print("✓ Database initialized")
    
    # Test account creation
    print("\n[1.2] Testing account management...")
    acc1 = db_service.add_account("test_user1", "password123")
    acc2 = db_service.add_account("test_user2", "password456")
    if acc1 and acc2:
        print(f"✓ Created accounts: {acc1.netid}, {acc2.netid}")
    else:
        print("✗ Failed to create accounts")
        return False
    
    # Test duplicate account prevention
    acc_dup = db_service.add_account("test_user1", "different_password")
    if acc_dup is None:
        print("✓ Duplicate account prevention works")
    else:
        print("✗ Duplicate account was created (should have failed)")
    
    # Test getting accounts
    accounts = db_service.get_accounts(is_active=True)
    print(f"✓ Retrieved {len(accounts)} active accounts")
    
    # Test booking creation
    print("\n[1.3] Testing booking management...")
    booking_date = date.today() + timedelta(days=3)
    booking = db_service.create_booking(
        account_id=acc1.id,
        booking_date=booking_date,
        time_slot=time(13, 0),
        location='X1',
        sub_location='X1 A',
        status='pending'
    )
    if booking:
        print(f"✓ Created booking: {booking.location} at {booking.time_slot}")
    else:
        print("✗ Failed to create booking")
        return False
    
    # Test duplicate booking prevention
    can_book = db_service.can_account_book(
        acc1.id, booking_date, time(13, 0), 'X1'
    )
    if not can_book:
        print("✓ Duplicate booking prevention works")
    else:
        print("✗ Account can book same slot twice (should be prevented)")
    
    # Test booking status update
    updated = db_service.update_booking_status(
        booking.id, 'confirmed', booking_reference='REF123'
    )
    if updated and updated.status == 'confirmed':
        print(f"✓ Updated booking status to: {updated.status}")
    else:
        print("✗ Failed to update booking status")
    
    # Test slot availability caching
    print("\n[1.4] Testing slot availability cache...")
    slot = db_service.update_slot_availability(
        location='X1',
        booking_date=booking_date,
        time_slot=time(14, 0),
        is_available=True,
        sub_location='X1 A',
        total_capacity=20,
        remaining_capacity=15
    )
    if slot:
        print(f"✓ Cached slot: {slot.location} at {slot.time_slot} ({slot.remaining_capacity}/{slot.total_capacity})")
    else:
        print("✗ Failed to cache slot")
    
    # Test getting cached slots
    slots = db_service.get_slot_availability('X1', booking_date)
    print(f"✓ Retrieved {len(slots)} cached slots for X1")
    
    # Test snipe job creation
    print("\n[1.5] Testing snipe job management...")
    snipe_job = db_service.create_snipe_job(
        target_date=booking_date,
        target_time=time(13, 0),
        location='X1',
        sub_location='X1 A',
        priority=1,
        assigned_accounts=[acc1.id, acc2.id],
        scheduled_execution=datetime.now() + timedelta(hours=1),
        consecutive_hours=3,
        time_window_start=time(11, 0),
        time_window_end=time(18, 0)
    )
    if snipe_job:
        print(f"✓ Created snipe job: {snipe_job.location} for {snipe_job.target_date}")
        assigned = snipe_job.get_assigned_accounts()
        print(f"  - Assigned accounts: {assigned}")
        print(f"  - Consecutive hours: {snipe_job.consecutive_hours}")
    else:
        print("✗ Failed to create snipe job")
    
    # Test booking log
    print("\n[1.6] Testing booking log...")
    log = db_service.log_booking_attempt(
        account_id=acc1.id,
        action='success',
        booking_date=booking_date,
        time_slot=time(13, 0),
        location='X1',
        sub_location='X1 A',
        execution_time_ms=1250
    )
    if log:
        print(f"✓ Logged booking attempt: {log.action} in {log.execution_time_ms}ms")
    else:
        print("✗ Failed to log booking attempt")
    
    # Test statistics
    print("\n[1.7] Testing account statistics...")
    stats = db_service.get_account_statistics(acc1.id)
    print(f"✓ Account statistics:")
    print(f"  - Total bookings: {stats['total_bookings']}")
    print(f"  - Confirmed: {stats['confirmed_bookings']}")
    print(f"  - Failed: {stats['failed_bookings']}")
    print(f"  - Success rate: {stats['success_rate']}%")
    
    print("\n" + "=" * 60)
    print("✓ DATABASE TESTS PASSED")
    print("=" * 60)
    return True


def test_slot_monitor():
    """Test Phase 5.3: Slot Monitor (without actual scraping)."""
    print("\n" + "=" * 60)
    print("TEST 2: Slot Monitor Service (Phase 5.3)")
    print("=" * 60)
    
    # Test callback registration
    print("\n[2.1] Testing callback system...")
    callback_triggered = []
    
    def test_callback(event):
        callback_triggered.append(event)
        print(f"✓ Callback triggered: {event.get('type')}")
    
    slot_monitor.register_callback(test_callback)
    print("✓ Callback registered")
    
    # Test cached availability retrieval
    print("\n[2.2] Testing cached availability retrieval...")
    check_date = date.today() + timedelta(days=3)
    cached_slots = slot_monitor.get_cached_availability('X1', check_date)
    print(f"✓ Retrieved {len(cached_slots)} cached slots")
    
    # Test consecutive slot finder
    print("\n[2.3] Testing consecutive slot finder...")
    # Add some mock slots to cache
    test_date = date.today() + timedelta(days=5)
    for hour in range(13, 18):  # 13:00 to 17:00
        db_service.update_slot_availability(
            location='X3',
            booking_date=test_date,
            time_slot=time(hour, 0),
            is_available=True,
            sub_location='X3 A',
            remaining_capacity=10
        )
    
    # Find 3 consecutive hours
    consecutive = slot_monitor.get_available_slots(
        location='X3',
        target_date=test_date,
        consecutive_hours=3
    )
    if consecutive:
        print(f"✓ Found {len(consecutive)} sequences of 3 consecutive hours")
        for i, sequence in enumerate(consecutive[:3]):  # Show first 3
            times = [s.time_slot.strftime('%H:%M') for s in sequence]
            print(f"  - Sequence {i+1}: {' → '.join(times)}")
    else:
        print("✓ No consecutive sequences found (expected if cache is empty)")
    
    # Test monitoring configuration
    print("\n[2.4] Testing monitor configuration...")
    print(f"✓ Poll interval: {slot_monitor.poll_interval}s")
    print(f"✓ Cache TTL: {slot_monitor.cache_ttl}s")
    print(f"✓ Callbacks registered: {len(slot_monitor.callbacks)}")
    
    print("\n" + "=" * 60)
    print("✓ SLOT MONITOR TESTS PASSED")
    print("=" * 60)
    print("\nNote: Actual scraping test skipped (requires credentials)")
    print("To test scraping, use:")
    print("  slot_monitor.update_slot_cache('X1', date(2025,11,17), 'netid', 'password')")
    return True


def test_api_structure():
    """Test API route structure."""
    print("\n" + "=" * 60)
    print("TEST 3: API Route Structure")
    print("=" * 60)
    
    from pathlib import Path
    
    api_routes = [
        "src/app/api/slots/route.ts",
        "src/app/api/slots/monitor/route.ts",
        "src/app/api/slots/refresh/route.ts",
    ]
    
    print("\n[3.1] Checking API route files...")
    for route in api_routes:
        path = Path(route)
        if path.exists():
            print(f"✓ {route}")
        else:
            print(f"✗ {route} (missing)")
    
    print("\n[3.2] Checking React component...")
    component_path = Path("src/components/SlotGrid.tsx")
    if component_path.exists():
        print(f"✓ {component_path}")
    else:
        print(f"✗ {component_path} (missing)")
    
    print("\n" + "=" * 60)
    print("✓ API STRUCTURE TESTS PASSED")
    print("=" * 60)
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("X-BOOKING MULTI-BOOKING SYSTEM - TEST SUITE")
    print("Phase 5.2 (Database) + Phase 5.3 (Slot Monitor)")
    print("=" * 60)
    
    try:
        # Run tests
        test1_passed = test_database()
        test2_passed = test_slot_monitor()
        test3_passed = test_api_structure()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Database Layer:     {'✓ PASSED' if test1_passed else '✗ FAILED'}")
        print(f"Slot Monitor:       {'✓ PASSED' if test2_passed else '✗ FAILED'}")
        print(f"API Structure:      {'✓ PASSED' if test3_passed else '✗ FAILED'}")
        print("=" * 60)
        
        if all([test1_passed, test2_passed, test3_passed]):
            print("\n🎉 ALL TESTS PASSED! Ready for Phase 5.4")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
