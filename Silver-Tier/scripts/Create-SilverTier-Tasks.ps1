# Silver Tier - Windows Task Scheduler Setup
# Run these PowerShell commands as Administrator to set up scheduled tasks

$ErrorActionPreference = "Stop"
$vaultPath = "E:\Personal-AI-Employee-Hackathon-0-FTEs\AI_Employee_Vault"
$projectRoot = "E:\Personal-AI-Employee-Hackathon-0-FTEs"
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
  -Argument "scripts\gmail_watcher.py --vault $vaultPath" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 2) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

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
      -ErrorAction Stop
    
    Write-Host "  ✓ Gmail Watcher task created"
} catch {
    Write-Host "  ✗ Failed to create Gmail Watcher task: $_"
}

Write-Host ""

# ==============================================================================
# Task 2: Orchestrator - Process tasks every hour
# ==============================================================================
Write-Host "Creating Orchestrator task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\orchestrator.py --vault $vaultPath --once" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Hours 1) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Orchestrator" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Process pending tasks every hour" `
      -ErrorAction Stop
    
    Write-Host "  ✓ Orchestrator task created"
} catch {
    Write-Host "  ✗ Failed to create Orchestrator task: $_"
}

Write-Host ""

# ==============================================================================
# Task 3: Daily Briefing - Generate at 8 AM every day
# ==============================================================================
Write-Host "Creating Daily Briefing task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\orchestrator.py --vault $vaultPath --briefing" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_Daily_Briefing" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Generate daily CEO briefing at 8 AM" `
      -ErrorAction Stop
    
    Write-Host "  ✓ Daily Briefing task created"
} catch {
    Write-Host "  ✗ Failed to create Daily Briefing task: $_"
}

Write-Host ""

# ==============================================================================
# Task 4: LinkedIn Poster - Check for approved posts every 30 minutes
# ==============================================================================
Write-Host "Creating LinkedIn Poster task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\linkedin_poster.py --vault $vaultPath" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 30) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_LinkedIn_Poster" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Check and post approved LinkedIn posts every 30 minutes" `
      -ErrorAction Stop
    
    Write-Host "  ✓ LinkedIn Poster task created"
} catch {
    Write-Host "  ✗ Failed to create LinkedIn Poster task: $_"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Task Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "To view tasks:"
Write-Host "  Get-ScheduledTask -TaskName 'AI_Employee_*'"
Write-Host ""
Write-Host "To view task status:"
Write-Host "  Get-ScheduledTaskInfo -TaskName 'AI_Employee_Gmail_Watcher'"
Write-Host ""
Write-Host "To run a task manually:"
Write-Host "  Start-ScheduledTask -TaskName 'AI_Employee_Gmail_Watcher'"
Write-Host ""
Write-Host "To delete all AI Employee tasks:"
Write-Host "  Get-ScheduledTask -TaskName 'AI_Employee_*' | Unregister-ScheduledTask -Confirm:`$false"
Write-Host ""
