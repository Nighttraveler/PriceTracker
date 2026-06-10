import pytest
from unittest.mock import MagicMock
from normalizer import limpiar, es_combo, detectar_categoria, normalizar_unidad, Normalizer, _normalizar_para_match


# ── limpiar ──────────────────────────────────────────────────────────────────

class TestLimpiar:
    def test_lowercase(self):
        assert limpiar("Leche Entera") == "leche entera"

    def test_removes_accents(self):
        assert limpiar("Té Verde") == "te verde"
        assert limpiar("Jamón Serrano") == "jamon serrano"
        assert limpiar("Año Nuevo") == "ano nuevo"

    def test_removes_special_chars(self):
        assert limpiar("pan® integral™") == "pan integral"
        assert limpiar("sal & pimienta") == "sal pimienta"

    def test_normalizes_spaces(self):
        assert limpiar("  leche   entera  ") == "leche entera"

    def test_keeps_numbers(self):
        assert limpiar("Arroz 000 x 1kg") == "arroz 000 x 1kg"


# ── es_combo ─────────────────────────────────────────────────────────────────

class TestEsCombo:
    def test_combo_prefix(self):
        assert es_combo("combo dove shampoo y acondicionador") is True
        assert es_combo("combo familiar galletitas") is True

    def test_kit_prefix(self):
        assert es_combo("kit portable cepillo total 12 colgate x 30 g") is True

    def test_pack_prefix(self):
        assert es_combo("pack ahorro detergente skip x 3") is True

    def test_promo_prefix(self):
        assert es_combo("promo 2x1 shampoo head shoulders") is True

    def test_not_combo(self):
        assert es_combo("leche entera 1 lt") is False
        assert es_combo("galletitas dulces arcor") is False

    def test_doypack_not_combo(self):
        # "doypack" contiene "pack" pero no es un combo
        assert es_combo("aceitunas verdes doypack 180 g") is False
        assert es_combo("nescafe dolca suave doypack x 100gr") is False

    def test_combo_must_be_first_word(self):
        # "combo" en el medio no cuenta
        assert es_combo("aceite con combo sabor") is False


# ── detectar_categoria ────────────────────────────────────────────────────────

class TestDetectarCategoria:

    # Categorías nuevas
    def test_combos(self):
        assert detectar_categoria("combo dove shampoo cuidado") == "combos"

    def test_kit_es_combo(self):
        # Bug anterior: kit → es_combo=True pero categoria=otros
        assert detectar_categoria("kit portable cepillo total 12 colgate x 30 g") == "combos"

    def test_pack_es_combo(self):
        assert detectar_categoria("pack ahorro detergente skip x 3") == "combos"

    def test_promo_es_combo(self):
        assert detectar_categoria("promo 2x1 shampoo head shoulders") == "combos"

    def test_combo_tiene_prioridad_sobre_otras_categorias(self):
        # Aunque el nombre contenga keywords de higiene/limpieza, si es combo → combos
        assert detectar_categoria("combo shampoo dove y acondicionador") == "combos"
        assert detectar_categoria("kit limpieza hogar detergente lavandina") == "combos"

    def test_consistencia_es_combo_y_categoria(self):
        # Invariante: si es_combo() es True, detectar_categoria() siempre retorna "combos"
        casos = [
            "combo familiar galletitas arcor x 3",
            "kit cuidado personal dove",
            "pack ahorro yerba mate x 2",
            "promo verano gaseosa x 6",
        ]
        for nombre in casos:
            assert es_combo(nombre) is True
            assert detectar_categoria(nombre) == "combos", \
                f"Inconsistencia en '{nombre}': es_combo=True pero categoria != combos"

    def test_galletitas(self):
        assert detectar_categoria("galletitas dulces arcor x 100 g") == "galletitas"
        assert detectar_categoria("crackers integrales x 200 g") == "galletitas"
        assert detectar_categoria("wafers vainilla nestl x 150 g") == "galletitas"

    def test_confiteria(self):
        assert detectar_categoria("alfajor chocolate blanco bon o bon x 60 g") == "confiteria"
        assert detectar_categoria("caramelos halls mentol x 25 g") == "confiteria"
        assert detectar_categoria("tableta chocolate milka x 80 g") == "confiteria"
        assert detectar_categoria("chicles beldent menta x 16 g") == "confiteria"

    def test_snacks(self):
        assert detectar_categoria("papas fritas lays clasicas x 40 g") == "snacks"
        assert detectar_categoria("nachos sabor queso doritos x 40 g") == "snacks"

    def test_condimentos(self):
        assert detectar_categoria("mayonesa hellmanns original x 500 g") == "condimentos"
        assert detectar_categoria("mermelada durazno arcor x 454 g") == "condimentos"
        assert detectar_categoria("aceto balsamico cocinero x 250 ml") == "condimentos"
        assert detectar_categoria("ketchup heinz x 397 g") == "condimentos"
        assert detectar_categoria("aderezo caesar pampa x 250 g") == "condimentos"
        assert detectar_categoria("aji molido dos anclas x 50 g") == "condimentos"

    def test_conservas(self):
        assert detectar_categoria("aceitunas verdes descarozadas castell x 180 g") == "conservas"
        assert detectar_categoria("aceituna negra vanoli x 150 g") == "conservas"
        assert detectar_categoria("sardinas al natural la campagnola x 125 g") == "conservas"

    # Categorías existentes — expansión de keywords
    def test_bebidas_agua_saborizada(self):
        assert detectar_categoria("agua saborizada sin gas levite pomelo x 500 cc") == "bebidas"

    def test_bebidas_agua_mineral_multiword(self):
        # Bug corregido: "agua mineral" era multi-word y no matcheaba antes
        assert detectar_categoria("agua mineral sin gas villavicencio x 500 cc") == "bebidas"

    def test_bebidas_alcohol(self):
        assert detectar_categoria("vodka smirnoff x 750 cc") == "bebidas"
        assert detectar_categoria("gin beefeater x 700 cc") == "bebidas"
        assert detectar_categoria("fernet branca x 750 cc") == "bebidas"

    def test_bebidas_cafe(self):
        assert detectar_categoria("nescafe dolca original x 170 g") == "bebidas"

    def test_higiene_antitranspirante(self):
        assert detectar_categoria("antitranspirante aerosol rexona x 150 cc") == "higiene"

    def test_higiene_coloracion(self):
        assert detectar_categoria("coloracion rubio ceniza koleston x 1 un") == "higiene"

    def test_higiene_panales(self):
        assert detectar_categoria("panales babysec premium talle g x 40 un") == "higiene"
        assert detectar_categoria("panal huggies classic talle m x 50 un") == "higiene"

    def test_higiene_toallas_femeninas(self):
        assert detectar_categoria("toallas femeninas always sensitive x 8 un") == "higiene"

    def test_higiene_protector_solar(self):
        assert detectar_categoria("protector solar fps 50 nivea x 200 ml") == "higiene"

    def test_limpieza_alcohol(self):
        assert detectar_categoria("alcohol etilico 70 bialcohol x 1 lt") == "limpieza"
        assert detectar_categoria("alcohol gel con glicerina bialcohol x 250 cc") == "limpieza"

    def test_limpieza_insecticida(self):
        assert detectar_categoria("insecticida raid mata mosquitos x 360 cc") == "limpieza"

    def test_limpieza_quitamanchas(self):
        assert detectar_categoria("quitamanchas vanish oxi action x 450 g") == "limpieza"

    def test_almacen_avena(self):
        assert detectar_categoria("avena arrollada instantanea la anonima x 350 g") == "almacen"

    def test_almacen_caldo(self):
        assert detectar_categoria("caldo de verdura maggi x 12 u") == "almacen"

    def test_almacen_endulzante(self):
        assert detectar_categoria("endulzante stevia hileret x 200 g") == "almacen"

    def test_almacen_sopa_con_hierba(self):
        # "romero" en el nombre no debe ganar sobre "sopa" — almacen va antes que condimentos
        assert detectar_categoria("sopa de zapallo romero quick knorr x 63 g") == "almacen"
        assert detectar_categoria("sopa instantanea knorr quick zapallo romero 5 sobres") == "almacen"

    def test_mascotas_cat_chow(self):
        # Cat Chow no tiene "para gato" — se detecta por la palabra "cat"
        assert detectar_categoria("adulto pescado pollo cat chow 1 kg") == "mascotas"

    def test_mascotas_gatitos(self):
        # "para gatitos" no matchea "para gato" (substring) — se detecta por "gatito" (prefix)
        assert detectar_categoria("alimento humedo para gatitos cat chow 85 g pollo") == "mascotas"

    def test_lacteos_con_multiword(self):
        # "dulce de leche" era multi-word y no matcheaba antes
        assert detectar_categoria("dulce de leche la serenisima x 400 g") == "lacteos"

    def test_carnes_salchichas(self):
        assert detectar_categoria("salchichas viena la anonima x 340 g") == "carnes"

    def test_congelados(self):
        assert detectar_categoria("helado agua limpa x 80 ml") == "congelados"
        assert detectar_categoria("nuggets de pollo granja del sol x 300 g") == "congelados"

    # Falsos positivos que deben evitarse
    def test_detergente_no_es_bebidas(self):
        # "te" está en "detergente" como substring — no debe matchear bebidas
        assert detectar_categoria("detergente lavavajillas magistral x 750 cc") == "limpieza"

    def test_doypack_no_es_combo(self):
        # "doypack" contiene "pack" — no debe matchear combos
        assert detectar_categoria("aceitunas verdes doypack nucete x 150 g") == "conservas"
        assert detectar_categoria("nescafe dolca doypack x 100 g") == "bebidas"

    def test_galletitas_con_chocolate_es_galletita_no_confiteria(self):
        # galletitas tiene prioridad sobre confiteria en el orden del dict
        assert detectar_categoria("galletitas pepitos con chips de chocolate x 119 g") == "galletitas"

    def test_panificados_pan_no_matchea_panales(self):
        # "pan" es palabra corta (<5 chars) → exact match, no afecta "panales"
        assert detectar_categoria("panales huggies talle m x 50 un") != "panificados"

    def test_sal_no_matchea_salsa(self):
        # "sal" exact word match — no debe matchear "salsa"
        assert detectar_categoria("salsa de tomate arcor x 350 g") == "condimentos"

    def test_otros_para_productos_desconocidos(self):
        assert detectar_categoria("producto x de marca desconocida artesanal z") == "otros"


# ── normalizar_unidad ─────────────────────────────────────────────────────────

class TestNormalizarUnidad:
    def test_mililitros(self):
        assert normalizar_unidad("gaseosa cola x 500ml") == "500ml"

    def test_litros_a_ml(self):
        assert normalizar_unidad("leche entera x 1l") == "1000ml"
        assert normalizar_unidad("aceite girasol x 1.5l") == "1500ml"

    def test_gramos(self):
        assert normalizar_unidad("arroz x 500g") == "500g"

    def test_kilogramos_a_g(self):
        assert normalizar_unidad("harina x 1kg") == "1000g"
        assert normalizar_unidad("carne x 0.5kg") == "500g"

    def test_sin_unidad(self):
        assert normalizar_unidad("galletitas dulces arcor") is None

    def test_coma_como_decimal(self):
        assert normalizar_unidad("aceite x 1,5l") == "1500ml"


# ── _normalizar_para_match ────────────────────────────────────────────────────

class TestNormalizarParaMatch:
    """_normalizar_para_match normaliza solo para comparación, no afecta nombres guardados."""

    def test_cc_se_convierte_a_ml(self):
        assert _normalizar_para_match(limpiar("acondicionador 400 cc")) == "acondicionador 400ml"

    def test_numero_y_unidad_se_unen(self):
        # "400 ml" → "400ml" para que token_sort_ratio los trate como un solo token
        assert _normalizar_para_match(limpiar("jugo 500 ml")) == "jugo 500ml"
        # g se convierte a ml para equiparar notaciones distintas entre fuentes
        assert _normalizar_para_match(limpiar("aceite 900 g")) == "aceite 900ml"

    def test_grs_se_convierte_a_g_luego_a_ml(self):
        # grs → g → ml: normalización en cadena para comparación
        assert _normalizar_para_match(limpiar("arroz 500 grs")) == "arroz 500ml"

    def test_stopwords_removidos(self):
        assert _normalizar_para_match("leche con vitaminas") == "leche vitaminas"
        assert _normalizar_para_match("vitamina a y e") == "vitamina a e"
        assert _normalizar_para_match("aceite x 500ml") == "aceite 500ml"
        assert _normalizar_para_match("fernet edicion mundial 750ml") == "fernet mundial 750ml"

    def test_anio_marketing_se_elimina(self):
        # Años tipo "2026" en nombres de edición especial no distinguen el producto
        assert _normalizar_para_match(limpiar("fernet branca mundial 2026 750 ml")) == "fernet branca mundial 750ml"

    def test_no_afecta_nombres_sin_conectores(self):
        limpio = limpiar("Acondicionador Dove Hidratacion Vitamina A E 400ml")
        assert _normalizar_para_match(limpio) == "acondicionador dove hidratacion vitamina a e 400ml"

    def test_caso_real_dove_score_supera_umbral(self):
        """Los dos nombres del mismo producto deben quedar idénticos tras la normalización."""
        from rapidfuzz import fuzz
        m1 = _normalizar_para_match(limpiar("Acondicionador Dove Hidratacion Vitamina A E 400ml"))
        m2 = _normalizar_para_match(limpiar("Acondicionador Hidratacion con Vitamina A y E Dove x 400 cc"))
        assert fuzz.token_sort_ratio(m1, m2) >= 98, (
            f"Score {fuzz.token_sort_ratio(m1, m2):.1f} insuficiente.\n  m1={m1}\n  m2={m2}"
        )

    def test_caso_real_fernet_edicion_mundial(self):
        """Tres variantes del mismo fernet edición mundial deben normalizar al mismo producto."""
        from rapidfuzz import fuzz
        nombres = [
            "fernet branca edicion mundial 750 ml",
            "fernet branca mundial 2026 750 ml",
            "fernet edicion mundial branca x 750g",
        ]
        normalizados = [_normalizar_para_match(limpiar(n)) for n in nombres]
        for i in range(len(normalizados)):
            for j in range(i + 1, len(normalizados)):
                score = fuzz.token_sort_ratio(normalizados[i], normalizados[j])
                assert score >= 98, (
                    f"Score {score:.1f} entre variante {i+1} y {j+1} insuficiente.\n"
                    f"  m{i+1}={normalizados[i]}\n  m{j+1}={normalizados[j]}"
                )

    def test_diferente_tamanio_no_matchea(self):
        """400ml y 200ml deben seguir siendo distintos tras la normalización."""
        from rapidfuzz import fuzz
        m1 = _normalizar_para_match(limpiar("Acondicionador Dove Vitamina A E 400ml"))
        m2 = _normalizar_para_match(limpiar("Acondicionador Dove Vitamina A E 200ml"))
        # Los números distintos son capturados por el guard en Normalizer,
        # pero también el score debe bajar por el token diferente.
        assert fuzz.token_sort_ratio(m1, m2) < 98, (
            "400ml y 200ml son productos distintos — el score no debe superar el umbral"
        )


# ── Normalizer (clase con DB) ─────────────────────────────────────────────────

class TestNormalizerClass:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_db.get_all_productos.return_value = []
        self.normalizer = Normalizer(self.mock_db)

    def test_evitar_merge_animal_aime(self):
        # Productos similares pero de distinta marca no deben fusionarse
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "vino tinto cabernet sauvignon animal x 750 cc"}
        ]
        self.mock_db.insert_producto.return_value = 2

        producto_id = self.normalizer.obtener_o_crear_producto(
            "vino tinto cabernet sauvignon aime x 750 cc", fuente_id=1
        )
        assert producto_id == 2, "Animal y Aime son distintos — no deben fusionarse"

    def test_producto_existente_retorna_mismo_id(self):
        self.mock_db.get_all_productos.return_value = [
            {"id": 5, "nombre_normalizado": "leche entera la serenisima x 1 lt"}
        ]
        producto_id = self.normalizer.obtener_o_crear_producto(
            "Leche Entera La Serenisima x 1 Lt", fuente_id=1
        )
        assert producto_id == 5

    def test_producto_nuevo_llama_insert(self):
        self.mock_db.insert_producto.return_value = 99
        producto_id = self.normalizer.obtener_o_crear_producto(
            "Producto completamente nuevo xyz", fuente_id=1
        )
        assert producto_id == 99
        self.mock_db.insert_producto.assert_called_once()

    def test_combo_detectado_en_insert(self):
        self.mock_db.insert_producto.return_value = 10
        self.normalizer.obtener_o_crear_producto("combo dove shampoo x 2", fuente_id=1)

        _, kwargs = self.mock_db.insert_producto.call_args
        assert kwargs.get("es_combo") is True or self.mock_db.insert_producto.call_args[0][3] == 1

    def test_fusiona_mismo_producto_descrito_distinto_entre_fuentes(self):
        """Caso real: Carrefour y Día describen el mismo acondicionador Dove distinto."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "acondicionador dove hidratacion vitamina a e 400ml"}
        ]
        resultado = self.normalizer.obtener_o_crear_producto(
            "Acondicionador Hidratación con Vitamina A y E Dove x 400 cc",
            fuente_id=2,
        )
        assert resultado == 1, (
            "Mismo producto descrito distinto por dos fuentes debe mapearse al mismo ID"
        )
        self.mock_db.insert_producto.assert_not_called()

    def test_fusiona_fernet_edicion_mundial_variantes(self):
        """Fernet Branca Edición Mundial 750ml aparece con distintos nombres según la fuente."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 9957, "nombre_normalizado": "fernet branca edicion mundial 750 ml"}
        ]
        for nombre in [
            "fernet branca mundial 2026 750 ml",
            "fernet edicion mundial branca x 750g",
        ]:
            resultado = self.normalizer.obtener_o_crear_producto(nombre, fuente_id=2)
            assert resultado == 9957, (
                f"'{nombre}' debe mapearse al mismo producto (id 9957), no crear uno nuevo"
            )
        self.mock_db.insert_producto.assert_not_called()

    def test_no_fusiona_mismo_producto_diferente_tamanio(self):
        """400ml y 200ml son SKUs distintos y no deben fusionarse."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "acondicionador dove hidratacion vitamina a e 400ml"}
        ]
        self.mock_db.insert_producto.return_value = 2
        resultado = self.normalizer.obtener_o_crear_producto(
            "Acondicionador Dove Hidratación Vitamina A+E 200ml",
            fuente_id=2,
        )
        assert resultado == 2, "400ml y 200ml son tamaños distintos — no deben fusionarse"

    def test_cache_evita_queries_repetidas(self):
        self.mock_db.get_all_productos.return_value = []
        self.mock_db.insert_producto.return_value = 7

        self.normalizer.obtener_o_crear_producto("arroz largo fino x 500g", fuente_id=1)
        self.normalizer.obtener_o_crear_producto("arroz largo fino x 500g", fuente_id=1)

        # get_all_productos solo se llama la primera vez
        assert self.mock_db.get_all_productos.call_count == 1
