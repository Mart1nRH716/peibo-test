"""Servicio de lógica de negocio para la gestión de usuarios.

Este módulo centraliza las reglas de negocio, validaciones de unicidad (correo y username),
verificación de existencia de roles en catálogos, y coordinación de operaciones
de persistencia para los usuarios del sistema.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.rol_repository import RolRepository
from app.schemas.usuario_eschema import UsuarioCreate, UsuarioUpdate
from app.models.usuario_model import Usuario

class UsernameAlreadyExistsError(Exception):
	"""Excepción lanzada cuando se intenta registrar o actualizar un nombre de usuario ya existente."""
	pass

class EmailAlreadyExistsError(Exception):
	"""Excepción lanzada cuando se intenta registrar o actualizar un correo electrónico ya existente."""
	pass

class UserDoesNotExistError(Exception):
	"""Excepción lanzada cuando se busca un usuario que no se encuentra en la base de datos."""
	pass

class RoleDoesNotExistError(Exception):
	"""Excepción lanzada cuando el rol especificado no existe en el catálogo de la base de datos."""
	pass


class UsuarioService:
	"""Clase estática que agrupa la lógica de negocio y validaciones para los usuarios."""

	@staticmethod
	async def create_user(db: AsyncSession,usuario_in: UsuarioCreate) -> Usuario:
		"""Crea un nuevo usuario tras validar que el rol exista y que el username y email sean únicos."""
		rol_existente = await RolRepository.get_by_id(db, usuario_in.id_rol)
		if rol_existente is None:
			raise RoleDoesNotExistError("El rol indicado no existe")

		usuario_existente = await UsuarioRepository.get_by_username(db,username=usuario_in.username)

		if usuario_existente:
			raise UsernameAlreadyExistsError("El nombre de usuario ya está registrado")

		email_existente = await UsuarioRepository.get_by_email(db,email=usuario_in.email)

		if email_existente:
			raise EmailAlreadyExistsError("El correo electrónico ya está registrado")

		return await UsuarioRepository.create_user(db,usuario_in)

	@staticmethod
	async def get_by_id(db: AsyncSession, id_usuario: int) -> Usuario | None:
		"""Obtiene un usuario por su ID, lanzando una excepción si no existe."""
		usuario = await UsuarioRepository.get_by_id(db, id_usuario)
		if not usuario:
			raise UserDoesNotExistError("Usuario no encontrado")
		return usuario

	@staticmethod
	async def delete_user(db: AsyncSession, id_usuario: int) -> str:
		"""Elimina un usuario del sistema por su ID tras verificar su existencia previa."""
		usuario_a_eliminar = await UsuarioRepository.get_by_id(db, id_usuario)
		if not usuario_a_eliminar:
			raise UserDoesNotExistError("Usuario no encontrado")
		
		username = usuario_a_eliminar.username
		await UsuarioRepository.delete_user(db, usuario_a_eliminar)
		return username

	@staticmethod
	async def update_user(db: AsyncSession, id_usuario: int, datos_nuevos: UsuarioUpdate) -> Usuario:
		"""Actualiza parcialmente los datos de un usuario, validando existencia, roles y unicidad de campos."""
		usuario_existente = await UsuarioRepository.get_by_id(db, id_usuario)
		if not usuario_existente:
			raise UserDoesNotExistError("Usuario no encontrado")

		if datos_nuevos.id_rol is not None:
			rol_existente = await RolRepository.get_by_id(db, datos_nuevos.id_rol)
			if rol_existente is None:
				raise RoleDoesNotExistError("El rol indicado no existe")


		if datos_nuevos.username and datos_nuevos.username != usuario_existente.username:
			nombre_usuario_existente = await UsuarioRepository.get_by_username(db,username=datos_nuevos.username)
			if nombre_usuario_existente:
				raise UsernameAlreadyExistsError("El nombre de usuario ya está registrado")

		if datos_nuevos.email and datos_nuevos.email != usuario_existente.email:
			email_existente = await UsuarioRepository.get_by_email(db,email=datos_nuevos.email)
			if email_existente:
				raise EmailAlreadyExistsError("El correo electrónico ya está registrado")

		return await UsuarioRepository.update_user(db, usuario_existente, datos_nuevos)

