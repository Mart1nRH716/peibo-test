"""Repositorio de persistencia y consultas para la entidad Usuario.

Este módulo encapsula todas las operaciones de base de datos relacionadas con
los usuarios utilizando SQLAlchemy de forma asíncrona, incluyendo la gestión
de transacciones, manejo de errores de integridad y consultas optimizadas con joins.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.usuario_model import Usuario
from sqlalchemy import select

from app.schemas.usuario_eschema import UsuarioCreate, UsuarioUpdate
from app.utils.usuario_utils import hash_password

class UsuarioRepository:
	"""Clase estática que centraliza el acceso a datos para el modelo Usuario."""
	@staticmethod
	async def get_or_search(db: AsyncSession, username:str | None) -> list[Usuario]:
		"""Obtiene una lista de usuarios, permitiendo filtrar por coincidencia parcial en el username."""
		if username:
			stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.username.ilike(f'%{username}%'))
		else:
			stmt = select(Usuario).options(joinedload(Usuario.rol)).order_by(Usuario.id_usuario.asc())

		result = await db.scalars(stmt)
		return list(result.all())

	@staticmethod
	async def get_by_username(db: AsyncSession, username: str) -> Usuario | None:
		"""Busca y retorna un usuario específico por su nombre de usuario único."""
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.username == username)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	@staticmethod
	async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
		"""Busca y retorna un usuario específico por su correo electrónico único."""
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.email == email)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	@staticmethod
	async def get_by_id(db: AsyncSession, id_usuario: int) -> Usuario | None:
		"""Busca y retorna un usuario por su identificador primario (ID)."""
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.id_usuario == id_usuario)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()


	@staticmethod
	async def create_user(db: AsyncSession, usuario_in: UsuarioCreate) -> Usuario:
		"""Crea un nuevo usuario en la base de datos aplicando hash a su contraseña.

        Maneja un rollback automático en caso de errores de restricción de integridad.
        """
		usuario = Usuario(
			username=usuario_in.username, 
			password_hashed=hash_password(usuario_in.password),
			email=usuario_in.email,
			id_rol=usuario_in.id_rol,
			is_active=True
			)
		try:
			db.add(usuario)
			await db.commit()
			await db.refresh(usuario, attribute_names=["rol"])
			return usuario
		except IntegrityError:
			await db.rollback()
			raise


	@staticmethod
	async def delete_user(db: AsyncSession, usuario_in: Usuario) -> None:
		"""Elimina de forma permanente un registro de usuario de la base de datos."""
		try:
			await db.delete(usuario_in)
			await db.commit()
		except IntegrityError as e:
			await db.rollback()
			raise e

	@staticmethod
	async def update_user(db: AsyncSession, usuario_db: Usuario, datos_nuevos: UsuarioUpdate) -> Usuario:
		"""Actualiza parcialmente los campos de un usuario existente en base a los datos proporcionados.

        Maneja de manera independiente el cifrado de la contraseña si esta es modificada.
        """
		campos_actualizar = datos_nuevos.model_dump(exclude_unset=True, exclude_none=True,)
		try:
			for key, value in campos_actualizar.items():
				if key == "password":
					usuario_db.password_hashed = hash_password(value)
				else:
					setattr(usuario_db, key, value)
			await db.commit()
			await db.refresh(usuario_db, attribute_names=["rol"])
			return usuario_db
		except IntegrityError:
			await db.rollback()
			raise