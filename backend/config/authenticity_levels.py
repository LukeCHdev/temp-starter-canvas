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
        "accepted_sources": ["Regional cookbooks", "Cultural archives", "Traditional documentation"]
    },
    3: {
        "requires_official_source": False,
        "requires_native_language": True,
        "requires_country_domain": True,
        "must_be_marked": "Modern / Non-Traditional"
    }
}

def get_classification_name(rank: int) -> str:
    """Get classification name for a given rank."""
    return AUTHENTICITY_CLASSIFICATIONS.get(rank, "Unknown")

def get_validation_requirements(rank: int) -> dict:
    """Get validation requirements for a given rank."""
    return VALIDATION_REQUIREMENTS.get(rank, {})
