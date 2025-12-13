"""
Dialog for scaling recipe servings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSpinBox, QPushButton, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt


class RecipeScalingDialog(QDialog):
    """Dialog for scaling a recipe to different serving sizes."""
    
    def __init__(self, recipe, scaling_service, parent=None):
        super().__init__(parent)
        self.recipe = recipe
        self.scaling_service = scaling_service
        self.scaled_data = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Scale Recipe: {self.recipe.title}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Recipe info
        info_group = QGroupBox("Recipe Information")
        info_layout = QFormLayout()
        
        title_label = QLabel(self.recipe.title)
        title_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Recipe:", title_label)
        
        original_servings_label = QLabel(str(self.recipe.servings))
        info_layout.addRow("Original Servings:", original_servings_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Scaling controls
        scale_group = QGroupBox("Scale To")
        scale_layout = QHBoxLayout()
        
        scale_layout.addWidget(QLabel("Target Servings:"))
        
        self.servings_spin = QSpinBox()
        self.servings_spin.setMinimum(1)
        self.servings_spin.setMaximum(100)
        self.servings_spin.setValue(self.recipe.servings * 2)  # Default to double
        self.servings_spin.valueChanged.connect(self.on_servings_changed)
        scale_layout.addWidget(self.servings_spin)
        
        scale_layout.addStretch()
        
        # Quick scale buttons
        quick_label = QLabel("Quick Scale:")
        scale_layout.addWidget(quick_label)
        
        half_btn = QPushButton("½")
        half_btn.clicked.connect(lambda: self.quick_scale(0.5))
        scale_layout.addWidget(half_btn)
        
        double_btn = QPushButton("2x")
        double_btn.clicked.connect(lambda: self.quick_scale(2))
        scale_layout.addWidget(double_btn)
        
        triple_btn = QPushButton("3x")
        triple_btn.clicked.connect(lambda: self.quick_scale(3))
        scale_layout.addWidget(triple_btn)
        
        scale_group.setLayout(scale_layout)
        layout.addWidget(scale_group)
        
        # Scale factor display
        self.scale_factor_label = QLabel()
        self.scale_factor_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.scale_factor_label)
        
        # Preview of scaled ingredients
        preview_group = QGroupBox("Scaled Ingredients Preview")
        preview_layout = QVBoxLayout()
        
        self.ingredients_preview = QTextEdit()
        self.ingredients_preview.setReadOnly(True)
        self.ingredients_preview.setMinimumHeight(200)
        preview_layout.addWidget(self.ingredients_preview)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Note about instructions
        note_label = QLabel(
            "Note: Cooking times and instructions will remain the same. "
            "You may need to adjust baking times or pan sizes for very large scaling."
        )
        note_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save as New Recipe")
        save_btn.clicked.connect(self.on_save)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Initial preview
        self.update_preview()
    
    def quick_scale(self, factor: float):
        """Quick scale button handler."""
        target = int(self.recipe.servings * factor)
        if target < 1:
            target = 1
        self.servings_spin.setValue(target)
    
    def on_servings_changed(self, value: int):
        """Handle servings value change."""
        self.update_preview()
    
    def update_preview(self):
        """Update the preview of scaled ingredients."""
        target_servings = self.servings_spin.value()
        
        try:
            self.scaled_data = self.scaling_service.scale_recipe(self.recipe, target_servings)
            
            # Update scale factor label
            scale_factor = self.scaled_data['scale_factor']
            self.scale_factor_label.setText(
                f"Scaling by {scale_factor:.2f}x "
                f"({self.recipe.servings} → {target_servings} servings)"
            )
            
            # Update ingredients preview
            ingredients_text = self.scaling_service.format_scaled_ingredients_text(
                self.scaled_data['ingredients']
            )
            self.ingredients_preview.setPlainText(ingredients_text)
            
        except Exception as e:
            self.ingredients_preview.setPlainText(f"Error scaling recipe: {str(e)}")
    
    def on_save(self):
        """Handle save button click."""
        if self.scaled_data:
            self.accept()
        else:
            self.reject()
    
    def get_scaled_data(self):
        """Return the scaled recipe data."""
        return self.scaled_data
