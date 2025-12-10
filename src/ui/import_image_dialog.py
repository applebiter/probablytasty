"""
Dialog for importing recipes from images (supports multiple images per recipe).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QFileDialog, QListWidget, QListWidgetItem, 
    QMessageBox, QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QIcon
from pathlib import Path
import base64
import json


class ImageExtractionWorker(QThread):
    """Worker thread for extracting recipe from images using vision model."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(dict)  # Extracted recipe data
    error = Signal(str)  # Error message
    
    def __init__(self, image_paths, ollama_url, vision_model):
        super().__init__()
        self.image_paths = image_paths
        self.ollama_url = ollama_url
        self.vision_model = vision_model
        
    def run(self):
        """Extract recipe from images."""
        try:
            import requests
            
            self.progress.emit("Encoding images...")
            
            # Encode all images to base64
            encoded_images = []
            for i, path in enumerate(self.image_paths, 1):
                self.progress.emit(f"Processing image {i}/{len(self.image_paths)}...")
                with open(path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    encoded_images.append(image_data)
            
            # Construct prompt for recipe extraction
            prompt = """Extract the complete recipe from these images. The recipe may span multiple pages/images, so read them in order.

Please extract and format as follows:

TITLE: [Recipe name]

DESCRIPTION: [Brief description if available]

SERVINGS: [Number of servings]

PREP TIME: [Preparation time]
COOK TIME: [Cooking time]
TOTAL TIME: [Total time]

INGREDIENTS:
[List all ingredients, one per line, exactly as shown]

INSTRUCTIONS:
[List all steps, preserving numbering if present]

NOTES:
[Any additional notes, tips, or variations]

Be thorough and capture all text from all images in order."""

            self.progress.emit(f"Sending {len(self.image_paths)} image(s) to vision model...")
            
            # Call Ollama vision API with all images
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": encoded_images,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for accuracy
                        "num_predict": 2048  # Allow long responses
                    }
                },
                timeout=300  # 5 minute timeout for processing
            )
            
            response.raise_for_status()
            result = response.json()
            
            extracted_text = result.get('response', '')
            
            if not extracted_text:
                self.error.emit("Vision model returned empty response")
                return
            
            self.progress.emit("Parsing extracted text...")
            
            # Parse the extracted text into structured format
            parsed_data = self._parse_extracted_text(extracted_text)
            parsed_data['raw_text'] = extracted_text
            
            self.finished.emit(parsed_data)
            
        except requests.exceptions.Timeout:
            self.error.emit("Request timed out. Try with fewer/smaller images or a faster model.")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Vision model request failed: {str(e)}")
        except Exception as e:
            self.error.emit(f"Failed to extract recipe: {str(e)}")
    
    def _parse_extracted_text(self, text):
        """Parse structured recipe data from extracted text."""
        import re
        
        data = {
            'title': '',
            'description': '',
            'servings': '',
            'prep_time': '',
            'cook_time': '',
            'total_time': '',
            'ingredients': [],
            'instructions': '',
            'notes': ''
        }
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove **bold**
        text = text.replace('---', '')  # Remove horizontal rules
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            # Skip empty lines and pure markdown
            stripped = line.strip()
            if not stripped or stripped == '---':
                continue
            
            line_upper = stripped.upper()
            
            # Detect sections (handle both "TITLE:" and "**TITLE:**" formats)
            if 'TITLE:' in line_upper:
                # Extract everything after "TITLE:"
                match = re.search(r'TITLE:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['title'] = match.group(1).strip()
                current_section = None
            elif 'DESCRIPTION:' in line_upper:
                match = re.search(r'DESCRIPTION:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['description'] = match.group(1).strip()
                current_section = 'description'
            elif 'SERVINGS:' in line_upper:
                match = re.search(r'SERVINGS:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['servings'] = match.group(1).strip()
                current_section = None
            elif 'PREP TIME:' in line_upper:
                match = re.search(r'PREP TIME:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['prep_time'] = match.group(1).strip()
                current_section = None
            elif 'COOK TIME:' in line_upper:
                match = re.search(r'COOK TIME:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['cook_time'] = match.group(1).strip()
                current_section = None
            elif 'TOTAL TIME:' in line_upper:
                match = re.search(r'TOTAL TIME:\s*(.+)', line, re.IGNORECASE)
                if match:
                    data['total_time'] = match.group(1).strip()
                current_section = None
            elif 'INGREDIENTS:' in line_upper:
                current_section = 'ingredients'
            elif 'INSTRUCTIONS:' in line_upper:
                current_section = 'instructions'
            elif 'NOTES:' in line_upper or 'ADDITIONAL' in line_upper:
                current_section = 'notes'
            else:
                # Add content to current section
                if current_section == 'description':
                    # Continue multi-line description
                    if not stripped.startswith(('-', '•', '*', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        data['description'] += ' ' + stripped
                elif current_section == 'ingredients':
                    # Clean up ingredient line - remove bullets and list markers
                    # Be careful not to remove digits that are part of measurements
                    ingredient = stripped
                    # Remove leading bullets/markers: "- ", "* ", "• "
                    ingredient = re.sub(r'^[-•*]\s+', '', ingredient)
                    # Remove leading numbers with periods/parens: "1. ", "1) "
                    ingredient = re.sub(r'^\d+[.)]\s+', '', ingredient)
                    # Skip section headers or empty lines
                    if ingredient and not ingredient.endswith(':') and len(ingredient) > 2:
                        data['ingredients'].append(ingredient)
                elif current_section == 'instructions':
                    # Keep line structure for instructions
                    # Remove leading numbers/bullets: "1. ", "2) ", "- "
                    instruction = re.sub(r'^[-•*]\s+', '', stripped)
                    instruction = re.sub(r'^\d+[.)]\s+', '', instruction)
                    if instruction and len(instruction) > 2:
                        data['instructions'] += instruction + '\n'
                elif current_section == 'notes':
                    # Skip lines that look like section headers
                    if not stripped.endswith(':'):
                        data['notes'] += stripped + '\n'
        
        # Clean up - remove extra whitespace
        data['title'] = ' '.join(data['title'].split())
        data['description'] = ' '.join(data['description'].split())
        data['servings'] = ' '.join(data['servings'].split())
        data['prep_time'] = ' '.join(data['prep_time'].split())
        data['cook_time'] = ' '.join(data['cook_time'].split())
        data['total_time'] = ' '.join(data['total_time'].split())
        data['instructions'] = data['instructions'].strip()
        data['notes'] = data['notes'].strip()
        
        return data


class ImportImageDialog(QDialog):
    """Dialog for importing recipes from images."""
    
    recipe_extracted = Signal(dict)  # Emitted when recipe is extracted
    
    def __init__(self, ollama_url, vision_model, parent=None):
        super().__init__(parent)
        self.ollama_url = ollama_url
        self.vision_model = vision_model
        self.image_paths = []
        self.worker = None
        
        self.setWindowTitle("Import Recipe from Images")
        self.setMinimumSize(900, 700)
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Check if vision model is configured
        if not self.vision_model:
            warning = QLabel("⚠️ No vision model configured. Please configure a vision model in Settings.")
            warning.setStyleSheet("color: orange; font-weight: bold; padding: 10px;")
            layout.addWidget(warning)
        
        # Instructions
        instructions = QLabel(
            "Select one or more images of a recipe (recipe cards, cookbook pages, handwritten notes).\n"
            "For multi-page recipes, select all pages in order - they will be processed together."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Image selection area
        image_section = QHBoxLayout()
        
        # Image list
        image_list_layout = QVBoxLayout()
        image_list_label = QLabel("Selected Images:")
        image_list_layout.addWidget(image_list_label)
        
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(150)
        image_list_layout.addWidget(self.image_list)
        
        # Image buttons
        image_btn_layout = QHBoxLayout()
        self.add_images_btn = QPushButton("Add Images...")
        self.add_images_btn.clicked.connect(self._select_images)
        image_btn_layout.addWidget(self.add_images_btn)
        
        self.remove_image_btn = QPushButton("Remove Selected")
        self.remove_image_btn.clicked.connect(self._remove_selected_image)
        self.remove_image_btn.setEnabled(False)
        image_btn_layout.addWidget(self.remove_image_btn)
        
        self.clear_images_btn = QPushButton("Clear All")
        self.clear_images_btn.clicked.connect(self._clear_images)
        self.clear_images_btn.setEnabled(False)
        image_btn_layout.addWidget(self.clear_images_btn)
        
        image_btn_layout.addStretch()
        image_list_layout.addLayout(image_btn_layout)
        
        image_section.addLayout(image_list_layout)
        layout.addLayout(image_section)
        
        # Extract button (above preview)
        extract_layout = QHBoxLayout()
        extract_layout.addStretch()
        
        self.extract_btn = QPushButton("Extract Recipe")
        self.extract_btn.clicked.connect(self._extract_recipe)
        self.extract_btn.setEnabled(False)
        extract_layout.addWidget(self.extract_btn)
        
        layout.addLayout(extract_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Splitter for preview and extracted text
        splitter = QSplitter(Qt.Horizontal)
        
        # Extracted text preview
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Extracted Recipe (preview):")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Extracted recipe will appear here after processing...")
        preview_layout.addWidget(self.preview_text)
        
        from PySide6.QtWidgets import QWidget
        preview_widget = QWidget()
        preview_widget.setLayout(preview_layout)
        splitter.addWidget(preview_widget)
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.import_btn = QPushButton("Import to Database")
        self.import_btn.clicked.connect(self._import_recipe)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.image_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _select_images(self):
        """Open file dialog to select images."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Recipe Images",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )
        
        if file_paths:
            for path in file_paths:
                if path not in self.image_paths:
                    self.image_paths.append(path)
                    item = QListWidgetItem(Path(path).name)
                    item.setData(Qt.UserRole, path)
                    self.image_list.addItem(item)
            
            self._update_buttons()
    
    def _remove_selected_image(self):
        """Remove selected image from list."""
        current_item = self.image_list.currentItem()
        if current_item:
            path = current_item.data(Qt.UserRole)
            self.image_paths.remove(path)
            self.image_list.takeItem(self.image_list.row(current_item))
            self._update_buttons()
    
    def _clear_images(self):
        """Clear all images."""
        self.image_paths.clear()
        self.image_list.clear()
        self._update_buttons()
    
    def _on_selection_changed(self):
        """Handle image selection change."""
        has_selection = self.image_list.currentItem() is not None
        self.remove_image_btn.setEnabled(has_selection)
    
    def _update_buttons(self):
        """Update button states."""
        has_images = len(self.image_paths) > 0
        has_vision_model = bool(self.vision_model)
        
        self.extract_btn.setEnabled(has_images and has_vision_model)
        self.clear_images_btn.setEnabled(has_images)
        
        # Show image count
        if has_images:
            count = len(self.image_paths)
            plural = "s" if count > 1 else ""
            self.image_list.setToolTip(f"{count} image{plural} selected")
    
    def _extract_recipe(self):
        """Extract recipe from selected images."""
        if not self.image_paths:
            QMessageBox.warning(self, "No Images", "Please select at least one image.")
            return
        
        if not self.vision_model:
            QMessageBox.warning(
                self, 
                "No Vision Model", 
                "Please configure a vision model in Settings (e.g., llama3.2-vision:11b)"
            )
            return
        
        # Disable buttons during extraction
        self.add_images_btn.setEnabled(False)
        self.remove_image_btn.setEnabled(False)
        self.clear_images_btn.setEnabled(False)
        self.extract_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_label.setVisible(True)
        self.progress_label.setText("Initializing...")
        
        # Start extraction worker
        self.worker = ImageExtractionWorker(
            self.image_paths,
            self.ollama_url,
            self.vision_model
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_extraction_finished)
        self.worker.error.connect(self._on_extraction_error)
        self.worker.start()
    
    def _on_progress(self, message):
        """Handle progress update."""
        self.progress_label.setText(message)
    
    def _on_extraction_finished(self, recipe_data):
        """Handle successful extraction."""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Re-enable buttons
        self.add_images_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.clear_images_btn.setEnabled(True)
        
        # Store extracted data
        self.extracted_data = recipe_data
        
        # Show extracted text
        self.preview_text.setPlainText(recipe_data.get('raw_text', ''))
        
        # Enable import button
        self.import_btn.setEnabled(True)
        
        # Clean up worker
        self.worker.wait()
        self.worker.deleteLater()
        self.worker = None
        
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Successfully extracted recipe: {recipe_data.get('title', 'Untitled')}\n\n"
            "Review the text below and make any corrections before importing."
        )
    
    def _on_extraction_error(self, error_msg):
        """Handle extraction error."""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # Re-enable buttons
        self.add_images_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.clear_images_btn.setEnabled(True)
        
        # Clean up worker
        if self.worker:
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None
        
        QMessageBox.critical(self, "Extraction Failed", error_msg)
    
    def _import_recipe(self):
        """Import the extracted recipe."""
        if not hasattr(self, 'extracted_data'):
            return
        
        # Show progress while importing
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_label.setVisible(True)
        self.progress_label.setText("Importing recipe to database...")
        
        # Disable buttons
        self.import_btn.setEnabled(False)
        self.extract_btn.setEnabled(False)
        
        # Force UI update
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # Emit signal with extracted data (don't close yet - wait for controller to finish)
        self.recipe_extracted.emit(self.extracted_data)
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Extraction in Progress",
                "Recipe extraction is still in progress. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
