#!/bin/bash
set -e

VERSION=${1:-"0.3.0"}
ARCH="x86_64"

echo "Building Mueta v${VERSION} for Linux (${ARCH})..."

# Install build dependencies
pip install pyinstaller
pip install .

# Build binary
pyinstaller mueta.spec

# Create release directory
mkdir -p release

# 1. Create Tarball
echo "Creating .tar.gz..."
tar -czvf "release/mueta-${VERSION}-linux-${ARCH}.tar.gz" -C dist mueta

# 2. Create DEB Package
if command -v fpm &> /dev/null; then
    echo "Creating .deb package..."
    fpm -s dir -t deb \
        -n mueta \
        -v "${VERSION}" \
        --description "Music metadata fetcher CLI" \
        --url "https://github.com/oodenX/mueta" \
        --maintainer "oodenX <ven3428set@163.com>" \
        --license "MIT" \
        --depends "libchromaprint-tools" \
        -p "release/mueta_${VERSION}_amd64.deb" \
        dist/mueta=/usr/local/bin/mueta
else
    echo "Skipping .deb creation (fpm not installed)"
fi

# 3. Create RPM Package
if command -v fpm &> /dev/null; then
    echo "Creating .rpm package..."
    fpm -s dir -t rpm \
        -n mueta \
        -v "${VERSION}" \
        --description "Music metadata fetcher CLI" \
        --url "https://github.com/oodenX/mueta" \
        --maintainer "oodenX <ven3428set@163.com>" \
        --license "MIT" \
        --depends "chromaprint-tools" \
        -p "release/mueta-${VERSION}-1.x86_64.rpm" \
        dist/mueta=/usr/local/bin/mueta
else
    echo "Skipping .rpm creation (fpm not installed)"
fi

echo "Build complete! Artifacts in release/"
