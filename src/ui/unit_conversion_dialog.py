"""
Unit conversion dialog for recipe ingredients.
"""

from fractions import Fraction
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


def format_quantity_as_fraction(value):
    """
    Convert decimal to common cooking fractions (1/2, 1/3, 1/4, 2/3, 3/4).
    Only use fractions that are actually used in cooking.
    Stores as simple decimals: 0.3 for 1/3, 0.6 for 2/3 (easier for scaling).
    """
    if value == int(value):
        return str(int(value))
    
    # Common cooking fractions with their simple decimal approximations
    common_fractions = {
        0.25: "1/4",
        0.3: "1/3",    # Stored as 0.3 (not repeating), displayed as 1/3
        0.5: "1/2",
        0.6: "2/3",    # Stored as 0.6 (not repeating), displayed as 2/3
        0.75: "3/4",
    }
    
    # Extract whole number part
    whole = int(value)
    decimal_part = value - whole
    
    # Find closest common fraction (within 0.08 tolerance for rounding)
    closest_frac = None
    min_diff = 0.08
    
    for dec_val, frac_str in common_fractions.items():
        diff = abs(decimal_part - dec_val)
        if diff < min_diff:
            min_diff = diff
            closest_frac = frac_str
    
    # Build result
    if closest_frac:
        if whole > 0:
            return f"{whole} {closest_frac}"
        else:
            return closest_frac
    else:
        # No close match to common fractions, use decimal
        if value < 1:
            return f"{value:.2f}"
        else:
            return f"{value:.1f}"


class UnitConversionDialog(QDialog):
    """Dialog for converting ingredient measurements between units."""
    
    def __init__(self, conversion_service, parent=None):
        super().__init__(parent)
        self.conversion_service = conversion_service
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Convert Units")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info = QLabel("Convert measurements between different units.")
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Input section
        form_layout = QFormLayout()
        
        # Ingredient name (optional, for better conversions)
        self.ingredient_input = QLineEdit()
        self.ingredient_input.setPlaceholderText("e.g., flour, sugar (optional)")
        form_layout.addRow("Ingredient:", self.ingredient_input)
        
        # Quantity input
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("e.g., 2.5")
        form_layout.addRow("Amount:", self.quantity_input)
        
        # From unit
        self.from_unit_combo = QComboBox()
        form_layout.addRow("From Unit:", self.from_unit_combo)
        
        # To unit
        self.to_unit_combo = QComboBox()
        form_layout.addRow("To Unit:", self.to_unit_combo)
        
        # Populate both combo boxes
        self.populate_units()
        
        layout.addLayout(form_layout)
        
        # Convert button
        convert_btn = QPushButton("Convert")
        convert_btn.clicked.connect(self.perform_conversion)
        convert_btn.setDefault(True)
        layout.addWidget(convert_btn)
        
        # Result display
        self.result_label = QLabel("")
        self.result_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; "
            "padding: 15px; background-color: #f0f0f0; "
            "border: 1px solid #ccc; border-radius: 4px; margin-top: 10px;"
        )
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setMinimumHeight(60)
        layout.addWidget(self.result_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def populate_units(self):
        """Populate unit combo boxes with available units."""
        # Common units organized by type
        units = [
            # Volume (metric)
            "ml", "l",
            # Volume (US)
            "tsp", "tbsp", "cup", "fl oz", "pint", "quart", "gallon",
            # Mass (metric)
            "g", "kg",
            # Mass (imperial)
            "oz", "lb",
            # Count
            "count", "piece", "whole",
        ]
        
        self.from_unit_combo.addItems(units)
        self.to_unit_combo.addItems(units)
        
        # Set common defaults
        self.from_unit_combo.setCurrentText("cup")
        self.to_unit_combo.setCurrentText("g")
    
    def perform_conversion(self):
        """Perform the unit conversion and display result."""
        try:
            # Get input values
            quantity_text = self.quantity_input.text().strip()
            if not quantity_text:
                QMessageBox.warning(self, "Input Required", "Please enter an amount to convert.")
                return
            
            try:
                quantity = float(quantity_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for the amount.")
                return
            
            from_unit = self.from_unit_combo.currentText()
            to_unit = self.to_unit_combo.currentText()
            ingredient = self.ingredient_input.text().strip() or None
            
            # Perform conversion
            result = self.conversion_service.convert(
                quantity=quantity,
                from_unit=from_unit,
                to_unit=to_unit,
                ingredient_name=ingredient
            )
            
            if result is None:
                self.result_label.setText("❌ Cannot convert between these units")
                self.result_label.setStyleSheet(
                    "font-weight: bold; font-size: 14px; "
                    "padding: 15px; background-color: #ffe6e6; "
                    "border: 1px solid #cc0000; border-radius: 4px; margin-top: 10px; color: #cc0000;"
                )
            else:
                # Format result nicely
                if result == int(result):
                    result_text = f"{int(result)}"
                elif result < 0.01:
                    result_text = f"{result:.4f}"
                elif result < 1:
                    result_text = f"{result:.3f}"
                else:
                    result_text = f"{result:.2f}"
                
                ingredient_note = f" of {ingredient}" if ingredient else ""
                
                self.result_label.setText(
                    f"✓ {quantity_text} {from_unit}{ingredient_note} = {result_text} {to_unit}"
                )
                self.result_label.setStyleSheet(
                    "font-weight: bold; font-size: 14px; "
                    "padding: 15px; background-color: #e6f7e6; "
                    "border: 1px solid #00aa00; border-radius: 4px; margin-top: 10px; color: #006600;"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Conversion Error",
                f"An error occurred during conversion:\n{str(e)}"
            )
