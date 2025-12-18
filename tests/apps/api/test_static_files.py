"""Tests for static file serving and web chat interface."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bt_servant_engine.api_factory import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    """Test that root path redirects to the chat interface."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_index_html_exists(client):
    """Test that the static index.html file is served."""
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"Bible Study Assistant" in response.content
    assert b"chat-container" in response.content


def test_root_with_redirect_serves_chat_interface(client):
    """Test that following the root redirect serves the chat interface."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Bible Study Assistant" in response.content
    assert b"chat-container" in response.content
    assert b"Ask questions about scripture" in response.content


def test_static_files_have_correct_content_type(client):
    """Test that static HTML files have correct content type."""
    response = client.get("/static/index.html")
    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert "text/html" in content_type or "charset" in content_type
