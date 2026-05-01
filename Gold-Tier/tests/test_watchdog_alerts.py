"""
Test Watcher Watchdog AlertManager Integration

Verifies that the watchdog sends Slack alerts when watchers fail.
"""

import sys
import time
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from watcher_watchdog import WatcherWatchdog
from alerting import AlertManager, AlertSeverity


def test_watchdog_startup_alert():
    """Test that watchdog sends startup notification."""
    print("\n" + "="*60)
    print("TEST 1: Watchdog Startup Alert")
    print("="*60)

    vault_path = "AI_Employee_Vault"

    print("\nInitializing watchdog (should send startup alert)...")
    watchdog = WatcherWatchdog(
        vault_path=vault_path,
        check_interval=60,
        max_heartbeat_age=300,
        alert_threshold=3
    )

    print("\n[OK] Watchdog initialized")
    print("Check your Slack #all-ai-employee channel for startup notification")
    print("Expected: INFO alert 'Watcher Watchdog Started'")

    return True


def test_manual_alert():
    """Test sending a manual alert through AlertManager."""
    print("\n" + "="*60)
    print("TEST 2: Manual Alert Test")
    print("="*60)

    vault_path = "AI_Employee_Vault"
    alert_manager = AlertManager(vault_path=vault_path)

    print("\nSending test alert...")
    result = alert_manager.send_alert(
        severity=AlertSeverity.WARNING,
        title="Watchdog Integration Test",
        message="This is a test alert to verify the watchdog AlertManager integration is working correctly.",
        details={'test': True, 'component': 'watchdog'}
    )

    if result:
        print("[OK] Alert sent successfully")
        print("Check your Slack #all-ai-employee channel")
        print("Expected: WARNING alert 'Watchdog Integration Test'")
        return True
    else:
        print("[FAIL] Alert failed to send")
        return False


def test_simulated_watcher_failure():
    """Test alert when simulating a watcher failure."""
    print("\n" + "="*60)
    print("TEST 3: Simulated Watcher Failure Alert")
    print("="*60)

    vault_path = "AI_Employee_Vault"

    # Create watchdog with very short intervals for testing
    print("\nInitializing watchdog with short intervals...")
    watchdog = WatcherWatchdog(
        vault_path=vault_path,
        check_interval=5,  # Check every 5 seconds
        max_heartbeat_age=10,  # Consider stale after 10 seconds
        alert_threshold=2  # Alert after 2 failures (faster for testing)
    )

    print("\nWatchdog will check for heartbeats every 5 seconds")
    print("If no watchers are running, it will detect failures")
    print("After 2 consecutive failures, it will send a CRITICAL alert")
    print("\nRunning for 15 seconds...")

    # Run for 15 seconds (3 checks)
    start_time = time.time()
    check_count = 0

    while time.time() - start_time < 15:
        results = watchdog.check_all_watchers()
        check_count += 1

        healthy = sum(1 for h in results.values() if h)
        total = len(results)
        print(f"  Check {check_count}: {healthy}/{total} watchers healthy")

        time.sleep(5)

    print("\n[OK] Test completed")
    print("Check your Slack #all-ai-employee channel")
    print("Expected: CRITICAL alerts for unhealthy watchers (if no watchers running)")

    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WATCHDOG ALERTMANAGER INTEGRATION TEST")
    print("="*60)
    print("\nThis test verifies that the watchdog sends Slack alerts")
    print("Make sure SLACK_WEBHOOK_URL is set in your .env file")

    input("\nPress Enter to start tests...")

    results = []

    # Test 1: Startup alert
    try:
        results.append(("Startup Alert", test_watchdog_startup_alert()))
    except Exception as e:
        print(f"[FAIL] Test 1 failed: {e}")
        results.append(("Startup Alert", False))

    time.sleep(2)

    # Test 2: Manual alert
    try:
        results.append(("Manual Alert", test_manual_alert()))
    except Exception as e:
        print(f"[FAIL] Test 2 failed: {e}")
        results.append(("Manual Alert", False))

    time.sleep(2)

    # Test 3: Simulated failure (optional - takes 15 seconds)
    print("\n" + "="*60)
    response = input("Run simulated watcher failure test? (takes 15 seconds) [y/N]: ")
    if response.lower() == 'y':
        try:
            results.append(("Simulated Failure", test_simulated_watcher_failure()))
        except Exception as e:
            print(f"[FAIL] Test 3 failed: {e}")
            results.append(("Simulated Failure", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\nPassed: {passed_count}/{total_count}")

    if passed_count == total_count:
        print("\n[SUCCESS] All tests passed!")
        print("Check your Slack #all-ai-employee channel to verify alerts were received")
    else:
        print("\n[WARNING] Some tests failed")
        print("Check your .env file for SLACK_WEBHOOK_URL")

    print("="*60)


if __name__ == '__main__':
    main()
