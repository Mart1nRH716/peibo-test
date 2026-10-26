"""Configuración global de pruebas de integración (Pytest).

Este módulo define las fixtures de Pytest necesarias para levantar una base de datos
de pruebas aislada (`peibo_test`), gestionar motores y sesiones asíncronas de SQLAlchemy,
sobrescribir dependencias de FastAPI y proveer clientes HTTP de prueba junto con
utilidades de autenticación y creación rápida de usuarios y roles.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient

# Carga de variables de entorno de prueba
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
_test_database_url = os.environ.get("TEST_DATABASE_URL")
if not _test_database_url:
	raise RuntimeError(
		"TEST_DATABASE_URL es obligatoria y debe apuntar a la base PostgreSQL peibo_test."
	)

try:
	_parsed_test_url = make_url(_test_database_url)
except Exception as exc:
	raise RuntimeError("TEST_DATABASE_URL no es una URL válida.") from exc

# Validación para evitar ejecutar pruebas en bases productivas
if _parsed_test_url.database != "peibo_test":
	raise RuntimeError(
		"Por seguridad, las pruebas solo pueden usar una base llamada peibo_test."
	)

os.environ["DATABASE_URL"] = _test_database_url

from app.database import Base, get_db
from app.main import app
from app.models.usuario_model import Rol, Usuario
from app.schemas.enum import RolEnum
from app.utils.usuario_utils import hash_password

# Configuración del motor y fábrica de sesiones asíncronas para pruebas
_test_engine = create_async_engine(_test_database_url, poolclass=NullPool)
_TestingSessionLocal = async_sessionmaker(
	bind=_test_engine,
	class_=AsyncSession,
	autoflush=False,
	expire_on_commit=False,
)


@dataclass(frozen=True)
class TestUser:
	"""Estructura de datos ligera para representar un usuario dentro del contexto de pruebas."""
	id_usuario: int
	username: str
	email: str
	id_rol: int


@pytest.fixture(scope="session", autouse=True)
def dispose_test_engine() -> Iterator[None]:
	"""Cierra y descarta el motor de base de datos al finalizar toda la sesión de pruebas."""
	yield
	asyncio.run(_test_engine.dispose())


@pytest.fixture(autouse=True)
def isolated_test_database() -> Iterator[None]:
	"""Reincide y limpia la base de datos de pruebas antes de cada test, precargando los roles del sistema."""
	async def reset_database() -> None:
		async with _test_engine.begin() as connection:
			await connection.run_sync(Base.metadata.drop_all)
			await connection.run_sync(Base.metadata.create_all)

		async with _TestingSessionLocal() as session:
			session.add_all(
				[
					Rol(id_rol=role.value, rol_nombre=role.name.lower())
					for role in RolEnum
				]
			)
			await session.commit()

	asyncio.run(reset_database())
	yield


@pytest.fixture
def client() -> Iterator[TestClient]:
	"""Provee un cliente de pruebas HTTP (TestClient) con la inyección de base de datos sobresuelta."""
	previous_overrides = app.dependency_overrides.copy()

	async def override_get_db() -> AsyncIterator[AsyncSession]:
		async with _TestingSessionLocal() as session:
			yield session

	app.dependency_overrides[get_db] = override_get_db
	try:
		with TestClient(app) as test_client:
			yield test_client
	finally:
		app.dependency_overrides.clear()
		app.dependency_overrides.update(previous_overrides)


@pytest.fixture
def create_user() -> Iterator:
	"""Fixture auxiliar (Factory) para registrar usuarios de prueba personalizados en la base de datos."""
	def _create_user(
		username: str,
		email: str | None = None,
		password: str = "password123",
		id_rol: int = RolEnum.ADMIN.value,
		is_active: bool = True,
	) -> TestUser:
		async def persist_user() -> TestUser:
			async with _TestingSessionLocal() as session:
				user = Usuario(
					username=username,
					email=email or f"{username}@example.com",
					password_hashed=hash_password(password),
					id_rol=id_rol,
					is_active=is_active,
				)
				session.add(user)
				await session.commit()
				await session.refresh(user)
				return TestUser(
					id_usuario=user.id_usuario,
					username=user.username,
					email=user.email,
					id_rol=user.id_rol,
				)

		return asyncio.run(persist_user())

	yield _create_user


@pytest.fixture
def admin_user(create_user) -> TestUser:
	"""Crea y retorna un usuario administrador por defecto para las pruebas."""
	return create_user("admin_test", id_rol=RolEnum.ADMIN.value)


@pytest.fixture
def regular_user(create_user) -> TestUser:
	"""Crea y retorna un usuario con rol regular (FILMS) por defecto para las pruebas."""
	return create_user("regular_test", id_rol=RolEnum.FILMS.value)


@pytest.fixture
def auth_headers(client: TestClient, admin_user: TestUser) -> dict[str, str]:
	"""Obtiene y retorna las cabeceras de autorización HTTP con un token JWT de Administrador."""
	response = client.post(
		"/api/v1/usuarios/token",
		data={"username": admin_user.username, "password": "password123"},
	)
	assert response.status_code == 200
	return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def regular_auth_headers(client: TestClient, regular_user: TestUser) -> dict[str, str]:
	"""Obtiene y retorna las cabeceras de autorización HTTP con un token JWT de usuario regular."""
	response = client.post(
		"/api/v1/usuarios/token",
		data={"username": regular_user.username, "password": "password123"},
	)
	assert response.status_code == 200
	return {"Authorization": f"Bearer {response.json()['access_token']}"}
