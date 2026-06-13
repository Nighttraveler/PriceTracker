import pytest
from unittest.mock import MagicMock
from normalizer import clean_name, is_combo, detect_category, normalize_unit, Normalizer, _normalize_for_match


# ── clean_name ────────────────────────────────────────────────────────────────

class TestCleanName:
    def test_lowercase(self):
        assert clean_name("Leche Entera") == "leche entera"

    def test_removes_accents(self):
        assert clean_name("Té Verde") == "te verde"
        assert clean_name("Jamón Serrano") == "jamon serrano"
        assert clean_name("Año Nuevo") == "ano nuevo"

    def test_removes_special_chars(self):
        assert clean_name("pan® integral™") == "pan integral"
        assert clean_name("sal & pimienta") == "sal pimienta"

    def test_normalizes_spaces(self):
        assert clean_name("  leche   entera  ") == "leche entera"

    def test_keeps_numbers(self):
        assert clean_name("Arroz 000 x 1kg") == "arroz 000 x 1kg"


# ── is_combo ──────────────────────────────────────────────────────────────────

class TestIsCombo:
    def test_combo_prefix(self):
        assert is_combo("combo dove shampoo y acondicionador") is True
        assert is_combo("combo familiar galletitas") is True

    def test_kit_prefix(self):
        assert is_combo("kit portable cepillo total 12 colgate x 30 g") is True

    def test_pack_prefix(self):
        assert is_combo("pack ahorro detergente skip x 3") is True

    def test_promo_prefix(self):
        assert is_combo("promo 2x1 shampoo head shoulders") is True

    def test_not_combo(self):
        assert is_combo("leche entera 1 lt") is False
        assert is_combo("galletitas dulces arcor") is False

    def test_doypack_not_combo(self):
        # "doypack" contains "pack" but is not a combo
        assert is_combo("aceitunas verdes doypack 180 g") is False
        assert is_combo("nescafe dolca suave doypack x 100gr") is False

    def test_combo_must_be_first_word(self):
        # "combo" in the middle does not count
        assert is_combo("aceite con combo sabor") is False


# ── detect_category ───────────────────────────────────────────────────────────

class TestDetectCategory:

    def test_combos(self):
        assert detect_category("combo dove shampoo cuidado") == "combos"

    def test_kit_is_combo(self):
        assert detect_category("kit portable cepillo total 12 colgate x 30 g") == "combos"

    def test_pack_is_combo(self):
        assert detect_category("pack ahorro detergente skip x 3") == "combos"

    def test_promo_is_combo(self):
        assert detect_category("promo 2x1 shampoo head shoulders") == "combos"

    def test_combo_has_priority_over_other_categories(self):
        # Even if the name contains hygiene/cleaning keywords, combo wins
        assert detect_category("combo shampoo dove y acondicionador") == "combos"
        assert detect_category("kit limpieza hogar detergente lavandina") == "combos"

    def test_is_combo_and_category_are_consistent(self):
        # Invariant: if is_combo() is True, detect_category() always returns "combos"
        cases = [
            "combo familiar galletitas arcor x 3",
            "kit cuidado personal dove",
            "pack ahorro yerba mate x 2",
            "promo verano gaseosa x 6",
        ]
        for nombre in cases:
            assert is_combo(nombre) is True
            assert detect_category(nombre) == "combos", \
                f"Inconsistency in '{nombre}': is_combo=True but category != combos"

    def test_galletitas(self):
        assert detect_category("galletitas dulces arcor x 100 g") == "galletitas"
        assert detect_category("crackers integrales x 200 g") == "galletitas"
        assert detect_category("wafers vainilla nestl x 150 g") == "galletitas"

    def test_confiteria(self):
        assert detect_category("alfajor chocolate blanco bon o bon x 60 g") == "confiteria"
        assert detect_category("caramelos halls mentol x 25 g") == "confiteria"
        assert detect_category("tableta chocolate milka x 80 g") == "confiteria"
        assert detect_category("chicles beldent menta x 16 g") == "confiteria"

    def test_snacks(self):
        assert detect_category("papas fritas lays clasicas x 40 g") == "snacks"
        assert detect_category("nachos sabor queso doritos x 40 g") == "snacks"

    def test_condimentos(self):
        assert detect_category("mayonesa hellmanns original x 500 g") == "condimentos"
        assert detect_category("mermelada durazno arcor x 454 g") == "condimentos"
        assert detect_category("aceto balsamico cocinero x 250 ml") == "condimentos"
        assert detect_category("ketchup heinz x 397 g") == "condimentos"
        assert detect_category("aderezo caesar pampa x 250 g") == "condimentos"
        assert detect_category("aji molido dos anclas x 50 g") == "condimentos"

    def test_conservas(self):
        assert detect_category("aceitunas verdes descarozadas castell x 180 g") == "conservas"
        assert detect_category("aceituna negra vanoli x 150 g") == "conservas"
        assert detect_category("sardinas al natural la campagnola x 125 g") == "conservas"

    def test_bebidas_agua_saborizada(self):
        assert detect_category("agua saborizada sin gas levite pomelo x 500 cc") == "bebidas"

    def test_bebidas_agua_mineral_multiword(self):
        # "agua mineral" is multi-word and must match against the full name
        assert detect_category("agua mineral sin gas villavicencio x 500 cc") == "bebidas"

    def test_bebidas_alcohol(self):
        assert detect_category("vodka smirnoff x 750 cc") == "bebidas"
        assert detect_category("gin beefeater x 700 cc") == "bebidas"
        assert detect_category("fernet branca x 750 cc") == "bebidas"

    def test_bebidas_cafe(self):
        assert detect_category("nescafe dolca original x 170 g") == "bebidas"

    def test_higiene_antitranspirante(self):
        assert detect_category("antitranspirante aerosol rexona x 150 cc") == "higiene"

    def test_higiene_coloracion(self):
        assert detect_category("coloracion rubio ceniza koleston x 1 un") == "higiene"

    def test_higiene_panales(self):
        assert detect_category("panales babysec premium talle g x 40 un") == "higiene"
        assert detect_category("panal huggies classic talle m x 50 un") == "higiene"

    def test_higiene_toallas_femeninas(self):
        assert detect_category("toallas femeninas always sensitive x 8 un") == "higiene"

    def test_higiene_protector_solar(self):
        assert detect_category("protector solar fps 50 nivea x 200 ml") == "higiene"

    def test_limpieza_alcohol(self):
        assert detect_category("alcohol etilico 70 bialcohol x 1 lt") == "limpieza"
        assert detect_category("alcohol gel con glicerina bialcohol x 250 cc") == "limpieza"

    def test_limpieza_insecticida(self):
        assert detect_category("insecticida raid mata mosquitos x 360 cc") == "limpieza"

    def test_limpieza_quitamanchas(self):
        assert detect_category("quitamanchas vanish oxi action x 450 g") == "limpieza"

    def test_almacen_avena(self):
        assert detect_category("avena arrollada instantanea la anonima x 350 g") == "almacen"

    def test_almacen_caldo(self):
        assert detect_category("caldo de verdura maggi x 12 u") == "almacen"

    def test_almacen_endulzante(self):
        assert detect_category("endulzante stevia hileret x 200 g") == "almacen"

    def test_almacen_sopa_con_hierba(self):
        # "romero" in the name must not beat "sopa" — almacen comes before condimentos
        assert detect_category("sopa de zapallo romero quick knorr x 63 g") == "almacen"
        assert detect_category("sopa instantanea knorr quick zapallo romero 5 sobres") == "almacen"

    def test_mascotas_cat_chow(self):
        # Cat Chow lacks "para gato" — detected via the word "cat"
        assert detect_category("adulto pescado pollo cat chow 1 kg") == "mascotas"

    def test_mascotas_gatitos(self):
        # "para gatitos" doesn't match "para gato" (substring) — detected by "gatito" (prefix)
        assert detect_category("alimento humedo para gatitos cat chow 85 g pollo") == "mascotas"

    def test_lacteos_con_multiword(self):
        # "dulce de leche" is multi-word and must match against the full name
        assert detect_category("dulce de leche la serenisima x 400 g") == "lacteos"

    def test_carnes_salchichas(self):
        assert detect_category("salchichas viena la anonima x 340 g") == "carnes"

    def test_congelados(self):
        assert detect_category("helado agua limpa x 80 ml") == "congelados"
        assert detect_category("nuggets de pollo granja del sol x 300 g") == "congelados"

    # False positives that must be avoided
    def test_detergente_no_es_bebidas(self):
        # "te" appears inside "detergente" — must not match bebidas
        assert detect_category("detergente lavavajillas magistral x 750 cc") == "limpieza"

    def test_doypack_not_combo(self):
        # "doypack" contains "pack" — must not match combos
        assert detect_category("aceitunas verdes doypack nucete x 150 g") == "conservas"
        assert detect_category("nescafe dolca doypack x 100 g") == "bebidas"

    def test_galletitas_con_chocolate_is_galletita_not_confiteria(self):
        # galletitas comes before confiteria in CATEGORIAS order
        assert detect_category("galletitas pepitos con chips de chocolate x 119 g") == "galletitas"

    def test_pan_does_not_match_panales(self):
        # "pan" is a short word (<5 chars) → exact match only, does not affect "panales"
        assert detect_category("panales huggies talle m x 50 un") != "panificados"

    def test_sal_does_not_match_salsa(self):
        # "sal" exact word match — must not match inside "salsa"
        assert detect_category("salsa de tomate arcor x 350 g") == "condimentos"

    def test_otros_for_unknown_products(self):
        assert detect_category("producto x de marca desconocida artesanal z") == "otros"


# ── normalize_unit ────────────────────────────────────────────────────────────

class TestNormalizeUnit:
    def test_mililitros(self):
        assert normalize_unit("gaseosa cola x 500ml") == "500ml"

    def test_litros_a_ml(self):
        assert normalize_unit("leche entera x 1l") == "1000ml"
        assert normalize_unit("aceite girasol x 1.5l") == "1500ml"

    def test_gramos(self):
        assert normalize_unit("arroz x 500g") == "500g"

    def test_kilogramos_a_g(self):
        assert normalize_unit("harina x 1kg") == "1000g"
        assert normalize_unit("carne x 0.5kg") == "500g"

    def test_sin_unidad(self):
        assert normalize_unit("galletitas dulces arcor") is None

    def test_coma_como_decimal(self):
        assert normalize_unit("aceite x 1,5l") == "1500ml"


# ── _normalize_for_match ──────────────────────────────────────────────────────

class TestNormalizeForMatch:
    """_normalize_for_match normalizes only for comparison, not for storage."""

    def test_cc_se_convierte_a_ml(self):
        assert _normalize_for_match(clean_name("acondicionador 400 cc")) == "acondicionador 400ml"

    def test_numero_y_unidad_se_unen(self):
        # "400 ml" → "400ml" so that token_sort_ratio treats them as one token
        assert _normalize_for_match(clean_name("jugo 500 ml")) == "jugo 500ml"
        # g is converted to ml to normalize different notation between sources
        assert _normalize_for_match(clean_name("aceite 900 g")) == "aceite 900ml"

    def test_grs_se_convierte_a_g_luego_a_ml(self):
        # grs → g → ml: chained normalization for comparison
        assert _normalize_for_match(clean_name("arroz 500 grs")) == "arroz 500ml"

    def test_stopwords_removidos(self):
        assert _normalize_for_match("leche con vitaminas") == "leche vitaminas"
        assert _normalize_for_match("vitamina a y e") == "vitamina a e"
        assert _normalize_for_match("aceite x 500ml") == "aceite 500ml"
        assert _normalize_for_match("fernet edicion mundial 750ml") == "fernet mundial 750ml"

    def test_anio_marketing_se_elimina(self):
        # Marketing edition years like "2026" don't distinguish the product
        assert _normalize_for_match(clean_name("fernet branca mundial 2026 750 ml")) == "fernet branca mundial 750ml"

    def test_no_afecta_nombres_sin_conectores(self):
        limpio = clean_name("Acondicionador Dove Hidratacion Vitamina A E 400ml")
        assert _normalize_for_match(limpio) == "acondicionador dove hidratacion vitamina a e 400ml"

    def test_caso_real_dove_score_supera_umbral(self):
        """Two names for the same product must become identical after normalization."""
        from rapidfuzz import fuzz
        m1 = _normalize_for_match(clean_name("Acondicionador Dove Hidratacion Vitamina A E 400ml"))
        m2 = _normalize_for_match(clean_name("Acondicionador Hidratacion con Vitamina A y E Dove x 400 cc"))
        assert fuzz.token_sort_ratio(m1, m2) >= 98, (
            f"Score {fuzz.token_sort_ratio(m1, m2):.1f} insufficient.\n  m1={m1}\n  m2={m2}"
        )

    def test_caso_real_fernet_edicion_mundial(self):
        """Three variants of the same fernet mundial edition must normalize to the same product."""
        from rapidfuzz import fuzz
        nombres = [
            "fernet branca edicion mundial 750 ml",
            "fernet branca mundial 2026 750 ml",
            "fernet edicion mundial branca x 750g",
        ]
        normalizados = [_normalize_for_match(clean_name(n)) for n in nombres]
        for i in range(len(normalizados)):
            for j in range(i + 1, len(normalizados)):
                score = fuzz.token_sort_ratio(normalizados[i], normalizados[j])
                assert score >= 98, (
                    f"Score {score:.1f} between variant {i+1} and {j+1} insufficient.\n"
                    f"  m{i+1}={normalizados[i]}\n  m{j+1}={normalizados[j]}"
                )

    def test_diferente_tamanio_no_matchea(self):
        """400ml and 200ml must remain distinct after normalization."""
        from rapidfuzz import fuzz
        m1 = _normalize_for_match(clean_name("Acondicionador Dove Vitamina A E 400ml"))
        m2 = _normalize_for_match(clean_name("Acondicionador Dove Vitamina A E 200ml"))
        # Different numbers are caught by the guard in Normalizer,
        # but the score should also drop due to the different token.
        assert fuzz.token_sort_ratio(m1, m2) < 98, (
            "400ml and 200ml are different products — score must not exceed threshold"
        )


# ── Normalizer (class with DB) ────────────────────────────────────────────────

class TestNormalizerClass:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_db.get_all_productos.return_value = []
        self.normalizer = Normalizer(self.mock_db)

    def test_evitar_merge_animal_aime(self):
        # Similar products from different brands must not be merged
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "vino tinto cabernet sauvignon animal x 750 cc"}
        ]
        self.mock_db.insert_producto.return_value = 2

        producto_id = self.normalizer.get_or_create_product(
            "vino tinto cabernet sauvignon aime x 750 cc", fuente_id=1
        )
        assert producto_id == 2, "Animal and Aime are different — must not be merged"

    def test_producto_existente_retorna_mismo_id(self):
        self.mock_db.get_all_productos.return_value = [
            {"id": 5, "nombre_normalizado": "leche entera la serenisima x 1 lt"}
        ]
        producto_id = self.normalizer.get_or_create_product(
            "Leche Entera La Serenisima x 1 Lt", fuente_id=1
        )
        assert producto_id == 5

    def test_producto_nuevo_llama_insert(self):
        self.mock_db.insert_producto.return_value = 99
        producto_id = self.normalizer.get_or_create_product(
            "Producto completamente nuevo xyz", fuente_id=1
        )
        assert producto_id == 99
        self.mock_db.insert_producto.assert_called_once()

    def test_combo_detectado_en_insert(self):
        self.mock_db.insert_producto.return_value = 10
        self.normalizer.get_or_create_product("combo dove shampoo x 2", fuente_id=1)

        _, kwargs = self.mock_db.insert_producto.call_args
        assert kwargs.get("es_combo") is True or self.mock_db.insert_producto.call_args[0][3] == 1

    def test_fusiona_mismo_producto_descrito_distinto_entre_fuentes(self):
        """Real case: Carrefour and Día describe the same Dove conditioner differently."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "acondicionador dove hidratacion vitamina a e 400ml"}
        ]
        resultado = self.normalizer.get_or_create_product(
            "Acondicionador Hidratación con Vitamina A y E Dove x 400 cc",
            fuente_id=2,
        )
        assert resultado == 1, (
            "Same product described differently by two sources must map to the same ID"
        )
        self.mock_db.insert_producto.assert_not_called()

    def test_fusiona_fernet_edicion_mundial_variantes(self):
        """Fernet Branca Edición Mundial 750ml appears with different names per source."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 9957, "nombre_normalizado": "fernet branca edicion mundial 750 ml"}
        ]
        for nombre in [
            "fernet branca mundial 2026 750 ml",
            "fernet edicion mundial branca x 750g",
        ]:
            resultado = self.normalizer.get_or_create_product(nombre, fuente_id=2)
            assert resultado == 9957, (
                f"'{nombre}' must map to the same product (id 9957), not create a new one"
            )
        self.mock_db.insert_producto.assert_not_called()

    def test_no_fusiona_mismo_producto_diferente_tamanio(self):
        """400ml and 200ml are different SKUs and must not be merged."""
        self.mock_db.get_all_productos.return_value = [
            {"id": 1, "nombre_normalizado": "acondicionador dove hidratacion vitamina a e 400ml"}
        ]
        self.mock_db.insert_producto.return_value = 2
        resultado = self.normalizer.get_or_create_product(
            "Acondicionador Dove Hidratación Vitamina A+E 200ml",
            fuente_id=2,
        )
        assert resultado == 2, "400ml and 200ml are different sizes — must not be merged"

    def test_cache_evita_queries_repetidas(self):
        self.mock_db.get_all_productos.return_value = []
        self.mock_db.insert_producto.return_value = 7

        self.normalizer.get_or_create_product("arroz largo fino x 500g", fuente_id=1)
        self.normalizer.get_or_create_product("arroz largo fino x 500g", fuente_id=1)

        # get_all_productos should only be called on the first lookup
        assert self.mock_db.get_all_productos.call_count == 1
