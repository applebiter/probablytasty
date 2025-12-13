"""
Unit conversion service for ingredient quantities.
"""

from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class UnitDefinition:
    """Definition of a measurement unit."""
    name: str
    symbol: str
    unit_type: str  # "mass", "volume", "count"
    system: str  # "metric", "imperial", "us_customary"
    to_base_factor: float  # Conversion factor to base unit (grams for mass, ml for volume)


# Standard unit definitions
UNITS: Dict[str, UnitDefinition] = {
    # Mass units (base: grams)
    "g": UnitDefinition("gram", "g", "mass", "metric", 1.0),
    "gram": UnitDefinition("gram", "g", "mass", "metric", 1.0),
    "grams": UnitDefinition("gram", "g", "mass", "metric", 1.0),
    "kg": UnitDefinition("kilogram", "kg", "mass", "metric", 1000.0),
    "kilogram": UnitDefinition("kilogram", "kg", "mass", "metric", 1000.0),
    "kilograms": UnitDefinition("kilogram", "kg", "mass", "metric", 1000.0),
    "mg": UnitDefinition("milligram", "mg", "mass", "metric", 0.001),
    "milligram": UnitDefinition("milligram", "mg", "mass", "metric", 0.001),
    "milligrams": UnitDefinition("milligram", "mg", "mass", "metric", 0.001),
    "oz": UnitDefinition("ounce", "oz", "mass", "imperial", 28.3495),
    "ounce": UnitDefinition("ounce", "oz", "mass", "imperial", 28.3495),
    "ounces": UnitDefinition("ounce", "oz", "mass", "imperial", 28.3495),
    "lb": UnitDefinition("pound", "lb", "mass", "imperial", 453.592),
    "lbs": UnitDefinition("pound", "lb", "mass", "imperial", 453.592),
    "pound": UnitDefinition("pound", "lb", "mass", "imperial", 453.592),
    "pounds": UnitDefinition("pound", "lb", "mass", "imperial", 453.592),
    
    # Volume units (base: milliliters)
    "ml": UnitDefinition("milliliter", "ml", "volume", "metric", 1.0),
    "milliliter": UnitDefinition("milliliter", "ml", "volume", "metric", 1.0),
    "milliliters": UnitDefinition("milliliter", "ml", "volume", "metric", 1.0),
    "l": UnitDefinition("liter", "l", "volume", "metric", 1000.0),
    "liter": UnitDefinition("liter", "l", "volume", "metric", 1000.0),
    "liters": UnitDefinition("liter", "l", "volume", "metric", 1000.0),
    "tsp": UnitDefinition("teaspoon", "tsp", "volume", "us_customary", 4.92892),
    "teaspoon": UnitDefinition("teaspoon", "tsp", "volume", "us_customary", 4.92892),
    "teaspoons": UnitDefinition("teaspoon", "tsp", "volume", "us_customary", 4.92892),
    "tbsp": UnitDefinition("tablespoon", "tbsp", "volume", "us_customary", 14.7868),
    "tablespoon": UnitDefinition("tablespoon", "tbsp", "volume", "us_customary", 14.7868),
    "tablespoons": UnitDefinition("tablespoon", "tbsp", "volume", "us_customary", 14.7868),
    "cup": UnitDefinition("cup", "cup", "volume", "us_customary", 236.588),
    "cups": UnitDefinition("cup", "cup", "volume", "us_customary", 236.588),
    "fl oz": UnitDefinition("fluid ounce", "fl oz", "volume", "us_customary", 29.5735),
    "fluid ounce": UnitDefinition("fluid ounce", "fl oz", "volume", "us_customary", 29.5735),
    "fluid ounces": UnitDefinition("fluid ounce", "fl oz", "volume", "us_customary", 29.5735),
    "pt": UnitDefinition("pint", "pt", "volume", "us_customary", 473.176),
    "pint": UnitDefinition("pint", "pt", "volume", "us_customary", 473.176),
    "pints": UnitDefinition("pint", "pt", "volume", "us_customary", 473.176),
    "qt": UnitDefinition("quart", "qt", "volume", "us_customary", 946.353),
    "quart": UnitDefinition("quart", "qt", "volume", "us_customary", 946.353),
    "quarts": UnitDefinition("quart", "qt", "volume", "us_customary", 946.353),
    "gal": UnitDefinition("gallon", "gal", "volume", "us_customary", 3785.41),
    "gallon": UnitDefinition("gallon", "gal", "volume", "us_customary", 3785.41),
    "gallons": UnitDefinition("gallon", "gal", "volume", "us_customary", 3785.41),
    "drop": UnitDefinition("drop", "drop", "volume", "us_customary", 0.05),  # ~0.05 ml per drop
    "drops": UnitDefinition("drop", "drop", "volume", "us_customary", 0.05),
    "dash": UnitDefinition("dash", "dash", "volume", "us_customary", 0.62),  # ~1/8 tsp
    "pinch": UnitDefinition("pinch", "pinch", "volume", "us_customary", 0.31),  # ~1/16 tsp
    
    # Count units
    "count": UnitDefinition("count", "count", "count", "universal", 1.0),
    "piece": UnitDefinition("piece", "piece", "count", "universal", 1.0),
    "pieces": UnitDefinition("piece", "piece", "count", "universal", 1.0),
    "whole": UnitDefinition("whole", "whole", "count", "universal", 1.0),
    "clove": UnitDefinition("clove", "clove", "count", "universal", 1.0),
    "cloves": UnitDefinition("clove", "clove", "count", "universal", 1.0),
}

# Common ingredient densities (grams per ml)
# Used for volume <-> mass conversion when no specific override exists
INGREDIENT_DENSITIES = {
    "water": 1.0,
    "milk": 1.03,
    "cream": 1.01,
    "butter": 0.911,
    "oil": 0.92,
    "honey": 1.42,
    "sugar": 0.845,  # granulated, poured
    "flour": 0.507,  # all-purpose, spooned
    "salt": 1.217,
}

# Specific ingredient-unit conversions (overrides)
# Format: (ingredient_name, unit_symbol): grams_per_unit
INGREDIENT_UNIT_OVERRIDES = {
    ("flour", "cup"): 120.0,  # all-purpose flour, spooned and leveled
    ("sugar", "cup"): 200.0,  # granulated sugar
    ("brown sugar", "cup"): 220.0,  # packed
    ("butter", "cup"): 227.0,
    ("butter", "tbsp"): 14.2,
    ("honey", "cup"): 340.0,
    ("oil", "cup"): 218.0,
    ("milk", "cup"): 244.0,
    ("water", "cup"): 237.0,
    ("salt", "tsp"): 6.0,
    ("baking powder", "tsp"): 4.8,
    ("baking soda", "tsp"): 6.0,
}


class UnitConversionService:
    """Service for converting between different measurement units."""
    
    def __init__(self):
        self.units = UNITS
        self.ingredient_densities = INGREDIENT_DENSITIES
        self.ingredient_overrides = INGREDIENT_UNIT_OVERRIDES
    
    def convert(
        self, 
        quantity: float, 
        from_unit: str, 
        to_unit: str, 
        ingredient_name: Optional[str] = None
    ) -> float:
        """
        Convert quantity from one unit to another.
        
        Args:
            quantity: Amount to convert
            from_unit: Source unit symbol (e.g., "cup", "g")
            to_unit: Target unit symbol
            ingredient_name: Name of ingredient (for specific conversions)
            
        Returns:
            Converted quantity
            
        Raises:
            ValueError: If conversion is not possible
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        if from_unit not in self.units or to_unit not in self.units:
            raise ValueError(f"Unknown unit: {from_unit} or {to_unit}")
        
        from_def = self.units[from_unit]
        to_def = self.units[to_unit]
        
        # Same unit - no conversion needed
        if from_unit == to_unit:
            return quantity
        
        # Count units can only convert to count units
        if from_def.unit_type == "count" and to_def.unit_type == "count":
            return quantity
        
        # Same type - simple conversion using base factors
        if from_def.unit_type == to_def.unit_type:
            base_quantity = quantity * from_def.to_base_factor
            return base_quantity / to_def.to_base_factor
        
        # Cross-type conversion (volume <-> mass) requires ingredient info
        if from_def.unit_type != to_def.unit_type:
            if not ingredient_name:
                raise ValueError(
                    f"Cannot convert between {from_def.unit_type} and {to_def.unit_type} "
                    "without ingredient information"
                )
            
            return self._convert_cross_type(
                quantity, from_unit, to_unit, ingredient_name, from_def, to_def
            )
        
        raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")
    
    def _convert_cross_type(
        self,
        quantity: float,
        from_unit: str,
        to_unit: str,
        ingredient_name: str,
        from_def: UnitDefinition,
        to_def: UnitDefinition
    ) -> float:
        """Convert between volume and mass using ingredient-specific data."""
        ingredient_name = ingredient_name.lower()
        
        # Check for specific override first
        if from_def.unit_type == "volume":
            # Volume to mass
            override_key = (ingredient_name, from_unit)
            if override_key in self.ingredient_overrides:
                grams = quantity * self.ingredient_overrides[override_key]
                return grams / to_def.to_base_factor
        else:
            # Mass to volume
            override_key = (ingredient_name, to_unit)
            if override_key in self.ingredient_overrides:
                grams = quantity * from_def.to_base_factor
                return grams / self.ingredient_overrides[override_key]
        
        # Use density if available
        density = self.ingredient_densities.get(ingredient_name)
        if density is None:
            # Try to find partial match
            for key, value in self.ingredient_densities.items():
                if key in ingredient_name or ingredient_name in key:
                    density = value
                    break
        
        if density is None:
            raise ValueError(
                f"Cannot convert {from_unit} to {to_unit} for '{ingredient_name}': "
                "no density information available"
            )
        
        if from_def.unit_type == "volume":
            # Volume to mass: ml * (g/ml) = g
            ml = quantity * from_def.to_base_factor
            grams = ml * density
            return grams / to_def.to_base_factor
        else:
            # Mass to volume: g / (g/ml) = ml
            grams = quantity * from_def.to_base_factor
            ml = grams / density
            return ml / to_def.to_base_factor
    
    def format_for_display(
        self,
        quantity: float,
        unit: str,
        target_system: str = "metric",
        ingredient_name: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Format a quantity for display in the target unit system.
        
        Args:
            quantity: Amount in the given unit
            unit: Current unit symbol
            target_system: "metric" or "imperial"
            ingredient_name: Name of ingredient (for conversions)
            
        Returns:
            Tuple of (formatted_quantity, unit_symbol)
        """
        unit = unit.lower()
        
        if unit not in self.units:
            return quantity, unit
        
        unit_def = self.units[unit]
        
        # If already in target system, return as-is
        if unit_def.system == target_system or unit_def.system == "universal":
            return self._humanize_quantity(quantity, unit)
        
        # Convert to appropriate unit for target system
        if target_system == "metric":
            target_units = self._get_metric_units(unit_def.unit_type)
        else:
            target_units = self._get_imperial_units(unit_def.unit_type)
        
        # Try each target unit and pick the most human-readable
        best_quantity = quantity
        best_unit = unit
        
        for target_unit in target_units:
            try:
                converted = self.convert(quantity, unit, target_unit, ingredient_name)
                if 0.25 <= converted <= 1000:  # Reasonable range
                    best_quantity = converted
                    best_unit = target_unit
                    break
            except ValueError:
                continue
        
        return self._humanize_quantity(best_quantity, best_unit)
    
    def _get_metric_units(self, unit_type: str) -> list:
        """Get metric units for a given type, ordered by preference."""
        if unit_type == "mass":
            return ["g", "kg"]
        elif unit_type == "volume":
            return ["ml", "l"]
        else:
            return ["count"]
    
    def _get_imperial_units(self, unit_type: str) -> list:
        """Get imperial/US units for a given type, ordered by preference."""
        if unit_type == "mass":
            return ["oz", "lb"]
        elif unit_type == "volume":
            return ["tsp", "tbsp", "cup", "fl oz", "pt", "qt", "gal"]
        else:
            return ["count"]
    
    def _humanize_quantity(self, quantity: float, unit: str) -> Tuple[float, str]:
        """
        Make quantities more human-readable by rounding appropriately.
        
        Args:
            quantity: Numeric quantity
            unit: Unit symbol
            
        Returns:
            Tuple of (rounded_quantity, unit_symbol)
        """
        # For very small quantities, round to 2 decimal places
        if quantity < 1:
            return round(quantity, 2), unit
        
        # For medium quantities, round to 1 decimal place
        if quantity < 10:
            return round(quantity, 1), unit
        
        # For larger quantities, round to whole numbers
        return round(quantity), unit
    
    def get_common_fractions(self, decimal: float) -> Optional[str]:
        """
        Convert decimal to common fractions for imperial measurements.
        
        Args:
            decimal: Decimal value
            
        Returns:
            Fraction string or None if no good match
        """
        common_fractions = {
            0.125: "1/8",
            0.25: "1/4",
            0.333: "1/3",
            0.5: "1/2",
            0.667: "2/3",
            0.75: "3/4",
        }
        
        # Check for whole number plus fraction
        whole = int(decimal)
        remainder = decimal - whole
        
        for value, fraction in common_fractions.items():
            if abs(remainder - value) < 0.02:  # Tolerance
                if whole > 0:
                    return f"{whole} {fraction}"
                else:
                    return fraction
        
        return None
