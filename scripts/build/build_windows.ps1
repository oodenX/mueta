param (
    [string]$Version = "0.3.0"
)

Write-Host "Building Mueta v$Version for Windows..."

# Install build dependencies
pip install pyinstaller
pip install .

# Build binary
pyinstaller mueta.spec

# Create release directory
New-Item -ItemType Directory -Force -Path release

# 1. Create ZIP
Write-Host "Creating .zip package..."
$ZipPath = "release\mueta-$Version-windows-x86_64.zip"
Compress-Archive -Path dist\mueta.exe -DestinationPath $ZipPath -Force

# 2. Copy EXE
Write-Host "Copying executable..."
Copy-Item dist\mueta.exe -Destination release\mueta.exe -Force

Write-Host "Build complete! Artifacts in release\"
