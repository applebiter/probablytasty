"""
Tests for unit conversion service.
"""

import pytest
from src.services.unit_conversion import UnitConversionService


def test_same_unit_conversion():
    """Test conversion when source and target units are the same."""
    service = UnitConversionService()
    result = service.convert(5, "g", "g")
    assert result == 5


def test_metric_mass_conversion():
    """Test metric mass conversions."""
    service = UnitConversionService()
    
    # Grams to kilograms
    result = service.convert(1000, "g", "kg")
    assert result == 1
    
    # Kilograms to grams
    result = service.convert(2.5, "kg", "g")
    assert result == 2500


def test_volume_conversion():
    """Test volume conversions."""
    service = UnitConversionService()
    
    # Cups to tablespoons
    result = service.convert(1, "cup", "tbsp")
    assert abs(result - 16) < 0.1
    
    # Teaspoons to milliliters
    result = service.convert(1, "tsp", "ml")
    assert abs(result - 4.93) < 0.1


def test_ingredient_specific_conversion():
    """Test ingredient-specific conversions."""
    service = UnitConversionService()
    
    # Flour cup to grams
    result = service.convert(1, "cup", "g", "flour")
    assert abs(result - 120) < 1
    
    # Sugar cup to grams
    result = service.convert(1, "cup", "g", "sugar")
    assert abs(result - 200) < 1


def test_cross_type_conversion_without_ingredient():
    """Test that cross-type conversion fails without ingredient info."""
    service = UnitConversionService()
    
    with pytest.raises(ValueError):
        service.convert(1, "cup", "g")


def test_format_for_display():
    """Test quantity formatting for display."""
    service = UnitConversionService()
    
    # Test metric display
    quantity, unit = service.format_for_display(500, "g", "metric")
    assert quantity == 500
    assert unit == "g"
    
    # Test imperial display
    quantity, unit = service.format_for_display(1, "cup", "imperial")
    assert quantity == 1
    assert unit == "cup"


def test_common_fractions():
    """Test fraction conversion."""
    service = UnitConversionService()
    
    assert service.get_common_fractions(0.5) == "1/2"
    assert service.get_common_fractions(0.25) == "1/4"
    assert service.get_common_fractions(1.5) == "1 1/2"
    assert service.get_common_fractions(2.75) == "2 3/4"
