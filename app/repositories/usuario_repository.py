from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.usuario_model import Usuario
from sqlalchemy import select

from app.schemas.usuario_eschema import UsuarioCreate, UsuarioUpdate
from app.utils.usuario_utils import hash_password

class UsuarioRepository:
	@staticmethod
	async def get_or_search(db: AsyncSession, username:str | None) -> list[Usuario]:
		if username:
			stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.username.ilike(f'%{username}%'))
		else:
			stmt = select(Usuario).options(joinedload(Usuario.rol)).order_by(Usuario.id_usuario.asc())

		result = await db.scalars(stmt)
		return list(result.all())

	@staticmethod
	async def get_by_username(db: AsyncSession, username: str) -> Usuario | None:
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.username == username)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	@staticmethod
	async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.email == email)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()

	@staticmethod
	async def get_by_id(db: AsyncSession, id_usuario: int) -> Usuario | None:
		stmt = select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.id_usuario == id_usuario)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()


	@staticmethod
	async def create_user(db: AsyncSession, usuario_in: UsuarioCreate) -> Usuario:
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
		try:
			await db.delete(usuario_in)
			await db.commit()
		except IntegrityError as e:
			await db.rollback()
			raise e

	@staticmethod
	async def update_user(db: AsyncSession, usuario_db: Usuario, datos_nuevos: UsuarioUpdate) -> Usuario:
		campos_actualizar = datos_nuevos.model_dump(exclude_unset=True)
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