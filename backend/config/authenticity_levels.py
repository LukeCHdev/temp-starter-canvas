# Authenticity classification constants

AUTHENTICITY_RANKS = {
    "official": 1,
    "traditional": 2,
    "modern": 3
}

AUTHENTICITY_CLASSIFICATIONS = {
    1: "Official / Registered / Institutional",
    2: "Traditional / Historical / Local Certified",
    3: "Modern / Derived / Contemporary"
}

VALIDATION_REQUIREMENTS = {
    1: {
        "requires_official_source": True,
        "requires_native_language": True,
        "requires_country_domain": True,
        "accepted_bodies": ["DOP", "IGP", "AOP", "STG", "Culinary Academy", "Government Registry"]
    },
    2: {
        "requires_official_source": False,
        "requires_native_language": True,
        "requires_country_domain": True,
        "accepted_sources": ["Regional cookbooks", "Cultural archives", "Traditional documentation"],
        "pat_exception": True  # PAT status overrides strict requirements
    },
    3: {
        "requires_official_source": False,
        "requires_native_language": True,
        "requires_country_domain": True,
        "must_be_marked": "Modern / Non-Traditional"
    }
}

# PAT (Prodotto Agroalimentare Tradizionale) special rules
PAT_VALIDATION_RULES = {
    "description": "PAT status indicates ministerial recognition of traditional recipes",
    "overrides_requirements": [
        "native_language_validated",  # Preferred but not mandatory
        "country_domain_validated"    # Recommended but not required
    ],
    "accepted_sources": [
        "PAT Registry (Ministero dell'Agricoltura)",
        "Regional gastronomic archives",
        "Local culinary academies",
        "Municipal historical documentation",
        "Family-based traditional recipes",
        "Rural traditional dishes documentation"
    ],
    "classification_rank": 2,  # Always Level 2 - Traditional/Historical/Local
    "requires_cultural_validation": True,
    "supports_rare_recipes": True,
    "supports_family_recipes": True,
    "supports_localized_rural_dishes": True
}

# Official certification bodies
OFFICIAL_CERTIFICATIONS = {
    "PAT": "Prodotto Agroalimentare Tradizionale (Italy)",
    "DOP": "Denominazione di Origine Protetta",
    "IGP": "Indicazione Geografica Protetta",
    "STG": "Specialità Tradizionale Garantita",
    "AOP": "Appellation d'Origine Protégée (France)",
    "DOC": "Denominazione di Origine Controllata",
    "Accademia": "Italian Culinary Academy Recognition"
}

def is_pat_certified(recipe_data: dict) -> bool:
    """Check if recipe has PAT certification."""
    # Check in source references
    source_refs = recipe_data.get('source_references', [])
    for ref in source_refs:
        if 'PAT' in ref.get('description', '').upper() or \
           'PRODOTTO AGROALIMENTARE TRADIZIONALE' in ref.get('description', '').upper():
            return True
    
    # Check in validation notes
    validation = recipe_data.get('source_validation', {})
    notes = validation.get('validation_notes', '')
    if 'PAT' in notes.upper() or 'PRODOTTO AGROALIMENTARE TRADIZIONALE' in notes.upper():
        return True
    
    return False

def get_classification_name(rank: int) -> str:
    """Get classification name for a given rank."""
    return AUTHENTICITY_CLASSIFICATIONS.get(rank, "Unknown")

def get_validation_requirements(rank: int) -> dict:
    """Get validation requirements for a given rank."""
    return VALIDATION_REQUIREMENTS.get(rank, {})
