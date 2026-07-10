$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetScript = Join-Path $scriptDir "validate.py"
$requirementsFile = Join-Path $scriptDir "requirements.txt"
$binDir = Join-Path $HOME "bin"
$commandName = "javal"
$cmdPath = Join-Path $binDir "$commandName.cmd"
$ps1Path = Join-Path $binDir "$commandName.ps1"

if (-not (Test-Path -Path $targetScript -PathType Leaf)) {
    throw "Cannot find target script: $targetScript"
}

New-Item -ItemType Directory -Path $binDir -Force | Out-Null

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    return $null
}

$pythonCmd = Resolve-PythonCommand
if (-not $pythonCmd) {
    throw "Python interpreter not found. Install Python 3.10+ and re-run install.ps1."
}

if (Test-Path -Path $requirementsFile -PathType Leaf) {
    Write-Host "Installing Python dependencies..."
    if ($pythonCmd -eq "py -3") {
        py -3 -m pip install -r $requirementsFile
    } else {
        & $pythonCmd -m pip install -r $requirementsFile
    }
}

$escapedTargetForCmd = $targetScript.Replace('"', '""')
$escapedScriptDirForCmd = $scriptDir.Replace('"', '""')
$escapedTargetForPs1 = $targetScript.Replace('`', '``').Replace('"', '`"')
$escapedScriptDirForPs1 = $scriptDir.Replace('`', '``').Replace('"', '`"')

$cmdContent = @"
@echo off
set "_target=$escapedTargetForCmd"
set "_dir=$escapedScriptDirForCmd"
set "PYTHONPATH=%_dir%;%PYTHONPATH%"
where py >nul 2>nul && (
  py -3 "%_target%" %*
  exit /b
)
where python >nul 2>nul && (
  python "%_target%" %*
  exit /b
)
where python3 >nul 2>nul && (
  python3 "%_target%" %*
  exit /b
)
echo Python interpreter not found. Install Python or add py/python/python3 to PATH.
exit /b 1
"@

$ps1Template = @'
$target = "__TARGET__"
$codeValidatorDir = "__SCRIPT_DIR__"
$env:PYTHONPATH = "$codeValidatorDir;$env:PYTHONPATH"

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    py -3 "$target" @args
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    python "$target" @args
    exit $LASTEXITCODE
}

$python3 = Get-Command python3 -ErrorAction SilentlyContinue
if ($python3) {
    python3 "$target" @args
    exit $LASTEXITCODE
}

Write-Error "Python interpreter not found. Install Python or add py/python/python3 to PATH."
exit 1
'@

$ps1Content = $ps1Template.Replace("__TARGET__", $escapedTargetForPs1).Replace("__SCRIPT_DIR__", $escapedScriptDirForPs1)

Set-Content -Path $cmdPath -Value $cmdContent -Encoding Ascii
Set-Content -Path $ps1Path -Value $ps1Content -Encoding Ascii

Write-Host "Installed: $cmdPath"

function Normalize-PathEntry([string]$pathEntry) {
    if ([string]::IsNullOrWhiteSpace($pathEntry)) {
        return ""
    }
    return $pathEntry.Trim().TrimEnd('\').ToLowerInvariant()
}

$normalizedBinDir = Normalize-PathEntry $binDir

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userEntries = @()
if (-not [string]::IsNullOrWhiteSpace($userPath)) {
    $userEntries = $userPath -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
}

$userHasBin = $false
foreach ($entry in $userEntries) {
    if ((Normalize-PathEntry $entry) -eq $normalizedBinDir) {
        $userHasBin = $true
        break
    }
}

if (-not $userHasBin) {
    $updatedUserPath = (($userEntries + $binDir) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $updatedUserPath, "User")
    Write-Host "Added to user PATH: $binDir"
} else {
    Write-Host "User PATH already contains $binDir"
}

$sessionEntries = $env:Path -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
$sessionHasBin = $false
foreach ($entry in $sessionEntries) {
    if ((Normalize-PathEntry $entry) -eq $normalizedBinDir) {
        $sessionHasBin = $true
        break
    }
}

if (-not $sessionHasBin) {
    $env:Path = "$binDir;$env:Path"
    Write-Host "Updated current session PATH: $binDir"
}

Write-Host "Verify with: $commandName --help"
