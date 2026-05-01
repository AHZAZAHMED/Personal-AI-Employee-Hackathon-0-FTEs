# CEO Briefing - Windows Task Scheduler Setup
# Run as Administrator

$projectRoot = "E:\Personal-AI-Employee-Hackathon-0-FTEs\Gold-Tier"
$vaultPath = "$projectRoot\AI_Employee_Vault"
$pythonExe = "python"

Write-Host "========================================"
Write-Host "CEO Briefing - Task Scheduler Setup"
Write-Host "========================================"
Write-Host ""

# ==============================================================================
# Task: CEO Briefing - Every Monday at 8 AM
# ==============================================================================
Write-Host "Creating CEO Briefing task..."

$action = New-ScheduledTaskAction -Execute $pythonExe `
  -Argument "scripts\ceo_briefing_generator.py --vault AI_Employee_Vault --days 7" `
  -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

try {
    Register-ScheduledTask `
      -TaskName "AI_Employee_CEO_Briefing" `
      -Action $action `
      -Trigger $trigger `
      -Settings $settings `
      -Description "Generate weekly CEO briefing every Monday at 8 AM" `
      -ErrorAction Stop | Out-Null

    Write-Host "  [OK] CEO Briefing task created"
} catch {
    Write-Host "  [FAIL] CEO Briefing task: $_"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Task Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Created Tasks:"
Write-Host "  - AI_Employee_CEO_Briefing (Every Monday at 8 AM)"
Write-Host ""
Write-Host "To view tasks:"
Write-Host "  powershell -Command "Get-ScheduledTask -TaskName 'AI_Employee_*'""
Write-Host ""
Write-Host "To view task status:"
Write-Host "  powershell -Command "Get-ScheduledTaskInfo -TaskName 'AI_Employee_CEO_Briefing'""
Write-Host ""
Write-Host "To run task manually:"
Write-Host "  powershell -Command "Start-ScheduledTask -TaskName 'AI_Employee_CEO_Briefing'""
Write-Host ""
Write-Host "To delete task:"
Write-Host "  powershell -Command "Unregister-ScheduledTask -TaskName 'AI_Employee_CEO_Briefing' -Confirm:`$false""
Write-Host ""
