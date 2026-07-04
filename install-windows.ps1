# Installs the visa monitor as a Windows Task Scheduler job.
# Run once after cloning: right-click -> "Run with PowerShell"
# Or from PowerShell: .\install-windows.ps1

$ErrorActionPreference = "Stop"

$InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = (Get-Command python).Source
$TaskName   = "VisaAppointmentMonitor"
$LogFile    = "$env:USERPROFILE\AppData\Local\Logs\visa-monitor.log"

# Create log directory if it doesn't exist
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null

# Build the action: python monitor.py >> logfile 2>&1
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$InstallDir\monitor.py`"" `
    -WorkingDirectory $InstallDir

# Trigger: repeat every 5 minutes, starting now, indefinitely
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Settings: run even if on battery, restart on failure
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Monitor installed and running every 5 minutes."
Write-Host "Logs: $LogFile"
Write-Host "To stop: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
