"""Pruebas de integración para los endpoints de usuarios y autenticación.

Este módulo contiene una suite completa de pruebas utilizando Pytest y TestClient de FastAPI,
validando los flujos completos de autenticación OAuth2 (login), creación, listado,
búsqueda por filtros, actualización parcial (PATCH) y eliminación de usuarios,
comprobando rigurosamente los códigos de estado HTTP, permisos por roles y reglas de negocio.
"""


from fastapi.testclient import TestClient
import pytest
from typing import Protocol
from app.schemas.enum import RolEnum

USERS_URL = "/api/v1/usuarios/"
CREATE_USER_URL = "/api/v1/usuarios/crear-usuario"
TOKEN_URL = "/api/v1/usuarios/token"


class TestUser(Protocol):
	"""Protocolo tipado para representar los datos de un usuario dentro del contexto de pruebas."""

	__test__ = False

	id_usuario: int
	username: str
	email: str
	id_rol: int


def user_payload(
	username: str = "new_user",
	email: str = "new_user@example.com",
	password: str = "password123",
	id_rol: int = RolEnum.FILMS.value,
) -> dict[str, str | int]:
	"""Generador auxiliar de payloads para la creación y prueba de usuarios."""
	return {
		"username": username,
		"email": email,
		"password": password,
		"id_rol": id_rol,
	}


def token_for(client: TestClient, username: str, password: str = "password123") -> str:
	"""Solicita y retorna un token de acceso JWT para un usuario específico."""
	response = client.post(
		TOKEN_URL, data={"username": username, "password": password}
	)
	assert response.status_code == 200
	return response.json()["access_token"]


def test_login_returns_bearer_token(
	client: TestClient, admin_user: TestUser
) -> None:
	"""Verifica que un login exitoso retorne un token de acceso válido tipo Bearer."""
	response = client.post(
		TOKEN_URL,
		data={"username": admin_user.username, "password": "password123"},
	)

	assert response.status_code == 200
	assert response.json()["token_type"] == "bearer"
	assert response.json()["access_token"]


@pytest.mark.parametrize(
	("username", "password"),
	[("missing_user", "password123"), ("admin_test", "wrong-password")],
)
def test_login_rejects_invalid_credentials(
	client: TestClient, admin_user: TestUser, username: str, password: str
) -> None:
	"""Valida que el sistema rechace credenciales incorrectas o usuarios inexistentes con código 401."""
	response = client.post(
		TOKEN_URL, data={"username": username, "password": password}
	)

	assert response.status_code == 401
	assert response.json() == {
		"detail": "Nombre de usuario o contraseña incorrectos"
	}
	assert response.headers["www-authenticate"] == "Bearer"


def test_login_requires_oauth_form_fields(client: TestClient) -> None:
	"""Comprueba que el endpoint de token exija obligatoriamente los campos del formulario OAuth2."""
	response = client.post(TOKEN_URL, data={})

	assert response.status_code == 422
	assert {error["loc"][-1] for error in response.json()["detail"]} == {
		"username",
		"password",
	}


def test_create_user_returns_created_user(
	client: TestClient, auth_headers: dict[str, str]
) -> None:
	"""Verifica que un administrador pueda crear un usuario exitosamente y que se omitan campos sensibles."""
	response = client.post(
		CREATE_USER_URL, json=user_payload(), headers=auth_headers
	)

	assert response.status_code == 201
	assert response.json()["username"] == "new_user"
	assert response.json()["email"] == "new_user@example.com"
	assert response.json()["rol"]["id_rol"] == RolEnum.FILMS.value
	assert "password" not in response.json()
	assert "password_hashed" not in response.json()


def test_create_user_rejects_duplicate_username(
	client: TestClient, admin_user: TestUser, auth_headers: dict[str, str]
) -> None:
	"""Prueba que el sistema impida la creación de usuarios con un nombre de usuario ya existente (409)."""
	response = client.post(
		CREATE_USER_URL,
		json=user_payload(username=admin_user.username),
		headers=auth_headers,
	)

	assert response.status_code == 409
	assert response.json() == {
		"detail": "El nombre de usuario ya está registrado"
	}


def test_create_user_rejects_duplicate_email(
	client: TestClient, admin_user: TestUser, auth_headers: dict[str, str]
) -> None:
	"""Prueba que el sistema impida la creación de usuarios con un correo electrónico duplicado (409)."""
	response = client.post(
		CREATE_USER_URL,
		json=user_payload(email=admin_user.email),
		headers=auth_headers,
	)

	assert response.status_code == 409
	assert response.json() == {
		"detail": "El correo electrónico ya está registrado"
	}


def test_create_user_rejects_missing_role(
	client: TestClient, auth_headers: dict[str, str]
) -> None:
	"""Valida que se rechace la creación si se omite el campo obligatorio del rol (422)."""
	payload = user_payload()
	del payload["id_rol"]

	response = client.post(CREATE_USER_URL, json=payload, headers=auth_headers)

	assert response.status_code == 422
	assert any(
		error["loc"] == ["body", "id_rol"] and error["msg"] == "Field required"
		for error in response.json()["detail"]
	)


@pytest.mark.parametrize(
	("id_rol", "message"),
	[(0, "El rol indicado no existe"), (999, "El rol indicado no existe")],
)
def test_create_user_rejects_unknown_role(
	client: TestClient,
	auth_headers: dict[str, str],
	id_rol: int,
	message: str,
) -> None:
	"""Comprueba que se rechacen IDs de rol que no existan en el catálogo de la base de datos."""
	response = client.post(
		CREATE_USER_URL,
		json=user_payload(id_rol=id_rol),
		headers=auth_headers,
	)

	assert response.status_code == 422
	assert response.json() == {"detail": message}


def test_create_user_rejects_invalid_payload(
	client: TestClient, auth_headers: dict[str, str]
) -> None:
	"""Verifica las reglas de validación de Pydantic ante contraseñas demasiado cortas."""
	response = client.post(
		CREATE_USER_URL,
		json=user_payload(password="short"),
		headers=auth_headers,
	)

	assert response.status_code == 422
	assert any(
		error["loc"] == ["body", "password"]
		and error["msg"] == "String should have at least 8 characters"
		for error in response.json()["detail"]
	)


def test_create_user_requires_authentication(client: TestClient) -> None:
	"""Valida que no se pueda crear un usuario sin proveer un token de autenticación (401)."""
	response = client.post(CREATE_USER_URL, json=user_payload())

	assert response.status_code == 401
	assert response.json() == {"detail": "Not authenticated"}


def test_create_user_requires_admin_role(
	client: TestClient, regular_auth_headers: dict[str, str]
) -> None:
	"""Prueba que un usuario regular no tenga permisos para crear usuarios (403 Forbidden)."""
	response = client.post(
		CREATE_USER_URL, json=user_payload(), headers=regular_auth_headers
	)

	assert response.status_code == 403
	assert response.json() == {
		"detail": "No tienes los permisos necesarios para realizar esta acción."
	}


def test_get_users_returns_all_users(
	client: TestClient, admin_user: TestUser, auth_headers: dict[str, str]
) -> None:
	"""Verifica que se puedan listar los usuarios registrados en el sistema."""
	response = client.get(USERS_URL, headers=auth_headers)

	assert response.status_code == 200
	assert [user["username"] for user in response.json()] == [
		admin_user.username
	]


def test_get_users_filters_by_partial_username(
	client: TestClient,
	admin_user: TestUser,
	regular_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Comprueba que el endpoint de listado permita filtrar correctamente por coincidencia parcial de username."""
	response = client.get(
		USERS_URL, params={"username": "regular"}, headers=auth_headers
	)

	assert response.status_code == 200
	assert [user["username"] for user in response.json()] == [
		regular_user.username
	]
	assert admin_user.username not in [
		user["username"] for user in response.json()
	]


def test_get_users_requires_authentication(client: TestClient) -> None:
	"""Valida que listar usuarios requiera un token de autenticación válido."""
	response = client.get(USERS_URL)

	assert response.status_code == 401
	assert response.json() == {"detail": "Not authenticated"}


def test_get_users_rejects_inactive_user(client: TestClient, create_user) -> None:
	"""Verifica que un usuario inactivo no pueda consumir la API aunque posea un token."""
	inactive_user = create_user(
		"inactive_user", id_rol=RolEnum.FILMS.value, is_active=False
	)
	token = token_for(client, inactive_user.username)

	response = client.get(
		USERS_URL, headers={"Authorization": f"Bearer {token}"}
	)

	assert response.status_code == 400
	assert response.json() == {"detail": "Inactive user"}


def test_get_my_user_returns_authenticated_user(
	client: TestClient, admin_user: TestUser, auth_headers: dict[str, str]
) -> None:
	"""Comprueba que el endpoint /me retorne la información exacta del usuario autenticado."""
	response = client.get(f"{USERS_URL}me", headers=auth_headers)

	assert response.status_code == 200
	assert response.json()["id_usuario"] == admin_user.id_usuario
	assert response.json()["username"] == admin_user.username


@pytest.mark.parametrize(
	("token", "expected_detail"),
	[
		(None, "Not authenticated"),
		("invalid-token", "Could not validate credentials"),
	],
)
def test_get_my_user_rejects_missing_or_invalid_token(
	client: TestClient, token: str | None, expected_detail: str
) -> None:
	"""Valida que /me rechace peticiones sin token o con tokens inválidos o malformados."""
	headers = {} if token is None else {"Authorization": f"Bearer {token}"}

	response = client.get(f"{USERS_URL}me", headers=headers)

	assert response.status_code == 401
	assert response.json() == {"detail": expected_detail}
	assert response.headers["www-authenticate"] == "Bearer"


def test_get_my_user_rejects_inactive_user(
	client: TestClient, create_user
) -> None:
	"""Prueba que un usuario inactivo no pueda consultar su propio perfil en /me."""
	inactive_user = create_user(
		"inactive_me", id_rol=RolEnum.ADMIN.value, is_active=False
	)
	token = token_for(client, inactive_user.username)

	response = client.get(
		f"{USERS_URL}me", headers={"Authorization": f"Bearer {token}"}
	)

	assert response.status_code == 400
	assert response.json() == {"detail": "Inactive user"}


def test_update_user_changes_profile_and_password(
	client: TestClient,
	regular_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Verifica la actualización parcial (PATCH) de perfil y contraseña, y valida el nuevo login."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={"username": "updated_user", "password": "newpass123"},
		headers=auth_headers,
	)

	assert response.status_code == 200
	assert response.json()["username"] == "updated_user"
	assert "password" not in response.json()
	assert "password_hashed" not in response.json()

	login_response = client.post(
		TOKEN_URL,
		data={"username": "updated_user", "password": "newpass123"},
	)
	assert login_response.status_code == 200


def test_update_user_returns_not_found(
	client: TestClient, auth_headers: dict[str, str]
) -> None:
	"""Comprueba que se retorne un error 404 al intentar actualizar un ID de usuario inexistente."""
	response = client.patch(
		f"{USERS_URL}99999",
		json={"username": "updated_user"},
		headers=auth_headers,
	)

	assert response.status_code == 404
	assert response.json() == {"detail": "Usuario no encontrado"}


@pytest.mark.parametrize(
	("payload", "message"),
	[
		(
			{"username": "duplicate_user"},
			"El nombre de usuario ya está registrado",
		),
		(
			{"email": "duplicate@example.com"},
			"El correo electrónico ya está registrado",
		),
	],
)
def test_update_user_rejects_duplicate_fields(
	client: TestClient,
	create_user,
	regular_user: TestUser,
	auth_headers: dict[str, str],
	payload: dict[str, str],
	message: str,
) -> None:
	"""Valida que la actualización parcial rechace duplicidades en username o email (409 Conflict)."""
	create_user("duplicate_user", email="duplicate@example.com")

	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json=payload,
		headers=auth_headers,
	)

	assert response.status_code == 409
	assert response.json() == {"detail": message}


@pytest.mark.parametrize(
	("payload", "message"),
	[
		({"id_rol": 0}, "El rol indicado no existe"),
		({"id_rol": 999}, "El rol indicado no existe"),
	],
)
def test_update_user_rejects_invalid_role(
	client: TestClient,
	regular_user: TestUser,
	auth_headers: dict[str, str],
	payload: dict[str, int | None],
	message: str,
) -> None:
	"""Comprueba que se rechace la actualización si se asigna un ID de rol inexistente."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json=payload,
		headers=auth_headers,
	)

	assert response.status_code == 422
	assert response.json() == {"detail": message}


def test_update_user_keeps_current_role_when_null(
	client: TestClient,
	regular_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Verifica que el rol se mantenga intacto si se envía explícitamente como nulo en el PATCH."""
	current_role = regular_user.id_rol

	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={"id_rol": None},
		headers=auth_headers,
	)

	assert response.status_code == 200
	assert response.json()["rol"]["id_rol"] == current_role


def test_update_user_keeps_current_role_when_omitted(
	client: TestClient,
	regular_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Comprueba que el rol actual no cambie si el campo id_rol se omite por completo en el PATCH."""
	current_role = regular_user.id_rol

	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={},
		headers=auth_headers,
	)

	assert response.status_code == 200
	assert response.json()["rol"]["id_rol"] == current_role


def test_update_user_changes_role(
	client: TestClient,
	regular_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Valida que un administrador pueda actualizar exitosamente el rol de un usuario."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={"id_rol": RolEnum.ADMIN.value},
		headers=auth_headers,
	)

	assert response.status_code == 200
	assert response.json()["rol"]["id_rol"] == RolEnum.ADMIN.value


def test_update_user_rejects_invalid_payload(
	client: TestClient, regular_user: TestUser, auth_headers: dict[str, str]
) -> None:
	"""Prueba que se validen las restricciones de longitud mínima en campos del PATCH."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={"username": "x"},
		headers=auth_headers,
	)

	assert response.status_code == 422
	assert any(
		error["loc"] == ["body", "username"]
		and error["msg"] == "String should have at least 2 characters"
		for error in response.json()["detail"]
	)


def test_update_user_requires_authentication(
	client: TestClient, regular_user: TestUser
) -> None:
	"""Valida que actualizar un usuario requiera un token de autenticación (401)."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}", json={"username": "updated_user"}
	)

	assert response.status_code == 401
	assert response.json() == {"detail": "Not authenticated"}


def test_update_user_requires_admin_role(
	client: TestClient,
	regular_user: TestUser,
	regular_auth_headers: dict[str, str],
) -> None:
	"""Comprueba que un usuario regular no tenga permisos para actualizar perfiles ajenos (403)."""
	response = client.patch(
		f"{USERS_URL}{regular_user.id_usuario}",
		json={"username": "updated_user"},
		headers=regular_auth_headers,
	)

	assert response.status_code == 403
	assert response.json() == {
		"detail": "No tienes los permisos necesarios para realizar esta acción."
	}


def test_delete_user_removes_user(
	client: TestClient,
	create_user,
	auth_headers: dict[str, str],
) -> None:
	"""Verifica que un administrador pueda eliminar permanentemente un usuario del sistema."""
	target_user = create_user("delete_me", id_rol=RolEnum.FILMS.value)

	response = client.delete(
		f"{USERS_URL}{target_user.id_usuario}", headers=auth_headers
	)

	assert response.status_code == 200
	assert response.json() == {
		"detail": "Usuario delete_me eliminado exitosamente"
	}

	list_response = client.get(USERS_URL, headers=auth_headers)
	assert target_user.username not in [
		user["username"] for user in list_response.json()
	]


def test_delete_user_returns_not_found(
	client: TestClient, auth_headers: dict[str, str]
) -> None:
	"""Comprueba que se retorne un error 404 al intentar eliminar un ID de usuario inexistente."""
	response = client.delete(f"{USERS_URL}99999", headers=auth_headers)

	assert response.status_code == 404
	assert response.json() == {"detail": "Usuario no encontrado"}


def test_delete_user_rejects_self_deletion(
	client: TestClient,
	admin_user: TestUser,
	auth_headers: dict[str, str],
) -> None:
	"""Prueba la regla de negocio crítica que impide a un administrador eliminarse a sí mismo (400)."""
	response = client.delete(
		f"{USERS_URL}{admin_user.id_usuario}", headers=auth_headers
	)

	assert response.status_code == 400
	assert response.json() == {"detail": "No puedes eliminar tu propio usuario"}


def test_delete_user_requires_authentication(
	client: TestClient, regular_user: TestUser
) -> None:
	"""Valida que eliminar usuarios requiera un token de autenticación (401)."""
	response = client.delete(f"{USERS_URL}{regular_user.id_usuario}")

	assert response.status_code == 401
	assert response.json() == {"detail": "Not authenticated"}


def test_delete_user_requires_admin_role(
	client: TestClient,
	regular_user: TestUser,
	regular_auth_headers: dict[str, str],
) -> None:
	"""Comprueba que un usuario regular no tenga permisos para eliminar usuarios (403 Forbidden)."""
	response = client.delete(
		f"{USERS_URL}{regular_user.id_usuario}", headers=regular_auth_headers
	)

	assert response.status_code == 403
	assert response.json() == {
		"detail": "No tienes los permisos necesarios para realizar esta acción."
	}