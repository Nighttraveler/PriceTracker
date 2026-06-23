"""Tests for the /api/v1/* JSON endpoints."""
import pytest
from unittest.mock import MagicMock, patch

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["CACHE_TYPE"] = "SimpleCache"
    with flask_app.test_client() as c:
        yield c


def _mock_db(monkeypatch, **methods):
    """Patch api._get_db() to return a MagicMock with the given method return values."""
    db = MagicMock()
    for name, value in methods.items():
        getattr(db, name).return_value = value
    monkeypatch.setattr("api._get_db", lambda: db)
    return db


def test_dashboard_returns_200(client, monkeypatch):
    _mock_db(
        monkeypatch,
        stats={"fuentes": [{"nombre": "dia"}], "total": 10},
        get_top_baratos=[],
        get_highlights=[],
    )
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "stats" in data
    assert "top_baratos" in data
    assert "highlights" in data


def test_precios_returns_200(client, monkeypatch):
    _mock_db(
        monkeypatch,
        get_precios_rango=[],
        get_all_productos=[],
    )
    resp = client.get("/api/v1/precios")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "filas" in data
    assert "page" in data
    assert "total_pages" in data


def test_producto_404_on_unknown(client, monkeypatch):
    _mock_db(monkeypatch, get_producto_by_id=None)
    resp = client.get("/api/v1/producto/999999")
    assert resp.status_code == 404


def test_producto_returns_200(client, monkeypatch):
    _mock_db(
        monkeypatch,
        get_producto_by_id={"id": 1, "nombre_normalizado": "Leche"},
        get_historial_producto=[],
        get_variantes_producto=[],
    )
    resp = client.get("/api/v1/producto/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "prod" in data
    assert "fechas" in data
    assert "datasets" in data


def test_ahorro_returns_200(client, monkeypatch):
    _mock_db(
        monkeypatch,
        savings_by_category=[],
        optimal_cart=([], []),
    )
    resp = client.get("/api/v1/ahorro")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tabla_cat" in data
    assert "carrito" in data


def test_buscar_empty_query(client, monkeypatch):
    _mock_db(
        monkeypatch,
        get_all_fuentes=["dia", "anonima"],
        get_all_categorias=["lacteos"],
        buscar_productos=[],
    )
    resp = client.get("/api/v1/buscar")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["buscado"] is False
    assert data["resultados"] == []


def test_buscar_with_query(client, monkeypatch):
    _mock_db(
        monkeypatch,
        get_all_fuentes=["dia"],
        get_all_categorias=["lacteos"],
        buscar_productos=[{"id": 1, "nombre_normalizado": "Leche", "fuentes": {"dia": {"precio": 100}}}],
    )
    resp = client.get("/api/v1/buscar?q=leche")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["buscado"] is True
    assert len(data["resultados"]) == 1


def test_carrito_post_empty(client):
    resp = client.post("/api/v1/carrito", json={"ids": []})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["productos"] == []
    assert data["carrito"] == []


def test_carrito_post_invalid_ids(client):
    resp = client.post("/api/v1/carrito", json={"ids": ["abc", -1, 0]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["productos"] == []
