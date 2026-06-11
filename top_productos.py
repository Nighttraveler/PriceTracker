"""top_productos.py — Lista curada de items de canasta básica para la sección TOP del index.

Cada item define reglas de matching contra `productos.nombre_normalizado` (minúscula, sin
acentos; ver `normalizer.limpiar`). `db.get_top_baratos()` consume esta lista.

Estructura por item:
    label   -- texto a mostrar
    incluir -- lista AND. Cada elemento es:
                 * un string      -> debe aparecer (LIKE %term%)
                 * una lista       -> grupo OR: basta uno de sus términos
    excluir -- lista de términos que NO deben aparecer (NOT LIKE %term%)
    tamano  -- lista OR de patrones de tamaño (al menos uno debe aparecer);
               None / [] = sin restricción de tamaño

Nota: "500 g" ya cubre "500 grs" y "x 500 g" por substring; se agrega "500g" (sin espacio)
para los nombres que vienen pegados.
"""

TOP_ITEMS = [
    # --- núcleo Yani ---
    {"label": "Fideos 500g", "incluir": ["fideo"],
     "excluir": ["salsa"], "tamano": ["500 g", "500g"]},
    {"label": "Leche 1L", "incluir": ["leche"],
     "excluir": ["en polvo", "modif", "chocolatada", "condensada", "vegetal", "almendra"],
     "tamano": ["1 lt", "1lt", "1 l", "1000 cc"]},
    {"label": "Leche deslactosada", "excluir": ["en polvo", "modif", "chocolatada"], "tamano": None,
     # deslactosada y cero/zero lactosa = lo mismo -> grupo OR
     "incluir": ["leche",
                 ["deslacto", "cero lactosa", "zero lactosa", "sin lactosa", "0 lactosa"]]},
    {"label": "Arroz 1kg", "incluir": ["arroz"],
     "excluir": ["alfajor", "leche", "crema"], "tamano": ["1 kg", "1kg"]},
    {"label": "Yerba 1kg", "incluir": ["yerba"], "excluir": [], "tamano": ["1 kg", "1kg"]},
    {"label": "Azúcar 1kg", "incluir": ["azucar"],
     "excluir": ["sin azucar", "s azucar", "alfajor", "cacao", "vegetal"],
     "tamano": ["1 kg", "1kg"]},
    {"label": "Harina 000 1kg", "incluir": ["harina", "000"],
     "excluir": ["0000", "leudante"], "tamano": ["1 kg", "1kg"]},
    {"label": "Manteca 200g", "incluir": ["manteca"],
     "excluir": ["galletita", "mani", "cacao"], "tamano": ["200 g", "200g"]},
    {"label": "Queso rallado 150g", "incluir": ["queso", "rallado"],
     "excluir": ["aderezo", "sabor queso", "alimento", "base"],
     "tamano": ["150 g", "150g", "150 gr"]},
    {"label": "Papel higiénico x4 doble hoja", "incluir": ["papel", "higienico", "doble hoja"],
     "excluir": [],
     # pack de 4: cubre "4 ud/un/uni", "x4", "4x30", "4 x 30"
     "tamano": [" 4 u", "x4", "4x", "4 x"]},
    {"label": "Detergente 500ml", "incluir": ["detergente"],
     "excluir": ["cepillo", "repuesto cepillo"],
     "tamano": ["500 ml", "500ml", "500 cc"]},
    {"label": "Rollo de cocina x3", "incluir": ["rollo", "cocina"],
     "excluir": ["bolsa"],
     # pack de 3: cubre "3 ud/un/uni", "x3", "3 x 50"
     "tamano": [" 3 u", "x3", "3 x"]},
    # --- extras canasta básica argentina ---
    {"label": "Aceite girasol 900ml", "incluir": ["aceite"],
     "excluir": ["oliva", "mezcla", "rocio", "aerosol", "maiz", "pino", "limpiador"],
     "tamano": ["900 ml", "900ml", "900 cc"]},
    {"label": "Pan lactal", "incluir": ["pan", "lactal"],
     "excluir": ["rallado", "tostado", "hamburguesa", "pancho"], "tamano": None},
    {"label": "Polenta 500g", "incluir": ["polenta"],
     "excluir": [], "tamano": ["500 g", "500g"]},
    {"label": "Yogur", "incluir": ["yogur"],
     "excluir": ["aderezo", "salsa", "barrita", "barra", "cereal"], "tamano": None},
    {"label": "Lentejas 400g", "incluir": ["lenteja"],
     "excluir": ["sopa", "guiso listo"], "tamano": ["400 g", "400g"]},
    {"label": "Tomate triturado", "incluir": ["tomate", "triturado"],
     "excluir": [], "tamano": ["910 g", "910g", "950 g", "950g", "970 g", "970g"]},
    {"label": "Sal fina 500g", "incluir": ["sal", "fina"],
     "excluir": ["salsa", "sales"], "tamano": ["500 g", "500g"]},
    {"label": "Café molido/instantáneo",
     "incluir": ["cafe", ["molido", "instantaneo", "torrado", "tostado", "soluble"]],
     "excluir": ["cappuccino", "cubanito", "galletita", "filtro", "barrita",
                 "mani", "alfajor", "helado", "postre", "capsula", "saborizado"],
     "tamano": None},
]
