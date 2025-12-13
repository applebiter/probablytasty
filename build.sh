#!/bin/bash
# Build script for ProbablyTasty on Linux
# Creates standalone executable and optionally .deb package

set -e

echo "==================================="
echo "ProbablyTasty Build Script - Linux"
echo "==================================="
echo ""

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Build with PyInstaller
echo "📦 Building executable with PyInstaller..."
pyinstaller probablytasty.spec

if [ $? -eq 0 ]; then
    echo "✅ Executable built successfully!"
    echo "   Location: dist/ProbablyTasty/ProbablyTasty"
else
    echo "❌ Build failed!"
    exit 1
fi

# Ask about .deb package
echo ""
read -p "Do you want to create a .deb package? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Creating .deb package..."
    
    # Create directory structure
    mkdir -p debian/DEBIAN
    mkdir -p debian/usr/local/bin
    mkdir -p debian/usr/share/applications
    mkdir -p debian/usr/share/icons/hicolor/512x512/apps
    
    # Copy files
    cp -r dist/ProbablyTasty debian/usr/local/bin/
    cp icons/applebiter.png debian/usr/share/icons/hicolor/512x512/apps/probablytasty.png
    
    # Create control file
    cat > debian/DEBIAN/control << EOF
Package: probablytasty
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: applebiter <your-email@example.com>
Description: Intelligent Recipe Manager
 ProbablyTasty is an AI-powered recipe management application with
 natural language search, unit conversion, and self-contained HTML exports.
EOF
    
    # Create desktop entry
    cat > debian/usr/share/applications/probablytasty.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ProbablyTasty
Comment=Intelligent Recipe Manager
Exec=/usr/local/bin/ProbablyTasty/ProbablyTasty
Icon=probablytasty
Terminal=false
Categories=Office;Database;Utility;
EOF
    
    # Build package
    fakeroot dpkg-deb --build debian
    mv debian.deb probablytasty_1.0.0_amd64.deb
    
    # Cleanup
    rm -rf debian
    
    echo "✅ .deb package created: probablytasty_1.0.0_amd64.deb"
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "Output:"
ls -lh dist/ProbablyTasty/ProbablyTasty
[ -f probablytasty_1.0.0_amd64.deb ] && ls -lh probablytasty_1.0.0_amd64.deb
echo ""
echo "To test: ./dist/ProbablyTasty/ProbablyTasty"
