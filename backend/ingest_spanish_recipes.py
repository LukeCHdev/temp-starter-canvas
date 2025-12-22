#!/usr/bin/env python3
"""
One-time ingestion script for 71 Spanish recipes from Real Academia de Gastronomía.
Source: Approved, frozen JSON batches (1-14) from web crawl.

Schema mapping:
- name → recipe_name
- origin_country → "Spain" (canonical English form)
- origin_region → preserved in Spanish
- ingredients, instructions, authenticity_level, source_url → direct map

All recipes:
- published = True
- featured = False
- source = "Real Academia de Gastronomía"
"""

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

load_dotenv('.env')

# All 71 Spanish recipes from approved batches
SPANISH_RECIPES = [
    # Batch 1 (4 recipes)
    {
        "name": "Ajoblanco",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "miga de pan candeal", "quantity": 150, "unit": "g"},
            {"item": "almendras crudas peladas", "quantity": 200, "unit": "g"},
            {"item": "dientes de ajo pequeños", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": 150, "unit": "g"},
            {"item": "vinagre de Jerez", "quantity": 20, "unit": "g"},
            {"item": "agua fría", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "uva moscatel", "quantity": 200, "unit": "g"}
        ],
        "instructions": [
            "Poner el pan a remojo en agua fría durante 15 minutos.",
            "Triturar el pan con las almendras y los ajos.",
            "Agregar el aceite poco a poco sin dejar de batir.",
            "Incorporar el vinagre y sazonar.",
            "Añadir agua fría hasta obtener una crema suave y bien ligada.",
            "Servir el ajoblanco frío con las uvas moscatel peladas."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/ajoblanco/"
    },
    {
        "name": "Gazpacho Andaluz",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "miga de pan de víspera", "quantity": 100, "unit": "g"},
            {"item": "tomates rojos maduros", "quantity": 1000, "unit": "g"},
            {"item": "pepino", "quantity": 0.5, "unit": "unidad"},
            {"item": "cebolla", "quantity": 0.5, "unit": "unidad", "notes": "optional, regional variation (Andalucía)"},
            {"item": "pimiento verde", "quantity": 1, "unit": "unidad"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": 100, "unit": "g"},
            {"item": "vinagre de Jerez", "quantity": 30, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner la miga de pan a remojo en agua fría durante 20 minutos.",
            "Trocear los tomates y el pimiento verde. Pelar la cebolla, el pepino y los dientes de ajo.",
            "Poner los ingredientes preparados en el bol de la batidora. Agregar la miga de pan escurrida, el vinagre y la sal.",
            "Triturar hasta obtener una crema homogénea. Colar si fuera necesario.",
            "Emulsionar con el aceite sin dejar de batir. Enfriar.",
            "Servir el gazpacho frío."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/gazpacho-andaluz/"
    },
    {
        "name": "Paella Valenciana Tradicional",
        "origin_region": "Comunitat Valenciana",
        "ingredients": [
            {"item": "conejo", "quantity": 400, "unit": "g"},
            {"item": "pollo", "quantity": 400, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "garrofón tierno", "quantity": 150, "unit": "g"},
            {"item": "ferradura", "quantity": 250, "unit": "g"},
            {"item": "tomates maduros", "quantity": 100, "unit": "g"},
            {"item": "arroz bomba", "quantity": 300, "unit": "g"},
            {"item": "agua", "quantity": 1.5, "unit": "l"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharadita"},
            {"item": "hebras de azafrán", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar en trozos pequeños el conejo y el pollo. Calentar aceite en la paella. Dorar el conejo y el pollo por todos los lados. Sazonar.",
            "Incorporar el garrofón y las judías verdes troceadas.",
            "Bajar el fuego, e incorporar el tomate rallado. Remover hasta que suelte su agua.",
            "Agregar el pimentón, las hebras de azafrán y 1,5 l de agua. Sazonar. Cocer a fuego vivo durante 5 minutos.",
            "Bajar el fuego y continuar la cocción de 30 a 35 minutos o hasta que todos los ingredientes estén cocidos.",
            "Llevar a ebullición a fuego vivo, agregar el arroz, repartir bien y no volver a tocar. Cocer durante 10 minutos.",
            "Bajar el fuego y continuar la cocción de 8 a 10 minutos. El arroz tiene que quedar seco y con el grano entero.",
            "Reposar durante 5 minutos y servir en la misma paella."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/paella-valenciana/"
    },
    {
        "name": "Tortilla de Patata",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "patatas", "quantity": 800, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "abundante"},
            {"item": "huevos", "quantity": 6, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "cebolla", "quantity": None, "unit": "al gusto", "notes": "optional, regional variation (Toda España)"}
        ],
        "instructions": [
            "Pelar las patatas, lavar, secar y cortar en rodajas finas.",
            "Calentar abundante aceite en una sartén honda y poner las patatas. Freír a fuego medio hasta que estén tiernas y ligeramente doradas. Sacar y escurrir.",
            "Batir los huevos en un bol, agregar las patatas escurridas y sazonar. Dejar reposar al menos 15 minutos.",
            "Calentar 1 cucharada de aceite en una sartén y agregar la mezcla de huevos y patatas.",
            "Cuajar la tortilla por un lado, dar la vuelta con un plato o una tapadera y dejar que se cuaje por el otro lado.",
            "La tortilla tiene que estar ligeramente dorada por fuera y blanda por dentro."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/tortilla-de-patata/"
    },
    # Batch 2 (8 recipes)
    {
        "name": "Fabada Asturiana",
        "origin_region": "Principado de Asturias",
        "ingredients": [
            {"item": "fabes", "quantity": 500, "unit": "g"},
            {"item": "lacón", "quantity": 200, "unit": "g"},
            {"item": "tocino", "quantity": 200, "unit": "g"},
            {"item": "chorizos asturianos", "quantity": 2, "unit": "unidades"},
            {"item": "morcillas asturianas", "quantity": 2, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner las fabes a remojo en agua fría durante 12 horas. Disponer en otro recipiente el lacón y el tocino cubiertos de agua templada.",
            "En una cazuela poner las fabes con el agua en que han estado a remojo. Agregar el lacón y el tocino escurridos y cubrir todo con más agua fría.",
            "Cocer a fuego lento 1 hora. Espumar cuando sea necesario.",
            "Lavar los chorizos y las morcillas y pinchar con un cuchillo. Agregar a la cazuela de las fabes y continuar la cocción durante media hora más.",
            "Las fabes siempre tienen que estar cubiertas de agua. Si es necesario, añadir de vez en cuando agua fría en pequeñas cantidades.",
            "Diez minutos antes de terminar la cocción sazonar. Retirar del fuego y dejar reposar.",
            "Para servir cortar el lacón, el tocino, los chorizos y las morcillas."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/fabada-asturiana/"
    },
    {
        "name": "Cocido Madrileño",
        "origin_region": "Comunidad de Madrid",
        "ingredients": [
            {"item": "garbanzos", "quantity": 300, "unit": "g"},
            {"item": "morcillo de vaca", "quantity": 750, "unit": "g"},
            {"item": "huesos de jamón", "quantity": 2, "unit": "unidades"},
            {"item": "huesos de caña", "quantity": 2, "unit": "unidades"},
            {"item": "gallina", "quantity": 0.5, "unit": "unidad"},
            {"item": "nabo", "quantity": 1, "unit": "unidad"},
            {"item": "zanahorias", "quantity": 3, "unit": "unidades"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "rama de apio", "quantity": 1, "unit": "unidad"},
            {"item": "tocino entreverado", "quantity": 150, "unit": "g"},
            {"item": "patatas medianas", "quantity": 4, "unit": "unidades"},
            {"item": "chorizos", "quantity": 2, "unit": "unidades"},
            {"item": "repollo", "quantity": 750, "unit": "g"},
            {"item": "morcillas", "quantity": 2, "unit": "unidades"},
            {"item": "fideos finos", "quantity": 125, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner los garbanzos a remojo en agua caliente durante 12 horas. Lavar, escurrir y meter en una red para que no se deshagan. Lavar el morcillo, los huesos y la gallina.",
            "En una olla grande poner las carnes lavadas. Cubrir con agua fría y llevar a ebullición. Cocer durante 30 minutos. Espumar.",
            "Añadir los garbanzos, el nabo, las zanahorias y la cebolla peladas y enteras, la rama de apio y el tocino. Cuando rompa a hervir bajar el fuego y continuar la cocción a fuego bajo durante 2 horas.",
            "Media hora antes de terminar la cocción incorporar las patatas peladas y enteras.",
            "En otra cazuela cocer los chorizos y la morcilla en un poco de caldo.",
            "Cocer el repollo cortado en juliana, en agua hirviendo con sal, durante 20 minutos. Escurrir.",
            "Una vez hecho el cocido separar caldo de la cocción para hacer la sopa. Cocer los fideos en el caldo colado durante 5 minutos.",
            "Servir la sopa de fideos en una sopera. En una fuente, poner los garbanzos bien escurridos con las patatas, las verduras del caldo y el repollo. En otra fuente la carne y la gallina, el chorizo, la morcilla y el tocino partidos en trozos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cocido-madrileno/"
    },
    {
        "name": "Pulpo a la Gallega",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "pulpo", "quantity": 1.5, "unit": "kg"},
            {"item": "cebolla pequeña", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "pimentón dulce", "quantity": None, "unit": "al gusto"},
            {"item": "pimentón picante", "quantity": None, "unit": "al gusto"},
            {"item": "sal gorda", "quantity": None, "unit": "al gusto"},
            {"item": "patatas", "quantity": None, "unit": "al gusto", "notes": "optional, regional variation (Galicia)"}
        ],
        "instructions": [
            "Limpiar el pulpo. Quitar el pico que tiene entre los tentáculos y vaciar la cabeza. Golpear fuertemente con el mazo del mortero para ablandar.",
            "Poner el agua a hervir con la cebolla en una cazuela grande. Cuando rompa a hervir meter y sacar el pulpo 3 veces, antes de dejar cocer.",
            "Cuando el agua rompa a hervir de nuevo, meter el pulpo. Continuar la cocción durante 40 minutos. Pinchar y si está blando, retirar del fuego.",
            "Escurrir sobre un tazón boca abajo. Cortar con una tijera en trozos de 2 cm.",
            "Colocar en platos de madera. Poner un chorro de aceite, sal y espolvorear con los dos pimentones mezclados."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/pulpo-a-feira/"
    },
    {
        "name": "Crema Catalana",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "leche", "quantity": 1, "unit": "l"},
            {"item": "rama de canela", "quantity": 1, "unit": "unidad"},
            {"item": "piel de limón", "quantity": 1, "unit": "unidad"},
            {"item": "yemas de huevo", "quantity": 8, "unit": "unidades"},
            {"item": "azúcar", "quantity": 150, "unit": "g"},
            {"item": "maicena", "quantity": 30, "unit": "g"},
            {"item": "azúcar para caramelizar", "quantity": 4, "unit": "cucharadas"}
        ],
        "instructions": [
            "Poner en un cazo la leche con la rama de canela y la piel de limón. Calentar a fuego medio hasta que rompa a hervir. Retirar del fuego y colar.",
            "Batir las yemas con el azúcar y la maicena en un bol hasta que la preparación blanquee. Añadir la leche poco a poco sin dejar de batir.",
            "Calentar de nuevo a fuego medio, sin dejar de remover, hasta que haya espesado.",
            "Verter la crema en cazuelitas y dejar enfriar. Espolvorear con el azúcar y quemar para caramelizar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/crema-catalana/"
    },
    {
        "name": "Salmorejo",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "tomates rojos maduros", "quantity": 1.5, "unit": "kg"},
            {"item": "pan de hogaza", "quantity": 300, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": 100, "unit": "g"},
            {"item": "vinagre de vino blanco", "quantity": None, "unit": "al gusto", "notes": "optional, regional variation (Andalucía)"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "huevo duro", "quantity": 1, "unit": "unidad"},
            {"item": "jamón serrano", "quantity": 75, "unit": "g"}
        ],
        "instructions": [
            "Triturar los tomates y colar para retirar pieles y semillas.",
            "Mojar el pan con el tomate y triturar con el ajo. Añadir el aceite sin dejar de batir para emulsionar y aliñar con sal y vinagre.",
            "Servir el salmorejo frío con el huevo duro picado y el jamón en taquitos por encima."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/salmorejo/"
    },
    {
        "name": "Croquetas de Jamón",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "mantequilla", "quantity": 100, "unit": "g"},
            {"item": "harina", "quantity": 100, "unit": "g"},
            {"item": "leche", "quantity": 700, "unit": "g"},
            {"item": "jamón ibérico", "quantity": 100, "unit": "g"},
            {"item": "nuez moscada", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "huevos", "quantity": 2, "unit": "unidades"},
            {"item": "pan rallado", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva", "quantity": None, "unit": "abundante"}
        ],
        "instructions": [
            "En una cazuela a fuego medio derretir la mantequilla. Incorporar la harina. Rehogar unos minutos sin que tome color e incorporar la leche poco a poco sin parar de remover hasta que espese y esté lisa y brillante.",
            "Cuanto más se cueza, más cremosas las croquetas. Agregar el jamón picado, nuez moscada, pimienta y sal. Dejar enfriar la masa hasta que cuaje.",
            "Dar forma a las croquetas, pasar por huevo batido y pan rallado y freír en abundante aceite caliente. Escurrir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/croquetas-de-jamon/"
    },
    {
        "name": "Rabo de Toro",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "rabo de toro", "quantity": 2, "unit": "kg"},
            {"item": "cebollas grandes", "quantity": 4, "unit": "unidades"},
            {"item": "cabeza de ajos", "quantity": 1, "unit": "unidad"},
            {"item": "tomates maduros", "quantity": 4, "unit": "unidades"},
            {"item": "zanahorias", "quantity": 3, "unit": "unidades"},
            {"item": "hebras de azafrán", "quantity": None, "unit": "al gusto"},
            {"item": "laurel", "quantity": None, "unit": "al gusto"},
            {"item": "vino oloroso", "quantity": 0.5, "unit": "l"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "patatas", "quantity": 400, "unit": "g"},
            {"item": "pimienta negra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar bien los rabos, retirar la grasa y cortar por las coyunturas. Salpimentar.",
            "Pelar y picar las cebollas, las zanahorias y los tomates. Rehogar en un poco de aceite.",
            "Añadir los rabos, la cabeza de ajos entera, el azafrán previamente tostado y el laurel. Cocinar todo junto unos minutos y regar con el vino.",
            "Cocer tapado unas 3 horas o hasta que la carne se separe del hueso.",
            "Una vez cocidos dejar reposar durante 2 horas.",
            "Pelar las patatas y cortar en cuadrados. Freír en abundante aceite caliente. Escurrir sobre papel absorbente.",
            "Servir los rabos con las verduras y las patatas fritas."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/rabo-de-toro/"
    },
    {
        "name": "Albóndigas",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "magro de ternera picado", "quantity": 300, "unit": "g"},
            {"item": "magro de cerdo picado", "quantity": 200, "unit": "g"},
            {"item": "miga de pan", "quantity": 75, "unit": "g"},
            {"item": "leche", "quantity": 100, "unit": "g"},
            {"item": "huevos", "quantity": 2, "unit": "unidades"},
            {"item": "jamón serrano picado", "quantity": 100, "unit": "g", "notes": "optional, regional variation (Toda España)"},
            {"item": "perejil picado", "quantity": 1, "unit": "cucharada"},
            {"item": "harina de trigo", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "abundante"},
            {"item": "pimienta negra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad", "notes": "para la salsa"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades", "notes": "para la salsa"},
            {"item": "zanahoria", "quantity": 1, "unit": "unidad", "notes": "para la salsa"},
            {"item": "vino blanco seco", "quantity": 100, "unit": "g", "notes": "para la salsa"},
            {"item": "tomates", "quantity": 2, "unit": "unidades", "notes": "para la salsa"},
            {"item": "caldo de carne", "quantity": 500, "unit": "g", "notes": "para la salsa"}
        ],
        "instructions": [
            "Poner la miga de pan a remojo con leche.",
            "Batir los huevos en un bol. Agregar las carnes picadas, la miga de pan escurrida, el jamón serrano, el perejil, pimienta y sal. Mezclar muy bien. Coger porciones pequeñas y moldear en forma de bola con las manos.",
            "Pasar las albóndigas por harina y sacudir para retirar el exceso. Calentar aceite en una sartén y freír las albóndigas; escurrir sobre papel absorbente.",
            "En el mismo aceite rehogar la cebolla, los dientes de ajo y la zanahoria pelados y picados. Agregar el vino y dejar reducir un poco.",
            "Incorporar los tomates pelados, sin pepitas y picados. Continuar la cocción durante 5 minutos más. Añadir el caldo de carne, salpimentar y cocer durante 20 minutos.",
            "Pasar la salsa por el pasapurés si se desea.",
            "Poner la salsa con las albóndigas en una cazuela y cocer durante 15 minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/albondigas/"
    }
]

# Continue with remaining recipes in part 2...
