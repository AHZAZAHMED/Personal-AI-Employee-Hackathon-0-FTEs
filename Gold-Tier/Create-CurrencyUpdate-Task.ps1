# Currency Rate Update - Windows Task Scheduler Setup
# Run as Administrator

$projectRoot = "E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier"
$pythonExe = "python"

Write-Host "========================================"
Write-Host "Currency Rate Update - Task Scheduler Setup"
Write-Host "========================================"
Write-Host ""

# ==============================================================================
# Task: Currency Rate Update - Daily at 6 AM
# ==============================================================================
Write-Host "Creating Currency Rate Update task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\update_currency_rates.py" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Daily -At 6am

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Currency_Update" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Update currency rates daily from European Central Bank" `
      -ErrorAction Stop | Out-Null

    Write-Host "  [OK] Currency Rate Update task created"
} catch {
    Write-Host "  [FAIL] Currency Rate Update task: $_"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Task Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Created Tasks:"
Write-Host "  - AI_Employee_Currency_Update (Daily at 6 AM)"
Write-Host ""
Write-Host "To view tasks:"
Write-Host "  powershell -Command "Get-ScheduledTask -TaskName 'AI_Employee_Currency_Update'""
Write-Host ""
Write-Host "To run task manually:"
Write-Host "  powershell -Command "Start-ScheduledTask -TaskName 'AI_Employee_Currency_Update'""
Write-Host ""
Write-Host "To delete task:"
Write-Host "  powershell -Command "Unregister-ScheduledTask -TaskName 'AI_Employee_Currency_Update' -Confirm:`$false""
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Task will run daily at 6:00 AM"
Write-Host "  2. Rates will be updated automatically"
Write-Host "  3. Invoices will use latest exchange rates"
Write-Host ""
