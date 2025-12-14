# ProbablyTasty v1.0.1 Release Notes

## What's Fixed

### HTML Export
- **Fixed missing template**: Restored the HTML recipe export template that was missing in v1.0.0
- **Beautiful design**: Self-contained HTML exports with teal theme matching the app
- **Interactive features**: 
  - Scale recipes by servings with automatic fraction formatting (¼, ½, ¾)
  - Convert between imperial and metric units
  - Interactive ingredient checklist
  - Print-friendly layout

### User Interface
- **Fixed splitter ratio**: Changed default split to 50/50 (was 1:2) to prevent button text cutoff
- **Added User Guide**: New Help → User Guide menu item opens comprehensive documentation
- **Improved Guide display**: Proper vertical spacing and formatting for better readability

### Documentation
- **USER_GUIDE.md**: Comprehensive 14KB help guide covering all features
  - Getting Started
  - Adding Recipes (manual, URL, photo, file import)
  - Search and Tags
  - Kitchen Tools (scaling, conversion, shopping lists)
  - Exporting & Sharing
  - Settings and Troubleshooting
  - Quick Reference cheat sheet

### Code Quality
- **Removed debug output**: Cleaned up all console logging for professional operation
- **Fixed line endings**: Corrected run.sh script for Linux compatibility

## Installation

### Linux
1. Download `ProbablyTasty-v1.0.1-linux.tar.gz`
2. Extract: `tar -xzf ProbablyTasty-v1.0.1-linux.tar.gz`
3. Run: `cd ProbablyTasty && ./ProbablyTasty`

### Windows
1. Download `ProbablyTasty-v1.0.1-windows.zip`
2. Extract to a folder
3. Run: `ProbablyTasty.exe`

## Notes
- This release fixes critical issues from v1.0.0
- All features now fully functional in compiled executables
- HTML export tested and working with template properly bundled

## Full Changelog
- Restored HTML recipe export template (24KB with JavaScript interactivity)
- Fixed PyInstaller spec to include templates and documentation
- Added USER_GUIDE.md with elderly-friendly instructions
- Implemented User Guide dialog with CSS styling
- Changed UI splitter from 1:2 to 50/50 ratio
- Removed all debug console output
- Fixed run.sh permissions and line endings
