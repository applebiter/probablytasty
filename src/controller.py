"""
Application controller coordinating UI and services.
"""

from typing import Optional
from PySide6.QtWidgets import QFileDialog, QMessageBox
from sqlalchemy.orm import Session
from src.ui import MainWindow, RecipeEditorDialog
from src.services import RecipeService, SearchOrchestrator, LLMRouter, LLMProvider
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
        
        # Initialize LLM router
        self.llm_router = LLMRouter(
            preferred_provider=LLMProvider[config.DEFAULT_LLM_PROVIDER.upper()],
            openai_key=config.OPENAI_API_KEY,
            anthropic_key=config.ANTHROPIC_API_KEY,
            google_key=config.GOOGLE_API_KEY,
        )
        
        self.search_orchestrator = SearchOrchestrator(session, self.llm_router)
        self.importer = RecipeImporter(session)
        self.exporter = RecipeExporter(session)
        
        # Connect UI signals to controller methods
        self.connect_signals()
        
        # Load initial data
        self.load_all_recipes()
    
    def connect_signals(self):
        """Connect UI signals to controller methods."""
        self.window.on_search = self.handle_search
        self.window.on_recipe_selected = self.handle_recipe_selected
        self.window.on_new_recipe = self.handle_new_recipe
        self.window.on_edit_recipe = self.handle_edit_recipe
        self.window.on_delete_recipe = self.handle_delete_recipe
        self.window.on_import = self.handle_import
        self.window.on_export = self.handle_export
        self.window.on_preferences = self.handle_preferences
    
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
        
        self.window.statusBar().showMessage("Searching...")
        
        try:
            # Use LLM-powered search if available
            use_llm = self.llm_router.is_available()
            recipes = self.search_orchestrator.search(query, use_llm=use_llm)
            
            self.window.load_recipes(recipes)
            
            search_method = "AI-powered" if use_llm else "keyword"
            self.window.statusBar().showMessage(
                f"Found {len(recipes)} recipes using {search_method} search"
            )
        except Exception as e:
            QMessageBox.warning(
                self.window,
                "Search Error",
                f"An error occurred during search: {str(e)}"
            )
            self.window.statusBar().showMessage("Search failed")
    
    def handle_recipe_selected(self, item):
        """Handle recipe selection from list."""
        recipe_id = item.data(0x0100)  # Qt.UserRole
        recipe = self.recipe_service.get_recipe(recipe_id)
        
        if recipe:
            self.window.display_recipe(recipe)
            self.window.statusBar().showMessage(f"Viewing: {recipe.title}")
    
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
                    self.window.display_recipe(recipe)
                    self.window.statusBar().showMessage(f"Created: {recipe.title}")
                    
                except Exception as e:
                    QMessageBox.critical(
                        self.window,
                        "Error",
                        f"Failed to create recipe: {str(e)}"
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
                    
                    # Note: For simplicity, we're not updating ingredients/tags here
                    # In a full implementation, you'd want to handle this properly
                    
                    # Refresh display
                    updated_recipe = self.recipe_service.get_recipe(recipe.id)
                    self.load_all_recipes()
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
            "JSON Files (*.json);;Text Files (*.txt *.md);;All Files (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
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
    
    def handle_export(self):
        """Handle recipe export."""
        recipes = self.recipe_service.get_all_recipes()
        
        if not recipes:
            QMessageBox.information(
                self.window,
                "No Recipes",
                "There are no recipes to export."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Export Recipes",
            "recipes.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.exporter.export_to_json(recipes, file_path)
                QMessageBox.information(
                    self.window,
                    "Export Successful",
                    f"Exported {len(recipes)} recipes to {file_path}"
                )
                self.window.statusBar().showMessage("Export completed")
                
            except Exception as e:
                QMessageBox.critical(
                    self.window,
                    "Export Error",
                    f"Failed to export recipes: {str(e)}"
                )
    
    def handle_preferences(self):
        """Handle preferences dialog."""
        # TODO: Implement preferences dialog
        QMessageBox.information(
            self.window,
            "Preferences",
            "Preferences dialog coming soon!\n\n"
            f"Current LLM Provider: {config.DEFAULT_LLM_PROVIDER}\n"
            f"Unit System: {config.DEFAULT_UNIT_SYSTEM}"
        )
