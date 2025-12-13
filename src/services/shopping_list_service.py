"""
Service for generating shopping lists from multiple recipes.
"""

from typing import List, Dict, Tuple
from collections import defaultdict
from src.models import Recipe
from src.services.unit_conversion import UnitConversionService


class ShoppingListService:
    """Service to aggregate ingredients across multiple recipes."""
    
    # Unit hierarchy for consolidation (larger units to smaller)
    VOLUME_HIERARCHY = [
        ('gallon', 'gallon', 3785.41),  # ml
        ('quart', 'quart', 946.353),
        ('pint', 'pint', 473.176),
        ('cup', 'cup', 236.588),
        ('fl oz', 'fluid ounce', 29.5735),
        ('tbsp', 'tablespoon', 14.7868),
        ('tsp', 'teaspoon', 4.92892),
        ('l', 'liter', 1000.0),
        ('ml', 'milliliter', 1.0),
    ]
    
    # Cooking volume hierarchy for dry ingredients (uses cups/tablespoons, not quarts)
    COOKING_VOLUME_HIERARCHY = [
        ('cup', 'cup', 236.588),
        ('tbsp', 'tablespoon', 14.7868),
        ('tsp', 'teaspoon', 4.92892),
    ]
    
    MASS_HIERARCHY = [
        ('lb', 'lb', 453.592),  # grams
        ('oz', 'oz', 28.3495),
        ('kg', 'kg', 1000.0),
        ('g', 'g', 1.0),
    ]
    
    def __init__(self):
        self.conversion_service = UnitConversionService()
    
    def generate_shopping_list(self, recipes: List[Recipe]) -> Dict[str, List[Dict]]:
        """
        Generate a consolidated shopping list from multiple recipes.
        
        Args:
            recipes: List of recipes to include
            
        Returns:
            Dictionary with ingredient categories and consolidated items:
            {
                'Produce': [
                    {'name': 'onion', 'quantity': '2', 'unit': 'whole', 'recipes': ['Recipe A', 'Recipe B']},
                    ...
                ],
                'Dairy': [...],
                ...
            }
        """
        
        def normalize_ingredient_name(name: str) -> str:
            """Normalize ingredient names for better consolidation."""
            name_lower = name.lower().strip()
            
            # Don't normalize if name is too short or would become empty
            if len(name_lower.split()) <= 1:
                return name_lower
                
            # Remove common adjectives/descriptors that don't affect consolidation
            remove_words = ['fresh', 'dried', 'ground', 'whole', 'chopped', 'minced', 
                           'sliced', 'diced', 'crushed', 'finely', 'coarsely', 'raw']
            words = name_lower.split()
            filtered = [w for w in words if w not in remove_words]
            
            # Always return something - prefer filtered, fallback to original
            return ' '.join(filtered) if filtered else name_lower
        
        def categorize_ingredient(name: str) -> str:
            """Categorize ingredient based on its name."""
            name_lower = name.lower()
            
            # Seasonings/Spices (check first - most specific)
            seasoning_keywords = ['black pepper', 'cayenne pepper', 'red pepper flakes', 
                                'pepper flakes', 'ground black pepper', 'ground pepper',
                                'chili powder', 'hot pepper sauce', 'pepper sauce',
                                'salt', 'kosher salt', 'sea salt', 'seasoning', 
                                'oregano', 'cumin', 'cinnamon', 'paprika',
                                'hot sauce', 'tabasco', 'vanilla extract', 'extract', 
                                'liquid smoke', 'adobo', 'dried basil', 'dried oregano',
                                'dried minced', 'spice']
            
            # Baking (check before pantry due to shared keywords like 'sugar')
            baking_keywords = ['flour', 'all-purpose flour', 'baking powder', 'baking soda', 
                             'yeast', 'chocolate chip', 'cocoa', 'confectioners', 
                             'shortening', 'vegetable shortening',
                             'brown sugar', 'white sugar', 'sugar', 'honey']
            
            # Produce
            produce_keywords = ['bell pepper', 'onion', 'tomato', 'garlic', 'cabbage', 
                               'mushroom', 'cilantro', 'parsley', 'fresh basil', 
                               'lettuce', 'carrot', 'celery', 'potato', 'lemon', 
                               'lime', 'shallot', 'scallion', 'ginger', 'herb']
            
            # Meat/Protein
            meat_keywords = ['beef', 'pork', 'chicken', 'turkey', 'sausage', 'bacon', 
                           'meat', 'steak', 'tenderloin', 'ribs', 'pate', 'liver',
                           'shrimp', 'fish', 'tilapia', 'salmon', 'tuna', 'seafood',
                           'skinless']
            
            # Dairy
            dairy_keywords = ['milk', 'cream', 'cheese', 'butter', 'yogurt', 'sour cream',
                            'buttermilk', 'mozzarella', 'parmesan', 'cheddar', 'dairy']
            
            # Pantry (check last - most generic)
            pantry_keywords = ['oil', 'olive oil', 'vinegar', 'broth', 'stock', 'wine', 
                             'pasta', 'rice', 'bread', 'tortilla', 'dough', 'ketchup', 
                             'soy sauce', 'pizza sauce', 'sauce', 'cornstarch', 'bourbon', 
                             'liqueur', 'juice', 'egg', 'walnut', 'nut', 'water',
                             'puff pastry', 'pastry']
            
            # Check each category in order of specificity
            for keyword in seasoning_keywords:
                if keyword in name_lower:
                    return 'Seasonings'
            
            for keyword in baking_keywords:
                if keyword in name_lower:
                    return 'Baking'
            
            for keyword in produce_keywords:
                if keyword in name_lower:
                    return 'Produce'
            
            for keyword in meat_keywords:
                if keyword in name_lower:
                    return 'Meat'
            
            for keyword in dairy_keywords:
                if keyword in name_lower:
                    return 'Dairy'
            
            for keyword in pantry_keywords:
                if keyword in name_lower:
                    return 'Pantry'
            
            return 'Uncategorized'
        
        # Aggregate ingredients by name
        ingredient_totals = defaultdict(lambda: {
            'quantities': [],  # List of (amount, unit, recipe_title) tuples
            'category': None,
            'original_name': None,  # Store original name for display
        })
        
        for recipe in recipes:
            for ri in recipe.ingredients:
                ingredient = ri.ingredient
                
                # Parse quantity
                try:
                    quantity = float(ri.display_quantity)
                except (ValueError, TypeError):
                    # Handle ranges or non-numeric (keep as-is)
                    quantity = ri.display_quantity
                
                # Use ingredient name directly (disable normalization for now)
                ingredient_name = ingredient.name
                
                ingredient_totals[ingredient_name]['quantities'].append({
                    'amount': quantity,
                    'unit': ri.display_unit,
                    'recipe': recipe.title,
                    'preparation': ri.preparation,
                })
                
                # Store category if available
                if ingredient.category and not ingredient_totals[ingredient_name]['category']:
                    ingredient_totals[ingredient_name]['category'] = ingredient.category
        
        # Consolidate quantities for each ingredient
        consolidated_list = []
        
        for ingredient_name, data in ingredient_totals.items():
            quantities = data['quantities']
            # Use categorization function if ingredient doesn't have a category
            category = data['category'] or categorize_ingredient(ingredient_name)
            
            # Get list of recipes using this ingredient
            recipe_names = list(set(q['recipe'] for q in quantities))
            
            # Get preparations (if they vary), but filter out ones that look like full ingredient descriptions
            preparations = []
            for q in quantities:
                prep = q['preparation']
                if prep:
                    prep_lower = prep.lower()
                    # Skip if prep contains the ingredient name or contains numbers/units (looks like a full ingredient line)
                    if (ingredient_name.lower() not in prep_lower and 
                        not any(unit in prep_lower for unit in ['cup', 'tablespoon', 'teaspoon', 'tbsp', 'tsp', 'oz', 'lb', 'g', 'kg', 'ml', 'l']) and
                        not any(char.isdigit() for char in prep)):
                        preparations.append(prep)
            preparations = list(set(preparations))
            
            # Try to consolidate quantities
            consolidated = self._consolidate_quantities(quantities, ingredient_name)
            
            consolidated_list.append({
                'name': ingredient_name,
                'quantity': consolidated['amount'],
                'unit': consolidated['unit'],
                'category': category,
                'recipes': recipe_names,
                'preparations': preparations,
            })
        
        # Group by category
        categorized = defaultdict(list)
        for item in consolidated_list:
            categorized[item['category']].append(item)
        
        # Sort items within each category
        for category in categorized:
            categorized[category].sort(key=lambda x: x['name'])
        
        return dict(categorized)
    
    def _consolidate_quantities(self, quantities: List[Dict], ingredient_name: str = '') -> Dict:
        """
        Consolidate multiple quantities of the same ingredient.
        Converts to common units and sums, then expresses in largest appropriate unit.
        
        Args:
            quantities: List of quantity dicts with 'amount', 'unit', etc.
            ingredient_name: Name of the ingredient (for determining dry vs liquid)
            
        Returns:
            Dict with 'amount' and 'unit' for the consolidated quantity
        """
        # If only one quantity, return as-is
        if len(quantities) == 1:
            q = quantities[0]
            return {'amount': q['amount'], 'unit': q['unit']}
        
        # Separate numeric from non-numeric quantities
        numeric_quantities = []
        non_numeric = []
        
        for q in quantities:
            # Skip if amount is empty or invalid
            if q['amount'] in [None, '', ' '] or (isinstance(q['amount'], str) and q['amount'].strip() == ''):
                continue
            if isinstance(q['amount'], (int, float)):
                numeric_quantities.append(q)
            else:
                # Try to convert string to number
                try:
                    amount_str = str(q['amount']).strip()
                    if amount_str:  # Only if non-empty
                        amount_val = float(amount_str)
                        if amount_val > 0:  # Only include positive values
                            q['amount'] = amount_val
                            numeric_quantities.append(q)
                        else:
                            non_numeric.append(q)
                    else:
                        continue  # Skip empty strings
                except (ValueError, TypeError):
                    non_numeric.append(q)
        
        # If no numeric quantities, just list them
        if not numeric_quantities:
            amounts = []
            for q in quantities:
                unit = q['unit'].strip() if q['unit'] else ''
                if unit:
                    amounts.append(f"{q['amount']} {unit}")
                else:
                    amounts.append(str(q['amount']))
            return {'amount': ', '.join(amounts), 'unit': ''}
        
        # Check if all quantities use the same unit
        first_unit = numeric_quantities[0]['unit'].lower().strip()
        all_same_unit = all(q['unit'].lower().strip() == first_unit for q in numeric_quantities)
        
        if all_same_unit:
            # Same unit - just sum them directly
            total = sum(q['amount'] for q in numeric_quantities)
            return {'amount': total, 'unit': numeric_quantities[0]['unit']}
        
        # Different units - check if they're all the same type (e.g., all volume)
        unit_types = [self._get_unit_type(q['unit'].lower().strip()) for q in numeric_quantities]
        
        # If any unknown types or mixed types, can't consolidate
        if None in unit_types or len(set(unit_types)) > 1:
            # Format amounts as fractions before listing
            from src.ui.unit_conversion_dialog import format_quantity_as_fraction
            formatted_amounts = []
            for q in numeric_quantities:
                unit = q['unit'].strip() if q['unit'] else ''
                try:
                    formatted_qty = format_quantity_as_fraction(float(q['amount']))
                    if unit:
                        formatted_amounts.append(f"{formatted_qty} {unit}")
                    else:
                        formatted_amounts.append(formatted_qty)
                except:
                    if unit:
                        formatted_amounts.append(f"{q['amount']} {unit}")
                    else:
                        formatted_amounts.append(str(q['amount']))
            return {'amount': ', '.join(formatted_amounts), 'unit': ''}
        
        # All same type - convert to base unit and sum
        unit_type = unit_types[0]
        base_unit = 'ml' if unit_type == 'volume' else 'g' if unit_type == 'mass' else 'count'
        
        total_base = 0
        for q in numeric_quantities:
            try:
                # Convert to base unit
                converted = self.conversion_service.convert(
                    q['amount'],
                    q['unit'],
                    base_unit,
                    ingredient_name=None
                )
                total_base += converted
            except Exception as e:
                # If conversion fails, format and list them
                from src.ui.unit_conversion_dialog import format_quantity_as_fraction
                formatted_amounts = []
                for q in numeric_quantities:
                    try:
                        formatted_qty = format_quantity_as_fraction(float(q['amount']))
                        formatted_amounts.append(f"{formatted_qty} {q['unit']}")
                    except:
                        formatted_amounts.append(f"{q['amount']} {q['unit']}")
                return {'amount': ', '.join(formatted_amounts), 'unit': ''}
        
        # Format back to appropriate display units
        return self._format_consolidated_unit(total_base, unit_type, ingredient_name)
        
        # Add non-numeric quantities as note
        if non_numeric:
            amounts = [f"{q['amount']} {q['unit']}" for q in non_numeric]
            consolidated['amount'] = f"{consolidated['amount']} (+ {', '.join(amounts)})"
        
        return consolidated
    
    def _get_unit_type(self, unit: str) -> str:
        """Determine if unit is volume, mass, or count."""
        unit_lower = unit.lower().strip()
        
        # Check both singular and plural forms
        volume_units = ['ml', 'milliliter', 'milliliters', 'l', 'liter', 'liters',
                       'tsp', 'teaspoon', 'teaspoons', 'tbsp', 'tablespoon', 'tablespoons',
                       'cup', 'cups', 'fl oz', 'fluid ounce', 'fluid ounces',
                       'pint', 'pints', 'quart', 'quarts', 'gallon', 'gallons']
        mass_units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms',
                     'oz', 'ounce', 'ounces', 'lb', 'lbs', 'pound', 'pounds']
        count_units = ['count', 'piece', 'pieces', 'whole', 'item', 'items']
        
        if unit_lower in volume_units:
            return 'volume'
        elif unit_lower in mass_units:
            return 'mass'
        elif unit_lower in count_units:
            return 'count'
        
        return None
    
    def _format_consolidated_unit(self, amount: float, unit_type: str, ingredient_name: str = '') -> Dict:
        """
        Format amount in most appropriate unit(s).
        E.g., 30 oz -> 1 lb and 14 oz, 1500 ml -> 1 liter and 500 ml
        
        Args:
            amount: Amount in base units (ml for volume, g for mass, count for count)
            unit_type: 'volume', 'mass', or 'count'
            ingredient_name: Name of ingredient (for determining if dry)
            
        Returns:
            Dict with 'amount' and 'unit'
        """
        from src.ui.unit_conversion_dialog import format_quantity_as_fraction
        
        if unit_type == 'count':
            return {
                'amount': format_quantity_as_fraction(amount),
                'unit': 'whole'
            }
        
        # Get appropriate hierarchy
        if unit_type == 'volume':
            # Use cooking hierarchy for dry ingredients (flour, sugar, etc.)
            dry_ingredients = ['flour', 'sugar', 'salt', 'powder', 'starch', 'meal', 'rice', 'oat']
            is_dry = any(dry in ingredient_name.lower() for dry in dry_ingredients)
            hierarchy = self.COOKING_VOLUME_HIERARCHY if is_dry else self.VOLUME_HIERARCHY
        else:
            hierarchy = self.MASS_HIERARCHY
        
        # Find the largest unit that gives us >= 1 and use max 2 unit levels
        result_parts = []
        remaining = amount
        units_used = 0
        max_units = 2  # Only show 2 unit levels (e.g., "1 lb 14 oz", not "1 lb 14 oz 5 g")
        
        for unit_name, unit_symbol, unit_in_base in hierarchy:
            if remaining >= unit_in_base and units_used < max_units:
                # How many of this unit?
                count = int(remaining / unit_in_base)
                remaining = remaining % unit_in_base
                
                if count > 0:
                    result_parts.append({
                        'amount': format_quantity_as_fraction(count),
                        'unit': unit_symbol
                    })
                    units_used += 1
        
        # Handle remainder if it's significant and we haven't used max units yet
        # Only show remainder if it's >= 10% of the amount
        if remaining > (amount * 0.1) and units_used < max_units:
            # Find the most appropriate small unit for remainder
            for unit_name, unit_symbol, unit_in_base in reversed(hierarchy):
                remainder_in_unit = remaining / unit_in_base
                if 0.1 <= remainder_in_unit < 100:  # Reasonable range
                    result_parts.append({
                        'amount': format_quantity_as_fraction(remainder_in_unit),
                        'unit': unit_symbol
                    })
                    break
        
        # If we have results, format them
        if result_parts:
            if len(result_parts) == 1:
                # Pluralize unit if needed
                unit = result_parts[0]['unit']
                amount_str = result_parts[0]['amount']
                # Check if amount is > 1 (including fractions like "2 1/2")
                try:
                    # Parse amount to check if > 1
                    if ' ' in amount_str:  # Mixed fraction like "2 1/2"
                        should_pluralize = True
                    else:
                        val = float(amount_str.split('/')[0]) if '/' in amount_str else float(amount_str)
                        should_pluralize = val > 1
                except:
                    should_pluralize = False
                
                if should_pluralize and not unit.endswith('s'):
                    unit = unit + 's'
                    
                return {'amount': amount_str, 'unit': unit}
            else:
                # Multiple parts: "1 pound and 14 ounces"
                formatted_parts = []
                for i, p in enumerate(result_parts):
                    amount_str = p['amount']
                    unit = p['unit']
                    
                    # Pluralize if amount > 1
                    try:
                        if ' ' in amount_str:
                            should_pluralize = True
                        else:
                            val = float(amount_str.split('/')[0]) if '/' in amount_str else float(amount_str)
                            should_pluralize = val > 1
                    except:
                        should_pluralize = False
                    
                    if should_pluralize and not unit.endswith('s'):
                        unit = unit + 's'
                    
                    formatted_parts.append(f"{amount_str} {unit}")
                
                parts_str = ' and '.join(formatted_parts)
                return {'amount': parts_str, 'unit': ''}
        
        # Fallback to base unit
        base_unit = hierarchy[-1][1]
        return {
            'amount': format_quantity_as_fraction(amount),
            'unit': base_unit
        }
    
    def format_shopping_list_text(self, categorized_list: Dict[str, List[Dict]]) -> str:
        """
        Format shopping list as readable text with categories.
        
        Args:
            categorized_list: Output from generate_shopping_list()
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Add title
        lines.append("SHOPPING LIST")
        lines.append("=" * 40)
        lines.append("")
        
        # Sort categories for consistent ordering
        category_order = ['Produce', 'Meat', 'Dairy', 'Seasonings', 'Baking', 'Pantry', 'Uncategorized']
        
        def category_sort_key(cat):
            try:
                return category_order.index(cat)
            except ValueError:
                return len(category_order)  # Put unknown categories at the end
        
        sorted_categories = sorted(categorized_list.keys(), key=category_sort_key)
        
        # Format items by category
        for category in sorted_categories:
            items = categorized_list[category]
            if not items:
                continue
                
            # Add category header
            lines.append(f"\n{category.upper()}")
            lines.append("-" * 40)
            
            # Sort items alphabetically within category
            items.sort(key=lambda x: x['name'].lower())
            
            # Format items
            for item in items:
                # Format quantity as fraction if possible
                from src.ui.unit_conversion_dialog import format_quantity_as_fraction
                
                quantity = item['quantity']
                formatted_quantity = str(quantity)
                is_less_than_one = False
                
                # Try to format as fraction if it's numeric
                try:
                    # Check if it's a plain number (int, float, or numeric string without spaces)
                    if isinstance(quantity, (int, float)):
                        numeric_value = float(quantity)
                        formatted_quantity = format_quantity_as_fraction(numeric_value)
                        is_less_than_one = numeric_value < 1
                    elif isinstance(quantity, str):
                        # Try to convert string to float
                        if quantity.replace('.', '', 1).replace('-', '', 1).isdigit():
                            numeric_value = float(quantity)
                            formatted_quantity = format_quantity_as_fraction(numeric_value)
                            is_less_than_one = numeric_value < 1
                        elif ' ' not in quantity:
                            # Might be a single numeric value
                            numeric_value = float(quantity)
                            formatted_quantity = format_quantity_as_fraction(numeric_value)
                            is_less_than_one = numeric_value < 1
                except (ValueError, TypeError):
                    # Keep as-is if not numeric (like "1 lb 14 oz")
                    pass
                
                # Handle unit pluralization
                unit_str = ""
                if item['unit']:
                    unit = item['unit']
                    # Pluralize units if quantity > 1 (unless already plural or special cases)
                    should_pluralize = False
                    try:
                        # Check if quantity is greater than 1
                        if isinstance(quantity, (int, float)):
                            should_pluralize = quantity > 1
                        elif ' ' in formatted_quantity:  # Mixed number like "2 1/2"
                            should_pluralize = True
                        elif formatted_quantity not in ['1', '1/2', '1/3', '1/4', '2/3', '3/4']:
                            # Try to evaluate fraction or number
                            if '/' in formatted_quantity:
                                parts = formatted_quantity.split('/')
                                should_pluralize = int(parts[0]) > int(parts[1])
                            else:
                                should_pluralize = float(formatted_quantity) > 1
                    except:
                        pass
                    
                    if should_pluralize and not unit.endswith('s') and unit not in ['oz', 'tbsp', 'tsp']:
                        unit = unit + 's'
                    elif not should_pluralize and unit.endswith('s') and unit not in ['oz', 'tbsp', 'tsp']:
                        # Singularize if needed
                        unit = unit[:-1]
                        
                    unit_str = f" {unit}"
                
                prep_str = f" ({', '.join(item['preparations'])})" if item['preparations'] else ""
                
                # Format the line (use □ for checkbox)
                line = f"□ {formatted_quantity}{unit_str} {item['name']}{prep_str}"
                
                # Apply fractions to numbers in parentheses (e.g., "(0.5 pound)" -> "(1/2 pound)")
                import re
                def replace_decimal_in_parens(match):
                    decimal_str = match.group(1)
                    rest = match.group(2)
                    try:
                        decimal_val = float(decimal_str)
                        formatted = format_quantity_as_fraction(decimal_val)
                        return f"({formatted}{rest}"
                    except:
                        return match.group(0)
                
                line = re.sub(r'\((\d+\.\d+)([^)]*\))', replace_decimal_in_parens, line)
                
                lines.append(line)
        
        return '\n'.join(lines)
