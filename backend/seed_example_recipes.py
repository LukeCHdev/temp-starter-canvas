# Seed example recipes in Sous Chef Linguini format

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Example recipes in Sous Chef Linguini format
EXAMPLE_RECIPES = [
    {
        "slug": "melanzane-a-pullastiello-italy",
        "title_original": "Melanzane a Pullastiello",
        "title_translated": {
            "en": "Eggplants Pullastiello Style",
            "it": "Melanzane a Pullastiello",
            "es": "Berenjenas al Estilo Pullastiello",
            "fr": "Aubergines à la Pullastiello"
        },
        "country": "Italy",
        "region": "Mediterranean",
        "original_language": "it",
        "original_country_domain": ".it",
        "source_validation": {
            "official_source": False,
            "native_language_validated": True,
            "country_domain_validated": True,
            "validation_notes": "Traditional Neapolitan recipe, documented in local culinary archives",
            "authenticity_rank": 2
        },
        "source_references": [
            {
                "source_type": "traditional",
                "url": "https://www.cucinanapoletana.it",
                "description": "Archivi gastronomici napoletani",
                "language": "it",
                "domain": ".it"
            }
        ],
        "origin_story": "Ahhh… le melanzane a pullastiello! Una vera gemma della cucina napoletana tradizionale, rustica e saporita, oggi quasi scomparsa dalle tavole, ma amata da chi conosce le ricette popolari veraci. Una preparazione antica della cucina partenopea, diffusa soprattutto tra le famiglie popolari napoletane, che richiama il modo di cucinare tipico del pollo 'pullastiello' (cioè 'piccolo pollo') ripieno e stufato lentamente con pomodoro, formaggio e basilico, ma... al posto del pollo si usano le melanzane!",
        "cultural_background": "Il nome 'pullastiello' richiama la cucina povera: si imitava il pollo ripieno usando ingredienti vegetariani più economici. Un piatto vegetariano, ricco, cremoso, straordinariamente profumato che rappresenta l'ingegnosità della cucina napoletana popolare.",
        "authenticity_levels": [
            {
                "level": 2,
                "classification": "Traditional / Historical / Local Certified",
                "ingredients": [
                    {"item": "Melanzane viola grandi", "amount": 2, "unit": "pz", "unit_metric": "2 pz", "unit_imperial": "2 pieces", "notes": "meglio se tonde"},
                    {"item": "Fiordilatte", "amount": 200, "unit": "g", "unit_metric": "200g", "unit_imperial": "7oz", "notes": "ben scolato e tagliato a cubetti"},
                    {"item": "Uova", "amount": 2, "unit": "pz", "unit_metric": "2 pz", "unit_imperial": "2 eggs", "notes": ""},
                    {"item": "Parmigiano grattugiato", "amount": 100, "unit": "g", "unit_metric": "100g", "unit_imperial": "3.5oz", "notes": ""},
                    {"item": "Passata di pomodoro", "amount": 200, "unit": "g", "unit_metric": "200g", "unit_imperial": "7oz", "notes": ""},
                    {"item": "Aglio", "amount": 1, "unit": "spicchio", "unit_metric": "1 spicchio", "unit_imperial": "1 clove", "notes": ""},
                    {"item": "Basilico fresco", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                    {"item": "Pangrattato", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                    {"item": "Farina 00", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                    {"item": "Olio EVO", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                    {"item": "Olio di semi per friggere", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                    {"item": "Sale e pepe", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""}
                ],
                "method": [
                    {"step_number": 1, "instruction": "Lava e taglia le melanzane a fette spesse circa 1 cm. Cospargile di sale grosso e lasciale spurgare per 30 min in uno scolapasta. Sciacquale e asciugale bene.", "timing": "30 min", "temperature": None},
                    {"step_number": 2, "instruction": "Passa ogni fetta prima nella farina, poi nell'uovo sbattuto con un pizzico di sale e pepe, infine nel pangrattato. Friggile in olio di semi ben caldo finché dorate, poi scolale su carta assorbente.", "timing": "10-15 min", "temperature": {"celsius": 180, "fahrenheit": 356}},
                    {"step_number": 3, "instruction": "In una padella scalda olio EVO con uno spicchio d'aglio. Aggiungi la passata di pomodoro, un pizzico di sale e lascia cuocere per 10–15 minuti. Aggiungi qualche foglia di basilico fresco a fine cottura.", "timing": "15 min", "temperature": None},
                    {"step_number": 4, "instruction": "In una pirofila fai strati: salsa di pomodoro, melanzane, fiordilatte, parmigiano. Ripeti fino a esaurire gli ingredienti.", "timing": "5 min", "temperature": None},
                    {"step_number": 5, "instruction": "Cuoci in forno a 180°C per 20 minuti, finché la superficie è ben gratinata e il formaggio fuso.", "timing": "20 min", "temperature": {"celsius": 180, "fahrenheit": 356}}
                ],
                "differences": "Versione tradizionale napoletana della cucina povera",
                "cultural_explanation": "Rappresenta l'ingegnosità della cucina napoletana nel creare piatti vegetariani ricchi imitando preparazioni di carne"
            }
        ],
        "tools_techniques": ["Padella grande per friggere", "Pirofila da forno", "Carta assorbente", "Coltello affilato", "Ciotole per impanatura"],
        "notes": [
            "Il nome 'pullastiello' richiama la cucina povera: si imitava il pollo ripieno usando ingredienti vegetariani più economici",
            "Se vuoi una versione più ricca, puoi aggiungere salame napoletano a dadini o uova sode tra gli strati",
            "Perfetto da mangiare anche freddo il giorno dopo"
        ],
        "substitutions": [
            {
                "original_ingredient": "Fiordilatte",
                "substitute": "Mozzarella di bufala",
                "cultural_justification": "Più ricca e cremosa, mantiene l'autenticità campana",
                "authenticity_impact": "maintains"
            },
            {
                "original_ingredient": "Parmigiano",
                "substitute": "Pecorino Romano",
                "cultural_justification": "Alternativa tradizionale nel Sud Italia",
                "authenticity_impact": "maintains"
            }
        ],
        "scaling_info": {
            "base_servings": 4,
            "scalable": True,
            "scaling_notes": "Mantieni le proporzioni, aumenta il tempo di gratinatura se necessario"
        },
        "wine_pairing": {
            "enabled": True,
            "suggestions": [
                {"wine": "Aglianico del Taburno DOCG", "region": "Campania", "justification": "Origine regionale, sostiene bene la frittura e il pomodoro"},
                {"wine": "Piedirosso dei Campi Flegrei DOC", "region": "Campania", "justification": "Tipico vino partenopeo, perfetto con piatti popolari al forno"},
                {"wine": "Chianti Classico DOCG", "region": "Toscana", "justification": "L'acidità pulisce il palato dai grassi"},
                {"wine": "Cerasuolo d'Abruzzo DOC", "region": "Abruzzo", "justification": "Fresco ma strutturato: accompagna bene fritti e formaggi"},
                {"wine": "Lambrusco Grasparossa DOC", "region": "Emilia-Romagna", "justification": "Il perlage sgrassa e la leggera dolcezza contrasta l'acidità"}
            ]
        },
        "related_dishes": [
            {"dish_name": "Parmigiana di Melanzane", "recipe_slug": "parmigiana-melanzane-italy", "relationship": "similar"},
            {"dish_name": "Pasta alla Genovese", "recipe_slug": "pasta-genovese-italy", "relationship": "same-meal"}
        ],
        "seo_metadata": {
            "meta_title": "Melanzane a Pullastiello - Authentic Neapolitan Recipe | Sous Chef Linguini",
            "meta_description": "Traditional Neapolitan eggplant dish that imitates stuffed chicken. Rich, creamy, and full of flavor.",
            "keywords": ["melanzane", "pullastiello", "napoletano", "vegetarian", "authentic", "traditional"],
            "schema_json": {}
        },
        "status": "published",
        "manual_override": False,
        "override_reason": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
]

async def seed_examples():
    """Seed example recipes."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        for recipe in EXAMPLE_RECIPES:
            # Check if already exists
            existing = await db.recipes.find_one({"slug": recipe["slug"]})
            if existing:
                logger.info(f"Recipe {recipe['slug']} already exists, skipping")
                continue
            
            await db.recipes.insert_one(recipe)
            logger.info(f"✓ Added example recipe: {recipe['title_original']}")
        
        logger.info("Example recipes seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding examples: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_examples())
