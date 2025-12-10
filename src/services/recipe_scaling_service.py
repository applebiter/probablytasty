"""
Service for scaling recipe quantities.
"""

from typing import Dict, List, Tuple
from src.models import Recipe, RecipeIngredient


class RecipeScalingService:
    """Service to scale recipe quantities based on serving size."""
    
    def __init__(self):
        pass
    
    def scale_recipe(self, recipe: Recipe, target_servings: int) -> Dict:
        """
        Scale a recipe to a different number of servings.
        
        Args:
            recipe: The recipe to scale
            target_servings: The desired number of servings
            
        Returns:
            Dictionary with scaled recipe data including:
            - title: Original title with scaling note
            - servings: Target servings
            - prep_time_minutes, cook_time_minutes, total_time_minutes: Unchanged
            - ingredients: List of scaled ingredients with formatted quantities
            - instructions: Original instructions (user may need to adjust manually)
        """
        if not recipe.servings or recipe.servings == 0:
            raise ValueError("Original recipe must have a valid servings count")
        
        if target_servings <= 0:
            raise ValueError("Target servings must be greater than 0")
        
        # Calculate scaling factor
        scale_factor = target_servings / recipe.servings
        
        # Scale ingredients
        scaled_ingredients = []
        for ri in recipe.ingredients:
            scaled_ingredient = self._scale_ingredient(ri, scale_factor)
            scaled_ingredients.append(scaled_ingredient)
        
        # Build result
        result = {
            'title': f"{recipe.title} (scaled to {target_servings} servings)",
            'original_title': recipe.title,
            'servings': target_servings,
            'original_servings': recipe.servings,
            'scale_factor': scale_factor,
            'prep_time_minutes': recipe.prep_time_minutes,
            'cook_time_minutes': recipe.cook_time_minutes,
            'total_time_minutes': recipe.total_time_minutes,
            'ingredients': scaled_ingredients,
            'instructions': recipe.instructions,
            'description': recipe.description,
        }
        
        return result
    
    def _scale_ingredient(self, recipe_ingredient: RecipeIngredient, scale_factor: float) -> Dict:
        """
        Scale a single ingredient by the scaling factor.
        
        Args:
            recipe_ingredient: The ingredient to scale
            scale_factor: The multiplier (e.g., 2.0 for doubling)
            
        Returns:
            Dictionary with scaled ingredient data
        """
        ingredient = recipe_ingredient.ingredient
        
        # Try to parse and scale the quantity
        try:
            # Handle simple numeric quantities
            original_quantity = float(recipe_ingredient.display_quantity)
            scaled_quantity = original_quantity * scale_factor
            
            # Round to reasonable precision
            scaled_quantity = round(scaled_quantity, 3)
            
        except (ValueError, TypeError):
            # Handle ranges like "4-6" or special cases
            original_qty = recipe_ingredient.display_quantity
            if '-' in original_qty:
                # Try to scale a range
                try:
                    parts = original_qty.split('-')
                    min_val = float(parts[0].strip()) * scale_factor
                    max_val = float(parts[1].strip()) * scale_factor
                    scaled_quantity = f"{round(min_val, 2)}-{round(max_val, 2)}"
                except:
                    # Can't parse, keep original
                    scaled_quantity = original_qty
            else:
                # Keep original if we can't parse it
                scaled_quantity = original_qty
        
        return {
            'ingredient_name': ingredient.name,
            'quantity': scaled_quantity,
            'unit': recipe_ingredient.display_unit,
            'preparation': recipe_ingredient.preparation,
            'ingredient_id': ingredient.id,
        }
    
    def format_scaled_ingredients_text(self, scaled_ingredients: List[Dict]) -> str:
        """
        Format scaled ingredients as readable text.
        
        Args:
            scaled_ingredients: List of scaled ingredient dictionaries
            
        Returns:
            Formatted text string
        """
        from src.ui.unit_conversion_dialog import format_quantity_as_fraction
        
        lines = []
        for ing in scaled_ingredients:
            # Format quantity as fraction if numeric
            try:
                if isinstance(ing['quantity'], (int, float)):
                    formatted_qty = format_quantity_as_fraction(float(ing['quantity']))
                else:
                    formatted_qty = str(ing['quantity'])
            except:
                formatted_qty = str(ing['quantity'])
            
            text = f"{formatted_qty} {ing['unit']} {ing['ingredient_name']}"
            if ing.get('preparation'):
                text += f", {ing['preparation']}"
            lines.append(text)
        
        return '\n'.join(lines)
