"""
Database models for ProbablyTasty.
"""

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for recipe-tag many-to-many relationship
recipe_tags = Table(
    'recipe_tags',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Recipe(Base):
    """Recipe model."""
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    servings = Column(Integer)
    prep_time_minutes = Column(Integer)
    cook_time_minutes = Column(Integer)
    total_time_minutes = Column(Integer)
    source = Column(String(500))
    source_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ingredients = relationship('RecipeIngredient', back_populates='recipe', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=recipe_tags, back_populates='recipes')
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, title='{self.title}')>"


class Ingredient(Base):
    """Ingredient model."""
    __tablename__ = 'ingredients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    category = Column(String(100))
    
    # Relationships
    recipe_ingredients = relationship('RecipeIngredient', back_populates='ingredient')
    
    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}')>"


class RecipeIngredient(Base):
    """Junction table with additional fields for recipe-ingredient relationship."""
    __tablename__ = 'recipe_ingredients'
    
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))
    display_quantity = Column(String(50))
    display_unit = Column(String(50))
    order_index = Column(Integer)
    preparation = Column(String(200))  # e.g., "chopped", "diced", "sliced"
    
    # Relationships
    recipe = relationship('Recipe', back_populates='ingredients')
    ingredient = relationship('Ingredient', back_populates='recipe_ingredients')
    
    def __repr__(self):
        return f"<RecipeIngredient(recipe_id={self.recipe_id}, ingredient_id={self.ingredient_id}, quantity={self.quantity}, unit='{self.unit}')>"


class Tag(Base):
    """Tag model for categorizing recipes."""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey('tags.id'), nullable=True)
    
    # Relationships
    recipes = relationship('Recipe', secondary=recipe_tags, back_populates='tags')
    parent = relationship('Tag', remote_side=[id], backref='children')
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"
