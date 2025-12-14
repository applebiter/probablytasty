"""
Import/export utilities for recipes.
"""

import json
import sys
from typing import List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import Recipe, Ingredient, RecipeIngredient, Tag
from src.services.recipe_service import RecipeService

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class RecipeImporter:
    """Import recipes from various formats."""
    
    def __init__(self, session: Session):
        self.session = session
        self.recipe_service = RecipeService(session)
    
    def import_from_json(self, file_path: str) -> List[Recipe]:
        """
        Import recipes from JSON file.
        
        Expected format:
        {
            "recipes": [
                {
                    "title": "Recipe Name",
                    "description": "...",
                    "instructions": "...",
                    "servings": 4,
                    "prep_time_minutes": 15,
                    "cook_time_minutes": 30,
                    "source_url": "...",
                    "ingredients": [
                        {
                            "name": "flour",
                            "quantity": 2,
                            "unit": "cup",
                            "preparation": "sifted"
                        }
                    ],
                    "tags": ["vegetarian", "quick"]
                }
            ]
        }
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_recipes = []
        
        for recipe_data in data.get("recipes", []):
            try:
                # Create recipe
                recipe = self.recipe_service.create_recipe(
                    title=recipe_data["title"],
                    instructions=recipe_data["instructions"],
                    description=recipe_data.get("description"),
                    servings=recipe_data.get("servings", 4),
                    prep_time_minutes=recipe_data.get("prep_time_minutes"),
                    cook_time_minutes=recipe_data.get("cook_time_minutes"),
                    source_url=recipe_data.get("source_url"),
                )
                
                # Add ingredients
                for idx, ingredient_data in enumerate(recipe_data.get("ingredients", [])):
                    self.recipe_service.add_ingredient_to_recipe(
                        recipe_id=recipe.id,
                        ingredient_name=ingredient_data["name"],
                        quantity=ingredient_data["quantity"],
                        unit=ingredient_data["unit"],
                        display_quantity=ingredient_data.get("display_quantity", ingredient_data["quantity"]),
                        display_unit=ingredient_data.get("display_unit", ingredient_data["unit"]),
                        preparation=ingredient_data.get("preparation"),
                        order_index=idx,
                    )
                
                # Add tags
                for tag_name in recipe_data.get("tags", []):
                    self.recipe_service.add_tag_to_recipe(recipe.id, tag_name)
                
                imported_recipes.append(recipe)
                
            except Exception as e:
                print(f"Error importing recipe '{recipe_data.get('title', 'unknown')}': {e}")
                continue
        
        return imported_recipes
    
    def import_from_text(self, file_path: str) -> Recipe:
        """
        Import a single recipe from plain text/markdown file.
        Uses basic parsing to extract title, ingredients, and instructions.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        title = Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
        
        # Try to extract title from first line if it looks like a title
        if lines and (lines[0].startswith('#') or len(lines[0]) < 100):
            title = lines[0].strip('#').strip()
            lines = lines[1:]
        
        # Simple heuristic parsing
        ingredients_section = []
        instructions_section = []
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'ingredient' in line_lower:
                current_section = 'ingredients'
                continue
            elif 'instruction' in line_lower or 'direction' in line_lower or 'method' in line_lower:
                current_section = 'instructions'
                continue
            
            if current_section == 'ingredients' and line.strip():
                ingredients_section.append(line.strip())
            elif current_section == 'instructions' and line.strip():
                instructions_section.append(line.strip())
        
        # If no sections found, treat everything as instructions
        if not ingredients_section and not instructions_section:
            instructions_section = [line.strip() for line in lines if line.strip()]
        
        instructions = '\n'.join(instructions_section) if instructions_section else content
        
        # Create recipe
        recipe = self.recipe_service.create_recipe(
            title=title,
            instructions=instructions,
            description="Imported from text file",
        )
        
        # Parse and add ingredients (simple extraction)
        for ingredient_line in ingredients_section:
            # This is a very simple parser - could be enhanced
            parts = ingredient_line.strip('•-*').strip().split(None, 2)
            if len(parts) >= 2:
                try:
                    quantity = float(parts[0])
                    unit = parts[1] if len(parts) > 1 else ""
                    name = parts[2] if len(parts) > 2 else parts[1]
                    
                    self.recipe_service.add_ingredient_to_recipe(
                        recipe_id=recipe.id,
                        ingredient_name=name,
                        quantity=quantity,
                        unit=unit,
                    )
                except ValueError:
                    # Couldn't parse quantity, add as-is
                    self.recipe_service.add_ingredient_to_recipe(
                        recipe_id=recipe.id,
                        ingredient_name=ingredient_line,
                        quantity=1,
                        unit="",
                    )
        
        return recipe
    
    def import_from_html(self, file_path: str) -> List[Recipe]:
        """
        Import recipes from self-contained HTML file.
        Extracts JSON data from <script type="application/json" id="recipe-data"> tag.
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            raise ImportError("BeautifulSoup4 is required for HTML import. Install with: pip install beautifulsoup4")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the embedded JSON data
        json_script = soup.find('script', {'type': 'application/json', 'id': 'recipe-data'})
        
        if not json_script:
            raise ValueError("No recipe data found in HTML file. Expected <script type='application/json' id='recipe-data'>")
        
        recipe_data = json.loads(json_script.string)
        
        # Import as if it were JSON
        try:
            # Create recipe
            recipe = self.recipe_service.create_recipe(
                title=recipe_data["title"],
                instructions=recipe_data["instructions"],
                description=recipe_data.get("description"),
                servings=recipe_data.get("servings", 4),
                prep_time_minutes=recipe_data.get("prep_time_minutes"),
                cook_time_minutes=recipe_data.get("cook_time_minutes"),
                source_url=recipe_data.get("source_url"),
            )
            
            # Add ingredients
            for idx, ingredient_data in enumerate(recipe_data.get("ingredients", [])):
                self.recipe_service.add_ingredient_to_recipe(
                    recipe_id=recipe.id,
                    ingredient_name=ingredient_data["name"],
                    quantity=ingredient_data["quantity"],
                    unit=ingredient_data["unit"],
                    display_quantity=ingredient_data.get("display_quantity", ingredient_data["quantity"]),
                    display_unit=ingredient_data.get("display_unit", ingredient_data["unit"]),
                    preparation=ingredient_data.get("preparation"),
                    order_index=idx,
                )
            
            # Add tags
            for tag_name in recipe_data.get("tags", []):
                self.recipe_service.add_tag_to_recipe(recipe.id, tag_name)
            
            return [recipe]
            
        except Exception as e:
            print(f"Error importing recipe from HTML '{recipe_data.get('title', 'unknown')}': {e}")
            raise


class RecipeExporter:
    """Export recipes to various formats."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def export_to_json(self, recipes: List[Recipe], file_path: str):
        """Export recipes to JSON file."""
        recipes_data = []
        
        for recipe in recipes:
            recipe_dict = {
                "title": recipe.title,
                "description": recipe.description,
                "instructions": recipe.instructions,
                "servings": recipe.servings,
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "total_time_minutes": recipe.total_time_minutes,
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
            recipes_data.append(recipe_dict)
        
        data = {"recipes": recipes_data}
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_to_markdown(self, recipe: Recipe, file_path: str):
        """Export a single recipe to Markdown file."""
        lines = []
        
        # Title
        lines.append(f"# {recipe.title}\n")
        
        # Metadata
        meta = []
        if recipe.servings:
            meta.append(f"**Serves:** {recipe.servings}")
        if recipe.prep_time_minutes:
            meta.append(f"**Prep Time:** {recipe.prep_time_minutes} minutes")
        if recipe.cook_time_minutes:
            meta.append(f"**Cook Time:** {recipe.cook_time_minutes} minutes")
        if recipe.total_time_minutes:
            meta.append(f"**Total Time:** {recipe.total_time_minutes} minutes")
        
        if meta:
            lines.append(" | ".join(meta) + "\n")
        
        # Tags
        if recipe.tags:
            tags_text = ", ".join([f"*{tag.name}*" for tag in recipe.tags])
            lines.append(f"\n**Tags:** {tags_text}\n")
        
        # Description
        if recipe.description:
            lines.append(f"\n{recipe.description}\n")
        
        # Ingredients
        lines.append("\n## Ingredients\n")
        for ri in recipe.ingredients:
            ingredient_text = f"- {ri.display_quantity} {ri.display_unit} {ri.ingredient.name}"
            if ri.preparation:
                ingredient_text += f", {ri.preparation}"
            lines.append(ingredient_text)
        
        # Instructions
        lines.append("\n## Instructions\n")
        
        # Try to format instructions as numbered steps
        instructions = recipe.instructions.strip()
        instruction_lines = instructions.split('\n')
        
        # Check if already numbered
        if any(line.strip() and line.strip()[0].isdigit() for line in instruction_lines):
            lines.append(instructions)
        else:
            # Number the paragraphs
            step_num = 1
            for line in instruction_lines:
                if line.strip():
                    lines.append(f"{step_num}. {line.strip()}")
                    step_num += 1
                else:
                    lines.append("")
        
        # Source
        if recipe.source_url:
            lines.append(f"\n## Source\n\n{recipe.source_url}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def export_to_html(self, recipe: Recipe, file_path: str):
        """Export a single recipe to self-contained HTML file with embedded JavaScript."""
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required for HTML export. Install with: pip install jinja2")
        
        # Prepare recipe data
        recipe_data = {
            "title": recipe.title,
            "description": recipe.description,
            "instructions": recipe.instructions,
            "servings": recipe.servings,
            "prep_time_minutes": recipe.prep_time_minutes,
            "cook_time_minutes": recipe.cook_time_minutes,
            "total_time_minutes": recipe.total_time_minutes,
            "source_url": recipe.source_url,
            "ingredients": [
                {
                    "name": ri.ingredient.name,
                    "quantity": float(ri.display_quantity) if ri.display_quantity else 0,
                    "unit": ri.display_unit or "",
                    "preparation": ri.preparation or "",
                }
                for ri in recipe.ingredients
            ],
            "tags": [tag.name for tag in recipe.tags],
        }
        
        # Load template
        # PyInstaller compatibility: check if running as bundled exe
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = Path(sys._MEIPASS)
            template_path = base_path / "src" / "templates" / "recipe.html"
        else:
            # Running as script - __file__ is already in src/utils/
            base_path = Path(__file__).parent.parent  # Go up to project root
            template_path = base_path / "templates" / "recipe.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # Render with embedded JSON (properly indented)
        recipe_json = json.dumps(recipe_data, indent=2, ensure_ascii=False)
        html_output = template.render(
            title=recipe.title,
            description=recipe.description,
            recipe_json=recipe_json
        )
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
