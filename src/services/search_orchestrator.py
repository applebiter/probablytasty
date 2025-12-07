"""
Search orchestrator combining traditional and LLM-powered search.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Recipe, Tag, Ingredient
from src.services.llm_client import LLMRouter


class SearchOrchestrator:
    """Orchestrates recipe search with LLM assistance."""
    
    def __init__(self, session: Session, llm_router: LLMRouter):
        self.session = session
        self.llm_router = llm_router
    
    def search(
        self,
        query: str,
        max_results: int = 50,
        use_llm: bool = True,
    ) -> List[Recipe]:
        """
        Search recipes using natural language.
        
        Args:
            query: Natural language search query
            max_results: Maximum number of results to return
            use_llm: Whether to use LLM for query interpretation
            
        Returns:
            List of matching recipes
        """
        if use_llm and self.llm_router.is_available():
            # Use LLM to interpret the query
            filters = self._interpret_query_with_llm(query)
            if filters:
                return self._search_with_filters(filters, max_results)
        
        # Fall back to simple text search
        return self._simple_search(query, max_results)
    
    def _interpret_query_with_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """Use LLM to interpret natural language query into structured filters."""
        system_prompt = """You are a recipe search assistant. Convert natural language queries into structured filters.

Output ONLY valid JSON with these fields (all optional):
{
  "required_ingredients": ["ingredient1", "ingredient2"],
  "excluded_ingredients": ["ingredient3"],
  "tags_include": ["tag1", "tag2"],
  "tags_exclude": ["tag3"],
  "max_total_time_minutes": 30,
  "text_search": "keywords to search in title/description"
}

Examples:
Query: "quick vegetarian pasta under 30 minutes"
Output: {"tags_include": ["vegetarian"], "max_total_time_minutes": 30, "text_search": "pasta"}

Query: "chicken recipes without dairy"
Output: {"required_ingredients": ["chicken"], "excluded_ingredients": ["milk", "cheese", "cream", "butter"]}

Query: "dessert with chocolate"
Output: {"tags_include": ["dessert"], "required_ingredients": ["chocolate"]}"""

        messages = [
            {"role": "user", "content": f"Query: {query}\nOutput:"}
        ]
        
        try:
            response = self.llm_router.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=500,
            )
            
            if not response:
                return None
            
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code block markers
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()
            
            filters = json.loads(response)
            return filters
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response was: {response}")
            return None
        except Exception as e:
            print(f"Error interpreting query with LLM: {e}")
            return None
    
    def _search_with_filters(
        self,
        filters: Dict[str, Any],
        max_results: int,
    ) -> List[Recipe]:
        """Search recipes using structured filters."""
        query = self.session.query(Recipe)
        
        # Text search in title/description
        if "text_search" in filters and filters["text_search"]:
            search = f"%{filters['text_search']}%"
            query = query.filter(
                (Recipe.title.ilike(search)) | 
                (Recipe.description.ilike(search)) |
                (Recipe.instructions.ilike(search))
            )
        
        # Required ingredients
        if "required_ingredients" in filters:
            for ingredient_name in filters["required_ingredients"]:
                query = query.filter(
                    Recipe.ingredients.any(
                        Ingredient.name.ilike(f"%{ingredient_name}%")
                    )
                )
        
        # Excluded ingredients
        if "excluded_ingredients" in filters:
            for ingredient_name in filters["excluded_ingredients"]:
                query = query.filter(
                    ~Recipe.ingredients.any(
                        Ingredient.name.ilike(f"%{ingredient_name}%")
                    )
                )
        
        # Include tags
        if "tags_include" in filters:
            for tag_name in filters["tags_include"]:
                query = query.filter(
                    Recipe.tags.any(Tag.name.ilike(f"%{tag_name}%"))
                )
        
        # Exclude tags
        if "tags_exclude" in filters:
            for tag_name in filters["tags_exclude"]:
                query = query.filter(
                    ~Recipe.tags.any(Tag.name.ilike(f"%{tag_name}%"))
                )
        
        # Maximum time
        if "max_total_time_minutes" in filters:
            max_time = filters["max_total_time_minutes"]
            query = query.filter(
                (Recipe.total_time_minutes <= max_time) |
                (Recipe.total_time_minutes == None)
            )
        
        return query.order_by(Recipe.title).limit(max_results).all()
    
    def _simple_search(self, query: str, max_results: int) -> List[Recipe]:
        """Simple keyword-based search without LLM."""
        search = f"%{query}%"
        results = self.session.query(Recipe).filter(
            (Recipe.title.ilike(search)) |
            (Recipe.description.ilike(search)) |
            (Recipe.instructions.ilike(search))
        ).order_by(Recipe.title).limit(max_results).all()
        
        return results
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial input."""
        suggestions = []
        
        # Add matching recipe titles
        recipes = self.session.query(Recipe.title).filter(
            Recipe.title.ilike(f"%{partial_query}%")
        ).limit(5).all()
        suggestions.extend([r.title for r in recipes])
        
        # Add matching tags
        tags = self.session.query(Tag.name).filter(
            Tag.name.ilike(f"%{partial_query}%")
        ).limit(5).all()
        suggestions.extend([t.name for t in tags])
        
        # Add matching ingredients
        ingredients = self.session.query(Ingredient.name).filter(
            Ingredient.name.ilike(f"%{partial_query}%")
        ).limit(5).all()
        suggestions.extend([i.name for i in ingredients])
        
        return list(set(suggestions))[:10]  # Remove duplicates and limit
