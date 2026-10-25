from sqlalchemy.orm import Session
from app.repositories.usuario_repository import UsuarioRepository
from pwdlib import PasswordHash
from app.utils.usuario_utils import verify_password


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

async def autenticar_usuario(db: Session, username: str, password: str):
	usuario = await UsuarioRepository.get_by_username(db, username)
	if not usuario:
		verify_password(password, DUMMY_HASH)  # Verificación de contraseña dummy para evitar ataques de temporización
		return None
	if not verify_password(password, usuario.password_hashed):
		return None
	return usuario