"""
Recipe import service supporting URL scraping and LLM-based parsing.
"""

from typing import Optional, Dict, List
from recipe_scrapers import scrape_me
from bs4 import BeautifulSoup
import requests
from src.services.llm_client import LLMRouter


class RecipeImporter:
    """Service for importing recipes from URLs."""
    
    def __init__(self, llm_router: Optional[LLMRouter] = None):
        """Initialize the recipe importer.
        
        Args:
            llm_router: Optional LLM router for fallback parsing
        """
        self.llm_router = llm_router
    
    def import_from_url(self, url: str) -> Optional[Dict]:
        """Import a recipe from a URL.
        
        First tries recipe-scrapers (supports 100+ sites).
        Falls back to LLM parsing if scraper fails.
        
        Args:
            url: Recipe URL to import
            
        Returns:
            Dictionary with recipe data or None if import fails
        """
        # Try recipe-scrapers first
        try:
            recipe = self._scrape_with_library(url)
            if recipe:
                return recipe
        except Exception:
            pass  # Silently continue to LLM fallback
        
        # Fallback to LLM parsing if available
        if self.llm_router:
            try:
                return self._parse_with_llm(url)
            except Exception:
                pass  # Silently fail
        
        return None
    
    def _scrape_with_library(self, url: str) -> Optional[Dict]:
        """Scrape recipe using recipe-scrapers library.
        
        Args:
            url: Recipe URL
            
        Returns:
            Structured recipe data
        """
        scraper = scrape_me(url)
        
        # Extract ingredients with quantities
        raw_ingredients = [line.strip() for line in scraper.ingredients() if line and line.strip()]
        
        # Two-pass parsing: normalize first, then extract
        if self.llm_router and raw_ingredients:
            ingredients = self.parse_ingredients_batch(raw_ingredients)
        else:
            # Fallback to regex-only parsing
            ingredients = []
            for ingredient_line in raw_ingredients:
                try:
                    parsed = self.parse_ingredient_line(ingredient_line)
                    if parsed and parsed.get('name'):
                        ingredients.append(parsed)
                except Exception as e:
                    ingredients.append({
                        "quantity": "1",
                        "unit": "",
                        "name": ingredient_line,
                        "preparation": ""
                    })
        
        # Calculate total time
        total_time = None
        if scraper.total_time():
            total_time = scraper.total_time()
        elif scraper.cook_time() and scraper.prep_time():
            total_time = scraper.cook_time() + scraper.prep_time()
        
        # Get instructions - convert list to string if needed
        instructions = scraper.instructions()
        if isinstance(instructions, list):
            instructions = "\n".join(str(step) for step in instructions)
        
        return {
            "title": scraper.title(),
            "description": scraper.description() or "",
            "instructions": instructions,
            "servings": scraper.yields() if isinstance(scraper.yields(), int) else 4,
            "prep_time_minutes": scraper.prep_time() if scraper.prep_time() else None,
            "cook_time_minutes": scraper.cook_time() if scraper.cook_time() else None,
            "total_time_minutes": total_time,
            "source_url": url,
            "ingredients": ingredients,
            "tags": [],  # Could extract from recipe categories
            "image_url": scraper.image() if hasattr(scraper, 'image') else None,
        }
    
    def _parse_with_llm(self, url: str) -> Optional[Dict]:
        """Parse recipe using LLM as fallback.
        
        Args:
            url: Recipe URL
            
        Returns:
            Structured recipe data
        """
        # Fetch HTML
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Extract text content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text size for LLM (keep first 5000 chars)
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        # Ask LLM to parse
        prompt = f"""Extract recipe information from the following webpage text and return it in this exact JSON format:

{{
  "title": "Recipe name",
  "description": "Brief description",
  "instructions": "Step by step instructions",
  "servings": 4,
  "prep_time_minutes": 15,
  "cook_time_minutes": 30,
  "ingredients": [
    {{"quantity": "1", "unit": "cup", "name": "flour", "preparation": "sifted"}},
    {{"quantity": "2", "unit": "tablespoons", "name": "sugar", "preparation": ""}}
  ],
  "tags": ["dinner", "italian"]
}}

Webpage text:
{text}

Return ONLY the JSON, no other text."""

        response = self.llm_router.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse JSON from response
        import json
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                recipe_data = json.loads(response[json_start:json_end])
                recipe_data['source_url'] = url
                
                # Convert instructions list to string if needed
                if isinstance(recipe_data.get('instructions'), list):
                    recipe_data['instructions'] = "\n".join(str(step) for step in recipe_data['instructions'])
                
                return recipe_data
        except json.JSONDecodeError:
            pass  # Silently fail on JSON parse error
        
        return None
    
    def parse_ingredients_batch(self, raw_ingredients: list) -> list:
        """Parse multiple ingredients using two-pass approach: normalize then extract.
        
        Pass 1: LLM normalizes all ingredients into consistent format
        Pass 2: Simple extraction from normalized format
        
        Args:
            raw_ingredients: List of raw ingredient strings
            
        Returns:
            List of parsed ingredient dicts
        """
        # Pass 1: Normalize all ingredients at once
        ingredient_list = "\n".join(f"{i+1}. {ing}" for i, ing in enumerate(raw_ingredients))
        
        try:
            normalized_response = self.llm_router.chat(
                messages=[{"role": "user", "content": f'''Rewrite these ingredients in a consistent format: [quantity] [unit] [ingredient name], [preparation]

Rules:
- Keep quantities as decimals (0.5 not 1/2)
- Use full unit names (cup not c.)
- Separate preparation with comma
- If no quantity, use "1"
- If no unit, omit it

Examples:
"3 tablespoons all-purpose flour" → "3 tablespoons all-purpose flour"
"butter (1/2 cup, melted)" → "0.5 cup butter, melted"
"2 c. sugar" → "2 cups sugar"
"salt to taste" → "1 salt, to taste"

Ingredients:
{ingredient_list}

Return ONLY the normalized list, one per line, numbered:'''}],
                temperature=0.3,
                max_tokens=1000
            )
            
            if not normalized_response:
                return [self.parse_ingredient_line(ing) for ing in raw_ingredients]
            
            # Parse normalized lines
            normalized_lines = [line.strip() for line in normalized_response.split('\n') if line.strip()]
            # Remove numbering if present
            import re
            normalized_lines = [re.sub(r'^\d+\.\s*', '', line) for line in normalized_lines]
            
        except Exception as e:
            return [self.parse_ingredient_line(ing) for ing in raw_ingredients]
        
        # Pass 2: Extract structured data from normalized format
        ingredients = []
        
        for i, line in enumerate(normalized_lines):
            try:
                # Simple regex on normalized format
                match = re.match(r'^\s*([\d\.]+)\s+(\w+)\s+([^,]+)(?:,\s*(.+))?$', line)
                if match:
                    quantity = match.group(1)
                    unit = match.group(2)
                    name = match.group(3).strip()
                    preparation = match.group(4).strip() if match.group(4) else ""
                    
                    # Round quantity to 2 decimal places to avoid floating point mess
                    try:
                        quantity = str(round(float(quantity), 2))
                    except ValueError:
                        pass  # Keep as-is if not a valid number
                    
                    # Fix: If unit is an adjective (kosher, ground, fresh, etc), move to name
                    adjectives = ['kosher', 'ground', 'fresh', 'dried', 'frozen', 'canned', 'whole', 
                                  'chopped', 'minced', 'sliced', 'diced', 'large', 'small', 'medium',
                                  'coarse', 'fine', 'raw', 'cooked', 'unsalted', 'salted', 'sweet']
                    if unit.lower() in adjectives:
                        name = f"{unit} {name}"
                        unit = ""
                    
                    ingredients.append({
                        "quantity": quantity,
                        "unit": unit,
                        "name": name,
                        "preparation": preparation
                    })
                else:
                    # Try without unit
                    match = re.match(r'^\s*([\d\.]+)\s+([^,]+)(?:,\s*(.+))?$', line)
                    if match:
                        quantity = match.group(1)
                        # Round quantity to 2 decimal places
                        try:
                            quantity = str(round(float(quantity), 2))
                        except ValueError:
                            pass
                        
                        ingredients.append({
                            "quantity": quantity,
                            "unit": "",
                            "name": match.group(2).strip(),
                            "preparation": match.group(3).strip() if match.group(3) else ""
                        })
                    else:
                        # Fallback - use original
                        ingredients.append(self.parse_ingredient_line(raw_ingredients[i] if i < len(raw_ingredients) else line))
                        
            except Exception as e:
                ingredients.append({
                    "quantity": "1",
                    "unit": "",
                    "name": line,
                    "preparation": ""
                })
        
        return ingredients
    
    def parse_ingredient_line(self, line: str) -> Dict:
        """Parse an ingredient line into components.
        
        Uses regex first, LLM as fallback for complex cases.
        
        Args:
            line: Ingredient line like "2 cups flour, sifted"
            
        Returns:
            Dict with quantity, unit, name, preparation
        """
        import re
        
        # Try simple regex parsing first
        # Pattern: optional quantity, optional unit, ingredient name, optional preparation
        # Examples: "2 cups flour", "1/2 teaspoon salt", "3-4 large eggs, beaten"
        
        # Common units
        units = r'(?:cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|pounds?|lbs?|grams?|g|kg|ml|l|liters?|pint|quart|gallon|cloves?|whole|pieces?|slices?|drops?|pinch|dash)'
        
        # Quantity patterns: "2", "1/2", "2-3", "1 1/2", etc.
        qty_pattern = r'([\d\/-]+(?:\s+[\d\/]+)?|\d+(?:\.\d+)?)'
        
        # Try to match: quantity + unit + rest
        pattern = rf'^\s*({qty_pattern})?\s*({units})?\s*(.+?)(?:,\s*(.+))?$'
        match = re.match(pattern, line, re.IGNORECASE)
        
        if match:
            quantity = match.group(1) or "1"
            unit = match.group(2) or ""
            name = match.group(3).strip() if match.group(3) else line
            preparation = match.group(4).strip() if match.group(4) else ""
            
            # Only use regex result if we actually got a valid name
            if name and name != line:
                return {
                    "quantity": quantity.strip(),
                    "unit": unit.strip(),
                    "name": name,
                    "preparation": preparation
                }
        
        # If regex fails and LLM available, try multi-step parsing
        if self.llm_router:
            try:
                # Step 1: Extract quantity with clear examples
                quantity = "1"
                try:
                    step1 = self.llm_router.chat(
                        messages=[{"role": "user", "content": f'''Extract the NUMBER from this ingredient. Return ONLY the number, nothing else.

"2 cups flour" → 2
"1/2 teaspoon salt" → 1/2
"3-4 cloves garlic" → 3-4
"salt to taste" → 1

"{line}" →'''}],
                        temperature=0.0,
                        max_tokens=10
                    )
                except Exception:
                    step1 = None
                if step1:
                    # Extract only digits, slashes, hyphens, and periods
                    import re
                    match = re.search(r'[\d\.\/\-]+', step1)
                    if match:
                        extracted = match.group(0)
                        # Validate it's actually a number-like thing
                        if not any(word in extracted.lower() for word in ['cup', 'tablespoon', 'teaspoon', 'ounce', 'pound', 'gram', 'clove']):
                            quantity = extracted
                
                # Step 2: Extract unit with clear examples
                unit = ""
                try:
                    step2 = self.llm_router.chat(
                        messages=[{"role": "user", "content": f'''Extract the UNIT OF MEASUREMENT from this ingredient. Return ONLY the measurement unit word.

"2 cups flour" → cups
"1/2 teaspoon salt" → teaspoon
"3 cloves garlic" → cloves
"1 pound beef" → pound
"salt to taste" → none

"{line}" →'''}],
                        temperature=0.0,
                        max_tokens=10
                    )
                except Exception:
                    step2 = None
                if step2 and step2.lower().strip() != "none":
                    # Validate it's a unit word, not a number
                    import re
                    # If response contains mostly digits, it's wrong
                    if not re.search(r'^\d+[\d\.\/-]*$', step2.strip()):
                        words = step2.lower().split()
                        common_units = ['cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
                                      'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs', 'gram', 'grams', 'g',
                                      'kg', 'ml', 'liter', 'liters', 'l', 'clove', 'cloves', 'whole', 'piece', 'pieces',
                                      'quart', 'quarts', 'pint', 'pints', 'gallon', 'gallons', 'stalk', 'stalks']
                        for word in words:
                            if word in common_units:
                                unit = word
                                break
                
                # Step 3: What's left is the ingredient name
                # Remove quantity and unit from the line
                import re
                remaining = line
                
                # Remove ALL leading numbers first
                # Also remove parenthetical fractions like (1/2 pound)
                remaining = re.sub(r'^\s*[\d\.\/\-]+\s*', '', remaining).strip()
                remaining = re.sub(r'^\s*\([^\)]*\)\s*', '', remaining).strip()
                
                # Remove unit at start (with optional 's' for plurals)
                if unit:
                    unit_re = re.escape(unit) + r's?'  # Match singular or plural
                    remaining = re.sub(rf'^\s*{unit_re}\s+', '', remaining, flags=re.IGNORECASE).strip()
                
                # Remove packaging/container words
                packaging_words = ['can', 'jar', 'package', 'box', 'bottle', 'container']
                for word in packaging_words:
                    remaining = re.sub(rf'^\s*{word}s?\s+', '', remaining, flags=re.IGNORECASE).strip()
                
                if not remaining:  # Safety check
                    remaining = line
                
                # Step 4: Check if there's preparation
                preparation = ""
                name = remaining
                
                # Look for common preparation separators
                if remaining:
                    # Check for dash separator (most reliable)
                    if ' - ' in remaining or ' – ' in remaining:
                        parts = remaining.split(' - ' if ' - ' in remaining else ' – ', 1)
                        name = parts[0].strip()
                        preparation = parts[1].strip() if len(parts) > 1 else ""
                    # Check for comma followed by preparation verbs/words
                    elif ',' in remaining:
                        # Preparation indicators after comma
                        prep_indicators = ['cut ', 'sliced', 'diced', 'chopped', 'minced', 'peeled', 
                                          'seeded', 'cored', 'halved', 'quartered', 'crushed',
                                          'beaten', 'thawed', 'softened', 'melted', 'divided',
                                          'drained', 'rinsed', 'trimmed', 'removed', 'as needed',
                                          'or more', 'or less', 'to taste', 'optional', 'for ']
                        
                        # Split on comma and check each part
                        parts = remaining.split(',')
                        name_parts = []
                        prep_parts = []
                        found_prep = False
                        
                        for part in parts:
                            part_lower = part.strip().lower()
                            # Check if this part looks like a preparation instruction
                            is_prep = found_prep or any(indicator in part_lower for indicator in prep_indicators)
                            
                            if is_prep:
                                found_prep = True
                                prep_parts.append(part.strip())
                            else:
                                name_parts.append(part.strip())
                        
                        name = ', '.join(name_parts) if name_parts else remaining
                        preparation = ', '.join(prep_parts) if prep_parts else ""
                else:
                    name = remaining.strip() if remaining else line
                
                if name:  # Only return if we got something useful
                    result = {
                        "quantity": quantity,
                        "unit": unit,
                        "name": name,
                        "preparation": preparation
                    }
                    return result
                    
            except Exception:
                pass  # Fall through to ultimate fallback
        
        # Ultimate fallback - put everything in name
        return {
            "quantity": "1",
            "unit": "",
            "name": line,
            "preparation": ""
        }
