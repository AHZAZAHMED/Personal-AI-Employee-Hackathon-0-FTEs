# Silver Tier - Windows Task Scheduler Setup
# Run as Administrator

$projectRoot = "E:\Personal-AI-Employee-Hackathon-0-FTEs"
$vaultPath = "$projectRoot\Silver-Tier\AI_Employee_Vault"
$pythonExe = "python"

Write-Host "========================================"
Write-Host "AI Employee - Silver Tier Task Setup"
Write-Host "========================================"
Write-Host ""

# ==============================================================================
# Task 1: Gmail Watcher - Check every 2 minutes
# ==============================================================================
Write-Host "Creating Gmail Watcher task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\gmail_watcher.py --vault $vaultPath --interval 120" `
  -WorkingDirectory "$projectRoot\Silver-Tier"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 2)

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Gmail_Watcher" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Monitor Gmail for new messages every 2 minutes" `
      -ErrorAction Stop | Out-Null
    
    Write-Host "  [OK] Gmail Watcher task created"
} catch {
    Write-Host "  [FAIL] Gmail Watcher task: $_"
}

Write-Host ""

# ==============================================================================
# Task 2: Orchestrator - Process tasks every hour
# ==============================================================================
Write-Host "Creating Orchestrator task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\orchestrator.py --vault $vaultPath --once" `
  -WorkingDirectory "$projectRoot\Silver-Tier"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(1) `
  -RepetitionInterval (New-TimeSpan -Hours 1)

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Orchestrator" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Process pending tasks every hour" `
      -ErrorAction Stop | Out-Null
    
    Write-Host "  [OK] Orchestrator task created"
} catch {
    Write-Host "  [FAIL] Orchestrator task: $_"
}

Write-Host ""

# ==============================================================================
# Task 3: Daily Briefing - Generate at 8 AM every day
# ==============================================================================
Write-Host "Creating Daily Briefing task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\orchestrator.py --vault $vaultPath --once" `
  -WorkingDirectory "$projectRoot\Silver-Tier"

$trigger = New-ScheduledTaskTrigger -Daily -At 8am

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Daily_Briefing" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Generate daily CEO briefing at 8 AM" `
      -ErrorAction Stop | Out-Null
    
    Write-Host "  [OK] Daily Briefing task created"
} catch {
    Write-Host "  [FAIL] Daily Briefing task: $_"
}

Write-Host ""

# ==============================================================================
# Task 4: Approval Handler - Check for approved actions every 30 minutes
# ==============================================================================
Write-Host "Creating Approval Handler task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\approval_handler.py --vault $vaultPath" `
  -WorkingDirectory "$projectRoot\Silver-Tier"

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) `
  -RepetitionInterval (New-TimeSpan -Minutes 30)

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Approval_Handler" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Execute approved actions every 30 minutes" `
      -ErrorAction Stop | Out-Null
    
    Write-Host "  [OK] Approval Handler task created"
} catch {
    Write-Host "  [FAIL] Approval Handler task: $_"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Task Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Created Tasks:"
Write-Host "  - AI_Employee_Gmail_Watcher (every 2 min)"
Write-Host "  - AI_Employee_Orchestrator (every hour)"
Write-Host "  - AI_Employee_Daily_Briefing (daily at 8 AM)"
Write-Host "  - AI_Employee_Approval_Handler (every 30 min)"
Write-Host ""
Write-Host "To view tasks:"
Write-Host "  powershell -Command "Get-ScheduledTask -TaskName 'AI_Employee_*'""
Write-Host ""
Write-Host "To view task status:"
Write-Host "  powershell -Command "Get-ScheduledTaskInfo -TaskName 'AI_Employee_Gmail_Watcher'""
Write-Host ""
Write-Host "To run a task manually:"
Write-Host "  powershell -Command "Start-ScheduledTask -TaskName 'AI_Employee_Gmail_Watcher'""
Write-Host ""
Write-Host "To delete all tasks:"
Write-Host "  powershell -Command "Get-ScheduledTask -TaskName 'AI_Employee_*' | Unregister-ScheduledTask -Confirm:`$false""
