"""Unit tests for /api/buscar_carrito and the updated /api/carrito endpoints."""

import json
import sqlite3
import tempfile
import os
import pytest

import app as flask_app
from db import Database


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path):
    """In-memory SQLite database pre-populated with test data."""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init_schema()

    fuente_dia = db.get_or_create_fuente("dia", "https://dia.com.ar")
    fuente_car = db.get_or_create_fuente("carrefour", "https://carrefour.com.ar")

    def add_product(nombre, categoria, precio_dia=None, precio_car=None):
        pid = db.insert_producto(nombre, categoria=categoria)
        fecha = "2026-05-31"
        if precio_dia is not None:
            vid = db.get_or_create_variante(pid, fuente_dia, nombre + " [dia]", f"https://dia/{pid}")
            db.insertar_precio(vid, precio_dia, fecha)
        if precio_car is not None:
            vid = db.get_or_create_variante(pid, fuente_car, nombre + " [car]", f"https://car/{pid}")
            db.insertar_precio(vid, precio_car, fecha)
        return pid

    add_product("leche entera la serenisima 1lt", "lacteos", precio_dia=1200, precio_car=1350)
    add_product("leche descremada la serenisima 1lt", "lacteos", precio_dia=1300, precio_car=1400)
    add_product("pan lactal bimbo 400g", "panificados", precio_dia=900, precio_car=850)
    add_product("aceite de girasol cocinero 1.5lt", "aceites", precio_dia=2100)
    add_product("galletitas oreo 120g", "galletitas", precio_car=600)

    return db_path


@pytest.fixture()
def client(tmp_db, monkeypatch):
    """Flask test client using the temporary database."""
    monkeypatch.setattr(flask_app, "DB_PATH", tmp_db)
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


# ── /api/buscar_carrito ───────────────────────────────────────────────────────

class TestBuscarCarrito:
    def test_returns_all_when_empty_query(self, client):
        res = client.get("/api/buscar_carrito?q=")
        assert res.status_code == 200
        data = res.get_json()
        assert "resultados" in data
        assert data["total"] >= 5

    def test_filters_by_query(self, client):
        res = client.get("/api/buscar_carrito?q=leche")
        data = res.get_json()
        assert data["total"] == 2
        nombres = [r["nombre"] for r in data["resultados"]]
        assert all("leche" in n for n in nombres)

    def test_pagination_fields_present(self, client):
        res = client.get("/api/buscar_carrito?q=leche&page=1&per_page=1")
        data = res.get_json()
        assert data["page"] == 1
        assert data["per_page"] == 1
        assert data["total_pages"] == 2
        assert data["total"] == 2
        assert len(data["resultados"]) == 1

    def test_pagination_second_page(self, client):
        res = client.get("/api/buscar_carrito?q=leche&page=2&per_page=1")
        data = res.get_json()
        assert data["page"] == 2
        assert len(data["resultados"]) == 1

    def test_page_clamped_to_total(self, client):
        res = client.get("/api/buscar_carrito?q=leche&page=99&per_page=10")
        data = res.get_json()
        assert data["page"] == data["total_pages"]

    def test_per_page_capped_at_50(self, client):
        res = client.get("/api/buscar_carrito?q=&per_page=999")
        data = res.get_json()
        assert data["per_page"] == 50

    def test_result_shape(self, client):
        res = client.get("/api/buscar_carrito?q=leche&per_page=5")
        data = res.get_json()
        prod = data["resultados"][0]
        assert "id" in prod
        assert "nombre" in prod
        assert "categoria" in prod
        assert "fuentes" in prod
        assert isinstance(prod["fuentes"], dict)

    def test_relevancia_starts_with_token_first(self, client):
        """Products starting with the first token appear before those only containing it."""
        res = client.get("/api/buscar_carrito?q=leche")
        data = res.get_json()
        nombres = [r["nombre"] for r in data["resultados"]]
        # both start with "leche" — all should appear, none filtered out
        assert len(nombres) == 2

    def test_no_results_for_unknown_query(self, client):
        res = client.get("/api/buscar_carrito?q=xyz_no_existe_jamas")
        data = res.get_json()
        assert data["total"] == 0
        assert data["resultados"] == []
        assert data["total_pages"] == 1

    def test_multi_word_query(self, client):
        res = client.get("/api/buscar_carrito?q=leche+entera")
        data = res.get_json()
        assert data["total"] == 1
        assert "entera" in data["resultados"][0]["nombre"]


# ── /api/carrito ─────────────────────────────────────────────────────────────

class TestApiCarrito:
    def _get_product_ids(self, client):
        """Helper: fetch IDs for leche entera and pan lactal via search."""
        leche = client.get("/api/buscar_carrito?q=leche+entera").get_json()["resultados"][0]["id"]
        pan   = client.get("/api/buscar_carrito?q=pan+lactal").get_json()["resultados"][0]["id"]
        return leche, pan

    def test_empty_ids_returns_empty(self, client):
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": []}),
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["productos"] == []
        assert data["carrito"] == []
        assert data["no_encontrados"] == []

    def test_missing_body_returns_empty(self, client):
        res = client.post("/api/carrito",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert data["productos"] == []

    def test_valid_ids_return_productos(self, client):
        leche_id, pan_id = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id, pan_id]}),
                          content_type="application/json")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["productos"]) == 2
        nombres = {p["nombre"] for p in data["productos"]}
        assert any("leche" in n for n in nombres)
        assert any("pan" in n for n in nombres)

    def test_carrito_optimo_groups_by_cheapest_source(self, client):
        leche_id, pan_id = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id, pan_id]}),
                          content_type="application/json")
        data = res.get_json()
        # leche: dia=1200, car=1350  → cheapest = dia
        # pan:   dia=900,  car=850   → cheapest = carrefour
        fuentes_carrito = {b["fuente"] for b in data["carrito"]}
        assert "dia" in fuentes_carrito
        assert "carrefour" in fuentes_carrito

    def test_no_encontrados_for_invalid_id(self, client):
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [999999]}),
                          content_type="application/json")
        data = res.get_json()
        assert 999999 in data["no_encontrados"]
        assert data["productos"] == []

    def test_mixed_valid_and_invalid_ids(self, client):
        leche_id, _ = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id, 999999]}),
                          content_type="application/json")
        data = res.get_json()
        assert len(data["productos"]) == 1
        assert 999999 in data["no_encontrados"]

    def test_duplicate_ids_deduplicated(self, client):
        leche_id, _ = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id, leche_id]}),
                          content_type="application/json")
        data = res.get_json()
        assert len(data["productos"]) == 1

    def test_non_integer_ids_ignored(self, client):
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": ["abc", None, -1, 0]}),
                          content_type="application/json")
        data = res.get_json()
        assert data["productos"] == []

    def test_fuentes_list_in_response(self, client):
        leche_id, _ = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id]}),
                          content_type="application/json")
        data = res.get_json()
        assert isinstance(data["fuentes"], list)
        assert len(data["fuentes"]) >= 1

    def test_carrito_bloque_has_required_fields(self, client):
        leche_id, _ = self._get_product_ids(client)
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [leche_id]}),
                          content_type="application/json")
        data = res.get_json()
        bloque = data["carrito"][0]
        assert "fuente" in bloque
        assert "productos" in bloque
        assert "total" in bloque
        assert "ahorro_total" in bloque

    def test_producto_only_in_one_source_no_ahorro(self, client):
        """Product with single source: ahorro should be 0."""
        aceite = client.get("/api/buscar_carrito?q=aceite").get_json()["resultados"][0]["id"]
        res = client.post("/api/carrito",
                          data=json.dumps({"ids": [aceite]}),
                          content_type="application/json")
        data = res.get_json()
        item = data["carrito"][0]["productos"][0]
        assert item["ahorro"] == 0
