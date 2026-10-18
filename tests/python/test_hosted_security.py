from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from dofus_touch_economy.app import create_app
from dofus_touch_economy.config import Settings


@pytest.fixture
def hosted_client(app, session_factory):
    settings = replace(
        app.state.settings,
        allowed_hosts=("economy.example.test",),
        public_origin="https://economy.example.test",
    )
    hosted_app = create_app(settings=settings, session_factory=session_factory)
    with TestClient(hosted_app, base_url=settings.public_origin) as client:
        yield client


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"origin": "null"},
        {"origin": "https://other.example.test"},
        {"origin": "http://economy.example.test"},
        {"origin": "https://[invalid"},
        {"referer": "https://other.example.test/sales"},
        {"referer": "http://economy.example.test/sales"},
        {"origin": "null", "referer": "https://economy.example.test/sales"},
        {"origin": "https://economy.example.test", "sec-fetch-site": "cross-site"},
        {"origin": "https://other.example.test", "x-forwarded-host": "other.example.test"},
    ],
)
def test_hosted_api_denies_untrusted_writes(hosted_client, headers) -> None:
    response = hosted_client.post(
        "/api/v1/items",
        headers=headers,
        json={"display_name": "Hosted Synthetic Ore", "category": "Ore"},
    )

    assert response.status_code == 403
    assert hosted_client.get("/api/v1/items").json() == []


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "https://economy.example.test"},
        {"referer": "https://economy.example.test/items?query=ore"},
    ],
)
def test_hosted_api_accepts_same_origin_writes(hosted_client, headers) -> None:
    response = hosted_client.post(
        "/api/v1/items",
        headers=headers,
        json={"display_name": "Hosted Synthetic Ore", "category": "Ore"},
    )

    assert response.status_code == 201


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_hosted_html_also_requires_same_origin(hosted_client, method) -> None:
    response = hosted_client.request(method, "/sales")

    assert response.status_code == 403


def test_hosted_read_remains_usable_and_rejects_untrusted_host(hosted_client) -> None:
    response = hosted_client.get("/")
    assert response.status_code == 200
    assert 'href="/privacy"' in response.text
    assert 'href="/oauth2/sign_out"' in response.text
    assert hosted_client.get("/", headers={"host": "other.example.test"}).status_code == 400


def test_local_interface_has_no_proxy_sign_out(client) -> None:
    assert "/oauth2/sign_out" not in client.get("/").text


@pytest.mark.parametrize(
    "origin",
    [
        "http://economy.example.test",
        "https://economy.example.test/",
        "https://economy.example.test/path",
        "https://economy.example.test:443",
        "https://user@economy.example.test",
        "https://economy.example.test?query=1",
        "https://economy.example.test#fragment",
        "https://",
    ],
)
def test_hosted_origin_requires_exact_https_hostname(app, origin) -> None:
    with pytest.raises(ValueError, match="DOFUS_PUBLIC_ORIGIN"):
        replace(app.state.settings, public_origin=origin)


def test_hosted_origin_rejects_host_mismatch_and_wildcard(app) -> None:
    for allowed_hosts in [("localhost",), ("economy.example.test", "*")]:
        with pytest.raises(ValueError, match="exact hostname"):
            replace(
                app.state.settings,
                allowed_hosts=allowed_hosts,
                public_origin="https://economy.example.test",
            )


def test_hosted_origin_loads_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DOFUS_ALLOWED_HOSTS", "economy.example.test")
    monkeypatch.setenv("DOFUS_PUBLIC_ORIGIN", "https://economy.example.test")

    assert Settings.from_env().public_origin == "https://economy.example.test"
