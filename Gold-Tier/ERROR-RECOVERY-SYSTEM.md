# Error Recovery System - Gold Tier

**Reusable error handling for all AI Employee watchers**

---

## Overview

The Error Recovery System provides **production-grade reliability** for all AI Employee watchers (Gmail, Facebook, Instagram, Twitter, etc.).

**Features:**
- ✅ **Retry Logic** with exponential backoff
- ✅ **Circuit Breaker** to prevent cascading failures
- ✅ **Error Classification** (retry vs alert human)
- ✅ **90-Day Error Log Retention**
- ✅ **Health Monitoring**
- ✅ **Watchdog Process** for auto-restart

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ERROR RECOVERY SYSTEM                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  error_recovery  │     │    watchdog.py   │     │  Updated Watchers│
│     .py          │     │                  │     │                  │
│                  │     │  Monitors all    │     │  - Gmail         │
│  - Retry logic   │◀────│  watchers        │────▶│  - Facebook      │
│  - Circuit       │     │                  │     │  - Instagram     │
│    Breaker       │     │  - Auto-restart  │     │  - Twitter       │
│  - Error Logger  │     │  - Health check  │     │                  │
│  - Health Check  │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## Components

### **1. Error Recovery Module** (`error_recovery.py`)

**Purpose:** Reusable error handling for any watcher

**Key Features:**
- `@with_retry` decorator
- `CircuitBreaker` class
- `ErrorLogger` class
- `HealthChecker` class
- `classify_error()` function

---

### **2. Watchdog Process** (`watchdog.py`)

**Purpose:** Monitor and restart failed watchers

**Key Features:**
- Auto-restart on crash
- Rate limiting (max restarts per hour)
- Health status reporting
- PID file management

---

## Usage Examples

### **Example 1: Add Retry to Any Function**

```python
from error_recovery import with_retry

@with_retry(max_attempts=3, base_delay=1, max_delay=60)
def check_gmail():
    """Check Gmail for new messages."""
    # Your code here
    # Will automatically retry on failure
    pass
```

**What happens:**
- Tries up to 3 times
- Waits 1s, 2s, 4s between attempts (exponential backoff)
- Max 60s delay
- Doesn't retry auth/logic errors

---

### **Example 2: Use Circuit Breaker**

```python
from error_recovery import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)

def check_service():
    try:
        with breaker:
            # Your code here
            return api_call()
    except Exception as e:
        return "Service unavailable"
```

**What happens:**
- Opens after 5 failures
- Waits 5 minutes before testing again
- Prevents cascading failures

---

### **Example 3: Log Errors with 90-Day Retention**

```python
from error_recovery import ErrorLogger

error_logger = ErrorLogger('AI_Employee_Vault', retention_days=90)

try:
    check_gmail()
except Exception as e:
    error_logger.log_error(
        'gmail_watcher',
        e,
        context={'action': 'check_messages'},
        severity='ERROR'
    )
```

**What happens:**
- Logs to `AI_Employee_Vault/Logs/errors/YYYY-MM-DD.jsonl`
- Auto-deletes logs older than 90 days
- Structured JSON format

---

### **Example 4: Report Health Status**

```python
from error_recovery import HealthChecker

health = HealthChecker('AI_Employee_Vault')

# Report healthy
health.report_status('gmail_watcher', 'healthy')

# Report error
health.report_error('gmail_watcher', exception, recoverable=True)

# Get status
status = health.get_status('gmail_watcher')
```

**Health States:**
- `healthy` - Working normally
- `degraded` - Having issues but recoverable
- `unhealthy` - Not working, needs attention

---

### **Example 5: Run Watchdog**

```bash
# Monitor all watchers
python scripts/watchdog.py --vault AI_Employee_Vault

# Monitor specific watchers
python scripts/watchdog.py --vault AI_Employee_Vault \
  --watchers gmail_watcher orchestrator
```

**What happens:**
- Starts all watchers
- Monitors every 60 seconds
- Auto-restarts failed watchers
- Rate limits restarts (5/hour max)

---

## Error Classification

The system automatically classifies errors:

| Error Type | Examples | Retry? | Strategy |
|------------|----------|--------|----------|
| **TRANSIENT** | Timeout, network, rate limit | ✅ Yes | Exponential backoff |
| **AUTH** | Token expired, 401, 403 | ❌ No | Alert human |
| **LOGIC** | Parse error, missing field | ❌ No | Fix code |
| **SYSTEM** | Disk full, file locked | ⚠️ Immediate | Retry now |
| **UNKNOWN** | Other errors | ⚠️ Cautious | Retry with limits |

---

## Integration with Existing Watchers

### **Gmail Watcher** (Already Updated)

```python
# In gmail_watcher.py

from error_recovery import (
    with_retry,
    create_error_recovery
)

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, ...):
        super().__init__(vault_path, ...)
        
        # Initialize error recovery
        self.error_logger, self.health_checker, self.circuit_breaker = \
            create_error_recovery(vault_path)
    
    @with_retry(max_attempts=3, base_delay=1)
    def _authenticate(self):
        """Authenticate with retry logic."""
        # Your code here
```

---

### **Future: Facebook/Instagram/Twitter Watchers**

```python
# Same pattern for all social media watchers

from error_recovery import with_retry, create_error_recovery

class FacebookWatcher(BaseWatcher):
    def __init__(self, vault_path: str, ...):
        super().__init__(vault_path, ...)
        self.error_logger, self.health_checker, self.circuit_breaker = \
            create_error_recovery(vault_path)
    
    @with_retry(max_attempts=3, base_delay=2)
    def check_facebook():
        # Your code here
```

**One pattern, works for everything!**

---

## Configuration

### **Retry Settings**

```python
@with_retry(
    max_attempts=3,      # Number of retries
    base_delay=1.0,      # Initial delay (seconds)
    max_delay=60.0       # Maximum delay
)
```

**Exponential backoff formula:**
```
delay = min(base_delay * 2^(attempt-1), max_delay)
```

**Example:**
- Attempt 1: 1s
- Attempt 2: 2s
- Attempt 3: 4s
- Max: 60s

---

### **Circuit Breaker Settings**

```python
breaker = CircuitBreaker(
    failure_threshold=5,    # Failures before opening
    recovery_timeout=300    # Seconds to wait before testing
)
```

**States:**
1. **CLOSED** - Normal operation
2. **OPEN** - Failing, don't try
3. **HALF_OPEN** - Testing recovery

---

### **Watchdog Settings**

```python
watcher_config = WatcherConfig(
    name='Gmail Watcher',
    script='gmail_watcher.py',
    args=['--vault', 'AI_Employee_Vault'],
    check_interval=60,         # How often to check
    restart_delay=5,           # Wait before restart
    max_restarts_per_hour=5    # Rate limit
)
```

---

## File Structure

```
Gold-Tier/scripts/
├── error_recovery.py          ← Core error handling
├── watchdog.py                ← Process monitor
├── gmail_watcher.py           ← Uses error_recovery
├── facebook_watcher.py        ← Uses error_recovery
├── instagram_watcher.py       ← Uses error_recovery
└── twitter_watcher.py         ← Uses error_recovery

Gold-Tier/AI_Employee_Vault/Logs/
├── errors/
│   ├── 2026-03-21.jsonl      ← Daily error logs
│   └── 2026-03-22.jsonl
├── pids/
│   └── gmail_watcher.pid     ← Process IDs
├── health_status.json         ← Current health
├── watchdog.log              ← Watchdog logs
└── ...
```

---

## Testing

### **Test Error Recovery**

```bash
cd E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier

# Run error recovery tests
python scripts/error_recovery.py
```

**Expected Output:**
```
Service check: Success!
Circuit breaker test: Success!
Safe execute: Success!
Health status: {...}
```

---

### **Test Watchdog**

```bash
# Start watchdog (monitors all watchers)
python scripts/watchdog.py --vault AI_Employee_Vault

# Check logs
type AI_Employee_Vault\Logs\watchdog.log
```

---

## Troubleshooting

### **Problem: Watcher keeps restarting**

**Solution:** Check error logs
```bash
type AI_Employee_Vault\Logs\errors\*.jsonl | findstr "gmail_watcher"
```

---

### **Problem: Circuit breaker won't close**

**Solution:** Check what's failing
```python
from error_recovery import CircuitBreaker

breaker = CircuitBreaker()
print(breaker.get_status())
```

---

### **Problem: Watchdog not starting watchers**

**Solution:** Check permissions
```bash
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\Create-SilverTier-Tasks.ps1
```

---

## Best Practices

1. **Always use `@with_retry` for external APIs**
   - Gmail, Facebook, Instagram, Twitter, etc.
   - Prevents transient failures

2. **Use circuit breakers for critical services**
   - Prevents cascading failures
   - Gives services time to recover

3. **Log all errors with context**
   - Helps debugging
   - 90-day retention for audit

4. **Monitor health status**
   - Check `AI_Employee_Vault/Logs/health_status.json`
   - Alert on `unhealthy` status

5. **Rate limit restarts**
   - Prevents restart loops
   - 5 restarts/hour max

---

## Gold Tier Progress

| Feature | Status | Files |
|---------|--------|-------|
| ✅ Error Recovery Module | COMPLETE | `error_recovery.py` |
| ✅ Watchdog Process | COMPLETE | `watchdog.py` |
| ✅ Gmail Watcher Updated | COMPLETE | `gmail_watcher.py` |
| ✅ Facebook Watcher | COMPLETE | Uses error_recovery |
| ✅ Instagram Watcher | COMPLETE | Uses error_recovery |
| ✅ Twitter Watcher | COMPLETE | Uses error_recovery |

---

## Next Steps

Now that error recovery is complete:

1. ✅ **Error Recovery Module** - Working
2. ✅ **Watchdog Process** - Working
3. ✅ **Gmail Watcher** - Updated with error recovery

**Next Gold Tier features:**
- Weekly CEO Briefing
- Ralph Wiggum Loop
- Social Media Integrations

All will use the same error recovery system!

---

*Error Recovery System v1.0 | Gold Tier | AI Employee Hackathon 0*
