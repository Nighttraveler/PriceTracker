#!/usr/bin/env python3
"""
normalizer.py — Normaliza nombres de productos y hace fuzzy matching entre fuentes.
"""

import re
import unicodedata
from rapidfuzz import fuzz

UMBRAL_SIMILITUD = 98

# Orden importa: categorías más específicas primero para evitar falsos positivos.
CATEGORIAS = {
    # ── Combos / packs ─────────────────────────────────────────────────────────
    # Solo "combo" como palabra exacta — evita falsos positivos con "doypack", "packshot", etc.
    "combos": [
        "combo",
    ],

    # ── Conservas y encurtidos ──────────────────────────────────────────────────
    "conservas": [
        "aceituna", "pickles", "alcaucil", "anchoa", "sardina",
        "morron en lata", "choclo en lata", "arvejas en lata", "poroto en lata",
        "tomates perita", "tomates en lata", "pure de tomate",
        "concentrado de tomate", "pasta de tomate",
    ],

    # ── Fiambrería ──────────────────────────────────────────────────────────────
    "fiambreria": [
        "salame", "mortadela", "pate", "longaniza", "salchichon",
        "queso por salut", "fiambre", "bondiola", "copa",
    ],

    # ── Galletitas (antes de confitería para priorizar) ─────────────────────────
    "galletitas": [
        "galletita", "cracker", "wafer", "barquillo",
    ],

    # ── Snacks salados ──────────────────────────────────────────────────────────
    "snacks": [
        "papas fritas", "palomitas", "nachos", "chizito",
        "palito salado", "palitos salados", "poperine",
        "mani salado", "mani con", "mani tostado",
        "tostada de arroz",
    ],

    # ── Confitería / dulces ─────────────────────────────────────────────────────
    "confiteria": [
        "alfajor", "chocolate", "caramelo", "chicle", "gomita",
        "turron", "pochoclo", "golosina", "tableta", "bombon",
        "chupetine", "paleta dulce", "marshmallow", "oblea",
    ],

    # ── Condimentos y salsas ────────────────────────────────────────────────────
    "condimentos": [
        "mayonesa", "ketchup", "mostaza", "aderezo", "aceto",
        "salsa golf", "salsa de soja", "salsa bbq", "salsa worcestershire",
        "salsa teriyaki", "salsa de tomate", "salsa lista",
        "oregano", "aji molido", "pimienta", "comino", "curcuma",
        "pimenton", "paprika", "canela", "jengibre", "nuez moscada",
        "albahaca", "laurel", "romero", "tomillo", "coriandro",
        "condimento", "especia", "curry", "ajo en polvo",
        "mermelada", "dulce de batata", "miel",
        "vinagreta", "alioli", "caesar",
    ],

    # ── Lacteos ─────────────────────────────────────────────────────────────────
    "lacteos": [
        "leche", "yogur", "queso", "manteca", "ricota",
        "dulce de leche", "crema de leche", "crema para batir",
        "postre", "flan", "mousse",
    ],

    # ── Almacén ─────────────────────────────────────────────────────────────────
    "almacen": [
        "arroz", "fideo", "harina", "azucar", "aceite", "sal",
        "vinagre", "polenta", "lenteja", "garbanzo", "poroto",
        "atun", "yerba", "avena", "granola", "caldo",
        "endulzante", "edulcorante", "stevia", "maizena",
        "fecula", "levadura", "premezcla", "rebozador",
        "tapas para", "tapas de empanada",
        "aceite de oliva", "aceite de girasol",
        "gelatina", "gelatina en polvo",
    ],

    # ── Congelados (antes de carnes: nuggets de pollo → congelados, no carnes) ──
    "congelados": [
        "helado", "empanada", "pizza", "hamburguesa",
        "nugget", "bocadito", "precocido", "rebozado",
        "bastones de", "acelga congelada", "espinaca congelada",
    ],

    # ── Carnes ──────────────────────────────────────────────────────────────────
    "carnes": [
        "pollo", "carne", "bife", "milanesa", "cerdo",
        "pescado", "salchicha", "jamon", "asado", "costilla",
        "lomo", "vacuno", "pechuga", "molida", "filet",
        "medallon", "boca de dama",
    ],

    # ── Panificados ─────────────────────────────────────────────────────────────
    "panificados": [
        "pan", "tostada", "bizcocho", "factura", "medialuna",
        "budin", "magdalena", "baguette", "lactal", "brioche",
        "tortita", "chipas", "chipa",
    ],

    # ── Bebidas ─────────────────────────────────────────────────────────────────
    "bebidas": [
        "gaseosa", "jugo", "cerveza", "vino", "soda",
        "whisky", "vodka", "gin", "fernet", "ron",
        "aperitivo", "amargo", "tonica",
        "agua mineral", "agua saborizada", "agua con gas",
        "agua sin gas", "agua de mesa", "agua tonica",
        "te", "mate", "tisana", "nescafe", "cafe",
        "isotonica", "energizante", "bebida lactea",
        "nectar", "jugo de naranja",
    ],

    # ── Limpieza ─────────────────────────────────────────────────────────────────
    "limpieza": [
        "detergente", "lavandina", "suavizante", "jabon en polvo",
        "desengrasante", "papel de cocina", "bolsa de residuos",
        "bolsa para residuos", "aromatizante", "aromatizador",
        "jabon", "alcohol etilico", "alcohol puro", "alcohol gel",
        "alcohol en gel", "insecticida", "esponja", "quitamanchas",
        "abrillantador", "repelente", "aerosol desinfectante",
        "servilleta", "toalla de papel", "trapo", "pano",
        "limpiador", "desinfectante",
    ],

    # ── Higiene personal ─────────────────────────────────────────────────────────
    "higiene": [
        "shampoo", "acondicionador", "desodorante",
        "pasta dental", "papel higienico",
        "crema corporal", "cepillo dental", "agua micelar",
        "antitranspirante", "coloracion", "tinte para cabello",
        "maquina de afeitar", "maquina afeitar", "afeitadora",
        "espuma de afeitar", "crema de afeitar",
        "esmalte de", "esmalte para",
        "mascara de", "rimel", "base maquillaje",
        "protector solar", "bloqueador solar", "fps",
        "panal", "panale", "toalla femenina", "toallas femeninas",
        "protector diario", "tampon",
        "enjuague bucal", "hilo dental",
        "gel de ducha", "jabon liquido",
        "locion", "serum", "mascarilla",
        "toallita",
    ],

    # ── Verdulería / frutería ─────────────────────────────────────────────────
    "verduleria": [
        "papa ", "tomate", "cebolla", "zanahoria", "lechuga",
        "zapallo", "batata", "choclo", "brocoli", "espinaca",
        "limon", "naranja", "manzana", "banana", "pera",
        "durazno", "ciruela", "uva ", "frutilla", "frambuesa",
        "verdura", "fruta",
    ],
}


def limpiar(nombre: str) -> str:
    nombre = nombre.lower()
    nombre = unicodedata.normalize('NFKD', nombre)
    nombre = ''.join(c for c in nombre if not unicodedata.combining(c))
    nombre = re.sub(r'[^a-z0-9\s]', ' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre


def es_combo(nombre_limpio: str) -> bool:
    palabras_combo = {"combo", "pack", "kit", "promo"}
    primer_palabra = nombre_limpio.split()[0] if nombre_limpio.split() else ""
    return primer_palabra in palabras_combo


def detectar_categoria(nombre_limpio: str) -> str:
    palabras = set(nombre_limpio.split())
    for categoria, claves in CATEGORIAS.items():
        for clave in claves:
            if ' ' in clave:
                # Multi-word: substring en el nombre completo
                if clave in nombre_limpio:
                    return categoria
            elif len(clave) >= 5:
                # Palabra larga: prefix match — cubre plurales (galletita→galletitas)
                if any(p.startswith(clave) for p in palabras):
                    return categoria
            else:
                # Palabra corta (sal, te, gin): solo match exacto para evitar falsos positivos
                if clave.strip() in palabras:
                    return categoria
    return "otros"


def normalizar_unidad(nombre_limpio: str):
    patrones = [
        (r'(\d+(?:[.,]\d+)?)\s*ml\b',  lambda m: (float(m.group(1).replace(',', '.')), 'ml')),
        (r'(\d+(?:[.,]\d+)?)\s*l\b',   lambda m: (float(m.group(1).replace(',', '.')) * 1000, 'ml')),
        (r'(\d+(?:[.,]\d+)?)\s*g\b',   lambda m: (float(m.group(1).replace(',', '.')), 'g')),
        (r'(\d+(?:[.,]\d+)?)\s*kg\b',  lambda m: (float(m.group(1).replace(',', '.')) * 1000, 'g')),
    ]
    for patron, convertir in patrones:
        m = re.search(patron, nombre_limpio)
        if m:
            cantidad, unidad = convertir(m)
            return f"{int(cantidad)}{unidad}"
    return None


def extraer_numeros(nombre: str):
    return re.findall(r'\d+', nombre)


class Normalizer:
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def obtener_o_crear_producto(self, nombre_original: str, fuente_id: int) -> int:
        nombre_limpio = limpiar(nombre_original)

        if nombre_limpio in self._cache:
            return self._cache[nombre_limpio]

        productos = self.db.get_all_productos()
        mejor_score = 0
        mejor_id = None
        numeros_actuales = extraer_numeros(nombre_limpio)

        for prod in productos:
            numeros_prod = extraer_numeros(prod["nombre_normalizado"])
            if numeros_actuales and numeros_prod and set(numeros_actuales) != set(numeros_prod):
                score = 0
            else:
                score = fuzz.token_sort_ratio(nombre_limpio, prod["nombre_normalizado"])

            if score > mejor_score:
                mejor_score = score
                mejor_id = prod["id"]

        if mejor_score >= UMBRAL_SIMILITUD and mejor_id:
            self._cache[nombre_limpio] = mejor_id
            return mejor_id

        categoria = detectar_categoria(nombre_limpio)
        unidad = normalizar_unidad(nombre_limpio)
        combo = es_combo(nombre_limpio)
        nuevo_id = self.db.insert_producto(nombre_limpio, categoria, unidad, es_combo=combo)
        self._cache[nombre_limpio] = nuevo_id
        return nuevo_id
