"""
Dialog for generating shopping lists from multiple recipes.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
from typing import List
from src.models import Recipe


class ShoppingListDialog(QDialog):
    """Dialog for selecting recipes and generating a shopping list."""
    
    def __init__(self, all_recipes: List[Recipe], shopping_list_service, parent=None):
        super().__init__(parent)
        self.all_recipes = all_recipes
        self.shopping_list_service = shopping_list_service
        self.selected_recipes = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Generate Shopping List")
        self.setModal(True)
        self.resize(1000, 700)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info = QLabel(
            "Select recipes to include in your shopping list. "
            "Ingredients will be automatically consolidated and converted to appropriate units."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Main horizontal split: recipe selection | selected list | shopping list preview
        main_layout = QHBoxLayout()
        
        # Left side - Recipe selection with search
        left_group = QGroupBox("Available Recipes")
        left_layout = QVBoxLayout()
        
        # Search box
        from PySide6.QtWidgets import QLineEdit
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search recipes...")
        self.search_input.textChanged.connect(self.filter_recipes)
        left_layout.addWidget(self.search_input)
        
        # Recipe list with checkboxes
        self.recipe_list = QListWidget()
        self.recipe_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Populate with recipes
        for recipe in self.all_recipes:
            item = QListWidgetItem(recipe.title)
            item.setData(Qt.UserRole, recipe)
            item.setCheckState(Qt.Unchecked)
            self.recipe_list.addItem(item)
        
        # Connect item change to update preview
        self.recipe_list.itemChanged.connect(self.on_selection_changed)
        
        left_layout.addWidget(self.recipe_list)
        
        # Selection buttons
        select_btns = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_recipes)
        select_btns.addWidget(select_all_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_recipes)
        select_btns.addWidget(clear_btn)
        
        left_layout.addLayout(select_btns)
        
        left_group.setLayout(left_layout)
        main_layout.addWidget(left_group, 1)
        
        # Middle - Selected recipes list
        middle_group = QGroupBox("Selected Recipes")
        middle_layout = QVBoxLayout()
        
        self.selected_list = QListWidget()
        middle_layout.addWidget(self.selected_list)
        
        # Remove button
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_recipes)
        middle_layout.addWidget(remove_btn)
        
        middle_group.setLayout(middle_layout)
        main_layout.addWidget(middle_group, 1)
        
        # Right side - Shopping list preview
        right_group = QGroupBox("Shopping List Preview")
        right_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText(
            "Select recipes to see the consolidated shopping list..."
        )
        right_layout.addWidget(self.preview_text)
        
        right_group.setLayout(right_layout)
        main_layout.addWidget(right_group, 2)
        
        layout.addLayout(main_layout)
        
        # Status label
        self.status_label = QLabel("0 recipes selected")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.print_btn = QPushButton("Print...")
        self.print_btn.clicked.connect(self.print_shopping_list)
        button_layout.addWidget(self.print_btn)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_btn)
        
        self.export_btn = QPushButton("Export to File")
        self.export_btn.clicked.connect(self.export_to_file)
        button_layout.addWidget(self.export_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Initial update
        self.update_preview()
        self.update_button_states()
    
    def filter_recipes(self, search_text: str):
        """Filter recipe list based on search text."""
        search_lower = search_text.lower()
        
        for i in range(self.recipe_list.count()):
            item = self.recipe_list.item(i)
            recipe = item.data(Qt.UserRole)
            
            # Check if search matches title, description, or tags
            matches = search_lower in recipe.title.lower()
            if not matches and recipe.description:
                matches = search_lower in recipe.description.lower()
            if not matches and recipe.tags:
                matches = any(search_lower in tag.name.lower() for tag in recipe.tags)
            
            # Show/hide item based on match
            item.setHidden(not matches)
    
    def select_all_recipes(self):
        """Select all visible recipes."""
        for i in range(self.recipe_list.count()):
            item = self.recipe_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)
    
    def clear_all_recipes(self):
        """Clear all recipe selections."""
        for i in range(self.recipe_list.count()):
            item = self.recipe_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def remove_selected_recipes(self):
        """Remove selected recipes from the selected list."""
        selected_items = self.selected_list.selectedItems()
        for item in selected_items:
            recipe_title = item.text()
            
            # Uncheck the corresponding item in recipe_list
            for i in range(self.recipe_list.count()):
                recipe_item = self.recipe_list.item(i)
                if recipe_item.text() == recipe_title:
                    recipe_item.setCheckState(Qt.Unchecked)
                    break
    
    def on_selection_changed(self):
        """Handle recipe selection change."""
        self.update_selected_list()
        self.update_preview()
        self.update_button_states()
    
    def update_selected_list(self):
        """Update the list of selected recipes."""
        self.selected_list.clear()
        
        for i in range(self.recipe_list.count()):
            item = self.recipe_list.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_list.addItem(item.text())
    
    def update_button_states(self):
        """Enable/disable action buttons based on whether recipes are selected."""
        has_selection = len(self.selected_recipes) > 0
        self.print_btn.setEnabled(has_selection)
        self.copy_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
    
    def update_preview(self):
        """Update the shopping list preview."""
        # Get selected recipes
        self.selected_recipes = []
        for i in range(self.recipe_list.count()):
            item = self.recipe_list.item(i)
            if item.checkState() == Qt.Checked:
                recipe = item.data(Qt.UserRole)
                self.selected_recipes.append(recipe)
        
        # Update status
        count = len(self.selected_recipes)
        self.status_label.setText(
            f"{count} recipe{'s' if count != 1 else ''} selected"
        )
        
        # Generate shopping list
        if not self.selected_recipes:
            self.preview_text.clear()
            self.preview_text.setPlaceholderText(
                "Select recipes to see the consolidated shopping list..."
            )
            return
        
        try:
            categorized_list = self.shopping_list_service.generate_shopping_list(
                self.selected_recipes
            )
            formatted_text = self.shopping_list_service.format_shopping_list_text(
                categorized_list
            )
            self.preview_text.setPlainText(formatted_text)
        except Exception as e:
            self.preview_text.setPlainText(f"Error generating shopping list:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def copy_to_clipboard(self):
        """Copy shopping list to clipboard."""
        if not self.selected_recipes:
            QMessageBox.warning(
                self,
                "No Recipes Selected",
                "Please select at least one recipe to generate a shopping list."
            )
            return
        
        text = self.preview_text.toPlainText()
        if text:
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            
            self.status_label.setText(
                f"{len(self.selected_recipes)} recipes selected - Copied to clipboard!"
            )
            self.status_label.setStyleSheet("color: green; font-style: italic; padding: 5px;")
    
    def print_shopping_list(self):
        """Print the shopping list."""
        if not self.selected_recipes:
            QMessageBox.warning(
                self,
                "No Recipes Selected",
                "Please select at least one recipe to generate a shopping list."
            )
            return
        
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QTextDocument, QPageLayout
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            # Create a document with the shopping list text
            document = QTextDocument()
            text = self.preview_text.toPlainText()
            html_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            document.setHtml(html_text)
            document.print_(printer)
    
    def export_to_file(self):
        """Export shopping list to a text or PDF file."""
        if not self.selected_recipes:
            QMessageBox.warning(
                self,
                "No Recipes Selected",
                "Please select at least one recipe to generate a shopping list."
            )
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Shopping List",
            "shopping_list.txt",
            "Text Files (*.txt);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if filename:
            try:
                text = self.preview_text.toPlainText()
                
                # Check if PDF was selected
                if selected_filter == "PDF Files (*.pdf)" or filename.lower().endswith('.pdf'):
                    # Export as PDF
                    from PySide6.QtPrintSupport import QPrinter
                    from PySide6.QtGui import QTextDocument, QPageLayout
                    
                    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                    printer.setOutputFileName(filename)
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                    
                    document = QTextDocument()
                    html_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
                    document.setHtml(html_text)
                    document.print_(printer)
                else:
                    # Export as text
                    with open(filename, 'w') as f:
                        f.write(text)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Shopping list exported to:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export shopping list:\n{str(e)}"
                )
