$ErrorActionPreference = "Stop"

$binDir = Join-Path $HOME "bin"
$commandName = "javal"
$cmdPath = Join-Path $binDir "$commandName.cmd"
$ps1Path = Join-Path $binDir "$commandName.ps1"

foreach ($path in @($cmdPath, $ps1Path)) {
    if (Test-Path -Path $path) {
        Remove-Item -Path $path -Force
        Write-Host "Removed: $path"
    }
}

if ((Test-Path -Path $binDir) -and -not (Get-ChildItem -Path $binDir -Force | Select-Object -First 1)) {
    Remove-Item -Path $binDir -Force
}

Write-Host "Uninstalled command: $commandName"
Write-Host "If you added PATH manually, you can remove:"
Write-Host "$binDir"
