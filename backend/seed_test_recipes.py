# Seed Test Recipes for Sous-Chef Linguine
# This creates realistic test data for rankings and UI testing

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Test recipes data - diverse global recipes with ratings
TEST_RECIPES = [
    # Italian
    {
        "recipe_name": "Spaghetti alla Carbonara",
        "origin_country": "Italy",
        "origin_region": "Lazio",
        "origin_language": "it",
        "continent": "Europe",
        "authenticity_level": 1,
        "history_summary": "A Roman pasta dish documented by traditional institutions and rooted in mid-20th-century Lazio. The creamy sauce comes from eggs and cheese, never cream.",
        "characteristic_profile": "Rich, salty, creamy texture with smoky guanciale and sharp pecorino romano.",
        "no_no_rules": ["Never use cream", "Never use garlic or onion", "Must use guanciale, not pancetta or bacon"],
        "special_techniques": ["Mantecatura (creaming with pasta water off heat)"],
        "ingredients": [
            {"item": "Spaghetti", "amount": "380", "unit": "g", "notes": ""},
            {"item": "Guanciale", "amount": "150", "unit": "g", "notes": "cut into strips"},
            {"item": "Egg yolks", "amount": "4", "unit": "", "notes": ""},
            {"item": "Whole egg", "amount": "1", "unit": "", "notes": ""},
            {"item": "Pecorino Romano", "amount": "100", "unit": "g", "notes": "finely grated"},
            {"item": "Black pepper", "amount": "to taste", "unit": "", "notes": "freshly ground"}
        ],
        "instructions": [
            "Cook the guanciale in a cold pan until crispy and golden.",
            "Mix egg yolks, whole egg, pecorino, and generous black pepper in a bowl.",
            "Cook spaghetti in salted water until al dente.",
            "Reserve pasta water, then combine hot pasta with guanciale off heat.",
            "Add egg mixture and toss vigorously, using pasta water to create creamy sauce.",
            "Serve immediately with extra pecorino and pepper."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Frascati Superiore DOCG", "region": "Lazio", "reason": "High acidity cuts through egg and guanciale richness"},
                {"name": "Verdicchio dei Castelli di Jesi DOC", "region": "Marche", "reason": "Fresh, mineral white balancing salt and fat"}
            ],
            "notes": "Central Italian whites are classic; light reds also work if not oaky."
        },
        "average_rating": 4.9,
        "ratings_count": 156,
        "favorites_count": 89
    },
    {
        "recipe_name": "Risotto alla Milanese",
        "origin_country": "Italy",
        "origin_region": "Lombardy",
        "origin_language": "it",
        "continent": "Europe",
        "authenticity_level": 1,
        "history_summary": "A golden saffron risotto from Milan, traditionally served as accompaniment to Ossobuco. Dating back to the 16th century.",
        "characteristic_profile": "Luxuriously creamy with delicate saffron aroma and rich butter finish.",
        "no_no_rules": ["Never use pre-ground saffron", "Must use carnaroli or arborio rice", "Never rush the cooking"],
        "special_techniques": ["Tostatura (toasting rice)", "Adding broth one ladle at a time"],
        "ingredients": [
            {"item": "Carnaroli rice", "amount": "320", "unit": "g", "notes": ""},
            {"item": "Saffron threads", "amount": "0.5", "unit": "g", "notes": "steeped in warm broth"},
            {"item": "Beef broth", "amount": "1.2", "unit": "L", "notes": "kept warm"},
            {"item": "Butter", "amount": "80", "unit": "g", "notes": "cold, cubed"},
            {"item": "Parmigiano Reggiano", "amount": "60", "unit": "g", "notes": "grated"},
            {"item": "White onion", "amount": "1", "unit": "small", "notes": "finely diced"}
        ],
        "instructions": [
            "Sauté onion in butter until translucent.",
            "Toast rice until edges are transparent.",
            "Add warm broth one ladle at a time, stirring constantly.",
            "After 15 minutes, add saffron-infused broth.",
            "When rice is al dente, remove from heat.",
            "Vigorously stir in cold butter and parmesan (mantecatura).",
            "Rest 2 minutes, then serve."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Franciacorta Brut", "region": "Lombardy", "reason": "Local sparkling wine cuts through richness"}
            ],
            "notes": "Lombard wines pair naturally with this regional classic."
        },
        "average_rating": 4.8,
        "ratings_count": 98,
        "favorites_count": 67
    },
    {
        "recipe_name": "Pizza Margherita",
        "origin_country": "Italy",
        "origin_region": "Campania",
        "origin_language": "it",
        "continent": "Europe",
        "authenticity_level": 1,
        "history_summary": "Created in 1889 in Naples to honor Queen Margherita, featuring the colors of the Italian flag.",
        "characteristic_profile": "Charred, pillowy crust with sweet San Marzano tomatoes and creamy mozzarella.",
        "no_no_rules": ["Never use pre-shredded cheese", "Must use San Marzano tomatoes", "Dough must ferment 24+ hours"],
        "special_techniques": ["Long cold fermentation", "High-heat wood-fired baking"],
        "ingredients": [
            {"item": "00 flour", "amount": "500", "unit": "g", "notes": ""},
            {"item": "San Marzano tomatoes", "amount": "400", "unit": "g", "notes": "crushed by hand"},
            {"item": "Fresh mozzarella", "amount": "250", "unit": "g", "notes": "torn"},
            {"item": "Fresh basil", "amount": "10", "unit": "leaves", "notes": ""},
            {"item": "Extra virgin olive oil", "amount": "2", "unit": "tbsp", "notes": ""}
        ],
        "instructions": [
            "Mix flour, water, salt, and yeast. Knead until smooth.",
            "Cold ferment for 24-72 hours.",
            "Shape dough by hand, leaving edges thick.",
            "Spread crushed tomatoes, leaving border.",
            "Bake at highest oven temperature until charred spots appear.",
            "Add mozzarella, return to oven briefly.",
            "Finish with fresh basil and olive oil."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Lacryma Christi del Vesuvio", "region": "Campania", "reason": "Local volcanic wine with bright acidity"}
            ],
            "notes": "Neapolitan wines complement the local cuisine."
        },
        "average_rating": 4.7,
        "ratings_count": 234,
        "favorites_count": 145
    },
    # Japanese
    {
        "recipe_name": "Tonkotsu Ramen",
        "origin_country": "Japan",
        "origin_region": "Kyushu",
        "origin_language": "ja",
        "continent": "Asia",
        "authenticity_level": 2,
        "history_summary": "Born in Fukuoka in the 1940s, this pork bone broth ramen became the signature dish of Hakata.",
        "characteristic_profile": "Milky, collagen-rich broth with thin noodles and tender chashu.",
        "no_no_rules": ["Broth must simmer 12+ hours", "Noodles must be thin and straight"],
        "special_techniques": ["Continuous rolling boil for emulsification", "Kaedama (noodle refill)"],
        "ingredients": [
            {"item": "Pork bones", "amount": "2", "unit": "kg", "notes": "femur and neck bones"},
            {"item": "Thin ramen noodles", "amount": "400", "unit": "g", "notes": ""},
            {"item": "Chashu pork belly", "amount": "300", "unit": "g", "notes": "braised"},
            {"item": "Green onions", "amount": "4", "unit": "stalks", "notes": "thinly sliced"},
            {"item": "Soft-boiled eggs", "amount": "2", "unit": "", "notes": "marinated"}
        ],
        "instructions": [
            "Blanch pork bones, then scrub clean.",
            "Boil bones vigorously for 12-18 hours, adding water as needed.",
            "Strain and season broth with tare.",
            "Cook noodles for 30 seconds only.",
            "Assemble: broth, noodles, chashu, egg, green onions."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Junmai Sake", "region": "Japan", "reason": "Clean rice wine complements rich pork broth"}
            ],
            "notes": "Beer or sake preferred over wine."
        },
        "average_rating": 4.8,
        "ratings_count": 187,
        "favorites_count": 112
    },
    {
        "recipe_name": "Sushi Nigiri",
        "origin_country": "Japan",
        "origin_region": "Tokyo",
        "origin_language": "ja",
        "continent": "Asia",
        "authenticity_level": 1,
        "history_summary": "Edomae sushi originated in Tokyo Bay, using local fish and seasoned rice.",
        "characteristic_profile": "Perfect balance of vinegared rice and fresh fish, eaten in one bite.",
        "no_no_rules": ["Rice must be body temperature", "Never dip rice in soy sauce", "Eat within seconds of serving"],
        "special_techniques": ["Proper rice seasoning", "Hand-forming technique"],
        "ingredients": [
            {"item": "Sushi rice", "amount": "300", "unit": "g", "notes": "short-grain"},
            {"item": "Rice vinegar", "amount": "45", "unit": "ml", "notes": ""},
            {"item": "Fresh tuna", "amount": "200", "unit": "g", "notes": "sashimi grade"},
            {"item": "Wasabi", "amount": "10", "unit": "g", "notes": "freshly grated"}
        ],
        "instructions": [
            "Cook rice and season with vinegar mixture while hot.",
            "Cool rice to body temperature.",
            "Slice fish against the grain.",
            "Form rice into oval shape with wet hands.",
            "Add dab of wasabi, press fish on top.",
            "Serve immediately."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Daiginjo Sake", "region": "Japan", "reason": "Premium sake enhances delicate fish"}
            ],
            "notes": "Japanese beverages preferred."
        },
        "average_rating": 4.6,
        "ratings_count": 145,
        "favorites_count": 78
    },
    # French
    {
        "recipe_name": "Coq au Vin",
        "origin_country": "France",
        "origin_region": "Burgundy",
        "origin_language": "fr",
        "continent": "Europe",
        "authenticity_level": 2,
        "history_summary": "A rustic Burgundian dish of chicken braised in red wine, elevated by Julia Child to American fame.",
        "characteristic_profile": "Deeply savory with wine-enriched sauce and aromatic vegetables.",
        "no_no_rules": ["Must use good quality Burgundy wine", "Never skip the flambé step"],
        "special_techniques": ["Flambéing with cognac", "Long braising"],
        "ingredients": [
            {"item": "Chicken", "amount": "1.5", "unit": "kg", "notes": "cut into pieces"},
            {"item": "Burgundy wine", "amount": "750", "unit": "ml", "notes": "1 bottle"},
            {"item": "Lardons", "amount": "150", "unit": "g", "notes": ""},
            {"item": "Pearl onions", "amount": "20", "unit": "", "notes": "peeled"},
            {"item": "Mushrooms", "amount": "250", "unit": "g", "notes": "quartered"}
        ],
        "instructions": [
            "Marinate chicken in wine overnight.",
            "Brown chicken pieces and flambé with cognac.",
            "Sauté lardons, onions, and mushrooms separately.",
            "Braise chicken in marinade for 1.5 hours.",
            "Reduce sauce and add garnishes."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Burgundy Pinot Noir", "region": "Burgundy", "reason": "Same wine used in cooking creates harmony"}
            ],
            "notes": "Use the same wine for cooking and drinking."
        },
        "average_rating": 4.7,
        "ratings_count": 89,
        "favorites_count": 56
    },
    {
        "recipe_name": "Bouillabaisse",
        "origin_country": "France",
        "origin_region": "Provence",
        "origin_language": "fr",
        "continent": "Europe",
        "authenticity_level": 1,
        "history_summary": "A fisherman's stew from Marseille, protected by a charter defining authentic ingredients.",
        "characteristic_profile": "Saffron-scented broth with diverse Mediterranean fish and rouille.",
        "no_no_rules": ["Must include at least 4 types of local fish", "Never use salmon or freshwater fish"],
        "special_techniques": ["Sequential fish addition by firmness", "Emulsified rouille"],
        "ingredients": [
            {"item": "Mixed Mediterranean fish", "amount": "1.5", "unit": "kg", "notes": "scorpionfish, John Dory, monkfish"},
            {"item": "Saffron", "amount": "1", "unit": "g", "notes": ""},
            {"item": "Tomatoes", "amount": "400", "unit": "g", "notes": "crushed"},
            {"item": "Fennel", "amount": "1", "unit": "bulb", "notes": "sliced"},
            {"item": "Pastis", "amount": "50", "unit": "ml", "notes": ""}
        ],
        "instructions": [
            "Make fish stock from bones and heads.",
            "Sauté fennel, onion, tomatoes with saffron.",
            "Add stock and bring to vigorous boil.",
            "Add firm fish first, then delicate fish.",
            "Serve broth separately with rouille and croutons."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Cassis Blanc", "region": "Provence", "reason": "Local white wine from nearby Cassis"}
            ],
            "notes": "Provençal rosé also works beautifully."
        },
        "average_rating": 4.5,
        "ratings_count": 67,
        "favorites_count": 45
    },
    # Mexican
    {
        "recipe_name": "Mole Poblano",
        "origin_country": "Mexico",
        "origin_region": "Puebla",
        "origin_language": "es",
        "continent": "Americas",
        "authenticity_level": 1,
        "history_summary": "A complex sauce with pre-Hispanic roots, featuring over 20 ingredients including chocolate and multiple chilies.",
        "characteristic_profile": "Deep, complex sauce with subtle chocolate, warm spices, and mild heat.",
        "no_no_rules": ["Never use cocoa powder, only Mexican chocolate", "Must toast and grind spices fresh"],
        "special_techniques": ["Toasting and rehydrating chilies", "Building sauce in stages"],
        "ingredients": [
            {"item": "Dried mulato chilies", "amount": "4", "unit": "", "notes": ""},
            {"item": "Dried ancho chilies", "amount": "4", "unit": "", "notes": ""},
            {"item": "Mexican chocolate", "amount": "50", "unit": "g", "notes": ""},
            {"item": "Chicken", "amount": "1.5", "unit": "kg", "notes": ""},
            {"item": "Sesame seeds", "amount": "50", "unit": "g", "notes": "toasted"}
        ],
        "instructions": [
            "Toast and rehydrate dried chilies.",
            "Blend chilies with tomatoes, onion, garlic.",
            "Toast and grind spices and nuts.",
            "Fry paste in lard, simmer with broth.",
            "Add chocolate at the end.",
            "Simmer chicken in mole sauce."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Zinfandel", "region": "California", "reason": "Fruit-forward wine matches complex spices"}
            ],
            "notes": "Mexican beer or mezcal are traditional alternatives."
        },
        "average_rating": 4.9,
        "ratings_count": 123,
        "favorites_count": 98
    },
    {
        "recipe_name": "Tacos al Pastor",
        "origin_country": "Mexico",
        "origin_region": "Mexico City",
        "origin_language": "es",
        "continent": "Americas",
        "authenticity_level": 2,
        "history_summary": "Influenced by Lebanese immigrants' shawarma, transformed into a Mexican icon with adobo and pineapple.",
        "characteristic_profile": "Smoky, sweet, tangy pork with charred pineapple and fresh cilantro.",
        "no_no_rules": ["Must be cooked on vertical spit", "Pineapple is essential"],
        "special_techniques": ["Vertical spit roasting", "Adobo marination"],
        "ingredients": [
            {"item": "Pork shoulder", "amount": "1", "unit": "kg", "notes": "thinly sliced"},
            {"item": "Achiote paste", "amount": "100", "unit": "g", "notes": ""},
            {"item": "Pineapple", "amount": "1", "unit": "", "notes": ""},
            {"item": "Corn tortillas", "amount": "16", "unit": "", "notes": "small"},
            {"item": "White onion", "amount": "1", "unit": "", "notes": "diced"}
        ],
        "instructions": [
            "Marinate pork in adobo overnight.",
            "Stack marinated pork on vertical spit with pineapple on top.",
            "Roast slowly, shaving off cooked exterior.",
            "Warm tortillas on griddle.",
            "Serve with pineapple, onion, cilantro, salsa verde."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Gewürztraminer", "region": "Alsace", "reason": "Sweet spice complements achiote and pineapple"}
            ],
            "notes": "Mexican lager or agua fresca preferred."
        },
        "average_rating": 4.8,
        "ratings_count": 201,
        "favorites_count": 156
    },
    # Indian
    {
        "recipe_name": "Butter Chicken",
        "origin_country": "India",
        "origin_region": "Delhi",
        "origin_language": "hi",
        "continent": "Asia",
        "authenticity_level": 2,
        "history_summary": "Invented at Moti Mahal restaurant in Delhi in the 1950s, using leftover tandoori chicken.",
        "characteristic_profile": "Velvety tomato-cream sauce with tender tandoori chicken and warm spices.",
        "no_no_rules": ["Chicken must be tandoori-style first", "Never use cream powder"],
        "special_techniques": ["Tandoori marination", "Kasuri methi finishing"],
        "ingredients": [
            {"item": "Chicken thighs", "amount": "800", "unit": "g", "notes": "boneless"},
            {"item": "Yogurt", "amount": "200", "unit": "g", "notes": "for marinade"},
            {"item": "Tomato puree", "amount": "400", "unit": "g", "notes": ""},
            {"item": "Heavy cream", "amount": "200", "unit": "ml", "notes": ""},
            {"item": "Kasuri methi", "amount": "2", "unit": "tbsp", "notes": "dried fenugreek leaves"}
        ],
        "instructions": [
            "Marinate chicken in yogurt and spices.",
            "Grill or broil chicken until charred.",
            "Make sauce with tomatoes, butter, spices.",
            "Add cream and simmer.",
            "Add chicken and kasuri methi.",
            "Finish with butter."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Off-dry Riesling", "region": "Germany", "reason": "Slight sweetness balances spices"}
            ],
            "notes": "Lassi or mango juice are traditional."
        },
        "average_rating": 4.6,
        "ratings_count": 178,
        "favorites_count": 134
    },
    # Thai
    {
        "recipe_name": "Pad Thai",
        "origin_country": "Thailand",
        "origin_region": "Central Thailand",
        "origin_language": "th",
        "continent": "Asia",
        "authenticity_level": 2,
        "history_summary": "A national dish promoted by the Thai government in the 1930s-40s as a symbol of Thai identity.",
        "characteristic_profile": "Sweet, sour, salty, and savory with chewy rice noodles and crunchy peanuts.",
        "no_no_rules": ["Must use tamarind, not ketchup", "Noodles must not be mushy"],
        "special_techniques": ["High heat wok tossing", "Balancing the four flavors"],
        "ingredients": [
            {"item": "Rice noodles", "amount": "200", "unit": "g", "notes": "flat, medium width"},
            {"item": "Tamarind paste", "amount": "3", "unit": "tbsp", "notes": ""},
            {"item": "Palm sugar", "amount": "2", "unit": "tbsp", "notes": ""},
            {"item": "Shrimp", "amount": "200", "unit": "g", "notes": ""},
            {"item": "Roasted peanuts", "amount": "50", "unit": "g", "notes": "crushed"}
        ],
        "instructions": [
            "Soak noodles until pliable but not soft.",
            "Make sauce: tamarind, palm sugar, fish sauce.",
            "Stir-fry shrimp and tofu at high heat.",
            "Add noodles and sauce, toss quickly.",
            "Push aside, scramble eggs, mix together.",
            "Serve with peanuts, bean sprouts, lime."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Torrontés", "region": "Argentina", "reason": "Aromatic wine matches Thai flavors"}
            ],
            "notes": "Thai iced tea or Singha beer preferred."
        },
        "average_rating": 4.5,
        "ratings_count": 156,
        "favorites_count": 98
    },
    # Spanish
    {
        "recipe_name": "Paella Valenciana",
        "origin_country": "Spain",
        "origin_region": "Valencia",
        "origin_language": "es",
        "continent": "Europe",
        "authenticity_level": 1,
        "history_summary": "The original paella from Valencia traditionally contains rabbit, chicken, and snails - never seafood.",
        "characteristic_profile": "Smoky socarrat crust with saffron rice and tender meat.",
        "no_no_rules": ["Traditional Valenciana has NO seafood", "Never stir the rice", "Must develop socarrat"],
        "special_techniques": ["Developing socarrat (crispy bottom)", "Cooking over wood fire"],
        "ingredients": [
            {"item": "Bomba rice", "amount": "400", "unit": "g", "notes": ""},
            {"item": "Rabbit", "amount": "500", "unit": "g", "notes": "cut into pieces"},
            {"item": "Chicken", "amount": "500", "unit": "g", "notes": "cut into pieces"},
            {"item": "Green beans", "amount": "200", "unit": "g", "notes": "flat, Valencian style"},
            {"item": "Saffron", "amount": "1", "unit": "g", "notes": ""}
        ],
        "instructions": [
            "Brown meat in olive oil in paella pan.",
            "Add vegetables and cook until caramelized.",
            "Add tomato and paprika, cook briefly.",
            "Add water and simmer to make broth.",
            "Add rice and saffron, distribute evenly.",
            "Cook without stirring until socarrat forms.",
            "Rest 5 minutes before serving."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Monastrell", "region": "Valencia", "reason": "Local red grape complements smoky flavors"}
            ],
            "notes": "Valencian wines are the natural pairing."
        },
        "average_rating": 4.7,
        "ratings_count": 134,
        "favorites_count": 87
    },
    # Moroccan
    {
        "recipe_name": "Tagine of Lamb",
        "origin_country": "Morocco",
        "origin_region": "Marrakech",
        "origin_language": "ar",
        "continent": "Africa",
        "authenticity_level": 2,
        "history_summary": "Named after the conical clay pot, this slow-cooked dish showcases Moroccan spice mastery.",
        "characteristic_profile": "Fall-apart tender lamb with sweet dried fruit and aromatic spices.",
        "no_no_rules": ["Must use preserved lemons", "Cooking must be slow"],
        "special_techniques": ["Cooking in tagine pot", "Layering spices"],
        "ingredients": [
            {"item": "Lamb shoulder", "amount": "1", "unit": "kg", "notes": "cubed"},
            {"item": "Dried apricots", "amount": "150", "unit": "g", "notes": ""},
            {"item": "Preserved lemons", "amount": "2", "unit": "", "notes": ""},
            {"item": "Ras el hanout", "amount": "2", "unit": "tbsp", "notes": ""},
            {"item": "Honey", "amount": "3", "unit": "tbsp", "notes": ""}
        ],
        "instructions": [
            "Season lamb with ras el hanout.",
            "Brown lamb in tagine base.",
            "Add onions, garlic, ginger.",
            "Add water and simmer 1.5 hours.",
            "Add apricots and preserved lemons.",
            "Cook 30 more minutes.",
            "Drizzle with honey, garnish with almonds."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Grenache", "region": "Rhône", "reason": "Fruit-forward red complements sweet spices"}
            ],
            "notes": "Moroccan mint tea is traditional."
        },
        "average_rating": 4.6,
        "ratings_count": 78,
        "favorites_count": 54
    },
    # Greek
    {
        "recipe_name": "Moussaka",
        "origin_country": "Greece",
        "origin_region": "Athens",
        "origin_language": "el",
        "continent": "Europe",
        "authenticity_level": 2,
        "history_summary": "Modern Greek moussaka was codified by chef Nikolaos Tselementes in the 1920s with béchamel.",
        "characteristic_profile": "Layers of silky eggplant, spiced meat sauce, and creamy béchamel.",
        "no_no_rules": ["Eggplant must be salted and drained", "Béchamel must be thick"],
        "special_techniques": ["Salting eggplant", "Proper béchamel"],
        "ingredients": [
            {"item": "Eggplant", "amount": "3", "unit": "large", "notes": "sliced"},
            {"item": "Ground lamb", "amount": "500", "unit": "g", "notes": ""},
            {"item": "Tomato sauce", "amount": "400", "unit": "g", "notes": ""},
            {"item": "Béchamel sauce", "amount": "500", "unit": "ml", "notes": "thick"},
            {"item": "Cinnamon", "amount": "1", "unit": "tsp", "notes": ""}
        ],
        "instructions": [
            "Salt and drain eggplant slices 30 minutes.",
            "Fry or grill eggplant until golden.",
            "Make meat sauce with lamb, tomatoes, cinnamon.",
            "Make thick béchamel with egg yolks.",
            "Layer: eggplant, meat, eggplant, béchamel.",
            "Bake until golden brown.",
            "Rest 15 minutes before cutting."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Xinomavro", "region": "Macedonia, Greece", "reason": "Greek red with good tannins"}
            ],
            "notes": "Greek wines complement Greek cuisine."
        },
        "average_rating": 4.4,
        "ratings_count": 92,
        "favorites_count": 61
    },
    # Lebanese
    {
        "recipe_name": "Hummus",
        "origin_country": "Lebanon",
        "origin_region": "Beirut",
        "origin_language": "ar",
        "continent": "Middle East",
        "authenticity_level": 2,
        "history_summary": "A Levantine staple made from chickpeas, enjoyed across the Middle East for centuries.",
        "characteristic_profile": "Silky smooth with bright tahini and lemon, finished with olive oil.",
        "no_no_rules": ["Must remove chickpea skins for smooth texture", "Never skip the tahini"],
        "special_techniques": ["Removing chickpea skins", "Blending while hot"],
        "ingredients": [
            {"item": "Chickpeas", "amount": "400", "unit": "g", "notes": "dried, soaked overnight"},
            {"item": "Tahini", "amount": "100", "unit": "g", "notes": "quality"},
            {"item": "Lemon juice", "amount": "60", "unit": "ml", "notes": "fresh"},
            {"item": "Garlic", "amount": "2", "unit": "cloves", "notes": ""},
            {"item": "Olive oil", "amount": "50", "unit": "ml", "notes": "extra virgin"}
        ],
        "instructions": [
            "Cook soaked chickpeas until very soft.",
            "Remove skins by rubbing in water.",
            "Blend tahini and lemon juice first until white.",
            "Add hot chickpeas and blend until silky.",
            "Season with salt and garlic.",
            "Serve with olive oil and paprika."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Lebanese White", "region": "Bekaa Valley", "reason": "Local wine with citrus notes"}
            ],
            "notes": "Arak is the traditional pairing."
        },
        "average_rating": 4.3,
        "ratings_count": 145,
        "favorites_count": 89
    },
    # Australian
    {
        "recipe_name": "Meat Pie",
        "origin_country": "Australia",
        "origin_region": "Melbourne",
        "origin_language": "en",
        "continent": "Oceania",
        "authenticity_level": 2,
        "history_summary": "The iconic Australian meat pie is a handheld classic, best from bakeries across the country.",
        "characteristic_profile": "Flaky pastry encasing rich, gravy-laden minced beef.",
        "no_no_rules": ["Filling must be gravy-based, not dry", "Top must be puff pastry"],
        "special_techniques": ["Proper gravy consistency", "Crimping edges"],
        "ingredients": [
            {"item": "Beef mince", "amount": "500", "unit": "g", "notes": ""},
            {"item": "Beef stock", "amount": "300", "unit": "ml", "notes": ""},
            {"item": "Shortcrust pastry", "amount": "300", "unit": "g", "notes": "for base"},
            {"item": "Puff pastry", "amount": "200", "unit": "g", "notes": "for top"},
            {"item": "Worcestershire sauce", "amount": "2", "unit": "tbsp", "notes": ""}
        ],
        "instructions": [
            "Brown mince with onion.",
            "Add stock and Worcestershire, simmer until thick.",
            "Cool filling completely.",
            "Line pie tins with shortcrust.",
            "Fill and top with puff pastry.",
            "Egg wash and bake until golden."
        ],
        "wine_pairing": {
            "recommended_wines": [
                {"name": "Shiraz", "region": "Barossa Valley", "reason": "Bold Australian red for meat pie"}
            ],
            "notes": "Best with tomato sauce on top."
        },
        "average_rating": 4.2,
        "ratings_count": 67,
        "favorites_count": 34
    }
]


async def seed_recipes():
    """Seed test recipes into the database."""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    print("🍝 Seeding test recipes for Sous-Chef Linguine...")
    
    inserted = 0
    skipped = 0
    
    for recipe in TEST_RECIPES:
        # Generate slug
        slug = f"{recipe['recipe_name'].lower().replace(' ', '-')}-{recipe['origin_country'].lower()}"
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Check if exists
        existing = await db.recipes.find_one({"slug": slug})
        if existing:
            print(f"  ⏭️  Skipping {recipe['recipe_name']} (already exists)")
            skipped += 1
            continue
        
        # Build full recipe document
        recipe_doc = {
            **recipe,
            "slug": slug,
            "date_fetched": datetime.now(timezone.utc).isoformat(),
            "gpt_used": "Test Data (Sous-Chef Linguine)",
            "collection_method": "test_seed",
            "status": "published",
            "photos": [],
            "youtube_links": [],
            "original_source_urls": [],
            "views_count": random.randint(100, 1000),
            "comments_count": random.randint(5, 50),
            "verifications_count": random.randint(10, 100),
            "community_badge": None
        }
        
        await db.recipes.insert_one(recipe_doc)
        print(f"  ✅ Added: {recipe['recipe_name']} ({recipe['origin_country']})")
        inserted += 1
    
    print(f"\n✨ Seeding complete: {inserted} added, {skipped} skipped")
    
    # Print summary by continent
    print("\n📊 Recipes by Continent:")
    pipeline = [
        {"$group": {"_id": "$continent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    async for doc in db.recipes.aggregate(pipeline):
        print(f"  • {doc['_id']}: {doc['count']} recipes")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_recipes())
