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

# Batch 6-9 remaining recipes
SPANISH_RECIPES.extend([
    {
        "name": "Cuajada",
        "origin_region": "País Vasco",
        "ingredients": [
            {"item": "leche de oveja", "quantity": 1, "unit": "l"},
            {"item": "rama de canela", "quantity": 1, "unit": "unidad"},
            {"item": "cuajo", "quantity": 18, "unit": "gotas"}
        ],
        "instructions": [
            "Poner en un cazo la leche de oveja con la rama de canela al fuego.",
            "Cuando rompa a hervir retirar del fuego y dejar enfriar hasta que llegue a una temperatura entre 28 a 30°C. Retirar la rama de canela.",
            "Poner tres gotas de cuajo en 6 moldes de cristal o de barro. Incorporar la leche de oveja a la temperatura indicada, remover ligeramente y dejar enfriar hasta que cuaje.",
            "Servir en el mismo envase."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cuajada/"
    },
    {
        "name": "Arroz Negro",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "cebollas", "quantity": 1, "unit": "kg"},
            {"item": "arroz de grano medio", "quantity": 400, "unit": "g"},
            {"item": "chipirones con su tinta", "quantity": 400, "unit": "g"},
            {"item": "tomates maduros", "quantity": 125, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 100, "unit": "ml"},
            {"item": "caldo de pescado", "quantity": 1, "unit": "l"},
            {"item": "pimentón", "quantity": 1, "unit": "cucharadita"},
            {"item": "tinta de calamar", "quantity": 4, "unit": "paquetitos"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Pelar y picar las cebollas en trozos pequeños. Pochar en una sartén, con un poco de aceite, hasta caramelizar y obtener un color muy oscuro, durante una hora aprox.",
            "Preparar los demás ingredientes: Limpiar los chipirones, reservar la tinta y cortar en aros. Pelar los tomates y los ajos y picar. Poner el caldo de pescado a hervir.",
            "En una paella calentar el aceite. Saltear los chipirones y luego los ajos y el tomate. Añadir el pimentón y rehogar el arroz junto con la cebolla caramelizada.",
            "Mojar con el caldo caliente, sazonar y dejar cocer a fuego vivo 10 minutos. Añadir la tinta desleída en un poco de caldo. Dejar cocer de 6 a 8 minutos a fuego bajo.",
            "Comprobar si el arroz está cocido. Retirar del fuego, dejar reposar 5 minutos y servir en la misma paella."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/arroz-negro/"
    },
    {
        "name": "Sepia al Ajillo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "sepia", "quantity": 150, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 100, "unit": "ml"},
            {"item": "jugo de limón", "quantity": 1, "unit": "cucharada"},
            {"item": "pimentón picante", "quantity": 1, "unit": "cucharadita"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar la sepia y cortarla en tiras.",
            "En una cazuela a fuego fuerte calentar el aceite de oliva, saltear la sepia durante 2 minutos e incorporar el ajo laminado, el pimentón y el jugo de limón.",
            "Salpimentar y servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/sepia-al-ajillo/"
    },
    {
        "name": "Duelos y Quebrantos",
        "origin_region": "Castilla-La Mancha",
        "ingredients": [
            {"item": "chorizos blandos", "quantity": 3, "unit": "unidades"},
            {"item": "panceta o tocino", "quantity": 150, "unit": "g"},
            {"item": "huevos", "quantity": 8, "unit": "unidades"},
            {"item": "cebolletas", "quantity": 2, "unit": "unidades"},
            {"item": "dientes de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Picar las cebolletas en juliana y laminar los ajos. Pochar en 3 cucharadas de aceite y salpimentar.",
            "Cortar en dados el chorizo y la panceta. Incorporar al sofrito y cocinar hasta que estén bien dorados.",
            "Incorporar los huevos enteros, sazonar y cuando empiecen a cuajar apagar el fuego.",
            "Remover todo para que se forme un revuelto.",
            "Servir en el momento."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/duelos-y-quebrantos/"
    },
    {
        "name": "Coliflor al Ajoarriero",
        "origin_region": "Castilla y León",
        "ingredients": [
            {"item": "coliflor grande", "quantity": 1, "unit": "unidad"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 50, "unit": "g"},
            {"item": "pimentón", "quantity": 1, "unit": "cucharada"},
            {"item": "vinagre", "quantity": 2, "unit": "cucharadas"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Dividir en ramilletes la coliflor y cocer en agua hirviendo con sal. Escurrir cuando esté tierna y reservar algo del caldo de la cocción.",
            "Por un lado, hacer un majado: machacar en el mortero uno de los dientes de ajo con sal. Desleír la pasta que se forma con tres cucharadas del agua de cocer la coliflor y otras tres de aceite de oliva crudo.",
            "Por otro lado, poner el resto del aceite en una sartén y dorar el otro diente de ajo picado; retirar y fuera de fuego, incorporar el pimentón, mezclar bien y mojar con el vinagre.",
            "Unir el majado del mortero con el sofrito de la sartén. Mezclar bien y rociar con todo ello la coliflor."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/coliflor-al-ajoarriero/"
    },
    {
        "name": "Arroz con Costra",
        "origin_region": "Comunitat Valenciana",
        "ingredients": [
            {"item": "arroz bomba", "quantity": 400, "unit": "g"},
            {"item": "pollo troceado", "quantity": 400, "unit": "g"},
            {"item": "conejo troceado", "quantity": 300, "unit": "g"},
            {"item": "butifarras blanca y negra", "quantity": 300, "unit": "g"},
            {"item": "longanizas blanca y roja", "quantity": 250, "unit": "g"},
            {"item": "tomate triturado", "quantity": 200, "unit": "g"},
            {"item": "caldo de cocido", "quantity": None, "unit": "al gusto"},
            {"item": "garbanzos cocidos", "quantity": 100, "unit": "g"},
            {"item": "huevos camperos", "quantity": 6, "unit": "unidades"},
            {"item": "hebras de azafrán", "quantity": None, "unit": "al gusto"},
            {"item": "aceite", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar las butifarras en rodajas y marcar por ambos lados en la misma cazuela. Reservar hasta el final del arroz.",
            "Salpimentar el pollo y el conejo y dorar en una cazuela de barro con un fondo de aceite. Reservar.",
            "Trocear las longanizas y dorar también en la cazuela. Añadir el tomate, rehogar hasta que pierda el agua y agregar el arroz para sellar. Incorporar el pollo, el conejo y el azafrán.",
            "Cubrir el arroz con el caldo caliente y cocer 8 minutos a fuego medio-alto.",
            "Batir los huevos, salpimentar.",
            "Poner los garbanzos, colocar las butifarras y repartir los huevos por encima. Llevar al horno a 200º unos 10 minutos.",
            "Sacar del horno, dejar reposar 5 minutos y servir enseguida."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/arroz-con-costra/"
    },
    {
        "name": "Bacalao a la Llauna",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "bacalao en lomos", "quantity": 1.5, "unit": "kg"},
            {"item": "harina", "quantity": None, "unit": "al gusto"},
            {"item": "dientes de ajo en láminas", "quantity": 6, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 200, "unit": "ml"},
            {"item": "caldo de pescado", "quantity": 100, "unit": "ml"},
            {"item": "vino blanco seco", "quantity": 100, "unit": "ml"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharada"},
            {"item": "judías secas cocidas", "quantity": 500, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Desalar el bacalao, escurrir, enharinar y freír. Pasar a una llauna o una fuente de horno de metal.",
            "Colar el aceite de freír el bacalao, poner en otra sartén y freír en él los ajos en láminas; luego añadir el pimentón y mojar con el caldo de pescado y el vino, reducir un poco e incorporar a la fuente del bacalao.",
            "Colocar alrededor las judías ya hervidas.",
            "Meter al horno a 180º y dejar que se haga, unos 10 minutos. Debe quedar prácticamente sin caldo."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bacalao-a-la-llauna/"
    },
    {
        "name": "Ensalada Murciana",
        "origin_region": "Región de Murcia",
        "ingredients": [
            {"item": "bonito en escabeche", "quantity": 1, "unit": "lata"},
            {"item": "tomates enteros al natural", "quantity": 1, "unit": "lata"},
            {"item": "cebolleta", "quantity": 1, "unit": "unidad"},
            {"item": "huevo duro", "quantity": 1, "unit": "unidad"},
            {"item": "aceitunas de Cuquillo aliñadas", "quantity": 50, "unit": "g"},
            {"item": "vinagre", "quantity": 50, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": 110, "unit": "g"},
            {"item": "pimentón", "quantity": 0.5, "unit": "cucharadita"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Escurrir los tomates y cortar en gajos.",
            "Cortar el huevo duro en trozos.",
            "Pelar la cebolleta y cortar en juliana fina.",
            "En un bol mezclar el vinagre con el aceite, el pimentón, la pimienta y la sal. Batir bien hasta que quede todo muy mezclado.",
            "En una ensaladera colocar los tomates, el huevo duro, la cebolleta, el bonito y las aceitunas.",
            "Aliñar con la vinagreta y servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/ensalada-murciana/"
    },
    {
        "name": "Cocido Montañés",
        "origin_region": "Cantabria",
        "ingredients": [
            {"item": "alubias blancas", "quantity": 400, "unit": "g"},
            {"item": "nabo", "quantity": 1, "unit": "unidad"},
            {"item": "patata", "quantity": 1, "unit": "unidad"},
            {"item": "morcilla", "quantity": 1, "unit": "unidad"},
            {"item": "chorizo", "quantity": 1, "unit": "unidad"},
            {"item": "papada de cerdo", "quantity": 100, "unit": "g"},
            {"item": "rabo de cerdo", "quantity": 1, "unit": "unidad"},
            {"item": "oreja de cerdo", "quantity": 1, "unit": "unidad"},
            {"item": "tocino entreverado", "quantity": 100, "unit": "g"},
            {"item": "costilla de cerdo", "quantity": 100, "unit": "g"},
            {"item": "berza o repollo", "quantity": 200, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta negra en grano", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner las alubias a remojar la víspera en abundante agua fría. Al día siguiente, escurrir bien y colocar en una olla grande, junto con los demás ingredientes, excepto la berza. Cubrir todo con agua.",
            "Dejar cocer aproximadamente 2 h y 1/2 a fuego lento. Si se evapora mucho líquido, completar con un poco más de agua.",
            "Media hora antes de terminar la cocción, incorporar la berza lavada y cortada en tiras.",
            "Comprobar la sazón y servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cocido-montanes/"
    },
    {
        "name": "Arroz a la Zamorana",
        "origin_region": "Castilla y León",
        "ingredients": [
            {"item": "oreja de cerdo", "quantity": 1, "unit": "unidad"},
            {"item": "mano de cerdo", "quantity": 1, "unit": "unidad"},
            {"item": "morro de cerdo", "quantity": 1, "unit": "unidad"},
            {"item": "tomillo", "quantity": 1, "unit": "ramita"},
            {"item": "manteca de cerdo", "quantity": 2, "unit": "cucharadas"},
            {"item": "aceite de oliva", "quantity": 2, "unit": "cucharadas"},
            {"item": "cebollas grandes", "quantity": 2, "unit": "unidades"},
            {"item": "dientes de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "nabo", "quantity": 1, "unit": "unidad"},
            {"item": "jamón", "quantity": 180, "unit": "g"},
            {"item": "chorizo picado", "quantity": 1, "unit": "unidad"},
            {"item": "pimentón", "quantity": 2, "unit": "cucharadas"},
            {"item": "arroz redondo", "quantity": 360, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar la oreja, mano y morro de cerdo y escaldar en agua hirviendo durante unos minutos. Desechar el agua y poner a cocer en una cazuela cubiertos de agua salada con el tomillo durante unas 3 horas. Reservar el líquido.",
            "Deshuesar la mano y cortar en trocitos junto con la oreja y el morro.",
            "En una cazuela de barro calentar la manteca de cerdo y el aceite, incorporar la cebolla pelada y cortada finamente, los ajos pelados y en láminas, y los nabos en rodajas. Rehogar todo y cuando empiece a dorarse, añadir el jamón picado y las partes del cerdo.",
            "Mojar el conjunto con 1,5 l de caldo de la cocción de las carnes y dejar cocer lentamente hasta que los nabos estén tiernos.",
            "Agregar el pimentón, el arroz y rectificar de sal. Dejar cocer unos 8 minutos. Meter la cazuela en el horno precalentado unos 10 minutos más.",
            "Retirar del horno y dejar reposar 5 minutos. Servir en la misma cazuela."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/arroz-a-la-zamorana/"
    }
])

# Batch 10-14 remaining recipes
SPANISH_RECIPES.extend([
    {
        "name": "Berenjenas Fritas con Miel",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "berenjenas grandes", "quantity": 2, "unit": "unidades"},
            {"item": "leche", "quantity": 1, "unit": "l"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "harina", "quantity": None, "unit": "para rebozar"},
            {"item": "aceite", "quantity": None, "unit": "para freír"},
            {"item": "miel de caña", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar las berenjenas limpias en bastones conservando la piel.",
            "Remojar una media hora en la leche fría con sal.",
            "Escurrir y secar muy bien. Salpimentar los bastones y rebozar con harina.",
            "Freír en abundante aceite caliente hasta que estén dorados y crujientes.",
            "Servir recién hechos con miel de caña."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/berenjenas-fritas/"
    },
    {
        "name": "Castañas con Leche",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "castañas", "quantity": 1, "unit": "kg"},
            {"item": "hinojo", "quantity": 0.5, "unit": "bulbo"},
            {"item": "leche", "quantity": 1, "unit": "l"},
            {"item": "azúcar", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Pelar las castañas y quitar la película que las recubre.",
            "Poner a cocer de nuevo, ahora bien limpias, en agua con un poco de sal y el hinojo. A media cocción retirar del fuego y escurrir, desechando el hinojo.",
            "Poner con la leche ya caliente, de nuevo al fuego, dejar que cuezan hasta que estén tiernas.",
            "Poner en una fuente y dejar que se enfríen. Espolvorear con azúcar antes de servir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/castanas-con-leche/"
    },
    {
        "name": "Almendras Garrapiñadas",
        "origin_region": "Comunidad de Madrid",
        "ingredients": [
            {"item": "almendras crudas con piel", "quantity": 150, "unit": "g"},
            {"item": "azúcar", "quantity": 150, "unit": "g"},
            {"item": "aceite", "quantity": 1, "unit": "cucharada"},
            {"item": "zumo de limón", "quantity": 1, "unit": "cucharada"}
        ],
        "instructions": [
            "Tostar las almendras en una sartén caliente sin nada de grasa. Reservar.",
            "En una sartén profunda poner el azúcar y el zumo de limón al fuego. Remover con cuchara de madera y cuando empiece a tomar punto de caramelo, añadir las almendras enteras, removiendo bien.",
            "Mantener a fuego medio sin dejar de remover, hasta que el azúcar quede grumoso.",
            "En cuanto adquieran un color rubio tirando a tostado, sacar sobre una placa previamente untada con el aceite. Separar con un tenedor y dejar enfriar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/almendras-garrapinadas/"
    },
    {
        "name": "Espárragos Blancos con Huevo",
        "origin_region": "Comunidad Foral de Navarra",
        "ingredients": [
            {"item": "espárragos blancos frescos de Navarra", "quantity": 36, "unit": "unidades"},
            {"item": "sal", "quantity": 1, "unit": "cucharadita"},
            {"item": "azúcar", "quantity": 0.5, "unit": "cucharadita"},
            {"item": "huevos frescos", "quantity": 6, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "vinagre de vino", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Lavar y secar los espárragos. Pelar con un pelador sacando la piel superficialmente desde debajo de la yema hasta el final del tallo. Cortar la parte final más dura del tallo.",
            "En una cazuela alta poner el agua con el azúcar y la sal. Cuando empiece a hervir, introducir el manojo de espárragos con las yemas hacia arriba durante 30 minutos.",
            "Añadir los huevos en bolsitas de plástico engrasadas y continuar durante 3 minutos más.",
            "Retirar la cazuela y dejar reposar durante 5-10 minutos.",
            "Alinear en un plato los espárragos, poner encima los huevos cortados por la mitad y añadir vinagre y aceite al gusto."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/esparragos-blancos-cocidos-con-huevo-escalfado/"
    },
    {
        "name": "All i Pebre",
        "origin_region": "Comunitat Valenciana",
        "ingredients": [
            {"item": "anguila fresca", "quantity": 1, "unit": "kg"},
            {"item": "patata", "quantity": 1.2, "unit": "kg"},
            {"item": "cabezas de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "pimentón dulce", "quantity": 2, "unit": "cucharadas"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Freír los dientes de ajos picados en dos, en aceite a fuego suave. Reservar aparte.",
            "Pelar las patatas, lavar y chascar. Añadir al aceite en el que hemos frito los ajos, subir el fuego y cocinar durante cinco minutos. Añadir el pimentón, cubrir con agua, y cocinar hasta que las patatas estén blandas.",
            "Majar los ajos en un mortero con un poco de sal, y añadir la pasta de ajos a la cazuela, junto con la anguila troceada.",
            "Dejar que se haga a fuego medio todo junto durante unos 10-15 minutos.",
            "Rectificar de sal y pimienta, apagar y dejar reposar unos minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/all-i-pebre/"
    },
    {
        "name": "Espinacas a la Catalana",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "espinacas", "quantity": 2, "unit": "kg"},
            {"item": "aceite", "quantity": 1, "unit": "dl"},
            {"item": "ajo picado", "quantity": 1, "unit": "unidad"},
            {"item": "pasas gordas", "quantity": 50, "unit": "g"},
            {"item": "piñones", "quantity": 50, "unit": "g"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Hervir las espinacas en uno o dos dedos de agua y sal. Escurrir y enfriar con agua y hielos para que conserven el color verde.",
            "En una sartén con el aceite tostar apenas los piñones, a continuación, añadir las espinacas y las pasas. Salpimentar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/espinacas-a-la-catalana/"
    },
    {
        "name": "Casadielles",
        "origin_region": "Principado de Asturias",
        "ingredients": [
            {"item": "vino blanco", "quantity": 250, "unit": "g"},
            {"item": "yema de huevo grande", "quantity": 1, "unit": "unidad"},
            {"item": "mantequilla", "quantity": 120, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "una pizca"},
            {"item": "harina floja", "quantity": 500, "unit": "g"},
            {"item": "levadura en polvo", "quantity": 1, "unit": "cucharadita"},
            {"item": "nueces", "quantity": 230, "unit": "g"},
            {"item": "azúcar", "quantity": 100, "unit": "g"},
            {"item": "anís dulce", "quantity": 60, "unit": "ml"},
            {"item": "aceite", "quantity": 0.5, "unit": "l"}
        ],
        "instructions": [
            "Para la masa: Tamizar la harina con la levadura en polvo y mezclar con la mantequilla. Mezclar el vino con la yema. Añadir la mezcla seca en dos a tres partes, a mano sin amasar, solo hasta lograr una masa blanda.",
            "Extender con ayuda de un rodillo y doblar en tres. Repetir esta operación tres veces. Tapar y dejar reposar en la nevera una hora.",
            "Para el relleno: Picar a cuchillo la mitad de las nueces, y rallar el resto. Mezclar las nueces con el azúcar, el anís y la mantequilla.",
            "Montaje: Estirar porciones de masa de 2 mm de grosor y cortar cuadrados de 10x10. Humedecer los bordes con un poco de agua, poner una cucharada de relleno a un extremo de la masa, enrollar.",
            "Fritura: Calentar el aceite de oliva en un cazo profundo. Freír por tandas, hasta que queden dorados. Rebozar en azúcar cuando aún estén calientes."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/casadielles/"
    },
    {
        "name": "Besugo a la Madrileña",
        "origin_region": "Comunidad de Madrid",
        "ingredients": [
            {"item": "besugo grande", "quantity": 1, "unit": "unidad"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "dientes de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "patatas grandes", "quantity": 4, "unit": "unidades"},
            {"item": "aceite de oliva", "quantity": 1, "unit": "cucharón"},
            {"item": "pan rallado", "quantity": 100, "unit": "g"},
            {"item": "limón", "quantity": 1, "unit": "unidad"},
            {"item": "vino blanco", "quantity": 1, "unit": "vaso"},
            {"item": "pimienta blanca", "quantity": 1, "unit": "cucharadita"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar el pescado y hacer tres incisiones en el lomo introduciendo en cada una media luna de limón.",
            "Colocar el besugo en una bandeja para horno, sazonar con sal, pimienta y vino blanco y espolvorear con pan rallado mezclado con ajo picado.",
            "Rociar con una cucharada de aceite y meter al horno precalentado a 180º junto con un vaso de vino blanco sobre una cama de patatas y cebolla previamente asadas.",
            "Cocinar 20 minutos el primer kilo, añadiendo 10 minutos por cada kilo adicional."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/besugo-a-la-madrilena/"
    },
    {
        "name": "Alcachofas a la Montillana",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "alcachofas", "quantity": 1, "unit": "kg"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "jamón serrano en dados", "quantity": 75, "unit": "g"},
            {"item": "vino fino", "quantity": 200, "unit": "ml"},
            {"item": "limón", "quantity": 1, "unit": "unidad"},
            {"item": "almidón de maíz", "quantity": 1, "unit": "cucharadita"},
            {"item": "aceite de oliva virgen extra", "quantity": 50, "unit": "ml"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar las alcachofas y frotar con medio limón. Hervir en abundante agua con sal y retirar cuando estén tiernas.",
            "Rehogar la cebolla cortada muy pequeña y el ajo picado en el aceite. Cuando estén transparentes, añadir el almidón de maíz.",
            "Incorporar las alcachofas y mover bien. Añadir el jamón y el vino, bajar el fuego y dejar estofar 15 minutos suavemente.",
            "Añadir agua de la cocción de las alcachofas si hiciera falta, rectificar de sal."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/alcachofas-a-la-montillana/"
    },
    {
        "name": "Bocartes en Cazuela",
        "origin_region": "Cantabria",
        "ingredients": [
            {"item": "bocartes o anchoas", "quantity": 24, "unit": "unidades"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "vino blanco", "quantity": 0.5, "unit": "copa"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "vinagre de vino", "quantity": None, "unit": "al gusto"},
            {"item": "guindilla en vinagre", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar los bocartes, quitar la cabeza y las espinas. Lavar y secar bien.",
            "En una cazuela freír los ajos, añadir los bocartes y rehogar un poco a fuego fuerte moviendo la cazuela; mojar con el vino y un poco de vinagre.",
            "Espolvorear con la guindilla picada y dejar cocer unos cinco minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bocartes-en-cazuela/"
    },
    {
        "name": "Carrilleras de Cerdo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "carrilleras de cerdo ibérico", "quantity": 18, "unit": "unidades"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "cebollas dulces", "quantity": 3, "unit": "unidades"},
            {"item": "tomillo", "quantity": 1, "unit": "ramita"},
            {"item": "romero", "quantity": 1, "unit": "ramita"},
            {"item": "hojas de laurel", "quantity": 2, "unit": "unidades"},
            {"item": "vino tinto", "quantity": 1, "unit": "vaso"},
            {"item": "caldo de carne", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Salpimentar las carrilleras. Dorar en una cazuela con un poco de aceite. Retirar.",
            "En el mismo aceite estofar a fuego suave, las cebollas muy picadas.",
            "Volver a poner la carne en la cazuela, agregar las hierbas y dar un par de vueltas al conjunto.",
            "Agregar el vino tinto, subir el fuego y dejar que se evapore el alcohol.",
            "Cubrir con caldo o agua y dejar cocer a fuego suave unas dos horas.",
            "Deben de quedar jugosas y con salsa."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/carrilleras/"
    },
    {
        "name": "Bonito con Tomate",
        "origin_region": "País Vasco",
        "ingredients": [
            {"item": "bonito en tacos", "quantity": 1, "unit": "kg"},
            {"item": "tomates", "quantity": 3, "unit": "kg"},
            {"item": "cebolla", "quantity": 1, "unit": "unidad"},
            {"item": "diente de ajo", "quantity": 1, "unit": "unidad"},
            {"item": "pimiento verde", "quantity": 1, "unit": "unidad"},
            {"item": "hoja de laurel", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Limpiar el bonito de restos de piel y espinas. Sazonar los trozos de bonito.",
            "Dorar en una sartén por todos los lados con un poco de aceite caliente, dejando el centro crudo.",
            "Pelar y cortar la cebolla, el ajo y el pimiento en dados pequeños.",
            "Rehogar la cebolla y el pimiento en el aceite de dorar el bonito. Cuando estén transparentes añadir el ajo picado, los tomates limpios y troceados y la hoja de laurel.",
            "Cocer hasta que se evapore el agua que sueltan los tomates. Sazonar.",
            "Calentar la salsa de tomate al fuego y cuando rompa a hervir añadir el bonito dorado y cocer todo junto muy pocos minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bonito-con-tomate/"
    },
    {
        "name": "Canutillos de Crema",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "masa de hojaldre", "quantity": 500, "unit": "g"},
            {"item": "harina", "quantity": None, "unit": "para trabajar la masa"},
            {"item": "huevo batido", "quantity": 1, "unit": "unidad"},
            {"item": "leche", "quantity": 0.5, "unit": "l"},
            {"item": "azúcar", "quantity": 150, "unit": "g"},
            {"item": "yemas de huevo", "quantity": 6, "unit": "unidades"},
            {"item": "harina", "quantity": 20, "unit": "g"},
            {"item": "fécula de maíz", "quantity": 20, "unit": "g"},
            {"item": "azúcar glass", "quantity": None, "unit": "para espolvorear"}
        ],
        "instructions": [
            "Sobre una superficie enharinada extender el hojaldre. Cortar en tiras de unos 4 cm de ancho y enrollar en los moldes especiales para canutillos.",
            "Colocar sobre una placa de horno y pintar por la parte de arriba con huevo batido.",
            "Meter en horno precalentado a 200°C durante unos 15 minutos. Retirar con cuidado de los moldes y dejar enfriar para rellenar.",
            "Para la crema pastelera: Llevar a hervor la leche. En un bol batir las yemas con el azúcar hasta que blanqueen. Añadir la fécula de maíz y la harina. Añadir la leche a la mezcla de las yemas, sin dejar de batir. Poner de nuevo en el cazo a fuego suave y cocinar hasta que espese.",
            "Retirar del fuego y dejar enfriar. Una vez fría se pueden rellenar los canutillos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/canutillos-de-crema/"
    },
    {
        "name": "Boquerones en Vinagre",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "boquerones medianos", "quantity": 500, "unit": "g"},
            {"item": "agua", "quantity": 100, "unit": "g"},
            {"item": "vinagre blanco", "quantity": 100, "unit": "g"},
            {"item": "sal gorda", "quantity": 1, "unit": "cucharada sopera"},
            {"item": "aceite de oliva", "quantity": 100, "unit": "g"},
            {"item": "diente de ajo", "quantity": 1, "unit": "unidad"}
        ],
        "instructions": [
            "Limpiar bien los boquerones. Separar los lomos retirando la espina. Pasar por agua fría.",
            "Colocar en un recipiente los lomos de los boquerones y cubrir con el agua, el vinagre y la sal, durante 4 horas. Escurrir.",
            "Disponer en un plato. Rociar con aceite de oliva y ajo picado."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/boquerones-en-vinagre/"
    },
    {
        "name": "Cangrejos de Río",
        "origin_region": "Castilla y León",
        "ingredients": [
            {"item": "cangrejos de río", "quantity": 1, "unit": "kg"},
            {"item": "aceite de oliva", "quantity": 100, "unit": "g"},
            {"item": "dientes de ajo", "quantity": 3, "unit": "unidades"},
            {"item": "brandy", "quantity": 250, "unit": "g"},
            {"item": "vino blanco seco", "quantity": 250, "unit": "g"},
            {"item": "caldo de pescado", "quantity": 250, "unit": "g"},
            {"item": "salsa de tomate frito", "quantity": 200, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Lavar los cangrejos cuidadosamente retirando el intestino que tienen a lo largo del cuerpo.",
            "Poner el aceite en una cazuela y saltear los cangrejos hasta que éstos adquieran color rojo.",
            "Agregar los dientes de ajo picados y flambear con el brandy. Regar con el vino blanco, el caldo de pescado y el tomate.",
            "Dejar cocer todo junto unos 15 minutos. Salpimentar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cangrejos-de-rio/"
    },
    {
        "name": "Boquerones Fritos",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "boquerones medianos enteros", "quantity": 500, "unit": "g"},
            {"item": "harina", "quantity": 100, "unit": "g"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva", "quantity": 1, "unit": "dl"}
        ],
        "instructions": [
            "Retirar la cabeza y las vísceras de los boquerones. Dejar en agua con hielo durante una hora.",
            "Pasar por la harina, tamizar y freír en una sartén con el aceite a fuego vivo.",
            "Escurrir. Sazonar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/boquerones-fritos/"
    },
    {
        "name": "Tarta de Santiago",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "huevos", "quantity": 5, "unit": "unidades"},
            {"item": "azúcar", "quantity": 250, "unit": "g"},
            {"item": "ralladura de limón", "quantity": 1, "unit": "unidad"},
            {"item": "canela en polvo", "quantity": 1, "unit": "cucharadita"},
            {"item": "almendras molidas", "quantity": 250, "unit": "g"},
            {"item": "azúcar glas", "quantity": 50, "unit": "g"}
        ],
        "instructions": [
            "Batir los huevos con el azúcar. Agregar la ralladura de limón, la canela y las almendras molidas.",
            "Mezclar todos los ingredientes y rellenar un molde engrasado y enharinado.",
            "Meter en el horno precalentado a 160ºC durante 35 min. Sacar del horno y dejar enfriar.",
            "Desmoldar la tarta. Colocar encima una plantilla de la cruz de Santiago. Espolvorear con el azúcar glas y retirar la plantilla."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/tarta-de-santiago/"
    },
    {
        "name": "Huevos a la Flamenca",
        "origin_region": "Andalucía",
        "ingredients": [
            {"item": "judías verdes tiernas", "quantity": 100, "unit": "g"},
            {"item": "guisantes", "quantity": 100, "unit": "g"},
            {"item": "tomates", "quantity": 250, "unit": "g"},
            {"item": "patatas", "quantity": 150, "unit": "g"},
            {"item": "jamón", "quantity": 100, "unit": "g"},
            {"item": "chorizo", "quantity": 100, "unit": "g"},
            {"item": "aceite de oliva virgen extra", "quantity": None, "unit": "al gusto"},
            {"item": "cebolla pequeña", "quantity": 1, "unit": "unidad"},
            {"item": "huevos", "quantity": 6, "unit": "unidades"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Cortar las judías verdes en trocitos pequeños. Cocer con los guisantes en agua hirviendo con sal durante 10 min. Pasar por agua fría y escurrir.",
            "Pelar los tomates, quitar las semillas y picar. Pelar y cortar las patatas en dados y cocer en agua hirviendo durante 5 min. Escurrir. Cortar el jamón en tiras y el chorizo en dados.",
            "En un poco de aceite rehogar la cebolla pelada y picada fino. Cuando comience a tomar color, añadir el jamón y el tomate. Dejar reducir e incorporar las judías verdes, los guisantes, las patatas y el chorizo. Salpimentar.",
            "Repartir las verduras en cazuelitas individuales, hacer un hueco y cascar un huevo en cada una.",
            "Tapar las cazuelitas y meter en el horno precalentado a 200ºC hasta que las claras estén cuajadas."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/huevos-a-la-flamenca/"
    },
    {
        "name": "Canelones",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "ternera picada", "quantity": 160, "unit": "g"},
            {"item": "magro de cerdo picado", "quantity": 160, "unit": "g"},
            {"item": "pechuga de pollo en daditos", "quantity": 160, "unit": "g"},
            {"item": "cebolla picada", "quantity": 1, "unit": "unidad"},
            {"item": "vino blanco", "quantity": 1, "unit": "copa"},
            {"item": "paté de campaña", "quantity": 50, "unit": "g"},
            {"item": "tomate concentrado", "quantity": 2, "unit": "cucharadas"},
            {"item": "placas de canelones precocidos", "quantity": 18, "unit": "unidades"},
            {"item": "salsa bechamel", "quantity": 1, "unit": "l"},
            {"item": "queso rallado", "quantity": None, "unit": "al gusto"},
            {"item": "aceite", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Preparar el relleno poniendo en una sartén la cebolla picada con el aceite de oliva. Estofar e incorporar las carnes, rehogar todo junto.",
            "Mojar con el vino, dejar evaporar a fuego fuerte. Agregar el tomate, sazonar y rehogar todo junto a fuego bajo 20 minutos. Incorporar el paté, mezclar y dejar enfriar.",
            "Ablandar las placas de canelones en agua tibia con un chorrito de aceite. Escurrir, disponer sobre un paño seco y rellenar con la pasta.",
            "Disponer los canelones en una fuente de horno, cubrir con la bechamel, espolvorear con queso rallado y gratinar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/canelones/"
    },
    {
        "name": "Huevas Aliñadas",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "huevas de merluza", "quantity": 300, "unit": "g"},
            {"item": "pimiento rojo", "quantity": 50, "unit": "g"},
            {"item": "tomate", "quantity": 50, "unit": "g"},
            {"item": "cebolla dulce", "quantity": 50, "unit": "g"},
            {"item": "aceite de oliva", "quantity": 3, "unit": "cucharadas"},
            {"item": "vinagre blanco", "quantity": 1, "unit": "cucharada"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Envolver las huevas en papel transparente. Cocer 30 minutos en agua hirviendo.",
            "Pasarlas a un colador. Pinchar con cuchillo para que suelten el agua interior. Dejar enfriar y cortar en finas rodajas.",
            "Picar el pimiento, el tomate, la cebolla y mezclar con el aceite y el vinagre y la sal.",
            "Cubrir las huevas con la vinagreta."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/huevas-alinadas-2/"
    },
    {
        "name": "Tortilla de Bacalao",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "bacalao fresco desmigado desalado", "quantity": 150, "unit": "g"},
            {"item": "huevos medianos", "quantity": 4, "unit": "unidades"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva", "quantity": 2, "unit": "cucharadas"}
        ],
        "instructions": [
            "Batir los huevos. Mezclar con el bacalao. Salpimentar.",
            "En una sartén calentar el aceite. Incorporar la preparación.",
            "Cuajar la tortilla por todos los lados."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/tortilla-de-bacalao/"
    },
    {
        "name": "Filloas",
        "origin_region": "Galicia",
        "ingredients": [
            {"item": "huevos", "quantity": 4, "unit": "unidades"},
            {"item": "harina de trigo", "quantity": 50, "unit": "g"},
            {"item": "leche", "quantity": 330, "unit": "g"},
            {"item": "mantequilla", "quantity": 75, "unit": "g"},
            {"item": "azúcar glas", "quantity": 50, "unit": "g"},
            {"item": "canela molida", "quantity": 1, "unit": "cucharada"},
            {"item": "sal", "quantity": None, "unit": "una pizca"}
        ],
        "instructions": [
            "Batir los huevos en un recipiente. Agregar la harina, 50 g de mantequilla fundida, la leche y la sal. Mezclar muy bien.",
            "Poner una sartén al fuego y engrasar con un pellizco de mantequilla. Poner una cucharada de la preparación de modo que cubra el fondo de la sartén.",
            "Cuando esté dorada por un lado y se desprenda fácilmente de la sartén dar la vuelta.",
            "Repetir la operación con el resto de la masa.",
            "Doblar las filloas, colocar en un plato y espolvorear con el azúcar glas y la canela mezclados."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/filloas/"
    },
    {
        "name": "Cabrito Asado",
        "origin_region": "Castilla y León",
        "ingredients": [
            {"item": "cabrito", "quantity": 2, "unit": "kg"},
            {"item": "manteca de cerdo", "quantity": None, "unit": "al gusto"},
            {"item": "dientes de ajo", "quantity": 4, "unit": "unidades"},
            {"item": "tomillo", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "vino blanco", "quantity": 1, "unit": "copita"}
        ],
        "instructions": [
            "Majar los dientes de ajo con sal, tomillo y un poco de vino.",
            "Una vez bien limpio el cabrito se coloca, bien engrasado en manteca, sobre una fuente de horno.",
            "Hornear a 160º, y a los 30 minutos repartir el majado por encima del cabrito.",
            "Seguir horneando durante 1 hora y media más, dándole la vuelta a mitad de cocción, y regando de vez en cuando con la grasa que suelta y el resto del vino, hasta que esté dorado y tierno."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/cabrito-asado/"
    },
    {
        "name": "Almejas al Ajillo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "almejas frescas", "quantity": 300, "unit": "g"},
            {"item": "aceite de oliva", "quantity": 1, "unit": "dl"},
            {"item": "ajo", "quantity": 15, "unit": "g"},
            {"item": "cebolleta", "quantity": 1, "unit": "unidad"},
            {"item": "vino blanco", "quantity": 2, "unit": "dl"},
            {"item": "sal gorda", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta negra", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Poner las almejas en agua con hielo una hora.",
            "Pochar en una cazuela con el aceite caliente el ajo y la cebolleta. Incorporar el vino blanco.",
            "Cuando hierva añadir las almejas. Tapar hasta que las almejas se abran.",
            "Añadir la sal."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/almejas-al-ajillo/"
    },
    {
        "name": "Mejillones en Escabeche",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "mejillones frescos", "quantity": 1, "unit": "kg"},
            {"item": "pimiento rojo", "quantity": 50, "unit": "g"},
            {"item": "pimiento verde", "quantity": 50, "unit": "g"},
            {"item": "cebolla dulce", "quantity": 50, "unit": "g"},
            {"item": "vino blanco", "quantity": 1, "unit": "dl"},
            {"item": "aceite de oliva", "quantity": 50, "unit": "g"},
            {"item": "vinagre blanco", "quantity": 1, "unit": "cucharada sopera"},
            {"item": "pimienta negra", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Raspar con cuchillo las conchas de los mejillones debajo del grifo del agua.",
            "Poner una olla con el vino blanco y los mejillones a fuego vivo. Cocer hasta que se abran.",
            "Retirar del fuego y colar el caldo.",
            "Picar los pimientos y la cebolla. Salpimentar. Repartir por los mejillones y rociar con el aceite batido con el caldo."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/mejillones-en-vinagre/"
    },
    {
        "name": "Butifarra con Setas",
        "origin_region": "Cataluña",
        "ingredients": [
            {"item": "butifarras frescas", "quantity": 4, "unit": "unidades"},
            {"item": "rovellons o níscalos", "quantity": 250, "unit": "g"},
            {"item": "cebolla picada", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva", "quantity": 1, "unit": "dl"},
            {"item": "dientes de ajo", "quantity": 2, "unit": "unidades"},
            {"item": "tomate pelado y sin pepitas", "quantity": 0.5, "unit": "unidad"},
            {"item": "almendras tostadas", "quantity": 5, "unit": "unidades"},
            {"item": "caldo de carne", "quantity": 1, "unit": "dl"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "pimienta", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "En una cazuela pochar la cebolla en el aceite y dorar ligeramente. Añadir las butifarras y dorar por ambos lados.",
            "Añadir los rovellons limpios, y dejar cocinar unos minutos.",
            "Mientras, en un mortero, machacar todos los ingredientes de la picada.",
            "Espolvorear con ella la cazuela, y dejar cocer todo junto unos 15 minutos."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/butifarra-con-rovellons/"
    },
    {
        "name": "Buñuelos de Bacalao",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "bacalao fresco desmigado y desalado", "quantity": 200, "unit": "g"},
            {"item": "leche", "quantity": 2, "unit": "dl"},
            {"item": "harina", "quantity": 100, "unit": "g"},
            {"item": "huevo mediano", "quantity": 2, "unit": "unidades"},
            {"item": "pimienta blanca", "quantity": None, "unit": "al gusto"},
            {"item": "sal", "quantity": None, "unit": "al gusto"},
            {"item": "aceite de oliva", "quantity": 2, "unit": "dl"}
        ],
        "instructions": [
            "Picar finamente el bacalao, mezclar con el huevo batido, la leche y la harina hasta conseguir una masa espesa. Salpimentar.",
            "Calentar el aceite a fuego vivo en una sartén e incorporar cucharadas de la preparación.",
            "Freír hasta que queden doradas y crujientes. Escurrir."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bunuelos-de-bacalao-2/"
    },
    {
        "name": "Prueba de Picadillo",
        "origin_region": "Toda España",
        "ingredients": [
            {"item": "carne magra de cerdo picada", "quantity": 130, "unit": "g"},
            {"item": "tocino picado", "quantity": 30, "unit": "g"},
            {"item": "jamón serrano picado", "quantity": 30, "unit": "g"},
            {"item": "diente de ajo", "quantity": 1, "unit": "unidad"},
            {"item": "aceite de oliva", "quantity": 1, "unit": "cucharada sopera"},
            {"item": "pimentón dulce", "quantity": 1, "unit": "cucharada de café"},
            {"item": "vino blanco", "quantity": 1, "unit": "dl"},
            {"item": "sal", "quantity": None, "unit": "al gusto"}
        ],
        "instructions": [
            "Rehogar en una cazuela con el aceite de oliva, la carne, el tocino y el jamón.",
            "Agregar el ajo picado y el pimentón. Salar.",
            "Añadir el vino blanco y reducir.",
            "Por último, dejar hervir hasta que el líquido quede consumido. Sazonar."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/prueba-de-picadillo/"
    },
    {
        "name": "Buñuelos de Plátano",
        "origin_region": "Canarias",
        "ingredients": [
            {"item": "huevos", "quantity": 2, "unit": "unidades"},
            {"item": "harina", "quantity": 160, "unit": "g"},
            {"item": "azúcar", "quantity": 100, "unit": "g"},
            {"item": "levadura en polvo", "quantity": 10, "unit": "g"},
            {"item": "leche", "quantity": 200, "unit": "ml"},
            {"item": "aceite de oliva", "quantity": 2, "unit": "cucharadas"},
            {"item": "sal", "quantity": None, "unit": "una pizca"},
            {"item": "plátanos firmes", "quantity": 5, "unit": "unidades"},
            {"item": "brandy", "quantity": 1, "unit": "copita"},
            {"item": "azúcar en polvo", "quantity": 2, "unit": "cucharadas"},
            {"item": "aceite para freír", "quantity": 0.5, "unit": "l"}
        ],
        "instructions": [
            "Separar las yemas de las claras. En un bol poner la harina y la levadura tamizadas, hacer un hueco en el centro y añadir las yemas, el azúcar, el aceite, la leche y la sal. Mezclar bien todos los ingredientes.",
            "Tapar el bol y dejar reposar 2 horas. Partir los plátanos en rodajas y poner a macerar en el brandy.",
            "Montar las claras a punto de nieve e incorporar a la masa ya reposada, con movimientos envolventes.",
            "Escurrir los plátanos del brandy, secar y pasar de uno en uno por la masa.",
            "Cuando el aceite esté caliente, freír hasta que adquieran un color dorado.",
            "Retirar, escurrir y servir espolvoreados del azúcar en polvo."
        ],
        "source_url": "https://realacademiadegastronomia.com/recetas/bunuelos-de-platano/"
    }
])

def generate_slug(name):
    """Generate URL-friendly slug from recipe name"""
    slug = name.lower()
    slug = re.sub(r'[áàäâ]', 'a', slug)
    slug = re.sub(r'[éèëê]', 'e', slug)
    slug = re.sub(r'[íìïî]', 'i', slug)
    slug = re.sub(r'[óòöô]', 'o', slug)
    slug = re.sub(r'[úùüû]', 'u', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

async def ingest_recipes():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME')]
    
    inserted = 0
    skipped = 0
    
    print(f"Starting ingestion of {len(SPANISH_RECIPES)} Spanish recipes...")
    
    for recipe in SPANISH_RECIPES:
        # Check for duplicate by name + origin_region
        existing = await db.recipes.find_one({
            "recipe_name": recipe["name"],
            "origin_region": recipe["origin_region"]
        })
        
        if existing:
            print(f"  ⏭️  Skipping duplicate: {recipe['name']} ({recipe['origin_region']})")
            skipped += 1
            continue
        
        # Map to database schema
        doc = {
            "id": str(uuid4()),
            "recipe_name": recipe["name"],
            "slug": generate_slug(recipe["name"]),
            "origin_country": "Spain",  # Canonical English form
            "origin_region": recipe["origin_region"],
            "ingredients": recipe["ingredients"],
            "instructions": recipe["instructions"],
            "source_url": recipe.get("source_url", ""),
            "authenticity_level": 1,
            "published": True,
            "featured": False,
            "source": "Real Academia de Gastronomía",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "content_language": "es"
        }
        
        await db.recipes.insert_one(doc)
        print(f"  ✅ Inserted: {recipe['name']}")
        inserted += 1
    
    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Total Spanish recipes now: {await db.recipes.count_documents({'origin_country': 'Spain'})}")

if __name__ == "__main__":
    asyncio.run(ingest_recipes())
