"""
Database initialization script with sample data.
"""

from src.models.database import init_database, get_session
from src.services.recipe_service import RecipeService


def add_sample_data():
    """Add sample recipes to the database."""
    session = get_session()
    recipe_service = RecipeService(session)
    
    print("Adding sample recipes...")
    
    # Recipe 1: Classic Spaghetti Carbonara
    carbonara = recipe_service.create_recipe(
        title="Classic Spaghetti Carbonara",
        description="A traditional Italian pasta dish with eggs, cheese, and pancetta.",
        instructions="""1. Bring a large pot of salted water to boil and cook spaghetti according to package directions.
2. While pasta cooks, fry pancetta in a large skillet until crispy.
3. In a bowl, whisk together eggs, Parmesan cheese, and black pepper.
4. Drain pasta, reserving 1 cup pasta water.
5. Add hot pasta to the pancetta, remove from heat.
6. Quickly stir in egg mixture, adding pasta water to create a creamy sauce.
7. Serve immediately with extra Parmesan and black pepper.""",
        servings=4,
        prep_time_minutes=10,
        cook_time_minutes=20,
    )
    
    recipe_service.add_ingredient_to_recipe(carbonara.id, "spaghetti", 400, "g")
    recipe_service.add_ingredient_to_recipe(carbonara.id, "pancetta", 200, "g", preparation="diced")
    recipe_service.add_ingredient_to_recipe(carbonara.id, "eggs", 4, "count")
    recipe_service.add_ingredient_to_recipe(carbonara.id, "parmesan cheese", 100, "g", preparation="grated")
    recipe_service.add_ingredient_to_recipe(carbonara.id, "black pepper", 1, "tsp", preparation="freshly ground")
    
    recipe_service.add_tag_to_recipe(carbonara.id, "italian")
    recipe_service.add_tag_to_recipe(carbonara.id, "pasta")
    recipe_service.add_tag_to_recipe(carbonara.id, "quick")
    
    # Recipe 2: Vegetarian Buddha Bowl
    buddha_bowl = recipe_service.create_recipe(
        title="Vegetarian Buddha Bowl",
        description="A healthy and colorful bowl packed with vegetables, grains, and protein.",
        instructions="""1. Cook quinoa according to package directions.
2. Roast chickpeas with olive oil and spices at 400°F for 20 minutes.
3. Steam or roast sweet potato cubes until tender.
4. Sauté kale with garlic until wilted.
5. Prepare tahini dressing by whisking tahini, lemon juice, and water.
6. Assemble bowls with quinoa as base, add vegetables and chickpeas.
7. Drizzle with tahini dressing and top with avocado.""",
        servings=2,
        prep_time_minutes=15,
        cook_time_minutes=30,
    )
    
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "quinoa", 1, "cup")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "chickpeas", 400, "g")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "sweet potato", 2, "count", preparation="cubed")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "kale", 200, "g", preparation="chopped")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "avocado", 1, "count", preparation="sliced")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "tahini", 3, "tbsp")
    recipe_service.add_ingredient_to_recipe(buddha_bowl.id, "lemon juice", 2, "tbsp")
    
    recipe_service.add_tag_to_recipe(buddha_bowl.id, "vegetarian")
    recipe_service.add_tag_to_recipe(buddha_bowl.id, "healthy")
    recipe_service.add_tag_to_recipe(buddha_bowl.id, "vegan")
    
    # Recipe 3: Chocolate Chip Cookies
    cookies = recipe_service.create_recipe(
        title="Classic Chocolate Chip Cookies",
        description="Soft and chewy chocolate chip cookies that everyone loves.",
        instructions="""1. Preheat oven to 350°F (175°C).
2. Cream together butter and sugars until fluffy.
3. Beat in eggs and vanilla extract.
4. In separate bowl, whisk together flour, baking soda, and salt.
5. Gradually mix dry ingredients into wet ingredients.
6. Fold in chocolate chips.
7. Drop rounded tablespoons of dough onto baking sheets.
8. Bake for 10-12 minutes until edges are golden.
9. Cool on baking sheet for 5 minutes, then transfer to wire rack.""",
        servings=24,
        prep_time_minutes=15,
        cook_time_minutes=12,
    )
    
    recipe_service.add_ingredient_to_recipe(cookies.id, "butter", 1, "cup", preparation="softened")
    recipe_service.add_ingredient_to_recipe(cookies.id, "sugar", 0.75, "cup")
    recipe_service.add_ingredient_to_recipe(cookies.id, "brown sugar", 0.75, "cup", preparation="packed")
    recipe_service.add_ingredient_to_recipe(cookies.id, "eggs", 2, "count")
    recipe_service.add_ingredient_to_recipe(cookies.id, "vanilla extract", 2, "tsp")
    recipe_service.add_ingredient_to_recipe(cookies.id, "flour", 2.25, "cup")
    recipe_service.add_ingredient_to_recipe(cookies.id, "baking soda", 1, "tsp")
    recipe_service.add_ingredient_to_recipe(cookies.id, "salt", 1, "tsp")
    recipe_service.add_ingredient_to_recipe(cookies.id, "chocolate chips", 2, "cup")
    
    recipe_service.add_tag_to_recipe(cookies.id, "dessert")
    recipe_service.add_tag_to_recipe(cookies.id, "baking")
    recipe_service.add_tag_to_recipe(cookies.id, "cookies")
    
    print(f"✓ Added 3 sample recipes")
    
    session.close()


def main():
    """Initialize database and optionally add sample data."""
    print("=" * 50)
    print("ProbablyTasty Database Initialization")
    print("=" * 50)
    
    # Initialize database schema
    init_database()
    
    # Ask if user wants sample data
    response = input("\nWould you like to add sample recipes? (y/n): ").strip().lower()
    
    if response == 'y':
        add_sample_data()
        print("\n✓ Database initialization complete with sample data!")
    else:
        print("\n✓ Database initialization complete!")
    
    print("\nYou can now run the application with: python -m src.main")


if __name__ == "__main__":
    main()
