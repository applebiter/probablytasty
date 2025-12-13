"""
Main application entry point.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from src.models.database import init_database, get_session
from src.ui import MainWindow
from src.controller import AppController


def load_settings():
    """Load application settings."""
    try:
        settings_file = Path.home() / ".probablytasty" / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"font_size": 10, "theme": "light"}  # Defaults


def load_theme_stylesheet(theme: str) -> str:
    """Load theme stylesheet."""
    # PyInstaller compatibility
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        theme_file = base_path / "src" / "ui" / "themes" / f"{theme}.qss"
    else:
        theme_file = Path(__file__).parent / "ui" / "themes" / f"{theme}.qss"
    
    try:
        if theme_file.exists():
            with open(theme_file, 'r') as f:
                return f.read()
    except Exception as e:
        print(f"Failed to load theme {theme}: {e}")
    return ""


def main():
    """Main application function."""
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Load settings
    settings = load_settings()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ProbablyTasty")
    app.setOrganizationName("ProbablyTasty")
    
    # Set application icon
    icon_path = Path(__file__).parent.parent / "icons" / "applebiter.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Apply theme
    theme = settings.get("theme", "light")
    stylesheet = load_theme_stylesheet(theme)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Apply font size from settings
    font_size = settings.get("font_size", 10)
    font = QFont()
    font.setPointSize(font_size)
    app.setFont(font)
    
    # Get database session
    session = get_session()
    
    # Create main window
    window = MainWindow()
    
    # Create controller
    controller = AppController(session, window)
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
