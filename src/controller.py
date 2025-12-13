"""
Application controller coordinating UI and services.
"""

from typing import Optional
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from sqlalchemy.orm import Session
from src.ui import MainWindow, RecipeEditorDialog
from src.ui.unit_conversion_dialog import UnitConversionDialog
from src.services import RecipeService, SearchOrchestrator, LLMRouter, LLMProvider
from src.services.unit_conversion import UnitConversionService
from src.services.recipe_scaling_service import RecipeScalingService
from src.services.shopping_list_service import ShoppingListService
from src.utils import RecipeImporter, RecipeExporter
from src.models import Recipe
from src import config


class AppController:
    """Main application controller."""
    
    def __init__(self, session: Session, window: MainWindow):
        self.session = session
        self.window = window
        
        # Initialize services
        self.recipe_service = RecipeService(session)
        self.unit_conversion_service = UnitConversionService()
        self.recipe_scaling_service = RecipeScalingService()
        self.shopping_list_service = ShoppingListService()
        
        # Initialize LLM router
        self.llm_router = LLMRouter(
            preferred_provider=LLMProvider[config.DEFAULT_LLM_PROVIDER.upper()],
            openai_key=config.OPENAI_API_KEY,
            anthropic_key=config.ANTHROPIC_API_KEY,
            google_key=config.GOOGLE_API_KEY,
            ollama_url=config.OLLAMA_BASE_URL,
            ollama_model=config.OLLAMA_MODEL,
            ollama_context_length=config.OLLAMA_CONTEXT_LENGTH,
        )
        
        self.search_orchestrator = SearchOrchestrator(session, self.llm_router)
        self.importer = RecipeImporter(session)
        self.exporter = RecipeExporter(session)
        
        # Initialize URL importer
        from src.services.recipe_importer import RecipeImporter as URLImporter
        self.url_importer = URLImporter(self.llm_router)
        
        # Connect UI signals to controller methods
        self.connect_signals()
        
        # Load initial data
        self.load_all_recipes()
    
    def reload_settings(self):
        """Reload settings and reinitialize LLM router without restarting app."""
        # Reload config module
        import importlib
        importlib.reload(config)
        
        # Reinitialize LLM router with new settings
        self.llm_router = LLMRouter(
            preferred_provider=LLMProvider[config.DEFAULT_LLM_PROVIDER.upper()],
            openai_key=config.OPENAI_API_KEY,
            anthropic_key=config.ANTHROPIC_API_KEY,
            google_key=config.GOOGLE_API_KEY,
            ollama_url=config.OLLAMA_BASE_URL,
            ollama_model=config.OLLAMA_MODEL,
            ollama_context_length=config.OLLAMA_CONTEXT_LENGTH,
        )
        
        # Update dependent services
        self.search_orchestrator.llm_router = self.llm_router
        self.url_importer.llm_router = self.llm_router
        
        print(f"Settings reloaded: Provider={config.DEFAULT_LLM_PROVIDER}, Ollama model={config.OLLAMA_MODEL}")
    
    def connect_signals(self):
        """Connect UI signals to controller methods."""
        self.window.on_search = self.handle_search
        self.window.on_recipe_selected = self.handle_recipe_selected
        self.window.on_new_recipe = self.handle_new_recipe
        self.window.on_import_url = self.handle_import_url
        self.window.on_edit_recipe = self.handle_edit_recipe
        self.window.on_delete_recipe = self.handle_delete_recipe
        self.window.on_import = self.handle_import
        self.window.on_import_images = self.handle_import_images
        self.window.on_export = self.handle_export
        self.window.on_preferences = self.handle_preferences
        self.window.on_scale_recipe = self.handle_scale_recipe
        self.window.on_convert_units = self.handle_convert_units
        self.window.on_print_recipe = self.handle_print_recipe
        self.window.on_shopping_list = self.handle_shopping_list
    
    def load_all_recipes(self):
        """Load all recipes into the UI."""
        recipes = self.recipe_service.get_all_recipes()
        self.window.load_recipes(recipes)
        self.window.statusBar().showMessage(f"Loaded {len(recipes)} recipes")
    
    def handle_search(self):
        """Handle recipe search."""
        query = self.window.search_input.text().strip()
        
        if not query:
            self.load_all_recipes()
            return
        
        # Get max time filter
        max_time_text = self.window.max_time_combo.currentText()
        max_time = None
        if max_time_text != "Any":
            # Parse time from text like "30 min", "1 hour", "2 hours"
            if "min" in max_time_text:
                max_time = int(max_time_text.split()[0])
            elif "hour" in max_time_text:
                hours = int(max_time_text.split()[0])
                max_time = hours * 60
        
        self.window.statusBar().showMessage("Searching...")
        self.window.recipe_tree.setEnabled(False)  # Disable during search
        QApplication.processEvents()  # Force UI update
        
        try:
            # Use LLM only for complex queries (multiple words, questions, natural language)
            # Simple single-word searches use keyword matching for accuracy
            query_words = query.split()
            use_llm = (
                self.llm_router.is_available() and 
                (len(query_words) > 2 or any(word in query.lower() for word in ['how', 'what', 'with', 'without', 'quick', 'easy', 'healthy']))
            )
            recipes = self.search_orchestrator.search(query, use_llm=use_llm)
            
            # Apply time filter if set
            if max_time is not None:
                recipes = [r for r in recipes if r.total_time_minutes and r.total_time_minutes <= max_time]
            
            self.window.load_recipes(recipes)
            
            # Expand all search result nodes so user can see matches
            self.window.recipe_tree.expandAll()
            
            search_method = "AI-powered" if use_llm else "keyword"
            filter_text = f" (≤{max_time_text})" if max_time is not None else ""
            self.window.statusBar().showMessage(
                f"Found {len(recipes)} recipes using {search_method} search{filter_text}"
            )
        except Exception as e:
            QMessageBox.warning(
                self.window,
                "Search Error",
                f"An error occurred during search: {str(e)}"
            )
            self.window.statusBar().showMessage("Search failed")
        finally:
            self.window.recipe_tree.setEnabled(True)  # Re-enable after search
    
    def handle_recipe_selected(self, item, column=0):
        """Handle recipe selection from tree."""
        from PySide6.QtCore import Qt
        
        item_type = item.data(0, Qt.UserRole + 1)
        
        if item_type == "recipe":
            recipe_id = item.data(0, Qt.UserRole)
            recipe = self.recipe_service.get_recipe(recipe_id)
            
            if recipe:
                self.window.display_recipe(recipe)
                self.window.statusBar().showMessage(f"Viewing: {recipe.title}")
        elif item_type in ("tag", "category"):
            # Tag or category clicked - toggle expand/collapse
            item.setExpanded(not item.isExpanded())
        else:
            # Handle items without type set - check if it has children
            if item.childCount() > 0:
                item.setExpanded(not item.isExpanded())
    
    def handle_new_recipe(self):
        """Handle new recipe creation."""
        dialog = RecipeEditorDialog(self.window)
        
        if dialog.exec():
            recipe_data = dialog.get_recipe_data()
            if recipe_data:
                try:
                    # Create recipe
                    recipe = self.recipe_service.create_recipe(
                        title=recipe_data["title"],
                        instructions=recipe_data["instructions"],
                        description=recipe_data["description"],
                        servings=recipe_data["servings"],
                        prep_time_minutes=recipe_data["prep_time_minutes"],
                        cook_time_minutes=recipe_data["cook_time_minutes"],
                        source_url=recipe_data["source_url"],
                    )
                    
                    # Add ingredients
                    for idx, ing in enumerate(recipe_data["ingredients"]):
                        self.recipe_service.add_ingredient_to_recipe(
                            recipe_id=recipe.id,
                            ingredient_name=ing["name"],
                            quantity=ing["quantity"],
                            unit=ing["unit"],
                            preparation=ing["preparation"],
                            order_index=idx,
                        )
                    
                    # Add tags
                    for tag in recipe_data["tags"]:
                        self.recipe_service.add_tag_to_recipe(recipe.id, tag)
                    
                    # Refresh list and display new recipe
                    self.load_all_recipes()
                    self.window.expand_recipe_nodes(recipe.id)
                    self.window.display_recipe(recipe)
                    self.window.statusBar().showMessage(f"Created: {recipe.title}")
                    
                except Exception as e:
                    QMessageBox.critical(
                        self.window,
                        "Error",
                        f"Failed to create recipe: {str(e)}"
                    )
    
    def handle_import_url(self):
        """Handle import recipe from URL."""
        from src.ui.import_dialog import ImportRecipeDialog
        
        dialog = ImportRecipeDialog(self.url_importer, self.window)
        
        if dialog.exec():
            recipe_data = dialog.get_recipe_data()
            if recipe_data:
                try:
                    # Create recipe
                    recipe = self.recipe_service.create_recipe(
                        title=recipe_data["title"],
                        instructions=recipe_data["instructions"],
                        description=recipe_data["description"],
                        servings=recipe_data["servings"],
                        prep_time_minutes=recipe_data["prep_time_minutes"],
                        cook_time_minutes=recipe_data["cook_time_minutes"],
                        source_url=recipe_data["source_url"],
                    )
                    
                    # Add ingredients
                    for idx, ing in enumerate(recipe_data["ingredients"]):
                        print(f"  [DB] Saving ingredient #{idx+1}: name='{ing['name'][:30]}...', qty='{ing['quantity']}', unit='{ing['unit']}'")
                        self.recipe_service.add_ingredient_to_recipe(
                            recipe_id=recipe.id,
                            ingredient_name=ing["name"],
                            quantity=ing["quantity"],
                            unit=ing["unit"],
                            preparation=ing.get("preparation", ""),
                            order_index=idx,
                        )
                    
                    # Add tags
                    for tag in recipe_data.get("tags", []):
                        self.recipe_service.add_tag_to_recipe(recipe.id, tag)
                    
                    # Refresh list and display new recipe
                    self.load_all_recipes()
                    self.window.expand_recipe_nodes(recipe.id)
                    self.window.display_recipe(recipe)
                    self.window.statusBar().showMessage(f"Imported: {recipe.title}")
                    
                    QMessageBox.information(
                        self.window,
                        "Import Successful",
                        f"Recipe '{recipe.title}' has been imported!\n\n"
                        "You can now edit it to refine the details."
                    )
                    
                except Exception as e:
                    QMessageBox.critical(
                        self.window,
                        "Error",
                        f"Failed to import recipe: {str(e)}"
                    )
    
    def handle_edit_recipe(self):
        """Handle recipe editing."""
        if not self.window.current_recipe:
            QMessageBox.warning(
                self.window,
                "No Selection",
                "Please select a recipe to edit."
            )
            return
        
        recipe = self.window.current_recipe
        
        # Prepare recipe data for editor
        recipe_data = {
            "title": recipe.title,
            "description": recipe.description,
            "instructions": recipe.instructions,
            "servings": recipe.servings,
            "prep_time_minutes": recipe.prep_time_minutes or 0,
            "cook_time_minutes": recipe.cook_time_minutes or 0,
            "source_url": recipe.source_url,
            "ingredients": [
                {
                    "name": ri.ingredient.name,
                    "quantity": ri.display_quantity,
                    "unit": ri.display_unit,
                    "preparation": ri.preparation,
                }
                for ri in recipe.ingredients
            ],
            "tags": [tag.name for tag in recipe.tags],
        }
        
        dialog = RecipeEditorDialog(self.window, recipe_data)
        
        if dialog.exec():
            updated_data = dialog.get_recipe_data()
            if updated_data:
                try:
                    # Update basic recipe info
                    self.recipe_service.update_recipe(
                        recipe.id,
                        title=updated_data["title"],
                        description=updated_data["description"],
                        instructions=updated_data["instructions"],
                        servings=updated_data["servings"],
                        prep_time_minutes=updated_data["prep_time_minutes"],
                        cook_time_minutes=updated_data["cook_time_minutes"],
                        source_url=updated_data["source_url"],
                    )
                    
                    # Update ingredients - delete all existing and re-add
                    # This is simpler than trying to match and update
                    for ri in recipe.ingredients:
                        self.session.delete(ri)
                    self.session.flush()
                    
                    for idx, ing in enumerate(updated_data["ingredients"]):
                        self.recipe_service.add_ingredient_to_recipe(
                            recipe_id=recipe.id,
                            ingredient_name=ing["name"],
                            quantity=ing["quantity"],
                            unit=ing["unit"],
                            preparation=ing.get("preparation", ""),
                            order_index=idx,
                        )
                    
                    # Update tags - remove old ones and add new ones
                    for tag in recipe.tags[:]:  # Make a copy to avoid modification during iteration
                        self.recipe_service.remove_tag_from_recipe(recipe.id, tag.name)
                    
                    for tag_name in updated_data.get("tags", []):
                        self.recipe_service.add_tag_to_recipe(recipe.id, tag_name)
                    
                    # Refresh display
                    updated_recipe = self.recipe_service.get_recipe(recipe.id)
                    self.load_all_recipes()
                    self.window.expand_recipe_nodes(updated_recipe.id)
                    self.window.display_recipe(updated_recipe)
                    self.window.statusBar().showMessage(f"Updated: {updated_recipe.title}")
                    
                except Exception as e:
                    QMessageBox.critical(
                        self.window,
                        "Error",
                        f"Failed to update recipe: {str(e)}"
                    )
    
    def handle_delete_recipe(self):
        """Handle recipe deletion."""
        if not self.window.current_recipe:
            return
        
        recipe = self.window.current_recipe
        
        if self.recipe_service.delete_recipe(recipe.id):
            self.window.clear_recipe_display()
            self.load_all_recipes()
            self.window.statusBar().showMessage(f"Deleted: {recipe.title}")
        else:
            QMessageBox.critical(
                self.window,
                "Error",
                "Failed to delete recipe."
            )
    
    def handle_import(self):
        """Handle recipe import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Import Recipes",
            "",
            "HTML Recipe Files (*.html);;JSON Files (*.json);;Text Files (*.txt *.md);;All Files (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.html') or file_path.endswith('.htm'):
                    recipes = self.importer.import_from_html(file_path)
                    self.load_all_recipes()
                    recipe = recipes[0] if recipes else None
                    if recipe:
                        self.window.display_recipe(recipe)
                    QMessageBox.information(
                        self.window,
                        "Import Successful",
                        f"Imported recipe: {recipe.title}" if recipe else "Import complete"
                    )
                elif file_path.endswith('.json'):
                    recipes = self.importer.import_from_json(file_path)
                    self.load_all_recipes()
                    QMessageBox.information(
                        self.window,
                        "Import Successful",
                        f"Imported {len(recipes)} recipes."
                    )
                else:
                    recipe = self.importer.import_from_text(file_path)
                    self.load_all_recipes()
                    self.window.display_recipe(recipe)
                    QMessageBox.information(
                        self.window,
                        "Import Successful",
                        f"Imported recipe: {recipe.title}"
                    )
                
                self.window.statusBar().showMessage("Import completed")
                
            except Exception as e:
                QMessageBox.critical(
                    self.window,
                    "Import Error",
                    f"Failed to import recipes: {str(e)}"
                )
    
    def handle_import_images(self):
        """Handle recipe import from images."""
        from src.ui.import_image_dialog import ImportImageDialog
        
        self.import_image_dialog = ImportImageDialog(
            config.OLLAMA_BASE_URL,
            config.OLLAMA_VISION_MODEL,
            self.window
        )
        
        # Connect the recipe_extracted signal
        self.import_image_dialog.recipe_extracted.connect(self._process_image_import)
        
        self.import_image_dialog.exec()
    
    def _process_image_import(self, recipe_data):
        """Process the extracted recipe data from images."""
        try:
            # Parse the ingredients using the two-pass system
            raw_ingredients = recipe_data.get('ingredients', [])
            
            if raw_ingredients:
                self.window.statusBar().showMessage("Parsing ingredients...")
                parsed_ingredients = self.url_importer.parse_ingredients_batch(raw_ingredients)
            else:
                parsed_ingredients = []
            
            # Helper to parse time strings to minutes (e.g., "30 minutes", "1 hour 15 min")
            def parse_time_to_minutes(time_str):
                """Convert time string to minutes integer."""
                if not time_str or 'not specified' in time_str.lower():
                    return None
                import re
                # Try to extract numbers and units
                hours = re.search(r'(\d+)\s*(?:hour|hr)', time_str, re.IGNORECASE)
                minutes = re.search(r'(\d+)\s*(?:minute|min)', time_str, re.IGNORECASE)
                total = 0
                if hours:
                    total += int(hours.group(1)) * 60
                if minutes:
                    total += int(minutes.group(1))
                return total if total > 0 else None
            
            # Parse servings to integer
            def parse_servings(servings_str):
                """Convert servings string to integer."""
                if not servings_str:
                    return 4  # Default
                import re
                # Extract first number (e.g., "4-6" -> 4, "6" -> 6)
                match = re.search(r'(\d+)', servings_str)
                return int(match.group(1)) if match else 4
            
            # Combine description and notes if needed
            description = recipe_data.get('description', '')
            notes = recipe_data.get('notes', '')
            if notes:
                if description:
                    description += '\n\nNotes:\n' + notes
                else:
                    description = notes
            
            # Create recipe
            saved_recipe = self.recipe_service.create_recipe(
                title=recipe_data.get('title', 'Untitled Recipe'),
                description=description,
                instructions=recipe_data.get('instructions', 'No instructions provided.'),
                servings=parse_servings(recipe_data.get('servings', '')),
                prep_time_minutes=parse_time_to_minutes(recipe_data.get('prep_time', '')),
                cook_time_minutes=parse_time_to_minutes(recipe_data.get('cook_time', '')),
                source_url='image_import'
            )
            
            # Add ingredients to recipe
            for idx, ing in enumerate(parsed_ingredients):
                self.recipe_service.add_ingredient_to_recipe(
                    recipe_id=saved_recipe.id,
                    ingredient_name=ing["name"],
                    quantity=ing["quantity"],
                    unit=ing["unit"],
                    preparation=ing.get("preparation", ""),
                    order_index=idx,
                )
            
            # Refresh UI
            self.load_all_recipes()
            self.window.expand_recipe_nodes(saved_recipe.id)
            self.window.display_recipe(saved_recipe)
            
            self.window.statusBar().showMessage(
                f"Imported recipe from images: {saved_recipe.title}"
            )
            
            # Close the import dialog
            if hasattr(self, 'import_image_dialog') and self.import_image_dialog:
                self.import_image_dialog.accept()
                self.import_image_dialog = None
            
            QMessageBox.information(
                self.window,
                "Import Successful",
                f"Successfully imported recipe: {saved_recipe.title}\n\n"
                f"Parsed {len(parsed_ingredients)} ingredients."
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            
            # Print to console for debugging
            print("=" * 70)
            print("IMAGE IMPORT ERROR:")
            print(error_details)
            print("=" * 70)
            
            # Create a scrollable, copyable error dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            
            error_dialog = QDialog(self.window)
            error_dialog.setWindowTitle("Import Error")
            error_dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(error_dialog)
            
            # Error message
            from PySide6.QtWidgets import QLabel
            label = QLabel("Failed to import recipe from images. Error details below (you can copy this text):")
            label.setWordWrap(True)
            layout.addWidget(label)
            
            # Scrollable text area with full error
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setPlainText(f"Error: {str(e)}\n\nFull traceback:\n{error_details}")
            layout.addWidget(error_text)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(error_dialog.accept)
            layout.addWidget(close_btn)
            
            # Close the import dialog on error too
            if hasattr(self, 'import_image_dialog') and self.import_image_dialog:
                self.import_image_dialog.reject()
                self.import_image_dialog = None
            
            error_dialog.exec()
    
    def handle_export(self):
        """Handle recipe export."""
        # Check if a single recipe is selected for HTML export
        current_recipe = self.window.current_recipe
        recipes = self.recipe_service.get_all_recipes()
        
        if not recipes:
            QMessageBox.information(
                self.window,
                "No Recipes",
                "There are no recipes to export."
            )
            return
        
        # If a recipe is selected, offer HTML export option
        if current_recipe:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self.window,
                "Export Recipe",
                f"{current_recipe.title.replace(' ', '_')}.html",
                "HTML Recipe File (*.html);;JSON Files (*.json);;Markdown (*.md);;All Files (*)"
            )
        else:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self.window,
                "Export Recipes",
                "recipes.json",
                "JSON Files (*.json);;All Files (*)"
            )
        
        if file_path:
            try:
                if file_path.endswith('.html') or file_path.endswith('.htm'):
                    if not current_recipe:
                        QMessageBox.warning(
                            self.window,
                            "No Recipe Selected",
                            "Please select a recipe to export as HTML."
                        )
                        return
                    self.exporter.export_to_html(current_recipe, file_path)
                    QMessageBox.information(
                        self.window,
                        "Export Successful",
                        f"Exported '{current_recipe.title}' as self-contained HTML recipe.\n\n"
                        f"You can open this file in any web browser!\n"
                        f"Features: servings scaler, unit converter, print-friendly."
                    )
                elif file_path.endswith('.md'):
                    if not current_recipe:
                        QMessageBox.warning(
                            self.window,
                            "No Recipe Selected",
                            "Please select a recipe to export as Markdown."
                        )
                        return
                    self.exporter.export_to_markdown(current_recipe, file_path)
                    QMessageBox.information(
                        self.window,
                        "Export Successful",
                        f"Exported '{current_recipe.title}' to {file_path}"
                    )
                else:
                    self.exporter.export_to_json(recipes, file_path)
                    QMessageBox.information(
                        self.window,
                        "Export Successful",
                        f"Exported {len(recipes)} recipes to {file_path}"
                    )
                self.window.statusBar().showMessage("Export completed")
                
            except ImportError as e:
                QMessageBox.critical(
                    self.window,
                    "Export Error",
                    f"Missing required library: {str(e)}\n\n"
                    f"Please install: pip install jinja2 beautifulsoup4"
                )
            except Exception as e:
                QMessageBox.critical(
                    self.window,
                    "Export Error",
                    f"Failed to export: {str(e)}"
                )
    
    def handle_preferences(self):
        """Handle preferences dialog."""
        from src.ui.settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.window)
        if dialog.exec():  # Dialog was accepted (Save clicked)
            self.reload_settings()
            self.window.statusBar().showMessage("Settings applied successfully", 3000)
    
    def handle_scale_recipe(self):
        """Handle recipe scaling."""
        if not self.window.current_recipe:
            QMessageBox.warning(
                self.window,
                "No Recipe Selected",
                "Please select a recipe to scale."
            )
            return
        
        recipe = self.window.current_recipe
        
        # Check if recipe has servings defined
        if not recipe.servings or recipe.servings == 0:
            QMessageBox.warning(
                self.window,
                "Cannot Scale Recipe",
                "This recipe does not have a servings count defined. "
                "Please edit the recipe to add servings before scaling."
            )
            return
        
        try:
            from src.ui.recipe_scaling_dialog import RecipeScalingDialog
            
            dialog = RecipeScalingDialog(recipe, self.recipe_scaling_service, self.window)
            
            if dialog.exec():
                scaled_data = dialog.get_scaled_data()
                
                if scaled_data:
                    # Ask if user wants to save as new recipe
                    result = QMessageBox.question(
                        self.window,
                        "Save Scaled Recipe",
                        f"Save '{scaled_data['title']}' as a new recipe?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if result == QMessageBox.Yes:
                        # Create new recipe from scaled data
                        new_recipe = Recipe(
                            title=scaled_data['title'],
                            description=scaled_data['description'],
                            instructions=scaled_data['instructions'],
                            servings=scaled_data['servings'],
                            prep_time_minutes=scaled_data['prep_time_minutes'],
                            cook_time_minutes=scaled_data['cook_time_minutes'],
                            total_time_minutes=scaled_data['total_time_minutes'],
                        )
                        
                        # Save the recipe first to get an ID
                        self.session.add(new_recipe)
                        self.session.flush()
                        
                        # Add scaled ingredients
                        for ing_data in scaled_data['ingredients']:
                            # Convert quantity to string for storage
                            quantity_str = str(ing_data['quantity'])
                            
                            self.recipe_service.add_ingredient_to_recipe(
                                new_recipe.id,
                                ing_data['ingredient_name'],
                                quantity=quantity_str,
                                unit=ing_data['unit'],
                                display_quantity=quantity_str,
                                display_unit=ing_data['unit'],
                                preparation=ing_data.get('preparation')
                            )
                        
                        # Copy tags from original recipe
                        for tag in recipe.tags:
                            new_recipe.tags.append(tag)
                        
                        # Save the new recipe
                        self.session.add(new_recipe)
                        self.session.commit()
                        
                        # Refresh the recipe list
                        self.load_all_recipes()
                        
                        # Find and display the new recipe
                        self.window.expand_recipe_nodes(new_recipe.id)
                        self.window.display_recipe(new_recipe)
                        
                        self.window.statusBar().showMessage(
                            f"Scaled recipe saved: {new_recipe.title}"
                        )
        
        except Exception as e:
            print(f"Error scaling recipe: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.window,
                "Error",
                f"Failed to scale recipe:\n{str(e)}"
            )
    
    def handle_print_recipe(self):
        """Handle recipe printing."""
        if not self.window.current_recipe:
            QMessageBox.warning(
                self.window,
                "No Recipe Selected",
                "Please select a recipe to print."
            )
            return
        
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QTextDocument, QPageLayout
            from PySide6.QtCore import QMarginsF
            from src.ui.unit_conversion_dialog import format_quantity_as_fraction
            
            recipe = self.window.current_recipe
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            
            dialog = QPrintDialog(printer, self.window)
            if dialog.exec() == QPrintDialog.Accepted:
                # Build HTML document for the recipe
                html = f"<h1>{recipe.title}</h1>"
                
                # Metadata
                meta_parts = []
                if recipe.servings:
                    meta_parts.append(f"Serves {recipe.servings}")
                if recipe.prep_time_minutes:
                    meta_parts.append(f"Prep: {recipe.prep_time_minutes} min")
                if recipe.cook_time_minutes:
                    meta_parts.append(f"Cook: {recipe.cook_time_minutes} min")
                if recipe.total_time_minutes:
                    meta_parts.append(f"Total: {recipe.total_time_minutes} min")
                
                if meta_parts:
                    html += f"<p><i>{' | '.join(meta_parts)}</i></p>"
                
                # Description
                if recipe.description:
                    html += f"<p>{recipe.description}</p>"
                
                # Ingredients
                html += "<h2>Ingredients</h2><ul>"
                for ri in recipe.ingredients:
                    ingredient = ri.ingredient
                    try:
                        quantity_value = float(ri.display_quantity)
                        formatted_quantity = format_quantity_as_fraction(quantity_value)
                    except (ValueError, TypeError):
                        formatted_quantity = ri.display_quantity
                    
                    text = f"{formatted_quantity} {ri.display_unit} {ingredient.name}"
                    if ri.preparation:
                        text += f", {ri.preparation}"
                    html += f"<li>{text}</li>"
                html += "</ul>"
                
                # Instructions
                html += "<h2>Instructions</h2>"
                instructions = recipe.instructions.replace('\n', '<br>')
                html += f"<p>{instructions}</p>"
                
                # Tags
                if recipe.tags:
                    tag_names = ", ".join([tag.name for tag in recipe.tags])
                    html += f"<p><i>Tags: {tag_names}</i></p>"
                
                # Create document and print
                document = QTextDocument()
                document.setHtml(html)
                document.print_(printer)
                
        except Exception as e:
            print(f"Error printing recipe: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.window,
                "Error",
                f"Failed to print recipe:\n{str(e)}"
            )
    
    def handle_shopping_list(self):
        """Handle shopping list generation."""
        try:
            # Get all recipes
            all_recipes = self.recipe_service.get_all_recipes()
            
            if not all_recipes:
                QMessageBox.information(
                    self.window,
                    "No Recipes",
                    "You don't have any recipes yet. Add some recipes first!"
                )
                return
            
            from src.ui.shopping_list_dialog import ShoppingListDialog
            
            dialog = ShoppingListDialog(
                all_recipes,
                self.shopping_list_service,
                self.window
            )
            dialog.exec()
            
        except Exception as e:
            print(f"Error opening shopping list dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.window,
                "Error",
                f"Failed to generate shopping list:\n{str(e)}"
            )
    
    def handle_convert_units(self):
        """Handle unit conversion dialog."""
        try:
            dialog = UnitConversionDialog(self.unit_conversion_service, self.window)
            dialog.exec()
        except Exception as e:
            print(f"Error opening unit conversion dialog: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.window,
                "Error",
                f"Failed to open unit conversion dialog:\n{str(e)}"
            )
