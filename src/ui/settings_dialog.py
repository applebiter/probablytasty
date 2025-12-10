"""
Application settings and preferences dialog.
"""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QGroupBox, QCheckBox, QTabWidget, QWidget,
    QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal


class ModelPreloadWorker(QThread):
    """Worker thread for preloading Ollama models without blocking UI."""
    
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, url: str, model_name: str):
        super().__init__()
        self.url = url
        self.model_name = model_name
    
    def run(self):
        """Run the preload operation in background thread."""
        try:
            import requests
            
            # Step 1: Get currently loaded models and unload them
            try:
                ps_response = requests.get(f"{self.url}/api/ps", timeout=5)
                if ps_response.status_code == 200:
                    loaded_models = ps_response.json().get("models", [])
                    for loaded_model in loaded_models:
                        loaded_name = loaded_model.get("name", "")
                        if loaded_name:
                            unload_payload = {
                                "model": loaded_name,
                                "keep_alive": 0
                            }
                            requests.post(f"{self.url}/api/generate", json=unload_payload, timeout=5)
            except Exception as e:
                print(f"Warning: Could not check/unload existing models: {e}")
            
            # Step 2: Preload the new model
            preload_payload = {
                "model": self.model_name,
                "prompt": "",
                "keep_alive": "10m"
            }
            
            response = requests.post(
                f"{self.url}/api/generate",
                json=preload_payload,
                timeout=120,
                stream=True
            )
            response.raise_for_status()
            
            # Consume the streaming response fully to ensure completion
            for _ in response.iter_lines():
                pass
            
            self.finished.emit(True, f"Successfully preloaded:\n{self.model_name}\n\nThe model will stay loaded for 10 minutes of inactivity.")
            
        except requests.exceptions.Timeout:
            self.finished.emit(False, "Model loading took too long.\n\nLarge models may take 1-2 minutes to load on first use.")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, f"Could not connect to Ollama server at:\n{self.url}\n\nMake sure Ollama is running:\n  ollama serve")
        except Exception as e:
            self.finished.emit(False, f"Failed to preload model:\n{e}")


class SettingsDialog(QDialog):
    """Settings and preferences dialog."""
    
    def __init__(self, parent=None, settings_file=None):
        super().__init__(parent)
        self.settings_file = settings_file or Path.home() / ".probablytasty" / "settings.json"
        self.settings = self.load_settings()
        self.preload_worker = None
        self.preload_vision_worker = None
        self.init_ui()
        self.load_values()
    
    def closeEvent(self, event):
        """Ensure worker threads are stopped before closing."""
        if self.preload_worker and self.preload_worker.isRunning():
            # Don't allow closing while preload is running
            QMessageBox.warning(
                self,
                "Model Loading",
                "Please wait for model preload to complete before closing."
            )
            event.ignore()
            return
        if self.preload_vision_worker and self.preload_vision_worker.isRunning():
            # Don't allow closing while vision preload is running
            QMessageBox.warning(
                self,
                "Vision Model Loading",
                "Please wait for vision model preload to complete before closing."
            )
            event.ignore()
            return
        super().closeEvent(event)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Settings & Preferences")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Simple Settings Tab
        simple_tab = self.create_simple_tab()
        tabs.addTab(simple_tab, "Simple")
        
        # Advanced Settings Tab
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings_and_close)
        button_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def create_simple_tab(self) -> QWidget:
        """Create the simple settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info label
        info = QLabel(
            "ProbablyTasty works best with AI for natural language search.\n\n"
            "By default, it uses Ollama (free, runs on your computer).\n"
            "You can also use cloud AI services if you have API keys."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # AI Provider selection
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout()
        
        self.simple_provider_combo = QComboBox()
        self.simple_provider_combo.addItems([
            "Ollama (Free, Local)",
            "OpenAI",
            "Anthropic Claude",
            "Google Gemini",
            "None (Basic search only)"
        ])
        self.simple_provider_combo.currentIndexChanged.connect(self.on_simple_provider_changed)
        provider_layout.addRow("AI Service:", self.simple_provider_combo)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # API Key group (shown for cloud providers)
        self.simple_api_group = QGroupBox("API Key")
        api_layout = QFormLayout()
        
        self.simple_api_key_input = QLineEdit()
        self.simple_api_key_input.setEchoMode(QLineEdit.Password)
        self.simple_api_key_input.setPlaceholderText("Enter your API key here...")
        api_layout.addRow("API Key:", self.simple_api_key_input)
        
        api_help = QLabel()
        api_help.setWordWrap(True)
        api_help.setStyleSheet("color: #666; font-size: 11px;")
        self.simple_api_help = api_help
        api_layout.addRow("", api_help)
        
        self.simple_api_group.setLayout(api_layout)
        layout.addWidget(self.simple_api_group)
        
        # Display Settings group
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        display_layout.addRow("Theme:", self.theme_combo)
        
        theme_help = QLabel("Choose your preferred color theme. Changes apply immediately.")
        theme_help.setWordWrap(True)
        theme_help.setStyleSheet("color: #666; font-size: 11px;")
        display_layout.addRow("", theme_help)
        
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            "Small (10pt)",
            "Normal (12pt)",
            "Large (14pt)",
            "Extra Large (16pt)",
            "Huge (20pt)"
        ])
        self.font_size_combo.currentIndexChanged.connect(self.on_font_size_changed)
        display_layout.addRow("Font Size:", self.font_size_combo)
        
        font_help = QLabel("Adjust text size for better readability. Changes apply immediately.")
        font_help.setWordWrap(True)
        font_help.setStyleSheet("color: #666; font-size: 11px;")
        display_layout.addRow("", font_help)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ollama Configuration
        ollama_group = QGroupBox("Ollama Configuration")
        ollama_layout = QFormLayout()
        
        # URL with test button
        url_layout = QHBoxLayout()
        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setPlaceholderText("http://localhost:11434")
        url_layout.addWidget(self.ollama_url_input)
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_ollama_connection)
        url_layout.addWidget(self.test_connection_btn)
        
        self.connection_status = QLabel("")
        url_layout.addWidget(self.connection_status)
        
        ollama_layout.addRow("Ollama URL:", url_layout)
        
        # Model dropdown with preload button
        model_layout = QHBoxLayout()
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.setEditable(True)
        self.ollama_model_combo.setPlaceholderText("Test connection to load models...")
        model_layout.addWidget(self.ollama_model_combo)
        
        self.preload_model_btn = QPushButton("Preload Model")
        self.preload_model_btn.clicked.connect(self.preload_ollama_model)
        self.preload_model_btn.setToolTip("Hot-swap: unload current model and preload selected model")
        model_layout.addWidget(self.preload_model_btn)
        
        self.model_status = QLabel("")
        model_layout.addWidget(self.model_status)
        
        ollama_layout.addRow("Text Model:", model_layout)
        
        # Vision model dropdown with preload button for OCR/image import
        vision_model_layout = QHBoxLayout()
        self.ollama_vision_model_combo = QComboBox()
        self.ollama_vision_model_combo.setEditable(True)
        self.ollama_vision_model_combo.setPlaceholderText("Test connection to load models (optional)...")
        self.ollama_vision_model_combo.addItem("")  # Empty option for text-only
        vision_model_layout.addWidget(self.ollama_vision_model_combo)
        
        self.preload_vision_model_btn = QPushButton("Preload Vision Model")
        self.preload_vision_model_btn.clicked.connect(self.preload_ollama_vision_model)
        self.preload_vision_model_btn.setToolTip("Hot-swap: unload current model and preload selected vision model")
        vision_model_layout.addWidget(self.preload_vision_model_btn)
        
        self.vision_model_status = QLabel("")
        vision_model_layout.addWidget(self.vision_model_status)
        
        ollama_layout.addRow("Vision Model (optional):", vision_model_layout)
        
        self.ollama_context_combo = QComboBox()
        self.ollama_context_combo.addItems([
            "4096 - Small (faster, less context)",
            "8192 - Balanced (recommended)",
            "16384 - Large (slower, more context)",
            "32768 - Maximum (slowest, most context)"
        ])
        self.ollama_context_combo.setCurrentIndex(1)  # Default to 8192
        ollama_layout.addRow("Context Length:", self.ollama_context_combo)
        
        ollama_help = QLabel(
            "Ollama runs AI models locally on your computer or network.\n"
            "Higher context = better understanding but slower performance\n"
            "Vision model enables importing recipes from images/photos\n"
            "Default: http://localhost:11434"
        )
        ollama_help.setWordWrap(True)
        ollama_help.setStyleSheet("color: #666; font-size: 11px;")
        ollama_layout.addRow("", ollama_help)
        
        ollama_group.setLayout(ollama_layout)
        layout.addWidget(ollama_group)
        
        # OpenAI Configuration
        openai_group = QGroupBox("OpenAI Configuration")
        openai_layout = QFormLayout()
        
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        openai_layout.addRow("API Key:", self.openai_key_input)
        
        self.openai_model_input = QComboBox()
        self.openai_model_input.setEditable(True)
        self.openai_model_input.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        openai_layout.addRow("Model:", self.openai_model_input)
        
        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)
        
        # Anthropic Configuration
        anthropic_group = QGroupBox("Anthropic Claude Configuration")
        anthropic_layout = QFormLayout()
        
        self.anthropic_key_input = QLineEdit()
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-...")
        anthropic_layout.addRow("API Key:", self.anthropic_key_input)
        
        self.anthropic_model_input = QComboBox()
        self.anthropic_model_input.setEditable(True)
        self.anthropic_model_input.addItems([
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ])
        anthropic_layout.addRow("Model:", self.anthropic_model_input)
        
        anthropic_group.setLayout(anthropic_layout)
        layout.addWidget(anthropic_group)
        
        # Google Configuration
        google_group = QGroupBox("Google Gemini Configuration")
        google_layout = QFormLayout()
        
        self.google_key_input = QLineEdit()
        self.google_key_input.setEchoMode(QLineEdit.Password)
        self.google_key_input.setPlaceholderText("AIza...")
        google_layout.addRow("API Key:", self.google_key_input)
        
        self.google_model_input = QComboBox()
        self.google_model_input.setEditable(True)
        self.google_model_input.addItems([
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ])
        google_layout.addRow("Model:", self.google_model_input)
        
        google_group.setLayout(google_layout)
        layout.addWidget(google_group)
        
        # Preferred Provider
        provider_layout = QFormLayout()
        self.adv_provider_combo = QComboBox()
        self.adv_provider_combo.addItems(["ollama", "openai", "anthropic", "google", "none"])
        provider_layout.addRow("Preferred Provider:", self.adv_provider_combo)
        layout.addLayout(provider_layout)
        
        layout.addStretch()
        
        return widget
    
    def on_simple_provider_changed(self, index):
        """Handle simple provider selection change."""
        provider_map = ["ollama", "openai", "anthropic", "google", "none"]
        provider = provider_map[index]
        
        # Show/hide API key group
        needs_api_key = provider in ["openai", "anthropic", "google"]
        self.simple_api_group.setVisible(needs_api_key)
        
        # Update help text
        help_texts = {
            "openai": "Get your API key at: https://platform.openai.com/api-keys",
            "anthropic": "Get your API key at: https://console.anthropic.com/",
            "google": "Get your API key at: https://aistudio.google.com/app/apikey",
        }
        self.simple_api_help.setText(help_texts.get(provider, ""))
    
    def on_font_size_changed(self, index):
        """Apply font size change immediately."""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
        
        font_sizes = [10, 12, 14, 16, 20]
        font_size = font_sizes[index]
        
        # Apply to entire application immediately
        app = QApplication.instance()
        font = QFont()
        font.setPointSize(font_size)
        app.setFont(font)
    
    def load_settings(self) -> dict:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load settings: {e}")
        
        # Default settings
        return {
            "provider": "ollama",
            "ollama_url": "http://localhost:11434",
            "ollama_model": "llama2",
            "openai_key": "",
            "openai_model": "gpt-4o-mini",
            "anthropic_key": "",
            "anthropic_model": "claude-3-5-sonnet-20241022",
            "google_key": "",
            "google_model": "gemini-1.5-flash",
        }
    
    def on_theme_changed(self, index):
        """Handle theme selection change - apply immediately for live preview."""
        theme = "light" if index == 0 else "dark"
        self._apply_theme(theme)
    
    def _apply_theme(self, theme: str):
        """Apply theme immediately to the application."""
        from PySide6.QtWidgets import QApplication
        from pathlib import Path
        
        theme_file = Path(__file__).parent / "themes" / f"{theme}.qss"
        print(f"DEBUG: Applying theme '{theme}' from {theme_file}")
        print(f"DEBUG: Theme file exists: {theme_file.exists()}")
        try:
            if theme_file.exists():
                with open(theme_file, 'r') as f:
                    stylesheet = f.read()
                    app = QApplication.instance()
                    if app:
                        print(f"DEBUG: Applying stylesheet ({len(stylesheet)} chars)")
                        app.setStyleSheet(stylesheet)
                        print("DEBUG: Theme applied successfully")
                    else:
                        print("DEBUG: No QApplication instance found")
            else:
                print(f"DEBUG: Theme file not found: {theme_file}")
        except Exception as e:
            print(f"Failed to apply theme {theme}: {e}")
    
    def load_values(self):
        """Load settings values into UI."""
        # Simple tab
        provider_map = {"ollama": 0, "openai": 1, "anthropic": 2, "google": 3, "none": 4}
        self.simple_provider_combo.setCurrentIndex(provider_map.get(self.settings.get("provider", "ollama"), 0))
        
        # Load API key for selected provider
        provider = self.settings.get("provider", "ollama")
        if provider in ["openai", "anthropic", "google"]:
            self.simple_api_key_input.setText(self.settings.get(f"{provider}_key", ""))
        
        # Advanced tab
        self.ollama_url_input.setText(self.settings.get("ollama_url", "http://localhost:11434"))
        
        # Set saved model in combo (will be editable text if not in list)
        saved_model = self.settings.get("ollama_model", "llama2")
        self.ollama_model_combo.setCurrentText(saved_model)
        
        # Set vision model in combo (will be editable text if not in list)
        saved_vision_model = self.settings.get("ollama_vision_model", "")
        self.ollama_vision_model_combo.setCurrentText(saved_vision_model)
        
        # Set context length dropdown
        context_map = {4096: 0, 8192: 1, 16384: 2, 32768: 3}
        context_length = self.settings.get("ollama_context_length", 8192)
        self.ollama_context_combo.setCurrentIndex(context_map.get(context_length, 1))
        
        self.openai_key_input.setText(self.settings.get("openai_key", ""))
        self.openai_model_input.setCurrentText(self.settings.get("openai_model", "gpt-4o-mini"))
        self.anthropic_key_input.setText(self.settings.get("anthropic_key", ""))
        self.anthropic_model_input.setCurrentText(self.settings.get("anthropic_model", "claude-3-5-sonnet-20241022"))
        self.google_key_input.setText(self.settings.get("google_key", ""))
        self.google_model_input.setCurrentText(self.settings.get("google_model", "gemini-1.5-flash"))
        
        provider_map_adv = {"ollama": 0, "openai": 1, "anthropic": 2, "google": 3, "none": 4}
        self.adv_provider_combo.setCurrentIndex(provider_map_adv.get(self.settings.get("provider", "ollama"), 0))
        
        # Load theme
        theme = self.settings.get("theme", "light")
        self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)
        
        # Load font size
        font_size_map = {10: 0, 12: 1, 14: 2, 16: 3, 20: 4}
        font_size = self.settings.get("font_size", 10)
        self.font_size_combo.setCurrentIndex(font_size_map.get(font_size, 0))
    
    def save_settings_and_close(self):
        """Save settings and close dialog."""
        # Don't allow saving while preload is running
        if self.preload_worker and self.preload_worker.isRunning():
            QMessageBox.warning(
                self,
                "Model Loading",
                "Please wait for model preload to complete before saving."
            )
            return
        
        # Get provider from simple tab (simple tab has priority)
        provider_map = ["ollama", "openai", "anthropic", "google", "none"]
        simple_provider = provider_map[self.simple_provider_combo.currentIndex()]
        
        # Get context length from dropdown
        context_values = [4096, 8192, 16384, 32768]
        context_length = context_values[self.ollama_context_combo.currentIndex()]
        
        # Get font size from combo
        font_sizes = [10, 12, 14, 16, 20]
        font_size = font_sizes[self.font_size_combo.currentIndex()]
        
        # Get theme
        theme = "light" if self.theme_combo.currentIndex() == 0 else "dark"
        
        settings = {
            "provider": simple_provider,
            "ollama_url": self.ollama_url_input.text() or "http://localhost:11434",
            "ollama_model": self.ollama_model_combo.currentText() or "llama2",
            "ollama_vision_model": self.ollama_vision_model_combo.currentText() or "",
            "ollama_context_length": context_length,
            "openai_key": self.openai_key_input.text(),
            "openai_model": self.openai_model_input.currentText() or "gpt-4o-mini",
            "anthropic_key": self.anthropic_key_input.text(),
            "anthropic_model": self.anthropic_model_input.currentText() or "claude-3-5-sonnet-20241022",
            "google_key": self.google_key_input.text(),
            "google_model": self.google_model_input.currentText() or "gemini-1.5-flash",
            "theme": theme,
            "font_size": font_size,
        }
        
        # If simple tab API key is provided, update it
        if simple_provider in ["openai", "anthropic", "google"]:
            key = self.simple_api_key_input.text()
            if key:
                settings[f"{simple_provider}_key"] = key
        
        # Save to file
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Apply theme immediately
            self._apply_theme(theme)
            
            # Settings will be reloaded by controller - no restart needed
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n{e}"
            )
    
    def test_ollama_connection(self):
        """Test connection to Ollama server and load available models."""
        url = self.ollama_url_input.text() or "http://localhost:11434"
        url = url.rstrip('/')
        
        try:
            import requests
            
            # Show testing status
            self.connection_status.setText("Testing...")
            self.connection_status.setStyleSheet("color: #666;")
            self.test_connection_btn.setEnabled(False)
            
            # Force UI update
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # Test connection and get models
            response = requests.get(f"{url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            
            if not models:
                self.connection_status.setText("✗ No models found")
                self.connection_status.setStyleSheet("color: #d32f2f;")
                QMessageBox.warning(
                    self,
                    "No Models",
                    "Connection successful but no models found.\n\n"
                    "Install models with: ollama pull <model_name>"
                )
            else:
                # Success - populate dropdowns with full model names
                self.connection_status.setText("✓ Connected")
                self.connection_status.setStyleSheet("color: #4caf50;")
                
                # Clear and populate text model dropdown
                current_text = self.ollama_model_combo.currentText()
                self.ollama_model_combo.clear()
                
                # Clear and populate vision model dropdown (keep empty option)
                current_vision = self.ollama_vision_model_combo.currentText()
                self.ollama_vision_model_combo.clear()
                self.ollama_vision_model_combo.addItem("")  # Empty option for text-only
                
                for model in models:
                    # Use full name including tag (e.g., "llama2:latest")
                    model_name = model.get("name", "")
                    if model_name:
                        self.ollama_model_combo.addItem(model_name)
                        # Also add to vision model dropdown
                        self.ollama_vision_model_combo.addItem(model_name)
                
                # Try to restore previous selections
                index = self.ollama_model_combo.findText(current_text)
                if index >= 0:
                    self.ollama_model_combo.setCurrentIndex(index)
                
                vision_index = self.ollama_vision_model_combo.findText(current_vision)
                if vision_index >= 0:
                    self.ollama_vision_model_combo.setCurrentIndex(vision_index)
                
        except requests.exceptions.Timeout:
            self.connection_status.setText("✗ Timeout")
            self.connection_status.setStyleSheet("color: #d32f2f;")
            QMessageBox.warning(
                self,
                "Connection Timeout",
                f"Could not connect to Ollama server at:\n{url}\n\n"
                "Make sure Ollama is running:\n"
                "  ollama serve"
            )
        except requests.exceptions.ConnectionError:
            self.connection_status.setText("✗ Failed")
            self.connection_status.setStyleSheet("color: #d32f2f;")
            QMessageBox.warning(
                self,
                "Connection Failed",
                f"Could not connect to Ollama server at:\n{url}\n\n"
                "Make sure Ollama is running:\n"
                "  ollama serve"
            )
        except Exception as e:
            self.connection_status.setText("✗ Error")
            self.connection_status.setStyleSheet("color: #d32f2f;")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to connect to Ollama:\n{e}"
            )
        finally:
            self.test_connection_btn.setEnabled(True)
    
    def preload_ollama_model(self):
        """Unload current model and preload the selected model (async)."""
        url = self.ollama_url_input.text() or "http://localhost:11434"
        url = url.rstrip('/')
        model_name = self.ollama_model_combo.currentText()
        
        if not model_name:
            QMessageBox.warning(
                self,
                "No Model Selected",
                "Please select a model to preload."
            )
            return
        
        # Show loading status and disable buttons
        self.model_status.setText("Loading...")
        self.model_status.setStyleSheet("color: #666;")
        self.preload_model_btn.setEnabled(False)
        self.save_btn.setEnabled(False)  # Prevent saving while loading
        
        # Create and start worker thread
        self.preload_worker = ModelPreloadWorker(url, model_name)
        self.preload_worker.finished.connect(self.on_preload_finished)
        self.preload_worker.start()
    
    def on_preload_finished(self, success: bool, message: str):
        """Handle preload worker completion."""
        # Re-enable buttons
        self.preload_model_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Clean up worker thread
        if self.preload_worker:
            self.preload_worker.wait()  # Ensure thread is fully stopped
            self.preload_worker.deleteLater()
            self.preload_worker = None
        
        if success:
            self.model_status.setText("✓ Loaded")
            self.model_status.setStyleSheet("color: #4caf50;")
            QMessageBox.information(self, "Model Loaded", message)
        else:
            self.model_status.setText("✗ Failed")
            self.model_status.setStyleSheet("color: #d32f2f;")
            QMessageBox.warning(self, "Load Failed", message)
    
    def preload_ollama_vision_model(self):
        """Unload current vision model and preload the selected vision model (async)."""
        url = self.ollama_url_input.text() or "http://localhost:11434"
        url = url.rstrip('/')
        model_name = self.ollama_vision_model_combo.currentText()
        
        if not model_name:
            QMessageBox.information(
                self,
                "No Vision Model",
                "Vision model is optional. Leave empty for text-only operation."
            )
            return
        
        # Show loading status and disable buttons
        self.vision_model_status.setText("Loading...")
        self.vision_model_status.setStyleSheet("color: #666;")
        self.preload_vision_model_btn.setEnabled(False)
        self.save_btn.setEnabled(False)  # Prevent saving while loading
        
        # Create and start worker thread
        self.preload_vision_worker = ModelPreloadWorker(url, model_name)
        self.preload_vision_worker.finished.connect(self.on_vision_preload_finished)
        self.preload_vision_worker.start()
    
    def on_vision_preload_finished(self, success: bool, message: str):
        """Handle vision model preload worker completion."""
        # Re-enable buttons
        self.preload_vision_model_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Clean up worker thread
        if self.preload_vision_worker:
            self.preload_vision_worker.wait()  # Ensure thread is fully stopped
            self.preload_vision_worker.deleteLater()
            self.preload_vision_worker = None
        
        if success:
            self.vision_model_status.setText("✓ Loaded")
            self.vision_model_status.setStyleSheet("color: #4caf50;")
            QMessageBox.information(self, "Vision Model Loaded", message)
        else:
            self.vision_model_status.setText("✗ Failed")
            self.vision_model_status.setStyleSheet("color: #d32f2f;")
            QMessageBox.warning(self, "Load Failed", message)
    
    def get_settings(self) -> dict:
        """Get the current settings."""
        return self.settings
