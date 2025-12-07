# Unit conversion utilities

from typing import Dict, Optional

# Temperature conversions
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5/9

# Weight conversions
def grams_to_ounces(grams: float) -> float:
    """Convert grams to ounces."""
    return grams * 0.035274

def ounces_to_grams(ounces: float) -> float:
    """Convert ounces to grams."""
    return ounces * 28.3495

# Volume conversions
def ml_to_cups(ml: float) -> float:
    """Convert milliliters to US cups."""
    return ml * 0.00422675

def cups_to_ml(cups: float) -> float:
    """Convert US cups to milliliters."""
    return cups * 236.588

def ml_to_fl_oz(ml: float) -> float:
    """Convert milliliters to fluid ounces."""
    return ml * 0.033814

def fl_oz_to_ml(fl_oz: float) -> float:
    """Convert fluid ounces to milliliters."""
    return fl_oz * 29.5735

# Locale-based unit system
def get_unit_system(locale: str) -> Dict[str, str]:
    """Get unit system based on locale."""
    locale_lower = locale.lower()
    
    if locale_lower.startswith(('en-us', 'en_us')):
        return {
            'weight': 'oz',
            'volume': 'cups',
            'temperature': 'F'
        }
    elif locale_lower.startswith(('en-gb', 'en_gb', 'en-ca', 'en_ca')):
        # UK/Canada use hybrid
        return {
            'weight': 'g',
            'volume': 'ml',
            'temperature': 'C'
        }
    else:
        # Default to metric
        return {
            'weight': 'g',
            'volume': 'ml',
            'temperature': 'C'
        }

def convert_ingredient_units(amount: float, from_unit: str, to_unit: str) -> Optional[float]:
    """Convert ingredient units."""
    # Weight conversions
    if from_unit == 'g' and to_unit == 'oz':
        return grams_to_ounces(amount)
    elif from_unit == 'oz' and to_unit == 'g':
        return ounces_to_grams(amount)
    
    # Volume conversions
    elif from_unit == 'ml' and to_unit == 'cups':
        return ml_to_cups(amount)
    elif from_unit == 'cups' and to_unit == 'ml':
        return cups_to_ml(amount)
    elif from_unit == 'ml' and to_unit == 'fl_oz':
        return ml_to_fl_oz(amount)
    elif from_unit == 'fl_oz' and to_unit == 'ml':
        return fl_oz_to_ml(amount)
    
    # No conversion needed
    elif from_unit == to_unit:
        return amount
    
    return None
