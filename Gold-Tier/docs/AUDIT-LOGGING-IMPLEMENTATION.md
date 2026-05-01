# Structured Audit Logging Implementation

## Overview

This document describes the structured audit logging system implemented for the AI Employee Gold Tier to meet SOX and GDPR compliance requirements.

## Problem Statement

**From Audit Report (AUDIT-2 BROKEN #3):**
- No correlation IDs to trace Task → Approval → Execution → Result
- Approval handler logs events but NOT who approved
- Skills don't log execution (no audit trail)
- Cannot answer: "Who approved this email?" "Why was this sent?" "When was this executed?"

## Solution Architecture

### 1. Centralized Audit Logger (`scripts/audit_logger.py`)

**Features:**
- Correlation ID generation and tracking
- Structured JSONL logging format
- Thread-safe operations
- Daily log rotation
- Query capabilities by correlation ID
- Compliance report generation

**Key Methods:**
```python
# Generate correlation ID
correlation_id = audit_logger.generate_correlation_id()

# Log task lifecycle
audit_logger.log_task_created(correlation_id, task_type, task_data)
audit_logger.log_task_processing_started(correlation_id, task_id, task_type)
audit_logger.log_task_completed(correlation_id, task_id, result)

# Log approval workflow
audit_logger.log_approval_requested(correlation_id, action_type, details, approval_file)
audit_logger.log_approval_granted(correlation_id, approver, approval_time, action_type, approval_file)
audit_logger.log_approval_rejected(correlation_id, rejector, rejection_time, action_type, approval_file)

# Log action execution
audit_logger.log_action_started(correlation_id, action_type, actor, approver, approval_time)
audit_logger.log_action_completed(correlation_id, action_type, actor, result, approver, approval_time)
audit_logger.log_action_failed(correlation_id, action_type, actor, error, approver, approval_time)

# Skill-specific logging
audit_logger.log_email_sent(correlation_id, to, subject, approver, approval_time, result)
audit_logger.log_payment_processed(correlation_id, amount, recipient, approver, approval_time, result)
audit_logger.log_social_post_published(correlation_id, platform, approver, approval_time, result)
```

### 2. Approval Handler Integration (`scripts/approval_handler.py`)

**Changes:**
- Generates correlation_id when creating approval requests
- Stores correlation_id in approval file frontmatter
- Detects approval time (file modification time when moved to /Approved)
- Logs approval granted/rejected with approver information
- Passes correlation_id, approver, approval_time to executor callback

**Approval File Format:**
```yaml
---
type: approval_request
action: email_send
created: 2026-04-23T10:00:00
status: pending
correlation_id: abc-123-def-456
risk_level: medium
to: client@example.com
subject: Re: Inquiry
---
```

### 3. Orchestrator Integration (`scripts/orchestrator.py`)

**Changes:**
- Generates correlation_id for each task in `process_task()`
- Logs task creation, processing started, completion
- Passes correlation_id to approval handler
- Passes correlation_id, approver, approval_time to skills via executor callback
- Logs task completion with correlation_id

**Flow:**
```
Task Created → correlation_id generated
  ↓
Task Processing Started → logged with correlation_id
  ↓
Approval Requested → logged with correlation_id
  ↓
Human Approves → logged with correlation_id, approver, approval_time
  ↓
Action Executed → logged with correlation_id, approver, approval_time
  ↓
Task Completed → logged with correlation_id
```

### 4. Skills Integration

**Updated Skills:**
- `email_responder/service.py` - send_email() with audit logging
- `linkedin_posting/service.py` - publish_post() with audit logging
- `instagram_posting/service.py` - post_image() with audit logging
- `facebook_posting/service.py` - initialized audit_logger
- `whatsapp/service.py` - initialized audit_logger

**Pattern:**
```python
def action_method(self, params, correlation_id="", approver="", approval_time=""):
    # Log action started
    if correlation_id:
        self.audit_logger.log_action_started(
            correlation_id=correlation_id,
            action_type='action_name',
            actor='skill_name',
            approver=approver,
            approval_time=approval_time,
            metadata={'key': 'value'}
        )
    
    try:
        # Execute action
        result = do_action()
        
        # Log success
        if correlation_id:
            self.audit_logger.log_action_completed(
                correlation_id=correlation_id,
                action_type='action_name',
                actor='skill_name',
                result='success',
                approver=approver,
                approval_time=approval_time
            )
        
        return {"success": True}
    
    except Exception as e:
        # Log failure
        if correlation_id:
            self.audit_logger.log_action_failed(
                correlation_id=correlation_id,
                action_type='action_name',
                actor='skill_name',
                error=str(e),
                approver=approver,
                approval_time=approval_time
            )
        
        return {"success": False, "error": str(e)}
```

### 5. Audit Query Tool (`scripts/audit_query.py`)

**Features:**
- Query all events by correlation ID
- Show complete approval chain
- Generate compliance reports
- Search recent actions by type

**Usage:**
```bash
# Query by correlation ID
python scripts/audit_query.py --vault AI_Employee_Vault --correlation-id abc-123-def

# Show approval chain
python scripts/audit_query.py --vault AI_Employee_Vault --approval-chain abc-123-def

# Generate compliance report
python scripts/audit_query.py --vault AI_Employee_Vault --report --start 2026-04-01 --end 2026-04-23

# Search recent actions
python scripts/audit_query.py --vault AI_Employee_Vault --recent --action email_sent --days 7
```

## Audit Log Format

**Location:** `AI_Employee_Vault/Logs/audit/YYYY-MM-DD_audit.jsonl`

**Format:** JSONL (one JSON object per line)

**Example Entry:**
```json
{
  "timestamp": "2026-04-23T10:30:15.123456",
  "correlation_id": "abc-123-def-456",
  "action": "email_sent",
  "actor": "email_responder_skill",
  "approver": "human",
  "approval_time": "2026-04-23T10:30:00",
  "result": "success",
  "metadata": {
    "to": "client@example.com",
    "subject": "Re: Inquiry about services"
  }
}
```

## Compliance Features

### SOX Compliance
- ✅ Complete audit trail for all financial actions
- ✅ Immutable log files (append-only JSONL)
- ✅ Approval chain tracking (who, when, what, why)
- ✅ Correlation IDs link related events
- ✅ Timestamp on every event

### GDPR Compliance
- ✅ Data processing audit trail
- ✅ Can identify who processed what data
- ✅ Can identify when data was accessed/modified
- ✅ Query capabilities for data subject access requests

## Query Examples

### "Who approved this email?"
```bash
python scripts/audit_query.py --vault AI_Employee_Vault --approval-chain <correlation-id>
```

Output:
```
Action Type: email_send
Timeline:
  1. Approval Requested: 2026-04-23 10:00:00
  2. Approved By: human
     Approved At: 2026-04-23 10:30:00
  3. Executed At: 2026-04-23 10:30:15
     Result: success
```

### "What actions were taken today?"
```bash
python scripts/audit_query.py --vault AI_Employee_Vault --recent --days 1
```

### "Generate monthly compliance report"
```bash
python scripts/audit_query.py --vault AI_Employee_Vault --report --start 2026-04-01 --end 2026-04-30
```

Output:
```
Summary:
  Total Approvals Requested: 45
  Total Approvals Granted: 42
  Total Approvals Rejected: 3
  Total Actions Executed: 42
  Total Actions Failed: 2

Actions by Type:
  email_send: 30
  linkedin_post: 8
  payment_processed: 4

Approvers:
  - human
```

## Testing

See `tests/test_audit_logging.py` for comprehensive tests.

## Migration Notes

**Backward Compatibility:**
- Old `_log_event()` methods still work (kept for backward compatibility)
- New audit logging runs in parallel
- No breaking changes to existing code

**Gradual Rollout:**
- Core skills updated: email_responder, linkedin_posting, instagram_posting
- Other skills can be updated incrementally
- Skills without correlation_id still work (audit logging is optional)

## Performance Considerations

- **Thread-safe:** Uses threading.Lock for concurrent writes
- **Minimal overhead:** Append-only writes, no database queries
- **Daily rotation:** Logs rotate daily to prevent large files
- **Query performance:** JSONL format allows streaming reads

## Security Considerations

- **Immutable logs:** Append-only, cannot be modified after writing
- **Sensitive data:** Metadata is truncated (e.g., email body preview only)
- **Access control:** Logs stored in vault, protected by filesystem permissions

## Future Enhancements

1. **Log retention policy:** Auto-archive logs older than 90 days
2. **Log encryption:** Encrypt audit logs at rest
3. **Real-time monitoring:** Alert on suspicious patterns
4. **Advanced queries:** SQL-like query language for complex searches
5. **Export formats:** CSV, PDF reports for auditors
6. **User tracking:** Track actual human approver (not just "human")

## Troubleshooting

### No audit logs appearing
- Check `AI_Employee_Vault/Logs/audit/` directory exists
- Verify correlation_id is being passed to skills
- Check file permissions on audit directory

### Correlation ID not linking events
- Verify orchestrator is generating correlation_id
- Check approval_handler is passing correlation_id to executor
- Verify skills are receiving correlation_id parameter

### Query tool returns no results
- Check date range (logs are daily files)
- Verify correlation_id is correct
- Check audit log files exist for the date range

## References

- Audit Report: `AUDIT-REPORT.md` (AUDIT-2 BROKEN #3)
- Implementation: `scripts/audit_logger.py`
- Query Tool: `scripts/audit_query.py`
- Tests: `tests/test_audit_logging.py`
