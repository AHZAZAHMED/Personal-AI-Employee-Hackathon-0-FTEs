# AI Employee - Systemd Service Files

This directory contains systemd service files for running AI Employee components as system services.

## Services

### Core Services

1. **ai-employee-orchestrator.service** - Main orchestration loop
2. **ai-employee-gmail-watcher.service** - Gmail monitoring
3. **ai-employee-approval-handler.service** - Approval processing

### Optional Services

4. **ai-employee-ralph-wiggum.service** - Autonomous task completion loop

## Installation

### 1. Copy service files to systemd directory

```bash
sudo cp systemd/*.service /etc/systemd/system/
```

### 2. Update paths in service files

Edit each service file and update:
- `WorkingDirectory` - Path to Gold-Tier directory
- `ExecStart` - Path to Python and scripts
- `User` - Your username
- `Group` - Your group

### 3. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 4. Enable services (start on boot)

```bash
sudo systemctl enable ai-employee-orchestrator
sudo systemctl enable ai-employee-gmail-watcher
sudo systemctl enable ai-employee-approval-handler
```

### 5. Start services

```bash
sudo systemctl start ai-employee-orchestrator
sudo systemctl start ai-employee-gmail-watcher
sudo systemctl start ai-employee-approval-handler
```

## Management Commands

### Check status

```bash
sudo systemctl status ai-employee-orchestrator
sudo systemctl status ai-employee-gmail-watcher
sudo systemctl status ai-employee-approval-handler
```

### View logs

```bash
sudo journalctl -u ai-employee-orchestrator -f
sudo journalctl -u ai-employee-gmail-watcher -f
sudo journalctl -u ai-employee-approval-handler -f
```

### Restart services

```bash
sudo systemctl restart ai-employee-orchestrator
sudo systemctl restart ai-employee-gmail-watcher
sudo systemctl restart ai-employee-approval-handler
```

### Stop services

```bash
sudo systemctl stop ai-employee-orchestrator
sudo systemctl stop ai-employee-gmail-watcher
sudo systemctl stop ai-employee-approval-handler
```

### Disable services (don't start on boot)

```bash
sudo systemctl disable ai-employee-orchestrator
sudo systemctl disable ai-employee-gmail-watcher
sudo systemctl disable ai-employee-approval-handler
```

## Auto-Restart Policies

All services are configured with:
- **Restart=always** - Restart on any exit (crash, error, etc.)
- **RestartSec=10** - Wait 10 seconds before restarting
- **StartLimitBurst=5** - Allow 5 restarts
- **StartLimitIntervalSec=300** - Within 5 minutes

This prevents infinite restart loops while ensuring services recover from transient failures.

## Health Checks

Services log to:
- Systemd journal: `journalctl -u <service-name>`
- Application logs: `AI_Employee_Vault/Logs/<component>.log`

Use the health check script to verify all services are running:

```bash
python scripts/health_check.py
```

## Troubleshooting

### Service won't start

1. Check service status: `sudo systemctl status <service-name>`
2. Check logs: `sudo journalctl -u <service-name> -n 50`
3. Verify paths in service file
4. Check file permissions
5. Verify Python environment

### Service keeps restarting

1. Check application logs in `AI_Employee_Vault/Logs/`
2. Check for configuration errors
3. Verify API credentials
4. Check disk space

### Service not starting on boot

1. Verify service is enabled: `sudo systemctl is-enabled <service-name>`
2. Enable if needed: `sudo systemctl enable <service-name>`

## Security Notes

- Services run as non-root user (specified in `User=` directive)
- Credentials stored in vault directory (ensure proper permissions)
- Logs rotated automatically (see `scripts/logging_config.py`)

## Performance Tuning

### Adjust check intervals

Edit service files and modify script arguments:
- `--check-interval 60` - Check every 60 seconds
- `--check-interval 300` - Check every 5 minutes

### Resource limits

Add to service file under `[Service]`:

```ini
MemoryLimit=512M
CPUQuota=50%
```

## Monitoring

Use systemd's built-in monitoring:

```bash
# Check if service is active
systemctl is-active ai-employee-orchestrator

# Check if service is enabled
systemctl is-enabled ai-employee-orchestrator

# Show service properties
systemctl show ai-employee-orchestrator
```

## Uninstallation

```bash
# Stop services
sudo systemctl stop ai-employee-orchestrator
sudo systemctl stop ai-employee-gmail-watcher
sudo systemctl stop ai-employee-approval-handler

# Disable services
sudo systemctl disable ai-employee-orchestrator
sudo systemctl disable ai-employee-gmail-watcher
sudo systemctl disable ai-employee-approval-handler

# Remove service files
sudo rm /etc/systemd/system/ai-employee-*.service

# Reload systemd
sudo systemctl daemon-reload
```
