"""
Main application entry point.
"""

import sys
from PySide6.QtWidgets import QApplication
from src.models.database import init_database, get_session
from src.ui import MainWindow
from src.controller import AppController


def main():
    """Main application function."""
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ProbablyTasty")
    app.setOrganizationName("ProbablyTasty")
    
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
