"""
Main window for ProbablyTasty application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QTextEdit,
    QLabel, QSplitter, QMessageBox, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List
from src.models import Recipe


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_recipe: Optional[Recipe] = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ProbablyTasty - Recipe Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Recipe list and search
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Recipe details
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with search and recipe list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Search section
        search_label = QLabel("Search Recipes")
        search_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(search_label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, ingredients, or natural language...")
        self.search_input.returnPressed.connect(self.on_search)
        layout.addWidget(self.search_input)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.on_search)
        layout.addWidget(search_btn)
        
        # Recipe list
        recipes_label = QLabel("Recipes")
        recipes_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(recipes_label)
        
        self.recipe_list = QListWidget()
        self.recipe_list.itemClicked.connect(self.on_recipe_selected)
        layout.addWidget(self.recipe_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("New Recipe")
        new_btn.clicked.connect(self.on_new_recipe)
        button_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.on_delete_recipe)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with recipe details."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Recipe title
        self.recipe_title = QLabel("Select a recipe")
        self.recipe_title.setStyleSheet("font-weight: bold; font-size: 18px;")
        layout.addWidget(self.recipe_title)
        
        # Recipe metadata
        self.recipe_meta = QLabel("")
        self.recipe_meta.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.recipe_meta)
        
        # Description
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(desc_label)
        
        self.recipe_description = QTextEdit()
        self.recipe_description.setReadOnly(True)
        self.recipe_description.setMaximumHeight(100)
        layout.addWidget(self.recipe_description)
        
        # Ingredients
        ingredients_label = QLabel("Ingredients")
        ingredients_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(ingredients_label)
        
        self.ingredients_list = QListWidget()
        self.ingredients_list.setMaximumHeight(200)
        layout.addWidget(self.ingredients_list)
        
        # Instructions
        instructions_label = QLabel("Instructions")
        instructions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(instructions_label)
        
        self.recipe_instructions = QTextEdit()
        self.recipe_instructions.setReadOnly(True)
        layout.addWidget(self.recipe_instructions)
        
        # Edit button
        edit_btn = QPushButton("Edit Recipe")
        edit_btn.clicked.connect(self.on_edit_recipe)
        layout.addWidget(edit_btn)
        
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = file_menu.addAction("Import Recipes...")
        import_action.triggered.connect(self.on_import)
        
        export_action = file_menu.addAction("Export Recipes...")
        export_action.triggered.connect(self.on_export)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        preferences_action = settings_menu.addAction("Preferences...")
        preferences_action.triggered.connect(self.on_preferences)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)
    
    def load_recipes(self, recipes: List[Recipe]):
        """Load recipes into the list widget."""
        self.recipe_list.clear()
        for recipe in recipes:
            item = QListWidgetItem(recipe.title)
            item.setData(Qt.UserRole, recipe.id)
            self.recipe_list.addItem(item)
    
    def display_recipe(self, recipe: Recipe):
        """Display recipe details in the right panel."""
        self.current_recipe = recipe
        
        # Update title
        self.recipe_title.setText(recipe.title)
        
        # Update metadata
        meta_parts = []
        if recipe.servings:
            meta_parts.append(f"Serves {recipe.servings}")
        if recipe.prep_time_minutes:
            meta_parts.append(f"Prep: {recipe.prep_time_minutes} min")
        if recipe.cook_time_minutes:
            meta_parts.append(f"Cook: {recipe.cook_time_minutes} min")
        if recipe.total_time_minutes:
            meta_parts.append(f"Total: {recipe.total_time_minutes} min")
        
        self.recipe_meta.setText(" | ".join(meta_parts) if meta_parts else "")
        
        # Update description
        self.recipe_description.setText(recipe.description or "No description")
        
        # Update ingredients
        self.ingredients_list.clear()
        for ri in recipe.ingredients:
            ingredient = ri.ingredient
            text = f"{ri.display_quantity} {ri.display_unit} {ingredient.name}"
            if ri.preparation:
                text += f", {ri.preparation}"
            self.ingredients_list.addItem(text)
        
        # Update instructions
        self.recipe_instructions.setText(recipe.instructions)
        
        # Update tags display in metadata if present
        if recipe.tags:
            tag_text = ", ".join([tag.name for tag in recipe.tags])
            current_meta = self.recipe_meta.text()
            if current_meta:
                self.recipe_meta.setText(f"{current_meta}\nTags: {tag_text}")
            else:
                self.recipe_meta.setText(f"Tags: {tag_text}")
    
    def clear_recipe_display(self):
        """Clear the recipe display."""
        self.current_recipe = None
        self.recipe_title.setText("Select a recipe")
        self.recipe_meta.setText("")
        self.recipe_description.clear()
        self.ingredients_list.clear()
        self.recipe_instructions.clear()
    
    # Event handlers (to be connected to controller)
    def on_search(self):
        """Handle search button click."""
        pass  # Will be connected to controller
    
    def on_recipe_selected(self, item: QListWidgetItem):
        """Handle recipe selection."""
        pass  # Will be connected to controller
    
    def on_new_recipe(self):
        """Handle new recipe button."""
        pass  # Will be connected to controller
    
    def on_edit_recipe(self):
        """Handle edit recipe button."""
        pass  # Will be connected to controller
    
    def on_delete_recipe(self):
        """Handle delete recipe button."""
        if not self.current_recipe:
            QMessageBox.warning(self, "No Selection", "Please select a recipe to delete.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_recipe.title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            pass  # Will be connected to controller
    
    def on_import(self):
        """Handle import menu action."""
        pass  # Will be connected to controller
    
    def on_export(self):
        """Handle export menu action."""
        pass  # Will be connected to controller
    
    def on_preferences(self):
        """Handle preferences menu action."""
        pass  # Will be connected to controller
    
    def on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About ProbablyTasty",
            "<h3>ProbablyTasty</h3>"
            "<p>An intelligent recipe management application with AI-powered search.</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with PySide6 and Python</p>"
        )
