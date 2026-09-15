param([Parameter(Mandatory=$true)][string]$DocumentPath,
      [Parameter(Mandatory=$true)][string]$PdfPath)
$wordApp = $null
$wordDocument = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $resolvedDocument = (Resolve-Path -LiteralPath $DocumentPath).Path
    $wordDocument = $wordApp.Documents.Open($resolvedDocument, $false, $false)
    $null = $wordDocument.Fields.Update()
    foreach ($tocEntry in $wordDocument.TablesOfContents) { $tocEntry.Update() }
    $wordDocument.Repaginate()
    $wordDocument.Save()
    $wordDocument.ExportAsFixedFormat([System.IO.Path]::GetFullPath($PdfPath),17)
    Write-Output ('pages=' + $wordDocument.ComputeStatistics(2))
} finally {
    if ($null -ne $wordDocument) { $wordDocument.Close(0) }
    if ($null -ne $wordApp) { $wordApp.Quit() }
}
