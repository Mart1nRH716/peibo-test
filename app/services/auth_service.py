"""Servicio de autenticación y verificación de credenciales.

Este módulo encapsula la lógica de negocio relacionada con el proceso de login,
incluyendo la validación de existencia de usuarios, la verificación segura de contraseñas
con hashes y la mitigación de ataques de temporización (timing attacks).
"""
from sqlalchemy.orm import Session
from app.repositories.usuario_repository import UsuarioRepository
from pwdlib import PasswordHash
from app.utils.usuario_utils import verify_password


password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

async def autenticar_usuario(db: Session, username: str, password: str):
	"""Autentica a un usuario verificando sus credenciales en la base de datos.

    Aplica una verificación de contraseña ficticia (dummy) si el usuario no existe,
    lo que previene ataques de temporización (timing attacks) basados en el tiempo de respuesta.
    """
	usuario = await UsuarioRepository.get_by_username(db, username)
	if not usuario:
		# Verificación de contraseña dummy para evitar ataques de temporización
		verify_password(password, DUMMY_HASH)  
		return None
	if not verify_password(password, usuario.password_hashed):
		return None
	return usuario