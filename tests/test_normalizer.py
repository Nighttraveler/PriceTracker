import pytest
from unittest.mock import MagicMock
from normalizer import limpiar, es_combo, detectar_categoria, normalizar_unidad, Normalizer


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

    def test_cache_evita_queries_repetidas(self):
        self.mock_db.get_all_productos.return_value = []
        self.mock_db.insert_producto.return_value = 7

        self.normalizer.obtener_o_crear_producto("arroz largo fino x 500g", fuente_id=1)
        self.normalizer.obtener_o_crear_producto("arroz largo fino x 500g", fuente_id=1)

        # get_all_productos solo se llama la primera vez
        assert self.mock_db.get_all_productos.call_count == 1
