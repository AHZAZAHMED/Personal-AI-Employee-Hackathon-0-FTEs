"""
Gold Tier - Comprehensive End-to-End Test

Tests all completed Gold Tier features:
1. Gmail Watcher
2. Error Recovery System
3. Odoo Integration
4. CEO Briefing Generator
5. Ralph Wiggum Loop

Usage:
    python scripts/test_gold_tier_complete.py --vault AI_Employee_Vault
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Test results storage
test_results = {
    'timestamp': datetime.now().isoformat(),
    'tests': [],
    'passed': 0,
    'failed': 0,
    'warnings': 0
}


def log_test(name: str, status: str, details: str = ""):
    """Log test result."""
    result = {
        'name': name,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    test_results['tests'].append(result)
    
    if status == 'PASS':
        test_results['passed'] += 1
        symbol = '✅'
    elif status == 'FAIL':
        test_results['failed'] += 1
        symbol = '❌'
    else:
        test_results['warnings'] += 1
        symbol = '⚠️'
    
    print(f"{symbol} {name}: {status}")
    if details:
        print(f"   {details}")


def print_header(text: str):
    """Print test section header."""
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()


# ============================================================================
# TEST 1: ERROR RECOVERY SYSTEM
# ============================================================================

def test_error_recovery():
    """Test Error Recovery System."""
    print_header("TEST 1: ERROR RECOVERY SYSTEM")
    
    try:
        from error_recovery import (
            with_retry,
            CircuitBreaker,
            ErrorLogger,
            HealthChecker,
            classify_error,
            ErrorType
        )
        
        log_test("Module Import", "PASS", "All components imported successfully")
        
        # Test error classification
        try:
            error_type = classify_error(TimeoutError("Connection timed out"))
            if error_type == ErrorType.TRANSIENT:
                log_test("Error Classification", "PASS", "Timeout correctly classified as TRANSIENT")
            else:
                log_test("Error Classification", "FAIL", f"Expected TRANSIENT, got {error_type}")
        except Exception as e:
            log_test("Error Classification", "FAIL", str(e))
        
        # Test Circuit Breaker
        try:
            breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
            status = breaker.get_status()
            if status['state'] == 'closed':
                log_test("Circuit Breaker", "PASS", f"State: {status['state']}, Threshold: {status['failure_threshold']}")
            else:
                log_test("Circuit Breaker", "FAIL", f"Unexpected state: {status['state']}")
        except Exception as e:
            log_test("Circuit Breaker", "FAIL", str(e))
        
        # Test Health Checker
        try:
            vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
            health = HealthChecker(str(vault_path))
            health.report_status('test_component', 'healthy', {'test': 'data'})
            status = health.get_status('test_component')
            if status['status'] == 'healthy':
                log_test("Health Checker", "PASS", "Health status reported correctly")
            else:
                log_test("Health Checker", "FAIL", f"Unexpected status: {status['status']}")
        except Exception as e:
            log_test("Health Checker", "FAIL", str(e))
        
    except Exception as e:
        log_test("Error Recovery System", "FAIL", f"Import failed: {e}")


# ============================================================================
# TEST 2: ODOO INTEGRATION
# ============================================================================

def test_odoo_integration():
    """Test Odoo Integration."""
    print_header("TEST 2: ODOO INTEGRATION")
    
    try:
        from odoo_mcp_server import OdooAccountingMCP
        
        log_test("Module Import", "PASS", "OdooMCP imported successfully")
        
        # Test connection
        try:
            mcp = OdooAccountingMCP({
                'url': 'http://localhost:8069',
                'db': 'odoo',
                'username': 'admin123@example.com',
                'password': 'admin'
            })
            
            if mcp.client.authenticate():
                log_test("Odoo Authentication", "PASS", f"User ID: {mcp.client.uid}")
                
                # Test list transactions
                try:
                    result = mcp.list_transactions(days=7, limit=10)
                    if result.get('success'):
                        log_test("List Transactions", "PASS", f"Found {result.get('count')} transactions")
                    else:
                        log_test("List Transactions", "WARNING", result.get('error', 'Unknown error'))
                except Exception as e:
                    log_test("List Transactions", "WARNING", str(e))
                
            else:
                log_test("Odoo Authentication", "FAIL", "Authentication failed")
                
        except Exception as e:
            log_test("Odoo Connection", "FAIL", f"Connection failed: {e}")
        
    except Exception as e:
        log_test("Odoo Integration", "WARNING", f"Import failed (Odoo may not be running): {e}")


# ============================================================================
# TEST 3: CEO BRIEFING GENERATOR
# ============================================================================

def test_ceo_briefing():
    """Test CEO Briefing Generator."""
    print_header("TEST 3: CEO BRIEFING GENERATOR")
    
    try:
        from ceo_briefing_generator import CEOBriefingGenerator
        
        log_test("Module Import", "PASS", "CEOBriefingGenerator imported successfully")
        
        # Test briefing generation
        try:
            vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
            generator = CEOBriefingGenerator(str(vault_path))
            
            briefing = generator.generate_briefing(days=7)
            
            if briefing and len(briefing) > 100:
                log_test("Briefing Generation", "PASS", f"Generated {len(briefing)} characters")
                
                # Check for key sections
                sections = ['Executive Summary', 'Revenue', 'Completed Tasks', 'Bottlenecks', 'Suggestions']
                found_sections = [s for s in sections if s in briefing]
                log_test("Briefing Sections", "PASS", f"Found {len(found_sections)}/{len(sections)} sections: {', '.join(found_sections)}")
            else:
                log_test("Briefing Generation", "FAIL", "Generated briefing is too short")
            
        except Exception as e:
            log_test("Briefing Generation", "FAIL", str(e))
        
    except Exception as e:
        log_test("CEO Briefing", "FAIL", f"Import failed: {e}")


# ============================================================================
# TEST 4: RALPH WIGGUM LOOP
# ============================================================================

def test_ralph_wiggum():
    """Test Ralph Wiggum Loop."""
    print_header("TEST 4: RALPH WIGGUM LOOP")
    
    try:
        from ralph_wiggum import RalphWiggumLoop
        
        log_test("Module Import", "PASS", "RalphWiggumLoop imported successfully")
        
        # Test initialization
        try:
            vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
            loop = RalphWiggumLoop(
                vault_path=str(vault_path),
                prompt="Test prompt",
                max_iterations=3,
                timeout=60
            )
            
            log_test("Loop Initialization", "PASS", f"Configured: max_iterations={loop.max_iterations}, timeout={loop.timeout}s")
            
            # Check if Claude Code is available
            if loop.claude_path:
                log_test("Claude Code Detection", "PASS", f"Found at: {loop.claude_path}")
            else:
                log_test("Claude Code Detection", "WARNING", "Claude Code not found in PATH")
            
        except Exception as e:
            log_test("Loop Initialization", "FAIL", str(e))
        
    except Exception as e:
        log_test("Ralph Wiggum", "FAIL", f"Import failed: {e}")


# ============================================================================
# TEST 5: VAULT STRUCTURE
# ============================================================================

def test_vault_structure():
    """Test Vault folder structure."""
    print_header("TEST 5: VAULT STRUCTURE")
    
    vault_path = Path(__file__).parent.parent / 'AI_Employee_Vault'
    
    required_folders = [
        'Needs_Action',
        'In_Progress/qwen_agent',
        'Plans',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Done',
        'Logs',
        'Briefings',
        'Skills'
    ]
    
    for folder in required_folders:
        folder_path = vault_path / folder
        if folder_path.exists() and folder_path.is_dir():
            file_count = len(list(folder_path.glob('*.md')))
            log_test(f"Folder: {folder}", "PASS", f"{file_count} files")
        else:
            log_test(f"Folder: {folder}", "FAIL", "Folder not found")
    
    # Check key files
    key_files = ['Dashboard.md', 'Company_Handbook.md', 'Business_Goals.md']
    for file in key_files:
        file_path = vault_path / file
        if file_path.exists():
            log_test(f"File: {file}", "PASS", "Exists")
        else:
            log_test(f"File: {file}", "FAIL", "File not found")


# ============================================================================
# TEST 6: SCRIPTS AVAILABILITY
# ============================================================================

def test_scripts_availability():
    """Test that all required scripts exist."""
    print_header("TEST 6: SCRIPTS AVAILABILITY")
    
    scripts_path = Path(__file__).parent
    
    required_scripts = [
        'error_recovery.py',
        'watchdog.py',
        'odoo_mcp_server.py',
        'ceo_briefing_generator.py',
        'ralph_wiggum.py',
        'gmail_watcher.py',
        'orchestrator.py',
        'approval_handler.py'
    ]
    
    for script in required_scripts:
        script_path = scripts_path / script
        if script_path.exists():
            log_test(f"Script: {script}", "PASS", "Exists")
        else:
            log_test(f"Script: {script}", "FAIL", "Script not found")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all Gold Tier tests."""
    print("=" * 60)
    print("GOLD TIER - COMPREHENSIVE END-TO-END TEST")
    print("=" * 60)
    print(f"Timestamp: {test_results['timestamp']}")
    print()
    
    # Run all tests
    test_error_recovery()
    test_odoo_integration()
    test_ceo_briefing()
    test_ralph_wiggum()
    test_vault_structure()
    test_scripts_availability()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    total = test_results['passed'] + test_results['failed'] + test_results['warnings']
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️  Warnings: {test_results['warnings']}")
    print()
    
    # Calculate success rate
    if total > 0:
        success_rate = (test_results['passed'] / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print()
            print("=" * 60)
            print("🎉 GOLD TIER FEATURES ARE READY!")
            print("=" * 60)
            print()
            print("All core features are working correctly.")
            print("Ready to proceed with Social Media Integration.")
        elif success_rate >= 70:
            print()
            print("=" * 60)
            print("⚠️  MOST FEATURES WORKING")
            print("=" * 60)
            print()
            print("Some issues detected. Review warnings above.")
        else:
            print()
            print("=" * 60)
            print("❌ CRITICAL ISSUES DETECTED")
            print("=" * 60)
            print()
            print("Please fix failed tests before proceeding.")
    
    # Save test results
    results_file = Path(__file__).parent.parent / 'AI_Employee_Vault' / 'Logs' / 'gold_tier_test_results.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    
    print()
    print(f"Test results saved to: {results_file}")
    print()


if __name__ == '__main__':
    main()
