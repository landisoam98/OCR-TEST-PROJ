# Registers and starts the "BHP Scanner" background task. The installer runs this; it can be re-run safely.
param([Parameter(Mandatory)][string]$Exe, [Parameter(Mandatory)][string]$Config)
$ErrorActionPreference = "Stop"
$TaskName = "BHP Scanner"
$action = New-ScheduledTaskAction -Execute $Exe -Argument "--config `"$Config`" run" -WorkingDirectory (Split-Path $Exe)
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -StartWhenAvailable -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "Files scanned delivery notes into Year / Month / Customer folders." | Out-Null
Start-ScheduledTask -TaskName $TaskName
