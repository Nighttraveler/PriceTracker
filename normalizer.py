#!/usr/bin/env python3
"""
normalizer.py — Normaliza nombres de productos y hace fuzzy matching entre fuentes.
"""

import re
import unicodedata
from rapidfuzz import fuzz

UMBRAL_SIMILITUD = 98  # Aumentado para evitar fusiones incorrectas

CATEGORIAS = {
    "lacteos":     ["leche", "yogur", "queso", "manteca", "crema", "ricota", "dulce de leche"],
    "fiambrería":  ["salame", "mortadela", "paté", "queso por salut", "longaniza"],    
    "almacen":     ["arroz", "fideos", "harina", "azucar", "aceite", "sal", "vinagre", "polenta",
                    "legumbre", "lenteja", "garbanzo", "poroto", "atun", "yerba"],
    "carnes":      ["pollo", "carne", "bife", "milanesa", "cerdo", "pescado", "salchicha", "jamon", "asado", "costilla"],
    "panificados": ["pan", "galletita", "tostada", "bizcocho", "facturas", "medialunas", "budin"],
    "limpieza":    ["detergente", "lavandina", "suavizante", "jabon en polvo", "desengrasante",
                    "papel de cocina", "bolsa de residuos", "aromatizante", "pasta dental", "jabon"],
    "higiene":     ["shampoo", "acondicionador", "desodorante", "pasta dental", "papel higienico",
                    "jabón liquido", "crema corporal", "cepillo dental", "agua micelar"],
    "congelados":  ["helado", "empanada", "pizza", "hamburguesa", "nuggets", "bocadito"],
    "verduleria":  ["papa", "tomate", "cebolla", "zanahoria", "lechuga", "zapallo", "batata"],    
    "bebidas":     ["agua mineral", "gaseosa", "jugo", "cerveza", "vino", "té", "cafe", "soda", "whisky"]
}


def limpiar(nombre: str) -> str:
    nombre = nombre.lower()
    nombre = unicodedata.normalize('NFKD', nombre)
    nombre = ''.join(c for c in nombre if not unicodedata.combining(c))
    nombre = re.sub(r'[^a-z0-9\s]', ' ', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre


def detectar_categoria(nombre_limpio: str) -> str:
    for categoria, palabras_clave in CATEGORIAS.items():
        for palabra in palabras_clave:
            if palabra in nombre_limpio.split(' '):
                return categoria
    return "otros"


def normalizar_unidad(nombre_limpio: str):
    """Extrae cantidad y unidad del nombre. Ej: '1l' → (1000, 'ml')"""
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
        self._cache = {}  # nombre_limpio → producto_id

    def obtener_o_crear_producto(self, nombre_original: str, fuente_id: int) -> int:
        nombre_limpio = limpiar(nombre_original)

        # Cache local para evitar queries repetidas
        if nombre_limpio in self._cache:
            return self._cache[nombre_limpio]

        # Buscar entre productos existentes
        productos = self.db.get_all_productos()
        mejor_score = 0
        mejor_id = None
        
        numeros_actuales = extraer_numeros(nombre_limpio)

        for prod in productos:
            # Si ambos tienen números y no coinciden, forzar score bajo
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

        # No encontrado → crear nuevo
        categoria = detectar_categoria(nombre_limpio)
        unidad = normalizar_unidad(nombre_limpio)
        nuevo_id = self.db.insert_producto(nombre_limpio, categoria, unidad)
        self._cache[nombre_limpio] = nuevo_id
        return nuevo_id
