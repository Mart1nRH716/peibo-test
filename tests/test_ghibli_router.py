"""Pruebas de autorización por recurso para la API de Studio Ghibli."""

from fastapi.testclient import TestClient
import pytest

from app.schemas.enum import RolEnum
from app.services.ghibli_service import (
	GhibliItemNotFoundError,
	GhibliService,
	GhibliUpstreamError,
	InvalidGhibliResourceError,
)


GHIBLI_URL = "/api/v1/studios-ghibli"


@pytest.fixture
def stub_ghibli_service(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str | None]]:
	"""Evita llamadas de red y registra las consultas que llegan al servicio."""
	calls: list[tuple[str, str | None]] = []

	async def fake_get_ghibli_data(
		resource: str, item_id: str | None = None
	) -> dict[str, str | None]:
		calls.append((resource, item_id))
		return {"resource": resource, "item_id": item_id}

	monkeypatch.setattr(
		GhibliService, "get_ghibli_data", staticmethod(fake_get_ghibli_data)
	)
	return calls


def get_auth_headers(
	client: TestClient, username: str, password: str = "password123"
) -> dict[str, str]:
	response = client.post(
		"/api/v1/usuarios/token",
		data={"username": username, "password": password},
	)
	assert response.status_code == 200
	return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_role_can_request_its_ghibli_resource(
	client: TestClient,
	create_user,
	stub_ghibli_service: list[tuple[str, str | None]],
) -> None:
	user = create_user("films_user", id_rol=RolEnum.FILMS.value)
	headers = get_auth_headers(client, user.username)

	response = client.get(f"{GHIBLI_URL}/films", headers=headers)

	assert response.status_code == 200
	assert response.json() == {"resource": "films", "item_id": None}
	assert stub_ghibli_service == [("films", None)]


def test_role_cannot_request_another_ghibli_resource(
	client: TestClient,
	create_user,
	stub_ghibli_service: list[tuple[str, str | None]],
) -> None:
	user = create_user("films_user", id_rol=RolEnum.FILMS.value)
	headers = get_auth_headers(client, user.username)

	response = client.get(f"{GHIBLI_URL}/people", headers=headers)

	assert response.status_code == 403
	assert stub_ghibli_service == []


@pytest.mark.parametrize("resource", ["films", "people", "locations", "species", "vehicles"])
def test_admin_can_request_any_valid_ghibli_resource(
	client: TestClient,
	admin_user,
	resource: str,
	stub_ghibli_service: list[tuple[str, str | None]],
) -> None:
	headers = get_auth_headers(client, admin_user.username)

	response = client.get(f"{GHIBLI_URL}/{resource}", headers=headers)

	assert response.status_code == 200
	assert stub_ghibli_service == [(resource, None)]


def test_unknown_ghibli_resource_is_rejected_before_service_call(
	client: TestClient,
	admin_user,
	stub_ghibli_service: list[tuple[str, str | None]],
) -> None:
	headers = get_auth_headers(client, admin_user.username)

	response = client.get(f"{GHIBLI_URL}/unknown", headers=headers)

	assert response.status_code == 400
	assert stub_ghibli_service == []


def test_ghibli_route_requires_authentication(client: TestClient) -> None:
	response = client.get(f"{GHIBLI_URL}/films")

	assert response.status_code == 401


@pytest.mark.parametrize(
	("service_error", "expected_status", "expected_detail"),
	[
		(
			InvalidGhibliResourceError("El recurso 'unknown' no es válido."),
			400,
			"El recurso 'unknown' no es válido.",
		),
		(
			GhibliItemNotFoundError(
				"El elemento solicitado no existe en la API de Studio Ghibli."
			),
			404,
			"El elemento solicitado no existe en la API de Studio Ghibli.",
		),
		(
			GhibliUpstreamError(
				"Error al conectar con la API de Studio Ghibli: connection refused"
			),
			502,
			"Error al conectar con la API de Studio Ghibli: connection refused",
		),
	],
)
def test_router_maps_service_errors_to_http_responses(
	client: TestClient,
	admin_user,
	monkeypatch: pytest.MonkeyPatch,
	service_error: Exception,
	expected_status: int,
	expected_detail: str,
) -> None:
	async def raise_service_error(resource: str, item_id: str | None = None) -> None:
		raise service_error

	monkeypatch.setattr(
		GhibliService, "get_ghibli_data", staticmethod(raise_service_error)
	)
	headers = get_auth_headers(client, admin_user.username)

	response = client.get(f"{GHIBLI_URL}/films", headers=headers)

	assert response.status_code == expected_status
	assert response.json() == {"detail": expected_detail}