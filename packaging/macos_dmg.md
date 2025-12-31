# macOS DMG Packaging

## Prerequisites
- macOS system
- create-dmg tool: `brew install create-dmg`
- Build mueta binary using PyInstaller first

## Build Steps

### Method 1: Using create-dmg (Recommended)

```bash
#!/bin/bash
# build_dmg.sh

APP_NAME="Mueta"
VERSION="0.1.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"

# Build with PyInstaller
pyinstaller mueta.spec

# Create app bundle structure
mkdir -p "dist/${APP_NAME}.app/Contents/MacOS"
mkdir -p "dist/${APP_NAME}.app/Contents/Resources"

# Copy binary
cp dist/mueta "dist/${APP_NAME}.app/Contents/MacOS/"

# Create Info.plist
cat > "dist/${APP_NAME}.app/Contents/Info.plist" << EOF
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
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
</dict>
</plist>
EOF

# Create DMG
create-dmg \
  --volname "${APP_NAME}" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 185 \
  "${DMG_NAME}" \
  "dist/${APP_NAME}.app"
```

### Method 2: Homebrew Formula

Create `Formula/mueta.rb`:
```ruby
class Mueta < Formula
  desc "Music metadata fetcher"
  homepage "https://github.com/oodenX/mueta"
  url "https://github.com/oodenX/mueta/archive/v0.1.0.tar.gz"
  sha256 "PUT-SHA256-HERE"
  license "MIT"

  depends_on "python@3.12"
  depends_on "chromaprint"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/mueta", "--version"
  end
end
```

Then users can install via:
```bash
brew tap oodenX/mueta
brew install mueta
```
