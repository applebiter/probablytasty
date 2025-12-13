# Building Installers for ProbablyTasty

This guide explains how to build standalone installers for Windows and Linux.

## Prerequisites

### All Platforms
```bash
pip install pyinstaller
```

### Windows Only (for installer)
Download and install [Inno Setup](https://jrsoftware.org/isdl.php) (free, open-source)

### Linux Only (for .deb package)
```bash
sudo apt-get install dpkg-deb fakeroot
```

## Building the Application

### Step 1: Build with PyInstaller

**Windows:**
```cmd
pyinstaller probablytasty.spec
```

**Linux:**
```bash
pyinstaller probablytasty.spec
```

This creates a `dist/ProbablyTasty/` folder with the standalone application.

### Step 2: Test the Build

**Windows:**
```cmd
dist\ProbablyTasty\ProbablyTasty.exe
```

**Linux:**
```bash
./dist/ProbablyTasty/ProbablyTasty
```

## Creating Installers

### Windows Installer (.exe)

1. **Open Inno Setup Compiler**
2. **Load the script:** File → Open → Select `installer.iss`
3. **Edit GUID:** Replace `{YOUR-GUID-HERE}` with a unique GUID
   - Generate GUID: Tools → Generate GUID
4. **Compile:** Build → Compile
5. **Output:** `dist/installer/ProbablyTasty-Setup-1.0.0.exe`

**Or use command line:**
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

### Linux .deb Package

1. **Create package structure:**
```bash
mkdir -p debian/DEBIAN
mkdir -p debian/usr/local/bin
mkdir -p debian/usr/share/applications
mkdir -p debian/usr/share/icons/hicolor/512x512/apps
```

2. **Copy files:**
```bash
cp -r dist/ProbablyTasty debian/usr/local/bin/
cp icons/applebiter.png debian/usr/share/icons/hicolor/512x512/apps/probablytasty.png
```

3. **Create control file** (`debian/DEBIAN/control`):
```
Package: probablytasty
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: applebiter <your-email@example.com>
Description: Intelligent Recipe Manager
 ProbablyTasty is an AI-powered recipe management application with
 natural language search, unit conversion, and self-contained HTML exports.
 .
 Features include:
  - Multi-provider LLM support (OpenAI, Anthropic, Google, Ollama)
  - Smart shopping list generation
  - Recipe import from URLs and images
  - Dark/Light themes
```

4. **Create desktop entry** (`debian/usr/share/applications/probablytasty.desktop`):
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=ProbablyTasty
Comment=Intelligent Recipe Manager
Exec=/usr/local/bin/ProbablyTasty/ProbablyTasty
Icon=probablytasty
Terminal=false
Categories=Office;Database;Utility;
```

5. **Build the package:**
```bash
fakeroot dpkg-deb --build debian
mv debian.deb probablytasty_1.0.0_amd64.deb
```

6. **Install (for testing):**
```bash
sudo dpkg -i probablytasty_1.0.0_amd64.deb
```

## Troubleshooting

### Missing Dependencies
If PyInstaller misses dependencies, add them to `hiddenimports` in `probablytasty.spec`.

### Icon Not Working
- **Windows:** Convert PNG to ICO format: `convert applebiter.png -define icon:auto-resize=256,128,64,48,32,16 applebiter.ico`
- **Linux:** Icons should be PNG in hicolor directories

### Large File Size
- Enable UPX compression in `.spec` file (already enabled)
- Exclude unused libraries in `excludes` list

### Database Location
The app stores its database in `~/.probablytasty/data/` (user's home directory), so it's preserved across updates.

## Distribution

### Windows
- Distribute `ProbablyTasty-Setup-1.0.0.exe`
- Users double-click to install

### Linux
- **Ubuntu/Debian:** Distribute `.deb` file
- **Other distros:** Provide `.tar.gz` of `dist/ProbablyTasty/` folder
- **AppImage** (optional): Use `appimagetool` for universal Linux package

## Automated Build Script

Create `build.sh` (Linux) or `build.bat` (Windows):

**build.sh:**
```bash
#!/bin/bash
set -e

echo "Building ProbablyTasty..."
pyinstaller probablytasty.spec

echo "Creating .deb package..."
# Add .deb creation steps here

echo "Build complete!"
ls -lh dist/
```

**build.bat:**
```cmd
@echo off
echo Building ProbablyTasty...
pyinstaller probablytasty.spec

echo Creating installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

echo Build complete!
dir dist\installer\
```

Make executable:
```bash
chmod +x build.sh
./build.sh
```

## Code Signing (Optional but Recommended)

### Windows
Use `signtool.exe` with a code signing certificate to avoid "Unknown Publisher" warnings.

### macOS
Use Apple Developer certificate with `codesign` and `productbuild`.

## Next Steps

1. Test installer on clean system
2. Create GitHub releases with built installers
3. Add auto-update functionality
4. Set up CI/CD for automatic builds (GitHub Actions)
