# CS2-Chatbot Build Script (PowerShell)
# Builds a portable executable for Windows

param(
    [switch]$Clean,
    [switch]$Help
)

if ($Help) {
    Write-Host "CS2-Chatbot Build Script" -ForegroundColor Green
    Write-Host "Usage: .\build.ps1 [-Clean] [-Help]" -ForegroundColor White
    Write-Host "  -Clean  Clean build artifacts before building"
    Write-Host "  -Help   Show this help message"
    exit 0
}

Write-Host "Building CS2-Chatbot..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    if (Test-Path "release") { Remove-Item "release" -Recurse -Force }
}

# Remove old executable to ensure fresh build
if (Test-Path ".\release\CS2-Chatbot.exe") {
    Remove-Item ".\release\CS2-Chatbot.exe" -Force
}

Write-Host "Starting build..." -ForegroundColor Cyan

# Build directly with PyInstaller using our spec file
& ".\venv\Scripts\pyinstaller" "--clean" "--noconfirm" "CS2-Chatbot.spec"
$exitCode = $LASTEXITCODE

# Create release folder and copy files
if ($exitCode -eq 0 -and (Test-Path ".\dist\CS2-Chatbot.exe")) {
    # Create release folder
    if (-not (Test-Path "release")) { New-Item -ItemType Directory -Path "release" -Force | Out-Null }
    
    # Copy executable and documentation
    Copy-Item ".\dist\CS2-Chatbot.exe" ".\release\CS2-Chatbot.exe" -Force
    if (Test-Path "README.md") { Copy-Item "README.md" ".\release\" -Force }
    if (Test-Path "LICENSE") { Copy-Item "LICENSE" ".\release\" -Force }
    
    $fileInfo = Get-Item ".\release\CS2-Chatbot.exe"
    $sizeInMB = [math]::Round($fileInfo.Length / 1MB, 1)
    
    Write-Host ""
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable: .\release\CS2-Chatbot.exe ($sizeInMB MB)" -ForegroundColor Cyan
    Write-Host "Ready for distribution!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
