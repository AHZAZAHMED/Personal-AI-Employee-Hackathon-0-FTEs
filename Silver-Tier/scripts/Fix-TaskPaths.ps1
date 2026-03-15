# Fix Task Scheduler Paths - Complete Script
# Run this to fix all AI Employee tasks

Write-Host "=== FIXING TASK SCHEDULER PATHS ===" -ForegroundColor Green
Write-Host ""

# Find Python
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    exit 1
}
Write-Host "Python: $pythonPath" -ForegroundColor Green
Write-Host ""

# Paths
$projectRoot = "E:\Personal-AI-Employee-Hackathon-0-FTEs\Silver-Tier"
$vaultPath = "$projectRoot\AI_Employee_Vault"

# Delete old tasks
Write-Host "Deleting old tasks..." -ForegroundColor Yellow
Get-ScheduledTask -TaskName 'AI_Employee_*' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
Start-Sleep -Seconds 2

# Common settings
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

# Gmail Watcher
Write-Host "Creating Gmail Watcher..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction -Execute $pythonPath `
  -Argument "$projectRoot\scripts\gmail_watcher.py --vault $vaultPath --interval 120" `
  -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 2) `
  -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "AI_Employee_Gmail_Watcher" -Action $action -Trigger $trigger -Settings $settings -ErrorAction Stop | Out-Null
Write-Host "  [OK] Gmail Watcher" -ForegroundColor Green

# Orchestrator
Write-Host "Creating Orchestrator..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction -Execute $pythonPath `
  -Argument "$projectRoot\scripts\orchestrator.py --vault $vaultPath --once" `
  -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(1) `
  -RepetitionInterval (New-TimeSpan -Hours 1) `
  -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "AI_Employee_Orchestrator" -Action $action -Trigger $trigger -Settings $settings -ErrorAction Stop | Out-Null
Write-Host "  [OK] Orchestrator" -ForegroundColor Green

# Approval Handler
Write-Host "Creating Approval Handler..." -ForegroundColor Cyan
$action = New-ScheduledTaskAction -Execute $pythonPath `
  -Argument "$projectRoot\scripts\approval_handler.py --vault $vaultPath" `
  -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) `
  -RepetitionInterval (New-TimeSpan -Minutes 30) `
  -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "AI_Employee_Approval_Handler" -Action $action -Trigger $trigger -Settings $settings -ErrorAction Stop | Out-Null
Write-Host "  [OK] Approval Handler" -ForegroundColor Green

Write-Host ""
Write-Host "=== ALL TASKS CREATED ===" -ForegroundColor Green
Get-ScheduledTask -TaskName 'AI_Employee_*' | Select-Object TaskName, State | Format-Table

Write-Host ""
Write-Host "=== VERIFYING PATHS ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Gmail Watcher:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName 'AI_Employee_Gmail_Watcher' | Select-Object -ExpandProperty Actions | Format-List

Write-Host ""
Write-Host "Orchestrator:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName 'AI_Employee_Orchestrator' | Select-Object -ExpandProperty Actions | Format-List

Write-Host ""
Write-Host "Approval Handler:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName 'AI_Employee_Approval_Handler' | Select-Object -ExpandProperty Actions | Format-List

Write-Host ""
Write-Host "=== FIX COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Send a test email to ahzazahmedkhan159@gmail.com"
Write-Host "2. Wait 3 minutes"
Write-Host "3. Check: dir $vaultPath\Needs_Action\"
Write-Host ""
