"""
Recipe service for CRUD operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from src.models import Recipe, Ingredient, RecipeIngredient, Tag


class RecipeService:
    """Service for managing recipes."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_recipe(
        self,
        title: str,
        instructions: str,
        description: Optional[str] = None,
        servings: int = 4,
        prep_time_minutes: Optional[int] = None,
        cook_time_minutes: Optional[int] = None,
        source_url: Optional[str] = None,
    ) -> Recipe:
        """Create a new recipe."""
        total_time = None
        if prep_time_minutes and cook_time_minutes:
            total_time = prep_time_minutes + cook_time_minutes
        
        recipe = Recipe(
            title=title,
            description=description,
            instructions=instructions,
            servings=servings,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
            total_time_minutes=total_time,
            source_url=source_url,
        )
        
        self.session.add(recipe)
        self.session.commit()
        self.session.refresh(recipe)
        return recipe
    
    def get_recipe(self, recipe_id: int) -> Optional[Recipe]:
        """Get a recipe by ID."""
        return self.session.query(Recipe).filter(Recipe.id == recipe_id).first()
    
    def get_all_recipes(self, limit: Optional[int] = None) -> List[Recipe]:
        """Get all recipes."""
        query = self.session.query(Recipe).order_by(Recipe.title)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update_recipe(self, recipe_id: int, **kwargs) -> Optional[Recipe]:
        """Update a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        
        for key, value in kwargs.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)
        
        # Recalculate total time if prep or cook time changed
        if "prep_time_minutes" in kwargs or "cook_time_minutes" in kwargs:
            if recipe.prep_time_minutes and recipe.cook_time_minutes:
                recipe.total_time_minutes = recipe.prep_time_minutes + recipe.cook_time_minutes
        
        self.session.commit()
        self.session.refresh(recipe)
        return recipe
    
    def delete_recipe(self, recipe_id: int) -> bool:
        """Delete a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return False
        
        self.session.delete(recipe)
        self.session.commit()
        return True
    
    def search_recipes(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_time: Optional[int] = None,
    ) -> List[Recipe]:
        """
        Search recipes with filters.
        
        Args:
            query: Text to search in title and description
            tags: List of tag names to filter by
            max_time: Maximum total time in minutes
            
        Returns:
            List of matching recipes
        """
        q = self.session.query(Recipe)
        
        if query:
            search = f"%{query}%"
            q = q.filter(
                (Recipe.title.ilike(search)) | 
                (Recipe.description.ilike(search))
            )
        
        if tags:
            for tag_name in tags:
                q = q.filter(Recipe.tags.any(Tag.name == tag_name))
        
        if max_time:
            q = q.filter(
                (Recipe.total_time_minutes <= max_time) |
                (Recipe.total_time_minutes == None)
            )
        
        return q.order_by(Recipe.title).all()
    
    def add_ingredient_to_recipe(
        self,
        recipe_id: int,
        ingredient_name: str,
        quantity,  # Can be float or string (for ranges like "4-6")
        unit: str,
        display_quantity=None,  # Can be float or string
        display_unit: Optional[str] = None,
        preparation: Optional[str] = None,
        order_index: int = 0,
    ) -> Optional[RecipeIngredient]:
        """Add an ingredient to a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        
        # Get or create ingredient
        ingredient = self.session.query(Ingredient).filter(
            Ingredient.name == ingredient_name
        ).first()
        
        if not ingredient:
            ingredient = Ingredient(name=ingredient_name)
            self.session.add(ingredient)
            self.session.flush()
        
        # Create recipe ingredient
        # Handle quantity - convert to float if possible, otherwise 0
        try:
            qty_float = float(quantity) if quantity else 0.0
        except (ValueError, TypeError):
            # If it's a fraction like "1/2" or range like "4-6", store 0 and use display_quantity
            qty_float = 0.0
        
        # Convert display quantities to strings
        qty_str = str(quantity) if quantity else ""
        display_qty_str = str(display_quantity) if display_quantity and not isinstance(display_quantity, str) else (display_quantity or qty_str)
        
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient.id,
            quantity=qty_float,
            unit=unit,
            display_quantity=display_qty_str,
            display_unit=display_unit or unit,
            preparation=preparation,
            order_index=order_index,
        )
        
        self.session.add(recipe_ingredient)
        self.session.commit()
        self.session.refresh(recipe_ingredient)
        return recipe_ingredient
    
    def add_tag_to_recipe(self, recipe_id: int, tag_name: str) -> bool:
        """Add a tag to a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return False
        
        # Get or create tag
        tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            self.session.add(tag)
            self.session.flush()
        
        if tag not in recipe.tags:
            recipe.tags.append(tag)
            self.session.commit()
        
        return True
    
    def remove_tag_from_recipe(self, recipe_id: int, tag_name: str) -> bool:
        """Remove a tag from a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return False
        
        tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if tag and tag in recipe.tags:
            recipe.tags.remove(tag)
            self.session.commit()
            return True
        
        return False
    
    def get_all_tags(self) -> List[Tag]:
        """Get all available tags."""
        return self.session.query(Tag).order_by(Tag.name).all()
