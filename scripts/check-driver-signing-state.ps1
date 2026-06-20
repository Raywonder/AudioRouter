param(
    [string]$EndpointInstanceId = "ROOT\MEDIA\0000",
    [string]$DriverNamePattern = "ASIOA Audio Router Bridge"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "== $Title =="
}

Write-Section "Boot signing policy"
try {
    $secureBoot = Confirm-SecureBootUEFI
    Write-Host "Secure Boot: $secureBoot"
} catch {
    Write-Host "Secure Boot: unknown. Run this script from an elevated PowerShell prompt to query UEFI state. $($_.Exception.Message)"
}

try {
    $bcd = bcdedit /enum "{current}" 2>$null
    $testSigningMatch = $bcd | Select-String -Pattern "testsigning"
    $noIntegrityMatch = $bcd | Select-String -Pattern "nointegritychecks"
    $testSigning = if ($testSigningMatch) { $testSigningMatch.ToString() } else { "" }
    $noIntegrity = if ($noIntegrityMatch) { $noIntegrityMatch.ToString() } else { "" }
    if ($testSigning) {
        Write-Host $testSigning
    } else {
        Write-Host "TESTSIGNING: not listed for the current boot entry."
    }
    if ($noIntegrity) {
        Write-Host $noIntegrity
    } else {
        Write-Host "NoIntegrityChecks: not listed for the current boot entry."
    }
} catch {
    Write-Host "BCDEdit: unavailable from this shell. $($_.Exception.Message)"
}

Write-Section "ASIOA endpoint device"
$device = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object { $_.FriendlyName -match $DriverNamePattern -or $_.InstanceId -eq $EndpointInstanceId } |
    Select-Object -First 1

if (-not $device) {
    Write-Host "ASIOA endpoint device was not found."
} else {
    Write-Host "Instance: $($device.InstanceId)"
    Write-Host "Name: $($device.FriendlyName)"
    Write-Host "Status: $($device.Status)"

    $details = pnputil /enum-devices /instanceid $device.InstanceId /properties 2>$null |
        Select-String -Pattern "Problem Code|Problem Status|Driver Name|Driver Inf Path|Matching Device Id"
    foreach ($detail in $details) {
        Write-Host $detail.Line.Trim()
    }

    if ($device.Status -ne "OK") {
        Write-Host ""
        Write-Host "Meaning: Windows sees the ASIOA endpoint device, but it has not loaded successfully."
        Write-Host "If the problem code is 52, Windows is blocking the kernel endpoint driver because the driver is not trusted by the current boot signing policy."
    }
}

Write-Section "Recommended paths"
Write-Host "Production: submit the endpoint driver package through Microsoft Partner Center for attestation or WHQL/HLK signing."
Write-Host "Development only: disable Secure Boot, enable TESTSIGNING, reboot, then reinstall the endpoint package."
Write-Host "Secure Boot preproduction: use Microsoft Hardware Dev Center preproduction signing and provision the test machine with Microsoft's Secure Boot test policy."
