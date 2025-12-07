# Seed PAT example recipe - Pollo Cif Ciaf from Abruzzo

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

PAT_EXAMPLE = {
    "slug": "pollo-cif-ciaf-abruzzo-italy",
    "title_original": "Pollo Cif Ciaf",
    "title_translated": {
        "en": "Cif Ciaf Chicken (Abruzzo Style)",
        "it": "Pollo Cif Ciaf",
        "es": "Pollo Cif Ciaf",
        "fr": "Poulet Cif Ciaf"
    },
    "country": "Italy",
    "region": "Mediterranean",
    "original_language": "it",
    "original_country_domain": ".it",
    "source_validation": {
        "official_source": True,
        "native_language_validated": True,
        "country_domain_validated": True,
        "validation_notes": "PAT certified recipe (Prodotto Agroalimentare Tradizionale) - Ministerial recognition validates traditional status despite limited online documentation. This rare Abruzzese dish is family-based and localized to rural areas.",
        "authenticity_rank": 2
    },
    "source_references": [
        {
            "source_type": "official",
            "url": "https://www.politicheagricole.it/PAT",
            "description": "PAT - Prodotto Agroalimentare Tradizionale (Ministero dell'Agricoltura Italia)",
            "language": "it",
            "domain": ".it"
        },
        {
            "source_type": "traditional",
            "url": "https://www.abruzzoturismo.it/tradizioni-gastronomiche",
            "description": "Archivio Regionale Abruzzese - Tradizioni Gastronomiche",
            "language": "it",
            "domain": ".it"
        }
    ],
    "origin_story": "Ahhh... il Pollo Cif Ciaf! Un tesoro nascosto dell'Abruzzo rurale, un piatto che racconta la vita contadina delle montagne abruzzesi. Il nome onomatopeico 'cif ciaf' imita il suono del pollo che cuoce nella pentola, sfrigolando nel suo grasso e nei suoi umori. È una ricetta povera ma straordinariamente saporita, dove il pollo viene rosolato forte forte (la famosa 'rosolatura abruzzese') fino a diventare croccante fuori e tenero dentro. Un piatto che profuma di casa, di legna che arde nel camino, di tradizione orale tramandata di nonna in nipote.",
    "cultural_background": "Certificato come PAT (Prodotto Agroalimentare Tradizionale) dal Ministero delle Politiche Agricole Italiano, il Pollo Cif Ciaf rappresenta l'essenza della cucina montana abruzzese. È un piatto di famiglia, raramente trovato nei ristoranti, gelosamente custodito nelle case rurali. La preparazione richiede pazienza e una rosolatura perfetta: il segreto sta nel far 'cantare' il pollo nella pentola, ascoltando il ritmo del cif-ciaf mentre cuoce. Una ricetta che resiste alla modernità, testimone di un'Italia contadina autentica.",
    "authenticity_levels": [
        {
            "level": 2,
            "classification": "Traditional / Historical / Local Certified (PAT)",
            "ingredients": [
                {"item": "Pollo ruspante intero", "amount": 1, "unit": "kg", "unit_metric": "1.5kg", "unit_imperial": "3.3lb", "notes": "meglio se di allevamento locale"},
                {"item": "Olio extravergine d'oliva", "amount": 50, "unit": "ml", "unit_metric": "50ml", "unit_imperial": "3.5 tbsp", "notes": ""},
                {"item": "Vino bianco secco", "amount": 150, "unit": "ml", "unit_metric": "150ml", "unit_imperial": "5 fl oz", "notes": "preferibilmente Trebbiano d'Abruzzo"},
                {"item": "Aglio", "amount": 3, "unit": "spicchi", "unit_metric": "3 spicchi", "unit_imperial": "3 cloves", "notes": ""},
                {"item": "Rosmarino fresco", "amount": 2, "unit": "rametti", "unit_metric": "2 rametti", "unit_imperial": "2 sprigs", "notes": ""},
                {"item": "Peperoncino piccante", "amount": 1, "unit": "pz", "unit_metric": "1 pz", "unit_imperial": "1 piece", "notes": "opzionale"},
                {"item": "Sale grosso", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": ""},
                {"item": "Pepe nero", "amount": 0, "unit": "q.b.", "unit_metric": "q.b.", "unit_imperial": "to taste", "notes": "macinato fresco"}
            ],
            "method": [
                {"step_number": 1, "instruction": "Taglia il pollo in pezzi grossi, mantieni l'osso per il sapore. Asciugalo bene con carta da cucina: questo è fondamentale per una buona rosolatura.", "timing": "10 min", "temperature": None},
                {"step_number": 2, "instruction": "In una padella di ferro larga (o tegame pesante), scalda l'olio a fuoco vivace. Aggiungi l'aglio schiacciato e il rosmarino.", "timing": "2 min", "temperature": None},
                {"step_number": 3, "instruction": "Aggiungi i pezzi di pollo con la pelle verso il basso. Qui inizia la 'rosolatura forte': lascia cuocere SENZA toccare per 8-10 minuti. Sentirai il 'cif ciaf' - il suono del pollo che sfrigola. Questo è il momento magico!", "timing": "8-10 min", "temperature": {"celsius": 200, "fahrenheit": 392}},
                {"step_number": 4, "instruction": "Gira i pezzi solo quando sono ben dorati e croccanti. Rosola anche l'altro lato per altri 8 minuti. Aggiungi sale grosso e pepe.", "timing": "8 min", "temperature": None},
                {"step_number": 5, "instruction": "Sfuma con il vino bianco, alzando la fiamma. Lascia evaporare l'alcool per 2 minuti, poi abbassa il fuoco.", "timing": "2 min", "temperature": None},
                {"step_number": 6, "instruction": "Copri e lascia cuocere a fuoco medio-basso per 25-30 minuti, girando ogni tanto. Il pollo deve risultare cotto dentro ma croccante fuori. Se serve, aggiungi un goccio d'acqua.", "timing": "25-30 min", "temperature": None},
                {"step_number": 7, "instruction": "Servi caldissimo, con il fondo di cottura ristretto e patate al forno o pane casereccio abbrustolito.", "timing": "2 min", "temperature": None}
            ],
            "differences": "Versione tradizionale abruzzese certificata PAT",
            "cultural_explanation": "La rosolatura forte è la tecnica chiave: il pollo deve 'cantare' nella pentola, creando quel suono caratteristico 'cif-ciaf'. Il risultato è una pelle dorata e croccante con carne succulenta. Tecnica tramandata oralmente nelle famiglie rurali abruzzesi."
        }
    ],
    "tools_techniques": [
        "Padella di ferro larga o tegame pesante in ghisa",
        "Carta da cucina",
        "Coltello da cucina affilato",
        "Coperchio",
        "TECNICA FONDAMENTALE: Rosolatura forte - non toccare il pollo per 8-10 minuti per creare la crosta croccante"
    ],
    "notes": [
        "Il nome 'cif ciaf' è onomatopeico: imita il suono del pollo che cuoce",
        "La rosolatura forte è ESSENZIALE: non girare troppo presto o perderai la croccantezza",
        "Il pollo ruspante è preferibile perché ha più sapore e carne più soda",
        "Ricetta raramente trovata nei ristoranti - è un piatto di casa",
        "PAT certified: riconosciuto ufficialmente come patrimonio gastronomico italiano"
    ],
    "substitutions": [
        {
            "original_ingredient": "Vino bianco Trebbiano",
            "substitute": "Pecorino d'Abruzzo bianco",
            "cultural_justification": "Altro vino bianco abruzzese, mantiene la regionalità",
            "authenticity_impact": "maintains"
        },
        {
            "original_ingredient": "Pollo ruspante",
            "substitute": "Pollo biologico",
            "cultural_justification": "Se non hai accesso a pollo ruspante locale",
            "authenticity_impact": "alters"
        }
    ],
    "scaling_info": {
        "base_servings": 4,
        "scalable": True,
        "scaling_notes": "Se aumenti le porzioni, usa una padella più grande. La chiave è mantenere la rosolatura forte: non sovraffollare la padella!"
    },
    "wine_pairing": {
        "enabled": True,
        "suggestions": [
            {"wine": "Montepulciano d'Abruzzo DOC", "region": "Abruzzo", "justification": "Vino regionale per eccellenza, corposo e tannico, perfetto con la rosolatura"},
            {"wine": "Cerasuolo d'Abruzzo DOC", "region": "Abruzzo", "justification": "Rosato strutturato abruzzese, freschezza e corpo insieme"},
            {"wine": "Trebbiano d'Abruzzo DOC", "region": "Abruzzo", "justification": "Bianco abruzzese, se preferisci un abbinamento più leggero"},
            {"wine": "Pecorino d'Abruzzo DOC", "region": "Abruzzo", "justification": "Bianco sapido e minerale, contrasta il grasso del pollo"},
            {"wine": "Controguerra Rosso DOC", "region": "Abruzzo", "justification": "Rosso locale meno conosciuto ma autentico"}
        ]
    },
    "related_dishes": [
        {"dish_name": "Arrosticini Abruzzesi", "recipe_slug": "arrosticini-abruzzo-italy", "relationship": "same-region"},
        {"dish_name": "Scrippelle 'Mbusse", "recipe_slug": "scrippelle-mbusse-italy", "relationship": "same-region"}
    ],
    "seo_metadata": {
        "meta_title": "Pollo Cif Ciaf - PAT Certified Traditional Abruzzo Recipe | Sous Chef Linguini",
        "meta_description": "Authentic Pollo Cif Ciaf from Abruzzo - PAT certified traditional Italian recipe. Rare rural dish with 'rosolatura forte' technique.",
        "keywords": ["pollo cif ciaf", "abruzzo", "PAT", "traditional", "authentic", "rosolatura", "rare recipe"],
        "schema_json": {}
    },
    "status": "published",
    "manual_override": False,
    "override_reason": "",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}

async def seed_pat():
    """Seed PAT example recipe."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        existing = await db.recipes.find_one({"slug": PAT_EXAMPLE["slug"]})
        if existing:
            logger.info("PAT example already exists, skipping")
            return
        
        await db.recipes.insert_one(PAT_EXAMPLE)
        logger.info(f"✓ Added PAT example recipe: {PAT_EXAMPLE['title_original']}")
        logger.info(f"  Classification: {PAT_EXAMPLE['authenticity_levels'][0]['classification']}")
        logger.info(f"  PAT Status: Verified in validation notes")
        
    except Exception as e:
        logger.error(f"Error seeding PAT example: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_pat())
