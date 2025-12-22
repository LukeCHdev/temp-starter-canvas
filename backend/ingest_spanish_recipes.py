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

# Batch 3-4 recipes
SPANISH_RECIPES.extend([
    {
        "name": "Dorada a la Sal",
        "origin_region": "Región de Murcia",
        "ingredients": [
            {"item": "doradas de ración", "quantity": 6, "unit": "unidades"},
            {"item": "sal gorda", "quantity": None, "unit": "abundante"}
        ],
        "instructions": [
            "Para cocinar las doradas a la sal ni se desescaman, ni se abren para retirar las vísceras. Lavar, escurrir y secar muy bien.",
            "En una fuente de horno poner una capa de sal.",
            "Colocar las doradas encima y cubrir totalmente con más sal. Meter en el horno a 200ºC durante 15-20 minutos según el peso.",
            "Sacar del horno, romper la costra de sal y retirar con cuidado para que no se rompa la piel.",
            "Para servir desprender la piel y sacar los lomos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/dorada-a-la-sal/"
    },
    {
        "name": "Caldo Gallego",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "alubias blancas", "quantity": 100, "unit": "g"},
            {"item": "grelos o nabizas", "quantity": 1, "unit": "kg"},
            {"item": "patatas grandes", "quantity": 2, "unit": "unidades"},
            {"item": "unto", "quantity": 30, "unit": "g"},
            {"item": "lacón", "quantity": 1, "unit": "trozo"},
            {"item": "huesos de caña", "quantity": 2, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "chorizos", "quantity": None, "unit": "al gusto", "notes": "optional, regional variation (Galicia)"}
        ],
        "instructions": [
            "Poner en remojo las alubias en abundante agua fresca 24 horas antes.",
            "Lavar los grelos o nabizas y escaldar en agua hirviendo durante unos minutos para que pierda el amargor. Escurrir y reservar.",
            "Lavar bien las carnes y poner a cocer junto con el unto, en abundante agua. Pasada una hora de cocción añadir las alubias y dejar cocer media hora.",
            "Añadir los grelos escaldados y las patatas peladas y chascadas. Dejar cocinar media hora más o hasta que las patatas y grelos estén tiernos.",
            "Salar y dejar reposar, mejor de un día para otro."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/caldo-gallego/"
    },
    {
        "name": "Patatas a la Riojana",
        "origin_region": "La Rioja",
        "ingredients": [
            {"item": "patatas", "quantity": 1, "unit": "kg"},
            {"item": "aceite de oliva virgen", "quantity": None, "unit": "al gusto"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharadita"},
            {"item": "hoja de laurel", "quantity": 1, "unit": "unidad"},
            {"item": "guindilla", "quantity": 1, "unit": "unidad"},
            {"item": "chorizo", "quantity": 200, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Pelar la cebolla y cortar en juliana fina. Picar los ajos. En una cazuela poner un fondo de aceite y estofar la cebolla y los ajos. Incorporar el chorizo cortado.",
            "Pelar las patatas, chascar con cuchillo y agregar a la cazuela. Añadir el pimentón, mezclar para que no se queme e incorporar la hoja de laurel y la guindilla.",
            "Cubrir con agua y sazonar. Cocer a fuego medio durante unos 30-35 minutos o hasta que las patatas estén tiernas pero enteras."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/patatas-a-la-riojana/"
    },
    {
        "name": "Gambas al Ajillo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "gambas peladas", "quantity": 300, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "guindilla", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "En una sartén a fuego fuerte calentar el aceite.",
            "Incorporar el ajo en láminas, la guindilla e inmediatamente las gambas.",
            "Cocinar durante un minuto.",
            "Fuera del fuego incorporar la pimienta y la sal."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/gambas-al-ajillo/"
    },
    {
        "name": "Yemas de Santa Teresa",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "azúcar", "quantity": 85, "unit": "g"},
            {"item": "agua", "quantity": 50, "unit": "g"},
            {"item": "corteza de limón", "quantity": 0.5, "unit": "unidad"},
            {"item": "yemas de huevo", "quantity": 6, "unit": "unidades"},
            {"item": "azúcar en polvo", "quantity": None, "unit": "para rebozar"}
        ],
        "instructions": [
            "Poner en un cazo el azúcar, el agua y la corteza de limón. Cocer hasta obtener un almíbar de hebra fuerte.",
            "Batir las yemas en un recipiente y pasar por un colador a un cazo. Agregar el almíbar colado y poner de nuevo al fuego, sin dejar de mover con cuchara de madera hasta que la masa se desprenda de las paredes del cazo.",
            "Verter en una fuente y dejar enfriar.",
            "Formar unas bolas pequeñas y pasar por el azúcar en polvo.",
            "Poner cada una de las yemas en una cápsula de papel y servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/yemas/"
    },
    {
        "name": "Bonito en Escabeche",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "lomo de bonito", "quantity": 500, "unit": "g"},
            {"item": "cebolla dulce", "quantity": 150, "unit": "g"},
            {"item": "zanahoria", "quantity": 150, "unit": "g"},
            {"item": "vinagre blanco", "quantity": 1, "unit": "dl"},
            {"item": "aceite", "quantity": 1, "unit": "cucharada"},
            {"item": "agua", "quantity": 1, "unit": "l"},
            {"item": "granos de pimienta negra", "quantity": 10, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner en un puchero las verduras peladas y troceadas, el agua, el vinagre, el aceite, los granos de pimienta y la sal.",
            "Cocer 10 minutos, agregar el bonito, tapar y cocinar durante 2 minutos.",
            "Retirar del fuego, dejar reposar 5 minutos.",
            "Escurrir y dejar enfriar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bonito-en-escabeche/"
    },
    {
        "name": "Escalivada",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "berenjenas", "quantity": 4, "unit": "unidades"},
            {"item": "pimientos rojos grandes", "quantity": 4, "unit": "unidades"},
            {"item": "cebollas", "quantity": 4, "unit": "unidades"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Colocar en una bandeja de horno las berenjenas, los pimientos rojos y las cebollas. Rociar con aceite y meter en el horno a 190ºC de 35 a 40 min o hasta que las verduras estén tiernas.",
            "Para comprobar el punto de cocción, apretarlas entre los dedos. Dejar enfriar.",
            "Pelar las verduras y cortar en tiras largas.",
            "Poner en una bandeja las verduras preparadas. Espolvorear con los dientes de ajo pelados y picados, rociar con aceite y sazonar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/escalivada/"
    },
    {
        "name": "Fritura de Pescado",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "boquerones", "quantity": 300, "unit": "g"},
            {"item": "chipirones", "quantity": 300, "unit": "g"},
            {"item": "salmonetes pequeños", "quantity": 6, "unit": "unidades"},
            {"item": "pescadillas pequeñas", "quantity": 6, "unit": "unidades"},
            {"item": "anillas de calamar", "quantity": 200, "unit": "g"},
            {"item": "harina de garbanzo", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "abundante"},
            {"item": "limón", "quantity": 1, "unit": "unidad"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar los pescados: quitar las cabezas y las tripas a los boquerones; vaciar los chipirones; descamar los salmonetes y retirar las tripas; quitar las cabezas y las vísceras a las pescadillas. Sazonar.",
            "Pasar por harina, sacudir el exceso y freír las piezas por separado en abundante aceite caliente.",
            "Cuando estén dorados, sacar de la sartén y escurrir sobre papel absorbente."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/fritura-de-pescado/"
    },
    {
        "name": "Pimientos Rellenos de Carne",
        "origin_region": "La Rioja",
        "ingredients": [
            {"item": "pimientos del piquillo", "quantity": 18, "unit": "unidades"},
            {"item": "cebolla grande", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "carne de ternera picada", "quantity": 250, "unit": "g"},
            {"item": "magro de cerdo picado", "quantity": 250, "unit": "g"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharadita"},
            {"item": "salsa bechamel", "quantity": 200, "unit": "g"},
            {"item": "harina", "quantity": None, "unit": "para rebozar"},
            {"item": "huevos", "quantity": 2, "unit": "unidades"},
            {"item": "salsa de tomate", "quantity": 150, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Pelar y picar la cebolla fina y rehogar con un poco de aceite sin que coja color. Agregar la carne de ternera y la de cerdo y cocinar el conjunto a fuego lento hasta que las carnes estén hechas.",
            "Incorporar el pimentón, dar una vuelta y añadir la salsa bechamel. Mezclar, sazonar y dejar templar.",
            "Poner en una manga pastelera y rellenar los pimientos del piquillo.",
            "Pasar por harina, sacudir para retirar el exceso y luego por los huevos batidos. Freír en abundante aceite caliente hasta que estén dorados por todos lados. Escurrir sobre papel absorbente.",
            "Calentar la salsa de tomate y servir con los pimientos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/pimientos-rellenos/"
    },
    {
        "name": "Cordero al Chilindrón",
        "origin_region": "Comunidad Foral de Navarra",
        "ingredients": [
            {"item": "cordero", "quantity": 1.2, "unit": "kg"},
            {"item": "cebollas", "quantity": 2, "unit": "unidades"},
            {"item": "cabeza de ajo", "quantity": 1, "unit": "unidad"},
            {"item": "vino blanco", "quantity": 1, "unit": "vaso"},
            {"item": "pimientos choriceros", "quantity": 3, "unit": "unidades"},
            {"item": "ramita de tomillo", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva virgen", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar el cordero en trozos no muy grandes, salpimentar y dorar en una cazuela en un fondito de aceite. Reservar.",
            "Pochar en la misma cazuela la cebolla y el ajo picados.",
            "Cuando el agua que suelta la cebolla esté prácticamente evaporada, añadir la pulpa de los pimientos rojos choriceros.",
            "Volver a incorporar la carne, y añadir la ramita de tomillo y el vaso de vino blanco.",
            "Cocinar a fuego suave con tapa, hasta que la carne quede tierna, entre 30 y 45 minutos.",
            "Si es necesario añadir algo más de líquido puede servir el agua donde hemos dejado a remojo los pimientos choriceros o un poco de caldo."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cordero-al-chilindron/"
    }
])

# Batch 5-8 recipes
SPANISH_RECIPES.extend([
    {
        "name": "Revuelto de Setas",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "setas de temporada", "quantity": 200, "unit": "g"},
            {"item": "huevo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 2, "unit": "cucharadas"},
            {"item": "láminas finas de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta negra", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Lavar las setas con la ayuda de un cepillo de dientes levemente mojado con agua tibia.",
            "Calentar una sartén a fuego vivo con el aceite de oliva. Incorporar las setas y saltear 2 minutos.",
            "Añadir el ajo. Salpimentar.",
            "Incorporar el huevo solo revuelto, sin batir.",
            "Sacar la sartén del fuego y remover la mezcla hasta que empiece a cuajar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/revuelto-de-setas/"
    },
    {
        "name": "Almejas a la Marinera",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "almejas", "quantity": 1.5, "unit": "kg"},
            {"item": "vino blanco seco", "quantity": 200, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": 85, "unit": "g"},
            {"item": "cebolla grande", "quantity": 1, "unit": "unidad"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharadita"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Lavar las almejas en agua fría. Poner en un recipiente con 2 cucharadas de sal durante 30 min. Pasar por agua fría y poner en una cazuela a fuego vivo, con un chorrito de vino blanco.",
            "Tapar la cazuela hasta que las almejas se abran. Colar el caldo de la cocción de las almejas.",
            "Calentar el aceite en una cazuela de barro y rehogar la cebolla pelada y picada fina, sin que coja color. Agregar el pimentón, el resto del vino y el caldo de la cocción de las almejas. Cocer a fuego suave durante 2 min.",
            "Agregar las almejas, sazonar. Calentar todo junto y servir en la misma cazuela."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/almejas-a-la-marinera/"
    },
    {
        "name": "Torrijas",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "barra de pan de miga prieta de la víspera", "quantity": 1, "unit": "unidad"},
            {"item": "leche", "quantity": 1, "unit": "l"},
            {"item": "piel de limón", "quantity": 0.5, "unit": "unidad"},
            {"item": "canela en rama", "quantity": None, "unit": "al gusto"},
            {"item": "azúcar", "quantity": 75, "unit": "g"},
            {"item": "aceite de oliva o girasol", "quantity": None, "unit": "abundante"},
            {"item": "huevos", "quantity": 3, "unit": "unidades"},
            {"item": "azúcar y canela", "quantity": None, "unit": "para rebozar"}
        ],
        "instructions": [
            "Cocer la leche con la piel de limón, el palo de canela y el azúcar. Dejar templar.",
            "Cortar el pan en rebanadas gruesas y empapar en la leche. Reposar en rejilla, para que escurra bien.",
            "Rebozar las rebanadas de pan en los huevos batidos. Freír en abundante aceite caliente hasta dorar por ambos lados.",
            "Escurrir sobre papel absorbente. Rebozar en una mezcla de azúcar y canela."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/torrijas/"
    },
    {
        "name": "Sopa de Ajo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "pan de víspera", "quantity": 150, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "pimentón dulce", "quantity": 0.5, "unit": "cucharada"},
            {"item": "agua o caldo", "quantity": 1.5, "unit": "l"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar el pan en lonchas finas y pelar y picar los dientes de ajo.",
            "Calentar aceite en una sartén y freír el pan hasta que se dore. Agregar los dientes de ajo y antes de que cojan color espolvorear con el pimentón.",
            "Para que no se queme, poner rápidamente el agua caliente. Sazonar y cocer suavemente durante 10 min.",
            "Servir la sopa de ajo en cazuelas individuales de barro."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/sopa-de-ajo/"
    },
    {
        "name": "Pisto Manchego",
        "origin_region": "Castilla-La Mancha",
        "ingredients": [
            {"item": "pimientos verdes", "quantity": 500, "unit": "g"},
            {"item": "calabacines", "quantity": 500, "unit": "g"},
            {"item": "cebollas", "quantity": 500, "unit": "g"},
            {"item": "salsa de tomate", "quantity": 400, "unit": "g"},
            {"item": "diente de ajo", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Pelar las cebollas y lavar los pimientos y los calabacines. Cortar los pimientos, los calabacines y las cebollas en cuadraditos. Picar el ajo.",
            "En una cazuela con un fondo de aceite, freír las cebollas con los pimientos. Añadir el ajo y el calabacín y cocinar hasta que estén tiernos.",
            "Una vez hechos, incorporar la salsa de tomate. Dar un hervor todo junto. Sazonar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/pisto-manchego/"
    },
    {
        "name": "Migas",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "pan seco de víspera", "quantity": 600, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": 125, "unit": "g"},
            {"item": "pimiento verde", "quantity": 1, "unit": "unidad"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "tomates maduros", "quantity": 2, "unit": "unidades"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharada"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar el pan de víspera en trozos muy pequeños. Poner en un recipiente, humedecer con un poco de agua y tapar con un paño.",
            "Calentar el aceite en una sartén honda y rehogar el pimiento y la cebolla cortados finos, sin que tomen color. Incorporar los tomates y los ajos, pelados y picados. Continuar la cocción durante 5 minutos.",
            "Retirar del fuego, agregar el pimentón, dar una vuelta y añadir las migas.",
            "Mezclar, bajar el fuego y continuar la cocción lentamente. Mover a menudo para que no se agarren y sazonar. Servir las migas calientes."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/migas/"
    },
    {
        "name": "Leche Frita",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "leche", "quantity": 500, "unit": "g"},
            {"item": "piel de limón", "quantity": 0.5, "unit": "unidad"},
            {"item": "mantequilla", "quantity": 15, "unit": "g"},
            {"item": "yemas", "quantity": 2, "unit": "unidades"},
            {"item": "azúcar", "quantity": 100, "unit": "g"},
            {"item": "harina fina de maíz", "quantity": 100, "unit": "g"},
            {"item": "harina de trigo", "quantity": None, "unit": "para rebozar"},
            {"item": "huevo", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "para freír"},
            {"item": "azúcar y canela", "quantity": None, "unit": "para rebozar"}
        ],
        "instructions": [
            "Poner en un cazo al fuego la leche con la piel de limón y la mantequilla. Batir las yemas con el azúcar y agregar la harina de maíz. Incorporar la leche hirviendo colada y mezclar bien.",
            "Volver a poner al fuego suave, sin dejar de remover con las varillas, hasta que espese.",
            "Verter en una fuente rectangular de fondo bajo. Tapar con papel film pegado a la superficie para que no haga costra. Enfriar en la nevera durante dos horas.",
            "Cortar la crema en porciones. Pasar por harina y por el huevo batido. Freír en aceite caliente. Escurrir sobre papel absorbente.",
            "Pasar la leche frita por el azúcar y la canela mezclados."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/leche-frita/"
    },
    {
        "name": "Arroz con Leche",
        "origin_region": "Principado de Asturias",
        "ingredients": [
            {"item": "arroz redondo", "quantity": 175, "unit": "g"},
            {"item": "leche", "quantity": 1.5, "unit": "l"},
            {"item": "cáscara de limón", "quantity": 1, "unit": "unidad"},
            {"item": "canela en rama", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "una pizca"},
            {"item": "azúcar", "quantity": 250, "unit": "g"},
            {"item": "canela en polvo", "quantity": 1, "unit": "cucharada"}
        ],
        "instructions": [
            "Poner a hervir la leche con la cáscara de limón, la canela en rama y una pizca de sal. Cuando rompa a hervir, añadir el arroz. Cocer lentamente unos 30 minutos.",
            "Añadir el azúcar y seguir cociendo hasta que el arroz esté tierno; mover de vez en cuando e ir añadiendo un poco de leche caliente si fuera necesario. Debe quedar un poco líquido porque al enfriarse espesa.",
            "Servir espolvoreado con canela."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/arroz-con-leche/"
    },
    {
        "name": "Sobrasada con Queso Mahón Fundido",
        "origin_region": "Illes Balears",
        "ingredients": [
            {"item": "sobrasada", "quantity": 25, "unit": "g"},
            {"item": "queso de Mahón tierno", "quantity": 2, "unit": "lonchas finas"},
            {"item": "pan de coca tierno", "quantity": 1, "unit": "loncha"}
        ],
        "instructions": [
            "Precalentar el horno a 180º grados.",
            "Desmenuzar la sobrasada con un tenedor. Untar el pan de coca.",
            "Cubrir con las lonchas de queso de Mahón.",
            "Meter en el horno durante 4 minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/sobrasada-con-queso-mahon-fundido/"
    },
    {
        "name": "Conejo con Caracoles",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "conejo", "quantity": 2, "unit": "kg"},
            {"item": "caracoles", "quantity": 1, "unit": "kg"},
            {"item": "cebollas", "quantity": 2, "unit": "unidades"},
            {"item": "zanahorias", "quantity": 2, "unit": "unidades"},
            {"item": "tomate frito", "quantity": 100, "unit": "g"},
            {"item": "puerro", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva", "quantity": 200, "unit": "ml"},
            {"item": "tomillo", "quantity": None, "unit": "al gusto"},
            {"item": "hoja de laurel", "quantity": 1, "unit": "unidad"},
            {"item": "caldo de carne o ave", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Purgar los caracoles durante varios días. Lavar en agua con sal. Cambiar el agua varias veces hasta que salga limpia.",
            "Cortar el conejo en trozos y freír una vez pasados por harina; retirar. En el mismo aceite, sofreír las verduras peladas y picadas en trozos pequeños hasta que tomen un ligero color dorado. Volver a incorporar el conejo y añadir el tomate.",
            "Mientras, hacer la picada machacándola en un mortero. Incorporarla a la cazuela del conejo y rehogar unos minutos; mojar con el caldo y dejar cocer hasta que el conejo esté tierno.",
            "Cocer caracoles partiendo de agua fría a fuego lento, cuando empiecen a asomar dejar cocer 10 min. Escurrir. Añadir los caracoles al guiso.",
            "Terminar la cocción cocinándolo todo 10 minutos, rectificar de sal y servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/conejo-con-caracoles/"
    }
])
