# Country and Continent Normalization Maps
# Canonical storage is ENGLISH only

# Map localized country names to canonical English
COUNTRY_NORMALIZATION = {
    # Italian variants
    "italia": "Italy",
    "italie": "Italy",
    "italien": "Italy",
    # French variants
    "france": "France",
    "francia": "France",
    "frankreich": "France",
    # Spanish variants
    "españa": "Spain",
    "espagne": "Spain",
    "spagna": "Spain",
    "spanien": "Spain",
    # German variants
    "germany": "Germany",
    "germania": "Germany",
    "allemagne": "Germany",
    "alemania": "Germany",
    "deutschland": "Germany",
    # Portuguese variants
    "portugal": "Portugal",
    "portogallo": "Portugal",
    # Greek variants
    "greece": "Greece",
    "grecia": "Greece",
    "grèce": "Greece",
    "griechenland": "Greece",
    # Mexican variants
    "mexico": "Mexico",
    "messico": "Mexico",
    "mexique": "Mexico",
    "mexiko": "Mexico",
    "méxico": "Mexico",
    # Japanese variants
    "japan": "Japan",
    "giappone": "Japan",
    "japon": "Japan",
    "japón": "Japan",
    # Chinese variants
    "china": "China",
    "cina": "China",
    "chine": "China",
    # Indian variants
    "india": "India",
    "inde": "India",
    "indien": "India",
    # Thai variants
    "thailand": "Thailand",
    "thailandia": "Thailand",
    "thaïlande": "Thailand",
    # Vietnamese variants
    "vietnam": "Vietnam",
    "viêt nam": "Vietnam",
    # Korean variants
    "south korea": "South Korea",
    "corea del sud": "South Korea",
    "corée du sud": "South Korea",
    "corea del sur": "South Korea",
    "südkorea": "South Korea",
    # UK variants
    "united kingdom": "United Kingdom",
    "regno unito": "United Kingdom",
    "royaume-uni": "United Kingdom",
    "reino unido": "United Kingdom",
    "großbritannien": "United Kingdom",
    "uk": "United Kingdom",
    "england": "United Kingdom",
    # US variants
    "united states": "United States",
    "stati uniti": "United States",
    "états-unis": "United States",
    "estados unidos": "United States",
    "vereinigte staaten": "United States",
    "usa": "United States",
    "us": "United States",
    # Brazilian variants
    "brazil": "Brazil",
    "brasile": "Brazil",
    "brésil": "Brazil",
    "brasil": "Brazil",
    "brasilien": "Brazil",
    # Argentinian variants
    "argentina": "Argentina",
    "argentine": "Argentina",
    "argentinien": "Argentina",
    # Peruvian variants
    "peru": "Peru",
    "perù": "Peru",
    "pérou": "Peru",
    # Chilean variants
    "chile": "Chile",
    "chili": "Chile",
    "cile": "Chile",
    # Colombian variants
    "colombia": "Colombia",
    "colombie": "Colombia",
    "kolumbien": "Colombia",
    # Turkish variants
    "turkey": "Turkey",
    "turchia": "Turkey",
    "turquie": "Turkey",
    "turquía": "Turkey",
    "türkei": "Turkey",
    # Lebanese variants
    "lebanon": "Lebanon",
    "libano": "Lebanon",
    "liban": "Lebanon",
    "líbano": "Lebanon",
    "libanon": "Lebanon",
    # Moroccan variants
    "morocco": "Morocco",
    "marocco": "Morocco",
    "maroc": "Morocco",
    "marruecos": "Morocco",
    "marokko": "Morocco",
    # Egyptian variants
    "egypt": "Egypt",
    "egitto": "Egypt",
    "égypte": "Egypt",
    "egipto": "Egypt",
    "ägypten": "Egypt",
    # Indonesian variants
    "indonesia": "Indonesia",
    "indonésie": "Indonesia",
    "indonesien": "Indonesia",
    # Malaysian variants
    "malaysia": "Malaysia",
    "malesia": "Malaysia",
    "malaisie": "Malaysia",
    "malasia": "Malaysia",
    # Australian variants
    "australia": "Australia",
    "australie": "Australia",
    "australien": "Australia",
    # Add more as needed...
}

# Map canonical countries to continents
COUNTRY_TO_CONTINENT = {
    # Europe
    "Italy": "Europe",
    "France": "France",  # Will be fixed to Europe
    "Spain": "Europe",
    "Germany": "Europe",
    "Portugal": "Europe",
    "Greece": "Europe",
    "United Kingdom": "Europe",
    "Ireland": "Europe",
    "Belgium": "Europe",
    "Netherlands": "Europe",
    "Switzerland": "Europe",
    "Austria": "Europe",
    "Poland": "Europe",
    "Czech Republic": "Europe",
    "Hungary": "Europe",
    "Romania": "Europe",
    "Bulgaria": "Europe",
    "Croatia": "Europe",
    "Slovenia": "Europe",
    "Slovakia": "Europe",
    "Serbia": "Europe",
    "Bosnia and Herzegovina": "Europe",
    "Montenegro": "Europe",
    "North Macedonia": "Europe",
    "Albania": "Europe",
    "Kosovo": "Europe",
    "Ukraine": "Europe",
    "Russia": "Europe",
    "Belarus": "Europe",
    "Moldova": "Europe",
    "Lithuania": "Europe",
    "Latvia": "Europe",
    "Estonia": "Europe",
    "Finland": "Europe",
    "Sweden": "Europe",
    "Norway": "Europe",
    "Denmark": "Europe",
    "Iceland": "Europe",
    "Malta": "Europe",
    "Cyprus": "Europe",
    "Luxembourg": "Europe",
    "Monaco": "Europe",
    "Andorra": "Europe",
    "San Marino": "Europe",
    "Vatican City": "Europe",
    "Liechtenstein": "Europe",
    
    # Americas
    "United States": "Americas",
    "Mexico": "Americas",
    "Canada": "Americas",
    "Brazil": "Americas",
    "Argentina": "Americas",
    "Peru": "Americas",
    "Chile": "Americas",
    "Colombia": "Americas",
    "Venezuela": "Americas",
    "Ecuador": "Americas",
    "Bolivia": "Americas",
    "Paraguay": "Americas",
    "Uruguay": "Americas",
    "Cuba": "Americas",
    "Dominican Republic": "Americas",
    "Puerto Rico": "Americas",
    "Jamaica": "Americas",
    "Haiti": "Americas",
    "Trinidad and Tobago": "Americas",
    "Guatemala": "Americas",
    "Honduras": "Americas",
    "El Salvador": "Americas",
    "Nicaragua": "Americas",
    "Costa Rica": "Americas",
    "Panama": "Americas",
    "Belize": "Americas",
    "Guyana": "Americas",
    "Suriname": "Americas",
    
    # Asia
    "Japan": "Asia",
    "China": "Asia",
    "India": "Asia",
    "Thailand": "Asia",
    "Vietnam": "Asia",
    "South Korea": "Asia",
    "North Korea": "Asia",
    "Indonesia": "Asia",
    "Malaysia": "Asia",
    "Philippines": "Asia",
    "Singapore": "Asia",
    "Taiwan": "Asia",
    "Hong Kong": "Asia",
    "Macau": "Asia",
    "Myanmar": "Asia",
    "Cambodia": "Asia",
    "Laos": "Asia",
    "Bangladesh": "Asia",
    "Pakistan": "Asia",
    "Sri Lanka": "Asia",
    "Nepal": "Asia",
    "Bhutan": "Asia",
    "Afghanistan": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Syria": "Asia",
    "Lebanon": "Asia",
    "Jordan": "Asia",
    "Israel": "Asia",
    "Palestine": "Asia",
    "Saudi Arabia": "Asia",
    "United Arab Emirates": "Asia",
    "Qatar": "Asia",
    "Kuwait": "Asia",
    "Bahrain": "Asia",
    "Oman": "Asia",
    "Yemen": "Asia",
    "Turkey": "Asia",
    "Armenia": "Asia",
    "Georgia": "Asia",
    "Azerbaijan": "Asia",
    "Kazakhstan": "Asia",
    "Uzbekistan": "Asia",
    "Turkmenistan": "Asia",
    "Tajikistan": "Asia",
    "Kyrgyzstan": "Asia",
    "Mongolia": "Asia",
    "Brunei": "Asia",
    "Timor-Leste": "Asia",
    "Maldives": "Asia",
    
    # Africa
    "Morocco": "Africa",
    "Egypt": "Africa",
    "Tunisia": "Africa",
    "Algeria": "Africa",
    "Libya": "Africa",
    "South Africa": "Africa",
    "Nigeria": "Africa",
    "Kenya": "Africa",
    "Ethiopia": "Africa",
    "Ghana": "Africa",
    "Senegal": "Africa",
    "Ivory Coast": "Africa",
    "Cameroon": "Africa",
    "Tanzania": "Africa",
    "Uganda": "Africa",
    "Rwanda": "Africa",
    "Zimbabwe": "Africa",
    "Zambia": "Africa",
    "Mozambique": "Africa",
    "Madagascar": "Africa",
    "Mauritius": "Africa",
    "Sudan": "Africa",
    "South Sudan": "Africa",
    "Mali": "Africa",
    "Niger": "Africa",
    "Chad": "Africa",
    "Burkina Faso": "Africa",
    "Benin": "Africa",
    "Togo": "Africa",
    "Liberia": "Africa",
    "Sierra Leone": "Africa",
    "Guinea": "Africa",
    "Guinea-Bissau": "Africa",
    "Gambia": "Africa",
    "Mauritania": "Africa",
    "Cape Verde": "Africa",
    "Sao Tome and Principe": "Africa",
    "Equatorial Guinea": "Africa",
    "Gabon": "Africa",
    "Congo": "Africa",
    "Democratic Republic of the Congo": "Africa",
    "Angola": "Africa",
    "Namibia": "Africa",
    "Botswana": "Africa",
    "Lesotho": "Africa",
    "Eswatini": "Africa",
    "Malawi": "Africa",
    "Comoros": "Africa",
    "Seychelles": "Africa",
    "Djibouti": "Africa",
    "Eritrea": "Africa",
    "Somalia": "Africa",
    "Central African Republic": "Africa",
    "Burundi": "Africa",
    
    # Oceania
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    "Fiji": "Oceania",
    "Papua New Guinea": "Oceania",
    "Samoa": "Oceania",
    "Tonga": "Oceania",
    "Vanuatu": "Oceania",
    "Solomon Islands": "Oceania",
    "Micronesia": "Oceania",
    "Palau": "Oceania",
    "Marshall Islands": "Oceania",
    "Kiribati": "Oceania",
    "Nauru": "Oceania",
    "Tuvalu": "Oceania",
    "Guam": "Oceania",
    "French Polynesia": "Oceania",
    "New Caledonia": "Oceania",
}

# Fix France -> Europe (typo in original)
COUNTRY_TO_CONTINENT["France"] = "Europe"

# Localized country labels for UI display
COUNTRY_LABELS = {
    "Italy": {"en": "Italy", "it": "Italia", "fr": "Italie", "es": "Italia", "de": "Italien"},
    "France": {"en": "France", "it": "Francia", "fr": "France", "es": "Francia", "de": "Frankreich"},
    "Spain": {"en": "Spain", "it": "Spagna", "fr": "Espagne", "es": "España", "de": "Spanien"},
    "Germany": {"en": "Germany", "it": "Germania", "fr": "Allemagne", "es": "Alemania", "de": "Deutschland"},
    "United Kingdom": {"en": "United Kingdom", "it": "Regno Unito", "fr": "Royaume-Uni", "es": "Reino Unido", "de": "Vereinigtes Königreich"},
    "United States": {"en": "United States", "it": "Stati Uniti", "fr": "États-Unis", "es": "Estados Unidos", "de": "Vereinigte Staaten"},
    "Mexico": {"en": "Mexico", "it": "Messico", "fr": "Mexique", "es": "México", "de": "Mexiko"},
    "Japan": {"en": "Japan", "it": "Giappone", "fr": "Japon", "es": "Japón", "de": "Japan"},
    "China": {"en": "China", "it": "Cina", "fr": "Chine", "es": "China", "de": "China"},
    "India": {"en": "India", "it": "India", "fr": "Inde", "es": "India", "de": "Indien"},
    "Thailand": {"en": "Thailand", "it": "Thailandia", "fr": "Thaïlande", "es": "Tailandia", "de": "Thailand"},
    "Vietnam": {"en": "Vietnam", "it": "Vietnam", "fr": "Viêt Nam", "es": "Vietnam", "de": "Vietnam"},
    "South Korea": {"en": "South Korea", "it": "Corea del Sud", "fr": "Corée du Sud", "es": "Corea del Sur", "de": "Südkorea"},
    "Greece": {"en": "Greece", "it": "Grecia", "fr": "Grèce", "es": "Grecia", "de": "Griechenland"},
    "Turkey": {"en": "Turkey", "it": "Turchia", "fr": "Turquie", "es": "Turquía", "de": "Türkei"},
    "Lebanon": {"en": "Lebanon", "it": "Libano", "fr": "Liban", "es": "Líbano", "de": "Libanon"},
    "Morocco": {"en": "Morocco", "it": "Marocco", "fr": "Maroc", "es": "Marruecos", "de": "Marokko"},
    "Egypt": {"en": "Egypt", "it": "Egitto", "fr": "Égypte", "es": "Egipto", "de": "Ägypten"},
    "Brazil": {"en": "Brazil", "it": "Brasile", "fr": "Brésil", "es": "Brasil", "de": "Brasilien"},
    "Argentina": {"en": "Argentina", "it": "Argentina", "fr": "Argentine", "es": "Argentina", "de": "Argentinien"},
    "Peru": {"en": "Peru", "it": "Perù", "fr": "Pérou", "es": "Perú", "de": "Peru"},
    "Chile": {"en": "Chile", "it": "Cile", "fr": "Chili", "es": "Chile", "de": "Chile"},
    "Colombia": {"en": "Colombia", "it": "Colombia", "fr": "Colombie", "es": "Colombia", "de": "Kolumbien"},
    "Portugal": {"en": "Portugal", "it": "Portogallo", "fr": "Portugal", "es": "Portugal", "de": "Portugal"},
    "Indonesia": {"en": "Indonesia", "it": "Indonesia", "fr": "Indonésie", "es": "Indonesia", "de": "Indonesien"},
    "Malaysia": {"en": "Malaysia", "it": "Malesia", "fr": "Malaisie", "es": "Malasia", "de": "Malaysia"},
    "Australia": {"en": "Australia", "it": "Australia", "fr": "Australie", "es": "Australia", "de": "Australien"},
    # Add more as needed
}


def normalize_country(country_value: str) -> str:
    """
    Normalize a country name to canonical English.
    Returns the original if no normalization found.
    """
    if not country_value:
        return ""
    
    # Check if already canonical
    if country_value in COUNTRY_TO_CONTINENT:
        return country_value
    
    # Try lowercase lookup
    lookup = country_value.lower().strip()
    if lookup in COUNTRY_NORMALIZATION:
        return COUNTRY_NORMALIZATION[lookup]
    
    # Try title case as-is (might already be correct)
    title_case = country_value.strip().title()
    if title_case in COUNTRY_TO_CONTINENT:
        return title_case
    
    # Return original if no match
    return country_value


def get_continent(country: str) -> str:
    """Get continent for a canonical country name."""
    canonical = normalize_country(country)
    return COUNTRY_TO_CONTINENT.get(canonical, "")


def get_localized_country_label(canonical_country: str, language: str = "en") -> str:
    """Get localized display label for a country."""
    if canonical_country in COUNTRY_LABELS:
        return COUNTRY_LABELS[canonical_country].get(language, canonical_country)
    return canonical_country


def is_valid_country(country_value: str) -> bool:
    """Check if a country value is valid (canonical or normalizable)."""
    if not country_value:
        return False
    canonical = normalize_country(country_value)
    return canonical in COUNTRY_TO_CONTINENT
