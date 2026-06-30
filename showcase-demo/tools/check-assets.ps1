param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$manifestPath = Join-Path $Root "assets\asset-manifest.json"

if (-not (Test-Path -LiteralPath $manifestPath)) {
    Write-Error "Manifest not found: $manifestPath"
    exit 1
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$items = @()

foreach ($property in $manifest.backgrounds.PSObject.Properties) {
    $items += [pscustomobject]@{
        Type = "background"
        Key = $property.Name
        Path = $property.Value
    }
}

foreach ($property in $manifest.references.PSObject.Properties) {
    $items += [pscustomobject]@{
        Type = "reference"
        Key = $property.Name
        Path = $property.Value
    }
}

foreach ($property in $manifest.motions.PSObject.Properties) {
    $items += [pscustomobject]@{
        Type = "motion"
        Key = $property.Name
        Path = $property.Value
    }
}

$results = foreach ($item in $items) {
    $assetPath = Join-Path $Root $item.Path
    $exists = Test-Path -LiteralPath $assetPath
    [pscustomobject]@{
        Status = if ($exists) { "OK" } else { "MISSING" }
        Type = $item.Type
        Key = $item.Key
        Path = $item.Path
    }
}

$results | Format-Table -AutoSize

$missing = @($results | Where-Object { $_.Status -eq "MISSING" })
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "$($missing.Count) asset(s) missing. The showcase will use CSS/Canvas fallbacks for missing motion files."
    exit 2
}

Write-Host ""
Write-Host "All showcase assets are present."
