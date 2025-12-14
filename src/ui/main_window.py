"""
Main window for ProbablyTasty application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QTextEdit,
    QLabel, QSplitter, QMessageBox, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from typing import Optional, List
from pathlib import Path
from src.models import Recipe
from src.ui.unit_conversion_dialog import format_quantity_as_fraction


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
        
        # Set window icon
        icon_path = Path(__file__).parent.parent.parent / "icons" / "applebiter.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
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
        
        # Set initial splitter sizes (50/50 split)
        splitter.setSizes([1, 1])
        
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
        
        # Search buttons row
        search_btn_layout = QHBoxLayout()
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.on_search)
        search_btn_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("✕ Clear")
        clear_btn.clicked.connect(self.on_clear_search)
        search_btn_layout.addWidget(clear_btn)
        layout.addLayout(search_btn_layout)
        
        # Filters section
        from PySide6.QtWidgets import QComboBox, QCheckBox
        filters_layout = QHBoxLayout()
        
        # Max time filter
        time_label = QLabel("Total Time:")
        filters_layout.addWidget(time_label)
        
        self.max_time_combo = QComboBox()
        self.max_time_combo.addItems([
            "Any",
            "15 min",
            "30 min",
            "45 min",
            "1 hour",
            "2 hours"
        ])
        self.max_time_combo.currentTextChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.max_time_combo)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # Recipe tree view
        recipes_label = QLabel("Recipes")
        recipes_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(recipes_label)
        
        from PySide6.QtWidgets import QTreeWidget
        from PySide6.QtCore import Qt
        
        self.recipe_tree = QTreeWidget()
        self.recipe_tree.setHeaderHidden(True)
        self.recipe_tree.itemClicked.connect(self.on_recipe_selected)
        self.recipe_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recipe_tree.customContextMenuRequested.connect(self.on_tree_context_menu)
        layout.addWidget(self.recipe_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ New Recipe")
        new_btn.clicked.connect(self.on_new_recipe)
        button_layout.addWidget(new_btn)
        
        import_url_btn = QPushButton("🔗 Import URL")
        import_url_btn.clicked.connect(self.on_import_url)
        button_layout.addWidget(import_url_btn)
        
        import_images_btn = QPushButton("📷 Import Images")
        import_images_btn.clicked.connect(self.on_import_images)
        button_layout.addWidget(import_images_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
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
        
        # Ingredients with convert button
        ingredients_header = QHBoxLayout()
        ingredients_label = QLabel("Ingredients")
        ingredients_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        ingredients_header.addWidget(ingredients_label)
        
        ingredients_header.addStretch()
        
        self.scale_recipe_btn = QPushButton("Scale Recipe")
        self.scale_recipe_btn.clicked.connect(self.on_scale_recipe)
        self.scale_recipe_btn.setEnabled(False)
        ingredients_header.addWidget(self.scale_recipe_btn)
        
        self.convert_units_btn = QPushButton("Convert Units")
        self.convert_units_btn.clicked.connect(self.on_convert_units)
        self.convert_units_btn.setEnabled(False)
        ingredients_header.addWidget(self.convert_units_btn)
        
        layout.addLayout(ingredients_header)
        
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
        
        # Action buttons
        action_buttons = QHBoxLayout()
        action_buttons.addStretch()
        
        self.print_recipe_btn = QPushButton("🖨️ Print Recipe")
        self.print_recipe_btn.clicked.connect(self.on_print_recipe)
        self.print_recipe_btn.setEnabled(False)
        action_buttons.addWidget(self.print_recipe_btn)
        
        edit_btn = QPushButton("✏️ Edit Recipe")
        edit_btn.clicked.connect(self.on_edit_recipe)
        action_buttons.addWidget(edit_btn)
        
        layout.addLayout(action_buttons)
        
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        
        import_action = file_menu.addAction("📥 Import Recipes...")
        import_action.triggered.connect(self.on_import)
        
        import_url_action = file_menu.addAction("🔗 Import from URL...")
        import_url_action.triggered.connect(self.on_import_url)
        
        import_image_action = file_menu.addAction("📷 Import from Images...")
        import_image_action.triggered.connect(self.on_import_images)
        
        export_action = file_menu.addAction("📤 Export Recipes...")
        export_action.triggered.connect(self.on_export)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("🚪 Exit")
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu("🔧 Tools")
        
        shopping_list_action = tools_menu.addAction("🛒 Generate Shopping List...")
        shopping_list_action.triggered.connect(self.on_shopping_list)
        
        # Settings menu
        settings_menu = menubar.addMenu("⚙️ Settings")
        
        preferences_action = settings_menu.addAction("⚙️ Preferences...")
        preferences_action.triggered.connect(self.on_preferences)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = help_menu.addAction("ℹ️ About")
        about_action.triggered.connect(self.on_about)
    
    def load_recipes(self, recipes: List[Recipe]):
        """Load recipes into the tree widget organized by tags."""
        self.recipe_tree.clear()
        
        if not recipes:
            return
        
        self._build_tag_tree(recipes)
    
    def _build_tag_tree(self, recipes: List[Recipe]):
        """Build simple tree grouping recipes by tags (no hierarchy)."""
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt
        
        # Group recipes by tag
        recipes_by_tag = {}
        untagged_recipes = []
        
        for recipe in recipes:
            if recipe.tags:
                for tag in recipe.tags:
                    if tag.name not in recipes_by_tag:
                        recipes_by_tag[tag.name] = []
                    recipes_by_tag[tag.name].append(recipe)
            else:
                untagged_recipes.append(recipe)
        
        # Create tag folders and add recipes
        for tag_name in sorted(recipes_by_tag.keys()):
            tag_item = QTreeWidgetItem([f"{tag_name} ({len(recipes_by_tag[tag_name])})"])
            tag_item.setData(0, Qt.UserRole, None)
            tag_item.setData(0, Qt.UserRole + 1, "tag")
            self.recipe_tree.addTopLevelItem(tag_item)
            
            for recipe in sorted(recipes_by_tag[tag_name], key=lambda r: r.title):
                recipe_item = QTreeWidgetItem(tag_item, [recipe.title])
                recipe_item.setData(0, Qt.UserRole, recipe.id)
                recipe_item.setData(0, Qt.UserRole + 1, "recipe")
        
        # Add untagged recipes
        if untagged_recipes:
            untagged_item = QTreeWidgetItem([f"Untagged ({len(untagged_recipes)})"])
            untagged_item.setData(0, Qt.UserRole, None)
            untagged_item.setData(0, Qt.UserRole + 1, "category")
            self.recipe_tree.addTopLevelItem(untagged_item)
            
            for recipe in sorted(untagged_recipes, key=lambda r: r.title):
                recipe_item = QTreeWidgetItem(untagged_item, [recipe.title])
                recipe_item.setData(0, Qt.UserRole, recipe.id)
                recipe_item.setData(0, Qt.UserRole + 1, "recipe")
        
        # Keep all categories collapsed by default
        self.recipe_tree.collapseAll()
    
    def expand_recipe_nodes(self, recipe_id: int):
        """Expand all tag nodes that contain the specified recipe."""
        from PySide6.QtCore import Qt
        
        # Find all items with this recipe_id and expand their parents
        def find_and_expand(item, parent_item=None):
            # Check if this is a recipe item with matching ID
            if item.data(0, Qt.UserRole + 1) == "recipe" and item.data(0, Qt.UserRole) == recipe_id:
                # Expand the parent tag node
                if parent_item:
                    parent_item.setExpanded(True)
                return True
            
            # Recursively check children
            found = False
            for i in range(item.childCount()):
                if find_and_expand(item.child(i), item):
                    found = True
            
            return found
        
        # Search through all top-level items
        for i in range(self.recipe_tree.topLevelItemCount()):
            find_and_expand(self.recipe_tree.topLevelItem(i))
    
    def display_recipe(self, recipe: Recipe):
        """Display recipe details in the right panel."""
        self.current_recipe = recipe
        
        # Enable action buttons
        self.scale_recipe_btn.setEnabled(True)
        self.convert_units_btn.setEnabled(True)
        self.print_recipe_btn.setEnabled(True)
        
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
            # Convert display_quantity to fraction if it's numeric
            try:
                quantity_value = float(ri.display_quantity)
                formatted_quantity = format_quantity_as_fraction(quantity_value)
            except (ValueError, TypeError):
                # Keep as-is if not numeric (e.g., ranges like "4-6")
                formatted_quantity = ri.display_quantity
            
            text = f"{formatted_quantity} {ri.display_unit} {ingredient.name}"
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
        self.scale_recipe_btn.setEnabled(False)
        self.convert_units_btn.setEnabled(False)
        self.print_recipe_btn.setEnabled(False)
        self.recipe_title.setText("Select a recipe")
        self.recipe_meta.setText("")
        self.recipe_description.clear()
        self.ingredients_list.clear()
        self.recipe_instructions.clear()
    
    # Event handlers (to be connected to controller)
    def on_search(self):
        """Handle search button click"""
        pass  # Will be connected to controller
    
    def on_clear_search(self):
        """Clear search input and filters, return tree to default state"""
        self.search_input.clear()
        self.max_time_combo.setCurrentIndex(0)
        if hasattr(self, 'controller') and self.controller:
            self.controller.load_all_recipes()
            # Collapse all nodes back to default state
            self.recipe_tree.collapseAll()
    
    def on_filter_changed(self):
        """Handle filter change - trigger search if there's query text"""
        if self.search_input.text().strip():
            self.on_search()
    
    def on_recipe_selected(self, item, column=0):
        """Handle recipe selection from tree."""
        # This will be overridden by controller
        pass
    
    def on_tree_context_menu(self, position):
        """Handle right-click context menu on tree."""
        from PySide6.QtCore import Qt
        
        item = self.recipe_tree.itemAt(position)
        if not item:
            return
        
        item_type = item.data(0, Qt.UserRole + 1)
        menu = QMenu()
        
        if item_type == "recipe":
            edit_action = menu.addAction("Edit Recipe")
            menu.addSeparator()
            delete_action = menu.addAction("Delete Recipe")
            
            action = menu.exec_(self.recipe_tree.viewport().mapToGlobal(position))
            
            if action == edit_action:
                self.on_edit_recipe()
            elif action == delete_action:
                self.on_delete_recipe()
    
    def on_new_recipe(self):
        """Handle new recipe button."""
        pass  # Will be connected to controller
    
    def on_import_url(self):
        """Handle import from URL button."""
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
    
    def on_import_images(self):
        """Handle import from images menu action."""
        pass  # Will be connected to controller
    
    def on_export(self):
        """Handle export menu action."""
        pass  # Will be connected to controller
    
    def on_preferences(self):
        """Handle preferences menu action."""
        pass  # Will be connected to controller
    
    def on_scale_recipe(self):
        """Handle scale recipe button click."""
        pass  # Will be connected to controller
    
    def on_convert_units(self):
        """Handle convert units button click."""
        pass  # Will be connected to controller
    
    def on_print_recipe(self):
        """Handle print recipe button click."""
        pass  # Will be connected to controller
    
    def on_shopping_list(self):
        """Handle shopping list menu click."""
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
            "<p style='margin-top: 10px;'><i>Made by applebiter for his mother.</i></p>"
        )
