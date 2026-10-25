from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_eschema import UsuarioCreate
from app.models.usuario_model import Usuario

class UsernameAlreadyExistsError(Exception):
	pass

class EmailAlreadyExistsError(Exception):
	pass

class UserDoesNotExistError(Exception):
	pass


class UsuarioService:

	@staticmethod
	async def create_user(db: AsyncSession,usuario_in: UsuarioCreate) -> Usuario:
		usuario_existente = await UsuarioRepository.get_by_username(db,username=usuario_in.username)

		if usuario_existente:
			raise UsernameAlreadyExistsError("El nombre de usuario ya está registrado")

		email_existente = await UsuarioRepository.get_by_email(db,email=usuario_in.email)

		if email_existente:
			raise EmailAlreadyExistsError("El correo electrónico ya está registrado")

		return await UsuarioRepository.create_user(db,usuario_in)

	@staticmethod
	async def delete_user(db: AsyncSession, id_usuario: int) -> str:
		usuario_a_eliminar = await UsuarioRepository.get_by_id(db, id_usuario)
		if not usuario_a_eliminar:
			raise UserDoesNotExistError("Usuario no encontrado")
		
		username = usuario_a_eliminar.username
		await UsuarioRepository.delete_user(db, usuario_a_eliminar)
		return username

