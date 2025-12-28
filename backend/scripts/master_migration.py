"""
Master Data Migration Script for Recipe Visibility Fix
Normalizes: continent, country, slugs
Makes Admin visibility = Public visibility
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import asyncio
import re
import json

# ============================================================
# CONFIGURATION
# ============================================================

VALID_CONTINENTS = ["Europe", "Asia", "Africa", "Americas", "Oceania"]

# Country to Continent mapping (comprehensive)
COUNTRY_CONTINENT_MAP = {
    # Europe
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
    
    # Americas
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
    
    # Asia
    "Japan": "Asia", "China": "Asia", "India": "Asia", "Thailand": "Asia",
    "Vietnam": "Asia", "South Korea": "Asia", "North Korea": "Asia",
    "Indonesia": "Asia", "Malaysia": "Asia", "Philippines": "Asia",
    "Singapore": "Asia", "Taiwan": "Asia", "Hong Kong": "Asia", "Macau": "Asia",
    "Myanmar": "Asia", "Cambodia": "Asia", "Laos": "Asia", "Brunei": "Asia",
    "Bangladesh": "Asia", "Pakistan": "Asia", "Sri Lanka": "Asia",
    "Nepal": "Asia", "Bhutan": "Asia", "Maldives": "Asia",
    "Afghanistan": "Asia", "Iran": "Asia", "Iraq": "Asia",
    "Syria": "Asia", "Lebanon": "Asia", "Jordan": "Asia", "Israel": "Asia",
    "Palestine": "Asia", "Saudi Arabia": "Asia", "United Arab Emirates": "Asia",
    "Qatar": "Asia", "Kuwait": "Asia", "Bahrain": "Asia", "Oman": "Asia",
    "Yemen": "Asia", "Turkey": "Asia", "Armenia": "Asia", "Georgia": "Asia",
    "Azerbaijan": "Asia", "Kazakhstan": "Asia", "Uzbekistan": "Asia",
    "Turkmenistan": "Asia", "Tajikistan": "Asia", "Kyrgyzstan": "Asia",
    "Mongolia": "Asia", "Timor-Leste": "Asia",
    
    # Africa
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
    
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
    "Papua New Guinea": "Oceania", "Samoa": "Oceania", "Tonga": "Oceania",
    "Vanuatu": "Oceania", "Solomon Islands": "Oceania", "Micronesia": "Oceania",
    "Palau": "Oceania", "Marshall Islands": "Oceania", "Kiribati": "Oceania",
    "Nauru": "Oceania", "Tuvalu": "Oceania", "Guam": "Oceania",
    "French Polynesia": "Oceania", "New Caledonia": "Oceania",
}

# Invalid continent mappings
INVALID_CONTINENT_FIX = {
    "Middle East": "Asia",
    "Unknown": None,  # Will be derived from country
    "": None,
    None: None,
    "Levant": "Asia",
    "North Africa": "Africa",
    "Central America": "Americas",
    "South America": "Americas",
    "North America": "Americas",
    "Caribbean": "Americas",
    "Southeast Asia": "Asia",
    "East Asia": "Asia",
    "South Asia": "Asia",
    "Central Asia": "Asia",
    "Western Europe": "Europe",
    "Eastern Europe": "Europe",
    "Southern Europe": "Europe",
    "Northern Europe": "Europe",
}

# Compound country normalization
COMPOUND_COUNTRY_FIX = {
    "Nord Africa / Medio Oriente": "Morocco",
    "Levant (Medio Oriente)": "Lebanon",
    "United Kingdom / Australia–New Zealand": "United Kingdom",
    "Middle East": "Lebanon",
    "Levant": "Lebanon",
    "North Africa": "Morocco",
    "Southeast Asia": "Thailand",
    "Mediterranean": "Italy",
}

# Country name normalization
COUNTRY_NORMALIZATION = {
    "italia": "Italy", "italie": "Italy", "italien": "Italy",
    "francia": "France", "frankreich": "France",
    "españa": "Spain", "espagne": "Spain", "spagna": "Spain", "spanien": "Spain",
    "germania": "Germany", "allemagne": "Germany", "alemania": "Germany", "deutschland": "Germany",
    "messico": "Mexico", "mexique": "Mexico", "mexiko": "Mexico", "méxico": "Mexico",
    "giappone": "Japan", "japon": "Japan", "japón": "Japan",
    "cina": "China", "chine": "China",
    "thailandia": "Thailand", "thaïlande": "Thailand",
    "grecia": "Greece", "grèce": "Greece", "griechenland": "Greece",
    "turchia": "Turkey", "turquie": "Turkey", "turquía": "Turkey", "türkei": "Turkey",
    "libano": "Lebanon", "liban": "Lebanon", "líbano": "Lebanon", "libanon": "Lebanon",
    "marocco": "Morocco", "maroc": "Morocco", "marruecos": "Morocco", "marokko": "Morocco",
    "egitto": "Egypt", "égypte": "Egypt", "egipto": "Egypt", "ägypten": "Egypt",
    "brasile": "Brazil", "brésil": "Brazil", "brasil": "Brazil", "brasilien": "Brazil",
    "portogallo": "Portugal",
    "perù": "Peru", "pérou": "Peru", "perú": "Peru",
    "cile": "Chile", "chili": "Chile",
    "colombie": "Colombia", "kolumbien": "Colombia",
    "corea del sud": "South Korea", "corée du sud": "South Korea", "corea del sur": "South Korea", "südkorea": "South Korea",
    "regno unito": "United Kingdom", "royaume-uni": "United Kingdom", "reino unido": "United Kingdom", "großbritannien": "United Kingdom",
    "stati uniti": "United States", "états-unis": "United States", "estados unidos": "United States", "vereinigte staaten": "United States",
    "uk": "United Kingdom", "usa": "United States", "us": "United States",
}


def normalize_country(country_value):
    """Normalize country to canonical English name."""
    if not country_value:
        return ""
    
    # Check compound country fix first
    if country_value in COMPOUND_COUNTRY_FIX:
        return COMPOUND_COUNTRY_FIX[country_value]
    
    # Check if already canonical
    if country_value in COUNTRY_CONTINENT_MAP:
        return country_value
    
    # Try lowercase lookup
    lookup = country_value.lower().strip()
    if lookup in COUNTRY_NORMALIZATION:
        return COUNTRY_NORMALIZATION[lookup]
    
    # Try title case
    title_case = country_value.strip().title()
    if title_case in COUNTRY_CONTINENT_MAP:
        return title_case
    
    return country_value


def get_continent(country):
    """Get valid continent for a country."""
    if not country:
        return None
    
    normalized = normalize_country(country)
    return COUNTRY_CONTINENT_MAP.get(normalized, None)


def normalize_continent(continent_value, country=None):
    """Normalize continent to valid value, deriving from country if needed."""
    # If already valid, return as-is
    if continent_value in VALID_CONTINENTS:
        return continent_value
    
    # Check invalid continent mappings
    if continent_value in INVALID_CONTINENT_FIX:
        fixed = INVALID_CONTINENT_FIX[continent_value]
        if fixed:
            return fixed
    
    # Derive from country
    if country:
        derived = get_continent(country)
        if derived:
            return derived
    
    return None


def make_slug_unique(slug, existing_slugs):
    """Make a slug unique by adding suffix."""
    if slug not in existing_slugs:
        return slug
    
    suffixes = ["-2", "-variant", "-regional", "-traditional", "-alt"]
    for suffix in suffixes:
        new_slug = f"{slug}{suffix}"
        if new_slug not in existing_slugs:
            return new_slug
    
    # Fallback: add number
    counter = 3
    while f"{slug}-{counter}" in existing_slugs:
        counter += 1
    return f"{slug}-{counter}"


async def run_migration(dry_run=True):
    """Run the master migration."""
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['sous_chef_linguini_db']
    
    print("=" * 70)
    print(f"MASTER MIGRATION {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    print("=" * 70)
    
    # Get all recipes
    all_recipes = await db.recipes.find({}, {"_id": 0}).to_list(2000)
    published = [r for r in all_recipes if r.get("status") == "published"]
    
    print(f"\nTotal recipes: {len(all_recipes)}")
    print(f"Published recipes: {len(published)}")
    
    # Migration log
    mutations = {
        "continent_fixed": [],
        "country_normalized": [],
        "slug_deduplicated": [],
        "unpublished_incomplete": [],
        "name_backfilled": [],
    }
    
    # Track all slugs for deduplication
    all_slugs = set()
    slug_recipe_map = {}
    
    for recipe in all_recipes:
        slug = recipe.get("slug", "")
        if slug:
            if slug in slug_recipe_map:
                slug_recipe_map[slug].append(recipe)
            else:
                slug_recipe_map[slug] = [recipe]
                all_slugs.add(slug)
    
    # Process each published recipe
    for recipe in published:
        slug = recipe.get("slug", "")
        updates = {}
        
        # 1. Normalize country
        origin_country = recipe.get("origin_country", "") or ""
        if origin_country:
            normalized_country = normalize_country(origin_country)
            if normalized_country != origin_country:
                updates["origin_country"] = normalized_country
                mutations["country_normalized"].append({
                    "slug": slug,
                    "from": origin_country,
                    "to": normalized_country
                })
                origin_country = normalized_country
        
        # 2. Normalize/fix continent
        continent = recipe.get("continent", "") or ""
        if continent not in VALID_CONTINENTS:
            fixed_continent = normalize_continent(continent, origin_country)
            if fixed_continent:
                updates["continent"] = fixed_continent
                mutations["continent_fixed"].append({
                    "slug": slug,
                    "from": continent or "(empty)",
                    "to": fixed_continent,
                    "derived_from": origin_country if not continent else "mapping"
                })
        
        # 3. Backfill recipe name if missing
        recipe_name = recipe.get("recipe_name", "") or ""
        if not recipe_name:
            # Try translations
            translations = recipe.get("translations", {})
            for lang in ["en", "it", "fr", "es", "de"]:
                trans = translations.get(lang, {})
                if trans.get("recipe_name"):
                    updates["recipe_name"] = trans.get("recipe_name")
                    mutations["name_backfilled"].append({
                        "slug": slug,
                        "from_lang": lang,
                        "name": trans.get("recipe_name")
                    })
                    break
            
            # Try fallback fields
            if "recipe_name" not in updates:
                fallback_name = (recipe.get("title_original") or 
                                recipe.get("title") or 
                                slug.replace("-", " ").title())
                if fallback_name:
                    updates["recipe_name"] = fallback_name
                    mutations["name_backfilled"].append({
                        "slug": slug,
                        "from_field": "fallback",
                        "name": fallback_name
                    })
        
        # 4. Check if incomplete (must unpublish)
        final_name = updates.get("recipe_name", recipe.get("recipe_name", ""))
        final_country = updates.get("origin_country", origin_country)
        final_continent = updates.get("continent", recipe.get("continent", ""))
        ingredients = recipe.get("ingredients", []) or []
        instructions = recipe.get("instructions", []) or []
        
        is_incomplete = (
            not final_name or
            not final_country or
            final_continent not in VALID_CONTINENTS or
            not ingredients or len(ingredients) == 0 or
            not instructions or len(instructions) == 0
        )
        
        if is_incomplete:
            updates["status"] = "unpublished"
            updates["unpublish_reason"] = "incomplete_required_fields"
            mutations["unpublished_incomplete"].append({
                "slug": slug,
                "missing": {
                    "name": not final_name,
                    "country": not final_country,
                    "continent": final_continent not in VALID_CONTINENTS,
                    "ingredients": not ingredients or len(ingredients) == 0,
                    "instructions": not instructions or len(instructions) == 0
                }
            })
        
        # Apply updates
        if updates and not dry_run:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            updates["migration_applied"] = "master_visibility_fix_v1"
            await db.recipes.update_one(
                {"slug": slug},
                {"$set": updates}
            )
    
    # 5. Handle duplicate slugs
    for slug, recipes in slug_recipe_map.items():
        if len(recipes) > 1:
            # Keep first, rename others
            for i, recipe in enumerate(recipes[1:], start=2):
                old_slug = recipe.get("slug")
                new_slug = make_slug_unique(slug, all_slugs)
                all_slugs.add(new_slug)
                
                mutations["slug_deduplicated"].append({
                    "from": old_slug,
                    "to": new_slug,
                    "recipe_name": recipe.get("recipe_name", "")
                })
                
                if not dry_run:
                    await db.recipes.update_one(
                        {"slug": old_slug, "recipe_name": recipe.get("recipe_name")},
                        {"$set": {
                            "slug": new_slug,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "migration_applied": "master_visibility_fix_v1"
                        }}
                    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    
    print(f"\n[CONTINENT] Fixed: {len(mutations['continent_fixed'])}")
    for m in mutations['continent_fixed'][:10]:
        print(f"  - {m['slug']}: '{m['from']}' → '{m['to']}'")
    
    print(f"\n[COUNTRY] Normalized: {len(mutations['country_normalized'])}")
    for m in mutations['country_normalized'][:10]:
        print(f"  - {m['slug']}: '{m['from']}' → '{m['to']}'")
    
    print(f"\n[SLUG] Deduplicated: {len(mutations['slug_deduplicated'])}")
    for m in mutations['slug_deduplicated'][:10]:
        print(f"  - '{m['from']}' → '{m['to']}'")
    
    print(f"\n[NAME] Backfilled: {len(mutations['name_backfilled'])}")
    for m in mutations['name_backfilled'][:5]:
        print(f"  - {m['slug']}: '{m.get('name', '')[:40]}'")
    
    print(f"\n[UNPUBLISHED] Incomplete recipes: {len(mutations['unpublished_incomplete'])}")
    for m in mutations['unpublished_incomplete'][:10]:
        print(f"  - {m['slug']}: {m['missing']}")
    
    return mutations


async def validate_migration():
    """Validate migration results."""
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['sous_chef_linguini_db']
    
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    
    # Get counts
    total = await db.recipes.count_documents({})
    published = await db.recipes.count_documents({"status": "published"})
    
    # Visibility criteria (must match frontend exactly)
    visible = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$in": VALID_CONTINENTS},
        "origin_country": {"$exists": True, "$ne": None, "$ne": ""},
        "recipe_name": {"$exists": True, "$ne": None, "$ne": ""},
        "ingredients": {"$exists": True, "$ne": None, "$not": {"$size": 0}},
        "instructions": {"$exists": True, "$ne": None, "$not": {"$size": 0}}
    })
    
    # Check for remaining issues
    invalid_continents = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"continent": {"$exists": False}},
            {"continent": None},
            {"continent": ""},
            {"continent": {"$nin": VALID_CONTINENTS}}
        ]
    })
    
    missing_country = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"origin_country": {"$exists": False}},
            {"origin_country": None},
            {"origin_country": ""}
        ]
    })
    
    # Check duplicate slugs
    pipeline = [
        {"$match": {"status": "published"}},
        {"$group": {"_id": "$slug", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    duplicates = await db.recipes.aggregate(pipeline).to_list(100)
    
    print(f"\nTotal recipes: {total}")
    print(f"Published recipes: {published}")
    print(f"Truly visible recipes: {visible}")
    print(f"Hidden published: {published - visible}")
    print(f"\nRemaining issues:")
    print(f"  - Invalid continents: {invalid_continents}")
    print(f"  - Missing country: {missing_country}")
    print(f"  - Duplicate slugs: {len(duplicates)}")
    
    if published == visible:
        print("\n✅ SUCCESS: Admin published count === public recipe count")
    else:
        print(f"\n❌ GAP REMAINS: {published - visible} published but not visible")
        
        # List remaining blocked items
        blocked = await db.recipes.find(
            {
                "status": "published",
                "$or": [
                    {"continent": {"$nin": VALID_CONTINENTS}},
                    {"continent": {"$exists": False}},
                    {"continent": None},
                    {"continent": ""},
                    {"origin_country": {"$exists": False}},
                    {"origin_country": None},
                    {"origin_country": ""},
                    {"recipe_name": {"$exists": False}},
                    {"recipe_name": None},
                    {"recipe_name": ""},
                    {"ingredients": {"$exists": False}},
                    {"ingredients": None},
                    {"ingredients": {"$size": 0}},
                    {"instructions": {"$exists": False}},
                    {"instructions": None},
                    {"instructions": {"$size": 0}}
                ]
            },
            {"slug": 1, "recipe_name": 1, "continent": 1, "origin_country": 1, "_id": 0}
        ).to_list(50)
        
        print("\nBlocked recipes:")
        for r in blocked:
            print(f"  - {r.get('slug')}: continent={r.get('continent')}, country={r.get('origin_country')}")
    
    return {
        "total": total,
        "published": published,
        "visible": visible,
        "gap": published - visible,
        "invalid_continents": invalid_continents,
        "missing_country": missing_country,
        "duplicate_slugs": len(duplicates)
    }


if __name__ == "__main__":
    import sys
    
    dry_run = "--execute" not in sys.argv
    
    asyncio.run(run_migration(dry_run=dry_run))
    asyncio.run(validate_migration())
