$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot
foreach ($assetId in @('jacaranda_tree','shrub_03')) {
    $raw = Join-Path $projectRoot "assets/raw_downloads/$assetId"
    $used = Join-Path $projectRoot "assets/vegetation/$assetId"
    New-Item -ItemType Directory -Force -Path $raw,$used | Out-Null
    $files = Invoke-RestMethod "https://api.polyhaven.com/files/$assetId"
    $entry = $files.gltf.'1k'.gltf
    $entries = @(@{Name="$($assetId)_1k.gltf"; Value=$entry})
    $entries += @($entry.include.PSObject.Properties)
    foreach ($file in $entries) {
        $target = Join-Path $raw $file.Name
        $destination = Join-Path $used $file.Name
        New-Item -ItemType Directory -Force -Path (Split-Path $target),(Split-Path $destination) | Out-Null
        if (!(Test-Path -LiteralPath $target)) { Invoke-WebRequest -Uri $file.Value.url -OutFile $target }
        if ((Get-FileHash -LiteralPath $target -Algorithm MD5).Hash.ToLower() -ne $file.Value.md5) { throw "Checksum mismatch: $target" }
        Copy-Item -LiteralPath $target -Destination $destination -Force
        Write-Output "$assetId : $($file.Name) verified"
    }
}
