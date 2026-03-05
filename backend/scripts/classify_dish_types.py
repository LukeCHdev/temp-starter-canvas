"""
One-time migration script to classify all recipes by dish_type.
Categories: appetizer, aperitif, first-course, main-course, side-dish, dessert, street-food, festive
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Explicit slug-to-dish-type mapping
DISH_TYPE_MAP = {
    # === DESSERTS ===
    "arroz-con-leche": "dessert",
    "almendras-garrapinadas": "dessert",
    "baba-napoletano-al-rum-italy": "dessert",
    "bongo-italy": "dessert",
    "cannoli-di-ricotta-siciliani-italy": "dessert",
    "canutillos-de-crema": "dessert",
    "casadielles": "dessert",
    "castanas-con-leche": "dessert",
    "crema-catalana": "dessert",
    "cuajada": "dessert",
    "filloas": "dessert",
    "frittelle-di-riso-italy": "dessert",
    "gluai-buat-chi-thailand": "dessert",
    "khao-niew-dam-piek-maphrao-awn-thailand": "dessert",
    "leche-frita": "dessert",
    "panna-cotta-italy": "dessert",
    "sheqerpare-turkey": "dessert",
    "tarta-de-santiago": "dessert",
    "tiramisu-classico-italy": "dessert",
    "torrijas": "dessert",
    "yemas-de-santa-teresa": "dessert",
    "bunuelos-de-platano": "dessert",

    # === MAIN COURSES ===
    "albondigas": "main-course",
    "all-i-pebre": "main-course",
    "bacalao-a-la-llauna": "main-course",
    "baccala-alla-vicentina-italy": "main-course",
    "besugo-a-la-madrilena": "main-course",
    "boeuf-bourguignon-france": "main-course",
    "bombette-pugliesi-tradizionali-italy": "main-course",
    "bonito-con-tomate": "main-course",
    "butifarra-con-setas": "main-course",
    "butter-chicken-india": "main-course",
    "cabrito-asado": "main-course",
    "carbonada-chile": "main-course",
    "carbonada-chilena-chile": "main-course",
    "carrilleras-de-cerdo": "main-course",
    "cazuela-de-vacuno-chile": "main-course",
    "charquican-chile": "main-course",
    "cocido-madrileno": "main-course",
    "cocido-montanes": "main-course",
    "conejo-con-caracoles": "main-course",
    "coq-au-vin-france": "main-course",
    "cordero-al-chilindron": "main-course",
    "costillar-al-horno-con-papas-chango-chile": "main-course",
    "cotoletta-alla-milanese-italy": "main-course",
    "dorada-a-la-sal": "main-course",
    "fegato-alla-veneziana-italy": "main-course",
    "fergese-albania": "main-course",
    "gaeng-hung-ley-hunglay-curry-thailand": "main-course",
    "gulys-hungary": "main-course",
    "involtini-di-pesce-spada-alla-messinese-italy": "main-course",
    "kimchi-jjigae-south-korea": "main-course",
    "massaman-gai-thailand": "main-course",
    "meat-pie-australia": "main-course",
    "mole-poblano-mexico": "main-course",
    "moussaka-greece": "main-course",
    "pad-thai-goong-sod-thailand": "main-course",
    "pad-thai-thailand": "main-course",
    "paella-de-mariscos-spain": "main-course",
    "paella-valenciana-spain": "main-course",
    "paella-valenciana-tradicional": "main-course",
    "parmigiana-di-melanzane-parmigiana-alla-italiana-italy": "main-course",
    "pimientos-rellenos-de-carne": "main-course",
    "polpo-alla-luciana-italy": "main-course",
    "rabo-de-toro": "main-course",
    "sauerbraten-germany": "main-course",
    "saltimbocca-alla-romana-italy": "main-course",
    "sarmale-romania": "main-course",
    "shakshuka-tunisia": "main-course",
    "tagine-of-lamb-morocco": "main-course",
    "tave-kosi-albania": "main-course",
    "tonno-del-chianti-italy": "main-course",
    "trippa-alla-fiorentina-italy": "main-course",
    "bibimbap-south-korea": "main-course",
    "japan": "main-course",  # okonomiyaki
    "test-admin-recipe-france": "main-course",

    # === FIRST COURSES (soups, pastas, risottos) ===
    "ajoblanco": "first-course",
    "arroz-a-la-zamorana": "first-course",
    "arroz-con-costra": "first-course",
    "arroz-negro": "first-course",
    "bouillabaisse-france": "first-course",
    "caldo-gallego": "first-course",
    "canederli-allo-speck-italy": "first-course",
    "canelones": "first-course",
    "gnudi-italy": "first-course",
    "gnocchi-sbattui-de-marga-italy": "first-course",
    "pasta-alla-genovese-italy": "first-course",
    "pasta-e-patate-alla-napoletana-italy": "first-course",
    "ph-b-vietnam": "first-course",
    "pici-allaglione-italy": "first-course",
    "pizzoccheri-alla-valtellinese-italy": "first-course",
    "ragu-alla-bolognese-italy": "first-course",
    "ravioli-del-plin-italy": "first-course",
    "ribollita-italy": "first-course",
    "risi-e-bisi-italy": "first-course",
    "risotto-alla-milanese-italy": "first-course",
    "sopa-de-ajo": "first-course",
    "spaghetti-al-pomodoro-italy": "first-course",
    "spaghetti-alla-carbonara-italy": "first-course",
    "spaghetti-alle-vongole-italy": "first-course",
    "spaghetti-cacio-e-pepe-italy": "first-course",
    "tom-kha-gai-thailand": "first-course",
    "tom-yum-goong-thailand": "first-course",
    "tonkotsu-ramen-japan": "first-course",
    "tortellino-di-bologna-italy": "first-course",
    "trenette-al-pesto-genovese-italy": "first-course",
    "cacciucco-alla-livornese-italy": "first-course",
    "caldillo-de-congrio-chile": "first-course",
    "fabada-asturiana": "first-course",
    "kalapurka-chile": "first-course",
    "kalapurka-chile-1": "first-course",
    "gazpacho-andaluz": "first-course",
    "gazpacho-spain": "first-course",
    "salmorejo": "first-course",

    # === APPETIZERS ===
    "almejas-a-la-marinera": "appetizer",
    "almejas-al-ajillo": "appetizer",
    "bagna-cauda-italy": "appetizer",
    "boquerones-en-vinagre": "appetizer",
    "crostini-di-fegatini-toscani-italy": "appetizer",
    "ensalada-murciana": "appetizer",
    "escalivada": "appetizer",
    "esparragos-blancos-con-huevo": "appetizer",
    "gambas-al-ajillo": "appetizer",
    "huevas-alinadas": "appetizer",
    "hummus-lebanon": "appetizer",
    "mejillones-en-escabeche": "appetizer",
    "pulpo-a-la-gallega": "appetizer",
    "revuelto-de-setas": "appetizer",
    "sepia-al-ajillo": "appetizer",
    "som-tum-thailand": "appetizer",
    "yum-woon-sen-neua-thailand": "appetizer",
    "prueba-de-picadillo": "appetizer",

    # === APERITIF & SMALL PLATES ===
    "boquerones-fritos": "aperitif",
    "bunuelos-de-bacalao": "aperitif",
    "croquetas-de-jamon": "aperitif",
    "sobrasada-con-queso-mahon-fundido": "aperitif",
    "berenjenas-fritas-con-miel": "aperitif",
    "fritura-de-pescado": "aperitif",

    # === STREET FOOD ===
    "arancini-di-riso-classici-italy": "street-food",
    "byrek-albania": "street-food",
    "croissant-france": "street-food",
    "focaccia-genovese-fugassa-italy": "street-food",
    "pizza-margherita-italy": "street-food",
    "poutine-canada": "street-food",
    "sushi-nigiri-japan": "street-food",
    "tacos-al-pastor-mexico": "street-food",
    "tortilla-de-bacalao": "street-food",
    "tortilla-de-patata": "street-food",

    # === SIDE DISHES ===
    "alcachofas-a-la-montillana": "side-dish",
    "bocartes-en-cazuela": "side-dish",
    "coliflor-al-ajoarriero": "side-dish",
    "duelos-y-quebrantos": "side-dish",
    "espinacas-a-la-catalana": "side-dish",
    "fagioli-alluccelletto-italy": "side-dish",
    "huevos-a-la-flamenca": "side-dish",
    "migas": "side-dish",
    "patatas-a-la-riojana": "side-dish",
    "pesto-genovese-tradizionale-italy": "side-dish",
    "pisto-manchego": "side-dish",

    # === FESTIVE ===
    "bonito-en-escabeche": "festive",
    "cangrejos-de-rio": "festive",

    # === BATCH 2 - previously unclassified ===
    "tiramisu-italy": "dessert",
    "beef-wellington-united-kingdom": "main-course",
    "peking-duck-china": "main-course",
    "south-korea-2": "side-dish",
    "south-korea-variant": "side-dish",
    "south-korea-regional": "side-dish",
    "south-korea-traditional": "side-dish",
    "south-korea": "side-dish",
    "russia": "first-course",
    "russia-2": "street-food",
    "russia-variant": "street-food",
    "umu-pae-chile": "festive",
    "porotos-con-rocoto-chile": "main-course",
    "cazuela-de-guatitas-chile": "main-course",
    "papas-con-aji-rocoto-chile": "side-dish",
    "silvestre-chile": "main-course",
    "caiquen-al-estilo-kawesqar-chile": "main-course",
    "schiaffoni-allamatriciana-italy": "first-course",
    "saltimbocca-di-filetto-ai-fagiolini-e-yogurt-italy": "main-course",
    "carnitas-mexico": "main-course",
    "latvia": "appetizer",
    "carciofi-alla-giudia-italy": "appetizer",
    "verdure-mbuttunate-italy": "side-dish",
    "involtini-alla-romana-italy": "main-course",
    "costolette-di-agnello-scottadito-italy": "main-course",
    "fritto-allitaliana-italy": "appetizer",
    "schiacciata-alla-fiorentina-metodo-tradizionale-da-pasticceria-con-lievito-madre-italy": "dessert",
    "pappa-al-pomodoro-italy": "first-course",
    "zuppa-di-fagioli-italy": "first-course",
    "passatelli-in-brodo-italy": "first-course",
    "risotto-allo-champagne-italy": "first-course",
    "gnocchi-alla-sorrentina-italy": "first-course",
    "test-auto-translation-b115e195": "main-course",
}


async def run_migration():
    mongo_url = os.environ.get("MONGO_URL")
    client = AsyncIOMotorClient(mongo_url)
    db = client["sous_chef_linguini_db"]

    # Get all recipes
    recipes = await db.recipes.find({}, {"_id": 1, "slug": 1, "recipe_name": 1}).to_list(300)
    print(f"Total recipes: {len(recipes)}")

    updated = 0
    unclassified = []

    for recipe in recipes:
        slug = recipe.get("slug", "")
        dish_type = DISH_TYPE_MAP.get(slug)

        if dish_type:
            await db.recipes.update_one(
                {"_id": recipe["_id"]},
                {"$set": {"dish_type": dish_type}}
            )
            updated += 1
        else:
            unclassified.append(f"  {slug} ({recipe.get('recipe_name', '?')})")

    print(f"Updated: {updated}")
    if unclassified:
        print(f"Unclassified ({len(unclassified)}):")
        for u in unclassified:
            print(u)

    # Verify
    for dt in ["appetizer", "aperitif", "first-course", "main-course", "side-dish", "dessert", "street-food", "festive"]:
        count = await db.recipes.count_documents({"dish_type": dt})
        print(f"  {dt}: {count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
