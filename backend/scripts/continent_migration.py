"""
Continent Normalization Migration Script
Normalizes all published recipes to use canonical continent values:
- Europe, Asia, Americas, Africa, Middle East, Oceania
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# ============================================================
# CANONICAL CONTINENTS (6 valid values)
# ============================================================
VALID_CONTINENTS = ["Europe", "Asia", "Americas", "Africa", "Middle East", "Oceania"]

# ============================================================
# CONTINENT NORMALIZATION MAP
# ============================================================
CONTINENT_NORMALIZATION = {
    # North/South America -> Americas
    "North America": "Americas",
    "South America": "Americas",
    "Central America": "Americas",
    "Caribbean": "Americas",
    "Latin America": "Americas",
    
    # Multi-value / compound -> resolve to primary
    "Europe / Oceania": "Europe",  # Default to first
    "Nord Africa / Medio Oriente": "Africa",
    "Middle East / North Africa": "Middle East",
    "MENA": "Middle East",
    "North Africa": "Africa",
    
    # Sub-regions -> canonical
    "Southeast Asia": "Asia",
    "East Asia": "Asia",
    "South Asia": "Asia",
    "Central Asia": "Asia",
    "Western Europe": "Europe",
    "Eastern Europe": "Europe",
    "Southern Europe": "Europe",
    "Northern Europe": "Europe",
    "Sub-Saharan Africa": "Africa",
    "West Africa": "Africa",
    "East Africa": "Africa",
    
    # Variations
    "Oceana": "Oceania",
    "Australia": "Oceania",
    "Australasia": "Oceania",
    "Pacific": "Oceania",
}

# ============================================================
# COUNTRY -> CONTINENT MAPPING (COMPREHENSIVE)
# ============================================================
COUNTRY_TO_CONTINENT = {
    # EUROPE
    "Italy": "Europe", "France": "Europe", "Spain": "Europe", "Germany": "Europe",
    "Portugal": "Europe", "Greece": "Europe", "United Kingdom": "Europe", "UK": "Europe",
    "Ireland": "Europe", "Belgium": "Europe", "Netherlands": "Europe", "Switzerland": "Europe",
    "Austria": "Europe", "Poland": "Europe", "Czech Republic": "Europe", "Hungary": "Europe",
    "Romania": "Europe", "Bulgaria": "Europe", "Croatia": "Europe", "Slovenia": "Europe",
    "Slovakia": "Europe", "Serbia": "Europe", "Bosnia and Herzegovina": "Europe",
    "Montenegro": "Europe", "North Macedonia": "Europe", "Albania": "Europe", "Kosovo": "Europe",
    "Ukraine": "Europe", "Russia": "Europe", "Belarus": "Europe", "Moldova": "Europe",
    "Lithuania": "Europe", "Latvia": "Europe", "Estonia": "Europe", "Finland": "Europe",
    "Sweden": "Europe", "Norway": "Europe", "Denmark": "Europe", "Iceland": "Europe",
    "Malta": "Europe", "Cyprus": "Europe", "Luxembourg": "Europe", "Monaco": "Europe",
    "Andorra": "Europe", "San Marino": "Europe", "Vatican City": "Europe", "Liechtenstein": "Europe",
    
    # AMERICAS
    "United States": "Americas", "USA": "Americas", "US": "Americas",
    "Mexico": "Americas", "Canada": "Americas", "Brazil": "Americas",
    "Argentina": "Americas", "Peru": "Americas", "Chile": "Americas",
    "Colombia": "Americas", "Venezuela": "Americas", "Ecuador": "Americas",
    "Bolivia": "Americas", "Paraguay": "Americas", "Uruguay": "Americas",
    "Cuba": "Americas", "Dominican Republic": "Americas", "Puerto Rico": "Americas",
    "Jamaica": "Americas", "Haiti": "Americas", "Trinidad and Tobago": "Americas",
    "Guatemala": "Americas", "Honduras": "Americas", "El Salvador": "Americas",
    "Nicaragua": "Americas", "Costa Rica": "Americas", "Panama": "Americas",
    "Belize": "Americas", "Guyana": "Americas", "Suriname": "Americas",
    "Bahamas": "Americas", "Barbados": "Americas",
    
    # ASIA (East, South, Southeast, Central)
    "Japan": "Asia", "China": "Asia", "India": "Asia", "Thailand": "Asia",
    "Vietnam": "Asia", "South Korea": "Asia", "North Korea": "Asia",
    "Indonesia": "Asia", "Malaysia": "Asia", "Philippines": "Asia",
    "Singapore": "Asia", "Taiwan": "Asia", "Hong Kong": "Asia", "Macau": "Asia",
    "Myanmar": "Asia", "Cambodia": "Asia", "Laos": "Asia", "Brunei": "Asia",
    "Bangladesh": "Asia", "Pakistan": "Asia", "Sri Lanka": "Asia",
    "Nepal": "Asia", "Bhutan": "Asia", "Maldives": "Asia",
    "Afghanistan": "Asia", "Kazakhstan": "Asia", "Uzbekistan": "Asia",
    "Turkmenistan": "Asia", "Tajikistan": "Asia", "Kyrgyzstan": "Asia",
    "Mongolia": "Asia", "Timor-Leste": "Asia",
    
    # MIDDLE EAST
    "Turkey": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
    "Syria": "Middle East", "Lebanon": "Middle East", "Jordan": "Middle East",
    "Israel": "Middle East", "Palestine": "Middle East",
    "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East", "UAE": "Middle East",
    "Qatar": "Middle East", "Kuwait": "Middle East", "Bahrain": "Middle East",
    "Oman": "Middle East", "Yemen": "Middle East",
    "Armenia": "Middle East", "Georgia": "Middle East", "Azerbaijan": "Middle East",
    
    # AFRICA
    "Morocco": "Africa", "Egypt": "Africa", "Tunisia": "Africa",
    "Algeria": "Africa", "Libya": "Africa", "South Africa": "Africa",
    "Nigeria": "Africa", "Kenya": "Africa", "Ethiopia": "Africa",
    "Ghana": "Africa", "Senegal": "Africa", "Ivory Coast": "Africa",
    "Cameroon": "Africa", "Tanzania": "Africa", "Uganda": "Africa",
    "Rwanda": "Africa", "Zimbabwe": "Africa", "Zambia": "Africa",
    "Mozambique": "Africa", "Madagascar": "Africa", "Mauritius": "Africa",
    "Sudan": "Africa", "South Sudan": "Africa", "Mali": "Africa",
    "Niger": "Africa", "Chad": "Africa", "Burkina Faso": "Africa",
    "Benin": "Africa", "Togo": "Africa", "Liberia": "Africa",
    "Sierra Leone": "Africa", "Guinea": "Africa", "Guinea-Bissau": "Africa",
    "Gambia": "Africa", "Mauritania": "Africa", "Cape Verde": "Africa",
    "Sao Tome and Principe": "Africa", "Equatorial Guinea": "Africa",
    "Gabon": "Africa", "Congo": "Africa", "Democratic Republic of the Congo": "Africa",
    "Angola": "Africa", "Namibia": "Africa", "Botswana": "Africa",
    "Lesotho": "Africa", "Eswatini": "Africa", "Malawi": "Africa",
    "Comoros": "Africa", "Seychelles": "Africa", "Djibouti": "Africa",
    "Eritrea": "Africa", "Somalia": "Africa", "Central African Republic": "Africa",
    "Burundi": "Africa",
    
    # OCEANIA
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
    "Papua New Guinea": "Oceania", "Samoa": "Oceania", "Tonga": "Oceania",
    "Vanuatu": "Oceania", "Solomon Islands": "Oceania", "Micronesia": "Oceania",
    "Palau": "Oceania", "Marshall Islands": "Oceania", "Kiribati": "Oceania",
    "Nauru": "Oceania", "Tuvalu": "Oceania", "Guam": "Oceania",
    "French Polynesia": "Oceania", "New Caledonia": "Oceania",
}


def normalize_continent(continent_value: str, country: str = None) -> str:
    """
    Normalize continent to one of the 6 valid values.
    Uses country inference as fallback.
    """
    if not continent_value:
        # Try to infer from country
        if country and country in COUNTRY_TO_CONTINENT:
            return COUNTRY_TO_CONTINENT[country]
        return None
    
    # Already valid?
    if continent_value in VALID_CONTINENTS:
        return continent_value
    
    # Check normalization map
    if continent_value in CONTINENT_NORMALIZATION:
        return CONTINENT_NORMALIZATION[continent_value]
    
    # Check if it contains any valid continent keyword
    continent_lower = continent_value.lower()
    
    if "america" in continent_lower:
        return "Americas"
    if "africa" in continent_lower:
        return "Africa"
    if "asia" in continent_lower:
        return "Asia"
    if "europe" in continent_lower:
        return "Europe"
    if "oceania" in continent_lower or "australia" in continent_lower or "pacific" in continent_lower:
        return "Oceania"
    if "middle east" in continent_lower or "levant" in continent_lower:
        return "Middle East"
    
    # Try to infer from country
    if country and country in COUNTRY_TO_CONTINENT:
        return COUNTRY_TO_CONTINENT[country]
    
    return None


async def run_migration(mongo_url: str, db_name: str, dry_run: bool = True):
    """Run the continent normalization migration."""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 70)
    print(f"CONTINENT NORMALIZATION MIGRATION {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    print("=" * 70)
    print(f"Database: {db_name}")
    print(f"Valid continents: {VALID_CONTINENTS}")
    print()
    
    # Get all published recipes
    published_recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 1, "slug": 1, "recipe_name": 1, "continent": 1, "origin_country": 1}
    ).to_list(2000)
    
    print(f"Total published recipes: {len(published_recipes)}")
    
    # Track changes
    changes = []
    failed = []
    already_valid = 0
    
    for recipe in published_recipes:
        recipe_id = recipe.get("_id")
        slug = recipe.get("slug", "")
        current_continent = recipe.get("continent", "")
        country = recipe.get("origin_country", "")
        
        # Check if already valid
        if current_continent in VALID_CONTINENTS:
            already_valid += 1
            continue
        
        # Normalize
        new_continent = normalize_continent(current_continent, country)
        
        if new_continent and new_continent in VALID_CONTINENTS:
            changes.append({
                "id": recipe_id,
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "old_continent": current_continent or "(empty)",
                "new_continent": new_continent,
                "country": country,
                "inference_reason": "country" if not current_continent else "normalization"
            })
            
            if not dry_run:
                await db.recipes.update_one(
                    {"_id": recipe_id},
                    {"$set": {
                        "continent": new_continent,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "migration_applied": "continent_normalization_v1"
                    }}
                )
        else:
            failed.append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "current_continent": current_continent,
                "country": country,
                "reason": "Could not determine valid continent"
            })
    
    # Print results
    print()
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Already valid: {already_valid}")
    print(f"Normalized: {len(changes)}")
    print(f"Failed (need manual review): {len(failed)}")
    print()
    
    if changes:
        print("CHANGES:")
        for c in changes[:30]:  # Show first 30
            print(f"  [{c['slug']}] '{c['old_continent']}' -> '{c['new_continent']}' (via {c['inference_reason']})")
        if len(changes) > 30:
            print(f"  ... and {len(changes) - 30} more")
    
    if failed:
        print()
        print("FAILED (need manual review):")
        for f in failed[:20]:
            print(f"  [{f['slug']}] continent='{f['current_continent']}', country='{f['country']}'")
    
    return {
        "already_valid": already_valid,
        "normalized": len(changes),
        "failed": len(failed),
        "changes": changes,
        "failed_list": failed
    }


async def validate_migration(mongo_url: str, db_name: str):
    """Validate migration results."""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print()
    print("=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    
    # Count by status
    published = await db.recipes.count_documents({"status": "published"})
    
    # Count by continent (only valid continents)
    continent_counts = {}
    for continent in VALID_CONTINENTS:
        count = await db.recipes.count_documents({
            "status": "published",
            "continent": continent
        })
        continent_counts[continent] = count
    
    # Count invalid continents
    invalid_continents = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$nin": VALID_CONTINENTS}
    })
    
    # Count visible (has all required fields)
    visible = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$in": VALID_CONTINENTS},
        "origin_country": {"$exists": True, "$ne": None, "$ne": ""},
        "recipe_name": {"$exists": True, "$ne": None, "$ne": ""},
        "ingredients": {"$exists": True, "$ne": None, "$not": {"$size": 0}},
        "instructions": {"$exists": True, "$ne": None, "$not": {"$size": 0}}
    })
    
    total_in_continents = sum(continent_counts.values())
    
    print(f"Published recipes: {published}")
    print(f"Recipes with valid continents: {total_in_continents}")
    print(f"Recipes with invalid continents: {invalid_continents}")
    print(f"Fully visible recipes: {visible}")
    print()
    print("CONTINENT BREAKDOWN:")
    for continent, count in sorted(continent_counts.items(), key=lambda x: -x[1]):
        print(f"  {continent}: {count}")
    print(f"  TOTAL: {total_in_continents}")
    
    print()
    if invalid_continents == 0 and total_in_continents == published:
        print("✅ SUCCESS: All published recipes have valid continents!")
        print(f"✅ Public site should show: {visible} recipes")
    else:
        print(f"❌ ISSUES REMAIN: {invalid_continents} recipes with invalid continents")
        
        # Show what's still invalid
        invalid_list = await db.recipes.find(
            {
                "status": "published",
                "continent": {"$nin": VALID_CONTINENTS}
            },
            {"slug": 1, "continent": 1, "origin_country": 1, "_id": 0}
        ).limit(20).to_list(20)
        
        print("Invalid recipes:")
        for r in invalid_list:
            print(f"  {r.get('slug')}: continent='{r.get('continent')}', country='{r.get('origin_country')}'")
    
    return {
        "published": published,
        "valid_continents": total_in_continents,
        "invalid_continents": invalid_continents,
        "visible": visible,
        "continent_counts": continent_counts
    }


if __name__ == "__main__":
    import sys
    
    # Get database connection from environment
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'sous_chef_linguini_db')
    
    dry_run = "--execute" not in sys.argv
    
    print(f"Using database: {db_name}")
    print(f"MongoDB URL: {mongo_url[:50]}...")
    
    asyncio.run(run_migration(mongo_url, db_name, dry_run=dry_run))
    asyncio.run(validate_migration(mongo_url, db_name))
