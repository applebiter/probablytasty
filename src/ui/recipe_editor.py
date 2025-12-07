"""
Recipe editor dialog for creating and editing recipes.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QComboBox, QLabel,
)
from PySide6.QtCore import Qt
from typing import Optional, List, Tuple


class RecipeEditorDialog(QDialog):
    """Dialog for creating and editing recipes."""
    
    def __init__(self, parent=None, recipe_data: Optional[dict] = None):
        super().__init__(parent)
        self.recipe_data = recipe_data or {}
        self.init_ui()
        
        if recipe_data:
            self.load_recipe_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Recipe Editor")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Basic information form
        form_layout = QFormLayout()
        
        self.title_input = QLineEdit()
        form_layout.addRow("Title:", self.title_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_input)
        
        # Time and servings
        time_layout = QHBoxLayout()
        
        self.servings_input = QSpinBox()
        self.servings_input.setMinimum(1)
        self.servings_input.setMaximum(100)
        self.servings_input.setValue(4)
        time_layout.addWidget(QLabel("Servings:"))
        time_layout.addWidget(self.servings_input)
        
        self.prep_time_input = QSpinBox()
        self.prep_time_input.setMinimum(0)
        self.prep_time_input.setMaximum(1440)
        self.prep_time_input.setSuffix(" min")
        time_layout.addWidget(QLabel("Prep:"))
        time_layout.addWidget(self.prep_time_input)
        
        self.cook_time_input = QSpinBox()
        self.cook_time_input.setMinimum(0)
        self.cook_time_input.setMaximum(1440)
        self.cook_time_input.setSuffix(" min")
        time_layout.addWidget(QLabel("Cook:"))
        time_layout.addWidget(self.cook_time_input)
        
        time_layout.addStretch()
        form_layout.addRow("", time_layout)
        
        self.source_url_input = QLineEdit()
        form_layout.addRow("Source URL:", self.source_url_input)
        
        layout.addLayout(form_layout)
        
        # Ingredients section
        ingredients_label = QLabel("Ingredients")
        ingredients_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(ingredients_label)
        
        self.ingredients_table = QTableWidget()
        self.ingredients_table.setColumnCount(4)
        self.ingredients_table.setHorizontalHeaderLabels(
            ["Quantity", "Unit", "Ingredient", "Preparation"]
        )
        self.ingredients_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.ingredients_table.setMinimumHeight(150)
        layout.addWidget(self.ingredients_table)
        
        # Ingredient buttons
        ingredient_btn_layout = QHBoxLayout()
        add_ingredient_btn = QPushButton("Add Ingredient")
        add_ingredient_btn.clicked.connect(self.add_ingredient_row)
        ingredient_btn_layout.addWidget(add_ingredient_btn)
        
        remove_ingredient_btn = QPushButton("Remove Selected")
        remove_ingredient_btn.clicked.connect(self.remove_ingredient_row)
        ingredient_btn_layout.addWidget(remove_ingredient_btn)
        
        ingredient_btn_layout.addStretch()
        layout.addLayout(ingredient_btn_layout)
        
        # Instructions
        instructions_label = QLabel("Instructions")
        instructions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(instructions_label)
        
        self.instructions_input = QTextEdit()
        self.instructions_input.setMinimumHeight(200)
        layout.addWidget(self.instructions_input)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags (comma-separated):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., vegetarian, quick, dessert")
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def add_ingredient_row(self):
        """Add a new ingredient row to the table."""
        row = self.ingredients_table.rowCount()
        self.ingredients_table.insertRow(row)
        
        # Add default items
        self.ingredients_table.setItem(row, 0, QTableWidgetItem("1"))
        self.ingredients_table.setItem(row, 1, QTableWidgetItem("cup"))
        self.ingredients_table.setItem(row, 2, QTableWidgetItem(""))
        self.ingredients_table.setItem(row, 3, QTableWidgetItem(""))
    
    def remove_ingredient_row(self):
        """Remove the selected ingredient row."""
        current_row = self.ingredients_table.currentRow()
        if current_row >= 0:
            self.ingredients_table.removeRow(current_row)
    
    def load_recipe_data(self):
        """Load existing recipe data into the form."""
        if "title" in self.recipe_data:
            self.title_input.setText(self.recipe_data["title"])
        
        if "description" in self.recipe_data:
            self.description_input.setText(self.recipe_data["description"] or "")
        
        if "servings" in self.recipe_data:
            self.servings_input.setValue(self.recipe_data["servings"])
        
        if "prep_time_minutes" in self.recipe_data:
            self.prep_time_input.setValue(self.recipe_data["prep_time_minutes"] or 0)
        
        if "cook_time_minutes" in self.recipe_data:
            self.cook_time_input.setValue(self.recipe_data["cook_time_minutes"] or 0)
        
        if "source_url" in self.recipe_data:
            self.source_url_input.setText(self.recipe_data["source_url"] or "")
        
        if "instructions" in self.recipe_data:
            self.instructions_input.setText(self.recipe_data["instructions"])
        
        # Load ingredients
        if "ingredients" in self.recipe_data:
            for ingredient in self.recipe_data["ingredients"]:
                row = self.ingredients_table.rowCount()
                self.ingredients_table.insertRow(row)
                
                self.ingredients_table.setItem(
                    row, 0, QTableWidgetItem(str(ingredient.get("quantity", 1)))
                )
                self.ingredients_table.setItem(
                    row, 1, QTableWidgetItem(ingredient.get("unit", ""))
                )
                self.ingredients_table.setItem(
                    row, 2, QTableWidgetItem(ingredient.get("name", ""))
                )
                self.ingredients_table.setItem(
                    row, 3, QTableWidgetItem(ingredient.get("preparation", ""))
                )
        
        # Load tags
        if "tags" in self.recipe_data:
            tags_text = ", ".join(self.recipe_data["tags"])
            self.tags_input.setText(tags_text)
    
    def get_recipe_data(self) -> Optional[dict]:
        """Get the recipe data from the form."""
        # Validate required fields
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Please enter a recipe title.")
            return None
        
        instructions = self.instructions_input.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(self, "Validation Error", "Please enter cooking instructions.")
            return None
        
        # Collect ingredients
        ingredients = []
        for row in range(self.ingredients_table.rowCount()):
            quantity_item = self.ingredients_table.item(row, 0)
            unit_item = self.ingredients_table.item(row, 1)
            name_item = self.ingredients_table.item(row, 2)
            prep_item = self.ingredients_table.item(row, 3)
            
            if name_item and name_item.text().strip():
                try:
                    quantity = float(quantity_item.text() if quantity_item else 1)
                except ValueError:
                    quantity = 1
                
                ingredients.append({
                    "quantity": quantity,
                    "unit": unit_item.text().strip() if unit_item else "",
                    "name": name_item.text().strip(),
                    "preparation": prep_item.text().strip() if prep_item else "",
                })
        
        # Collect tags
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        return {
            "title": title,
            "description": self.description_input.toPlainText().strip(),
            "servings": self.servings_input.value(),
            "prep_time_minutes": self.prep_time_input.value(),
            "cook_time_minutes": self.cook_time_input.value(),
            "source_url": self.source_url_input.text().strip(),
            "instructions": instructions,
            "ingredients": ingredients,
            "tags": tags,
        }
