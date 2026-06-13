#!/usr/bin/env python3
"""
normalizer.py — Normalizes product names and performs fuzzy matching across sources.
"""

import re
import unicodedata
from rapidfuzz import fuzz

SIMILARITY_THRESHOLD = 98

# Order matters: more specific categories first to avoid false positives.
CATEGORIAS = {
    # ── Combos / packs ─────────────────────────────────────────────────────────
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

    # ── Galletitas ──────────────────────────────────────────────────────────────
    "galletitas": [
        "galletita", "galleta", "cracker", "wafer", "barquillo",
    ],

    # ── Snacks salados ──────────────────────────────────────────────────────────
    "snacks": [
        "papas fritas", "palomitas", "nachos", "chizito",
        "palito salado", "palitos salados", "poperine",
        "mani salado", "mani con", "mani tostado",
        "tostada de arroz", "tostadita",
    ],

    # ── Confitería / dulces ─────────────────────────────────────────────────────
    "confiteria": [
        "alfajor", "chocolate", "caramelo", "chicle", "gomita",
        "turron", "pochoclo", "golosina", "tableta", "bombon",
        "chupetine", "paleta dulce", "marshmallow", "oblea",
    ],

    # ── Higiene personal — before condimentos so that "romero", "jengibre",
    # "aceite de argan" in shampoo/conditioner names don't fall there ──────────
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

    # ── Almacén — before condimentos so that "sopa de ... romero" doesn't fall
    # into condimentos because of the herb keyword ───────────────────────────────
    "almacen": [
        "arroz", "fideo", "harina", "azucar", "aceite", "sal",
        "vinagre", "polenta", "lenteja", "garbanzo", "poroto",
        "atun", "yerba", "avena", "granola", "caldo",
        "endulzante", "edulcorante", "stevia", "maizena",
        "fecula", "levadura", "premezcla", "rebozador",
        "tapas para", "tapas de empanada",
        "aceite de oliva", "aceite de girasol",
        "gelatina", "gelatina en polvo",
        "pan rallado",
        "sopa",
    ],

    # ── Condimentos y salsas ────────────────────────────────────────────────────
    "condimentos": [
        "mayonesa", "ketchup", "mostaza", "aderezo", "aceto",
        "salsa golf", "salsa de soja", "salsa bbq", "salsa worcestershire",
        "salsa teriyaki", "salsa de tomate", "salsa lista",
        "filetto",
        "oregano", "aji molido", "pimienta", "comino", "curcuma",
        "pimenton", "paprika", "canela", "jengibre", "nuez moscada",
        "albahaca", "laurel", "romero", "tomillo", "coriandro",
        "condimento", "especia", "curry", "ajo en polvo",
        "saborizador", "mix de sabores",
        "mermelada", "dulce de batata", "miel",
        "vinagreta", "alioli", "caesar",
    ],

    # ── Lacteos ─────────────────────────────────────────────────────────────────
    "lacteos": [
        "leche", "yogur", "queso", "manteca", "ricota",
        "dulce de leche", "crema de leche", "crema para batir",
        "postre", "flan", "mousse",
    ],

    # ── Congelados — medallones are always frozen (meat, vegan, quinoa) ─────────
    "congelados": [
        "helado", "empanada", "pizza", "hamburguesa",
        "nugget", "bocadito", "precocido", "rebozado",
        "bastones de", "acelga congelada", "espinaca congelada",
        "medallon",
    ],

    # ── Mascotas — before carnes so that "alimento para perro sabor carne"
    # doesn't fall into carnes ──────────────────────────────────────────────────
    "mascotas": [
        "para perro", "para gato",
        "antipulgas", "antiparasitario",
        "arena para",
        "gatito",
        "cat",
    ],

    # ── Panificados — before carnes so that "baguetin sabor jamón" is bread ─────
    "panificados": [
        "pan", "tostada", "bizcocho", "factura", "medialuna",
        "budin", "magdalena", "baguet", "lactal", "brioche",
        "tortita", "chipas", "chipa",
    ],

    # ── Carnes ──────────────────────────────────────────────────────────────────
    "carnes": [
        "pollo", "carne", "bife", "milanesa", "cerdo",
        "pescado", "salchicha", "jamon", "asado", "costilla",
        "lomo", "vacuno", "pechuga", "molida", "filete",
        "boca de dama",
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

    # ── Verdulería / frutería ─────────────────────────────────────────────────
    "verduleria": [
        "papa ", "tomate", "cebolla", "zanahoria", "lechuga",
        "zapallo", "batata", "choclo", "brocoli", "espinaca",
        "limon", "naranja", "manzana", "banana", "pera",
        "durazno", "ciruela", "uva ", "frutilla", "frambuesa",
        "verdura", "fruta",
    ],
}


MATCH_STOPWORDS = frozenset({"con", "y", "x", "edicion"})


def clean_name(nombre: str) -> str:
    nombre = nombre.lower()
    nombre = unicodedata.normalize('NFKD', nombre)
    nombre = ''.join(c for c in nombre if not unicodedata.combining(c))
    nombre = re.sub(r'[^a-z0-9\s]', ' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre


def _normalize_for_match(nombre_limpio: str) -> str:
    """Extra normalization used ONLY for fuzzy comparison, not for storage.

    Resolves notation differences between sources without changing the stored name:
    - cc → ml  (1 cc = 1 ml, different sources use both)
    - grs → g
    - "400 ml" → "400ml"  (merges into a single token)
    - Ng → Nml  (g and ml treated as interchangeable; the number guard prevents
                 merging 400ml with 200ml)
    - years 20XX → removed (marketing edition names, don't distinguish the product)
    - strips connectors ("con", "y", "x", "edicion") which are pure noise
    """
    nombre = re.sub(r'\bcc\b', 'ml', nombre_limpio)
    nombre = re.sub(r'\bgrs\b', 'g', nombre)
    nombre = re.sub(r'(\d+)\s+(ml|g|kg|lt|l)\b', r'\1\2', nombre)
    nombre = re.sub(r'(\d+)g\b', r'\1ml', nombre)
    nombre = re.sub(r'\b20\d{2}\b', '', nombre)
    palabras = [p for p in nombre.split() if p not in MATCH_STOPWORDS]
    return ' '.join(palabras)


def is_combo(nombre_limpio: str) -> bool:
    palabras_combo = {"combo", "pack", "kit", "promo"}
    primer_palabra = nombre_limpio.split()[0] if nombre_limpio.split() else ""
    return primer_palabra in palabras_combo


def detect_category(nombre_limpio: str) -> str:
    # Combos take priority over every other category
    if is_combo(nombre_limpio):
        return "combos"

    palabras = set(nombre_limpio.split())
    for categoria, claves in CATEGORIAS.items():
        if categoria == "combos":
            continue  # already handled above
        for clave in claves:
            if ' ' in clave:
                # Multi-word: substring match against the full name
                if clave in nombre_limpio:
                    return categoria
            elif len(clave) >= 5:
                # Long word: prefix match — covers plurals (galletita→galletitas)
                if any(p.startswith(clave) for p in palabras):
                    return categoria
            else:
                # Short word (sal, te, gin): exact match only to avoid false positives
                if clave.strip() in palabras:
                    return categoria
    return "otros"


def normalize_unit(nombre_limpio: str):
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


def extract_numbers(nombre: str):
    return re.findall(r'\d+', nombre)


class Normalizer:
    def __init__(self, db):
        self.db = db
        self._cache = {}

    def get_or_create_product(self, nombre_original: str, fuente_id: int) -> int:
        nombre_limpio = clean_name(nombre_original)

        if nombre_limpio in self._cache:
            return self._cache[nombre_limpio]

        productos = self.db.get_all_productos()
        mejor_score = 0
        mejor_id = None
        nombre_match = _normalize_for_match(nombre_limpio)
        numeros_actuales = extract_numbers(nombre_match)

        for prod in productos:
            prod_match = _normalize_for_match(prod["nombre_normalizado"])
            numeros_prod = extract_numbers(prod_match)
            if numeros_actuales and numeros_prod and set(numeros_actuales) != set(numeros_prod):
                score = 0
            else:
                score = fuzz.token_sort_ratio(nombre_match, prod_match)

            if score > mejor_score:
                mejor_score = score
                mejor_id = prod["id"]

        if mejor_score >= SIMILARITY_THRESHOLD and mejor_id:
            self._cache[nombre_limpio] = mejor_id
            return mejor_id

        categoria = detect_category(nombre_limpio)
        unidad = normalize_unit(nombre_limpio)
        combo = is_combo(nombre_limpio)
        nuevo_id = self.db.insert_producto(nombre_limpio, categoria, unidad, es_combo=combo)
        self._cache[nombre_limpio] = nuevo_id
        return nuevo_id
