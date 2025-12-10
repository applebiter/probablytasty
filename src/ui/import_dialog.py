"""
Import recipe dialog for fetching recipes from URLs.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QTextEdit, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from typing import Optional, Dict


class ImportWorker(QThread):
    """Worker thread for importing recipes."""
    
    finished = Signal(object)  # Emits recipe data or None
    error = Signal(str)
    
    def __init__(self, url: str, importer):
        super().__init__()
        self.url = url
        self.importer = importer
    
    def run(self):
        """Import recipe in background thread."""
        try:
            recipe_data = self.importer.import_from_url(self.url)
            self.finished.emit(recipe_data)
        except Exception as e:
            self.error.emit(str(e))


class ImportRecipeDialog(QDialog):
    """Dialog for importing recipes from URLs."""
    
    def __init__(self, importer, parent=None):
        super().__init__(parent)
        self.importer = importer
        self.recipe_data = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Import Recipe from URL")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel(
            "Enter a recipe URL from any major cooking website.\n"
            "Supports AllRecipes, Food Network, NYTimes Cooking, and 100+ more!"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.example.com/recipe...")
        self.url_input.returnPressed.connect(self.fetch_recipe)
        url_layout.addWidget(self.url_input)
        
        fetch_btn = QPushButton("Fetch")
        fetch_btn.clicked.connect(self.fetch_recipe)
        url_layout.addWidget(fetch_btn)
        
        layout.addLayout(url_layout)
        
        # Preview area
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Recipe preview will appear here after fetching...")
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.accept)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def fetch_recipe(self):
        """Fetch recipe from URL."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Invalid URL", "Please enter a URL.")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_input.setText(url)
        
        # Show progress dialog
        progress = QProgressDialog("Fetching recipe...", None, 0, 0, self)
        progress.setWindowTitle("Import Recipe")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # Start worker thread
        self.worker = ImportWorker(url, self.importer)
        self.worker.finished.connect(lambda data: self.on_fetch_complete(data, progress))
        self.worker.error.connect(lambda err: self.on_fetch_error(err, progress))
        self.worker.start()
    
    def on_fetch_complete(self, recipe_data: Optional[Dict], progress: QProgressDialog):
        """Handle successful fetch."""
        progress.close()
        
        if not recipe_data:
            QMessageBox.warning(
                self,
                "Import Failed",
                "Could not extract recipe from URL.\n\n"
                "This site may not be supported, or the page may not contain a recipe."
            )
            return
        
        self.recipe_data = recipe_data
        self.display_preview(recipe_data)
        self.import_btn.setEnabled(True)
    
    def on_fetch_error(self, error: str, progress: QProgressDialog):
        """Handle fetch error."""
        progress.close()
        QMessageBox.critical(
            self,
            "Error",
            f"Failed to fetch recipe:\n\n{error}"
        )
    
    def display_preview(self, recipe_data: Dict):
        """Display recipe preview."""
        preview = f"""Title: {recipe_data.get('title', 'Unknown')}

Description: {recipe_data.get('description', 'None')}

Servings: {recipe_data.get('servings', 'Unknown')}
Prep Time: {recipe_data.get('prep_time_minutes', '?')} minutes
Cook Time: {recipe_data.get('cook_time_minutes', '?')} minutes

Ingredients ({len(recipe_data.get('ingredients', []))} items):
"""
        
        for ing in recipe_data.get('ingredients', [])[:10]:  # Show first 10
            preview += f"  • {ing.get('quantity', '')} {ing.get('unit', '')} {ing.get('name', '')}\n"
        
        if len(recipe_data.get('ingredients', [])) > 10:
            preview += f"  ... and {len(recipe_data['ingredients']) - 10} more\n"
        
        preview += f"\nInstructions:\n{recipe_data.get('instructions', 'None')[:500]}..."
        
        self.preview_text.setPlainText(preview)
    
    def get_recipe_data(self) -> Optional[Dict]:
        """Get the imported recipe data."""
        return self.recipe_data
