#!/bin/bash
set -e

VERSION=${1:-"0.3.0"}
ARCH=$(uname -m)

echo "Building Mueta v${VERSION} for macOS (${ARCH})..."

# Install build dependencies
pip install pyinstaller
pip install .

# Build binary
pyinstaller mueta.spec

# Create release directory
mkdir -p release

# 1. Create App Bundle Structure
echo "Creating App Bundle..."
APP_DIR="dist/Mueta.app"
mkdir -p "${APP_DIR}/Contents/MacOS"
cp dist/mueta "${APP_DIR}/Contents/MacOS/"

cat > "${APP_DIR}/Contents/Info.plist" << XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>mueta</string>
    <key>CFBundleIdentifier</key>
    <string>com.oodenx.mueta</string>
    <key>CFBundleName</key>
    <string>Mueta</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
XML

# 2. Create Tarball
echo "Creating .tar.gz..."
tar -czvf "release/mueta-${VERSION}-macos-${ARCH}.tar.gz" -C dist mueta

echo "Build complete! Artifacts in release/"
