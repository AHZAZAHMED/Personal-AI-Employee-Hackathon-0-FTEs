# Gold-Tier AI Employee - Setup Guide

## Overview
This is the Gold-Tier implementation of the AI Employee system with all 15 skills operational.

## System Status
✅ **15/15 Skills Working (100%)**

## Quick Start

### 1. Environment Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

### 2. Install Dependencies
```bash
pip install -r requirements_claude.txt
```

### 3. Start External Services

#### Odoo ERP (Required for 2 skills)
```bash
# Start Odoo and PostgreSQL containers
docker-compose up -d

# Verify Odoo is running
curl http://localhost:8069
```

#### Neon Database (Already configured)
The Neon PostgreSQL database is already configured in .env

### 4. Run the System
```bash
# Start the orchestrator
python scripts/orchestrator.py

# Or run individual skills
python skills/whatsapp/run_test.py
```

## Skills List (15/15)

### Communication Skills (5)
1. ✅ WhatsApp Messaging - Send WhatsApp messages via Twilio
2. ✅ Gmail Watcher - Monitor Gmail inbox for new emails
3. ✅ Email Responder - Generate AI-powered email responses
4. ✅ Facebook Posting - Post to Facebook pages
5. ✅ Instagram Posting - Post images to Instagram

### Business Skills (5)
6. ✅ Task Planning - Generate task plans with AI
7. ✅ Currency Updates - Update currency exchange rates
8. ✅ CEO Briefing - Generate executive briefings
9. ✅ LinkedIn Draft Creation - Create LinkedIn post drafts
10. ✅ Email to Invoice - Process emails and create Odoo invoices

### Integration Skills (3)
11. ✅ Odoo Accounting - Create invoices, customers, payments in Odoo
12. ✅ Sync Neon to Vault - Sync WhatsApp messages from Neon DB
13. ✅ File System Watcher - Monitor folders for new files

### System Skills (2)
14. ✅ Error Recovery - Classify and recover from errors
15. ✅ Health Monitoring - System health checks

## External Dependencies

### Required Services
- **Neon PostgreSQL**: For WhatsApp message storage (configured)
- **Odoo ERP**: For accounting features (Docker running on port 8069)
- **PostgreSQL**: For Odoo backend (Docker)

### API Integrations
- Facebook Graph API
- Instagram Graph API
- Twitter API
- Twilio WhatsApp API
- Gmail API
- Google Gemini AI

## Docker Services

### Start Services
```bash
docker-compose up -d
```

### Check Status
```bash
docker ps
```

### View Logs
```bash
docker logs odoo_community
docker logs odoo_postgres
```

### Stop Services
```bash
docker-compose down
```

## Testing

### Test All Skills
```bash
python test_failing_skills.py
```

### Test Individual Skills
```bash
# Test Odoo connection
python -c "from skills.odoo_accounting.skill import odoo_test_connection; print(odoo_test_connection())"

# Test Neon sync
python -c "from skills.sync_neon_vault.skill import sync_test_connection; print(sync_test_connection())"

# Test WhatsApp
python skills/whatsapp/run_test.py
```

## Configuration Files

- `.env` - Environment variables (gitignored)
- `.env.example` - Template for environment variables
- `docker-compose.yml` - Odoo and PostgreSQL services
- `AI_Employee_Vault/` - Task and data storage

## Troubleshooting

### Odoo Connection Failed
```bash
# Check if Odoo is running
curl http://localhost:8069

# Check credentials in .env
grep ODOO .env

# Restart Odoo
docker-compose restart odoo
```

### Neon Database Connection Failed
```bash
# Verify NEON_DATABASE_URL in .env
grep NEON_DATABASE_URL .env

# Test connection
python -c "from scripts.db_neon import NeonDatabase; db = NeonDatabase(); print(db.test_connection())"
```

### Skill Not Found
```bash
# Verify skill is registered
python scripts/skill_registry.py
```

## Recent Fixes (April 21, 2026)

### Fixed Skills
1. **sync_neon_to_vault** - Verified Neon DB connection
2. **odoo_accounting** - Added Odoo credentials and environment config
3. **email_to_invoice** - Fixed via Odoo dependency resolution

### Changes Made
- Recovered `scripts/odoo_mcp_server.py` from git history
- Copied `scripts/email_sender_mcp.py` from Silver-Tier
- Updated `skills/odoo_accounting/service.py` to use environment variables
- Added Odoo credentials to `.env`

## Production Deployment

### Pre-Deployment Checklist
- [ ] All credentials configured in .env
- [ ] Docker services running
- [ ] All 15 skills tested
- [ ] Monitoring configured
- [ ] Backup strategy in place

### Recommended Setup
1. Use environment-specific .env files
2. Set up log rotation
3. Configure alerting for failures
4. Schedule regular backups
5. Monitor API rate limits

## Support

For issues or questions:
1. Check the logs in `AI_Employee_Vault/Logs/`
2. Review skill-specific README files
3. Run diagnostic tests
4. Check Docker container logs

## License
[Your License Here]

## Contributors
- AI Employee Development Team
- Claude Sonnet 4.6 (AI Assistant)
