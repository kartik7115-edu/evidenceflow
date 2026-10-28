"""The single-container build serves the React app without shadowing the API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def built_frontend(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>EvidenceFlow</title>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("outside the build", encoding="utf-8")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    with TestClient(create_app()) as client:
        yield client


def test_root_and_unknown_pages_return_the_app(built_frontend):
    for path in ("/", "/reviews/123", "/screening"):
        response = built_frontend.get(path)
        assert response.status_code == 200, path
        assert "<title>EvidenceFlow</title>" in response.text


def test_build_assets_are_served_as_files(built_frontend):
    response = built_frontend.get("/assets/app.js")
    assert response.status_code == 200
    assert response.text == "console.log('ok')"


def test_api_docs_and_unknown_api_paths_are_not_shadowed(built_frontend):
    assert built_frontend.get("/api/health").json()["status"] == "ok"
    assert built_frontend.get("/openapi.json").json()["info"]["title"] == "EvidenceFlow API"
    missing = built_frontend.get("/api/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "HTTP_404"


def test_paths_cannot_escape_the_build_folder(built_frontend):
    response = built_frontend.get("/..%2Fsecret.txt")
    assert "outside the build" not in response.text


def test_nothing_is_mounted_without_a_build(tmp_path, monkeypatch):
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path / "missing"))
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 404
        assert client.get("/api/health").status_code == 200
