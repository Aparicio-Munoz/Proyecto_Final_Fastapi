from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_middleware_agrega_trazabilidad_y_headers_de_seguridad():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Process-Time"].endswith("ms")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_cors_permite_origen_local_configurado():
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in response.headers["access-control-allow-methods"]
