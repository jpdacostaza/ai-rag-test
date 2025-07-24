# PowerShell script to clean Python cache files
# Usage: .\cleanup_pycache.ps1

Write-Host "🧹 Cleaning Python cache files..." -ForegroundColor Green

$removedDirs = 0
$removedFiles = 0

# Remove __pycache__ directories
Get-ChildItem -Recurse -Directory -Name "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    $fullPath = Get-Item $_
    Write-Host "  🗑️  Removing directory: $fullPath" -ForegroundColor Yellow
    Remove-Item $_ -Recurse -Force
    $removedDirs++
}

# Remove .pyc files
Get-ChildItem -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  🗑️  Removing file: $($_.FullName)" -ForegroundColor Yellow
    Remove-Item $_.FullName -Force
    $removedFiles++
}

# Remove .pyo files  
Get-ChildItem -Recurse -File -Filter "*.pyo" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  🗑️  Removing file: $($_.FullName)" -ForegroundColor Yellow
    Remove-Item $_.FullName -Force
    $removedFiles++
}

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host "   📁 Directories removed: $removedDirs" -ForegroundColor Cyan
Write-Host "   📄 Files removed: $removedFiles" -ForegroundColor Cyan
