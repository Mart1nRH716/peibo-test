"""Endpoints de la API para la gestión y autenticación de usuarios.

Este módulo expone las rutas HTTP (REST) encargadas del flujo de autenticación JWT,
creación de usuarios, consulta de perfiles, actualización parcial (PATCH),
búsqueda por filtros y eliminación segura con validación de roles y permisos.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.usuario_model import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.enum import RolEnum
from app.schemas.usuario_eschema import Token, UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.security import RoleChecker
from app.services.auth_service import autenticar_usuario
from app.services.usuario_service import UsuarioService, UsernameAlreadyExistsError, EmailAlreadyExistsError, UserDoesNotExistError, RoleDoesNotExistError
from app.utils.security_utils import create_access_token, get_current_active_user

router = APIRouter(tags=["Usuarios"])

@router.post(
	"/token", 
	status_code=status.HTTP_200_OK, 
	response_model=Token,
	summary="Iniciar sesión",
	description="Autentica a un usuario mediante credenciales (username y password) y retorna un Token JWT de acceso.",
)
async def login(
	form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
	db: AsyncSession = Depends(get_db)
):
	"""Procesa el formulario de autenticación OAuth2 y genera el token de acceso Bearer."""
	usuario = await autenticar_usuario(db, form_data.username, form_data.password)
	if not usuario:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, 
			detail="Nombre de usuario o contraseña incorrectos", 
			headers={"WWW-Authenticate": "Bearer"}
		)
	token = create_access_token(data={"sub": usuario.username})
	return {"access_token": token, "token_type": "bearer"}


@router.post(
	"/crear-usuario", 
	status_code=status.HTTP_201_CREATED, 
	response_model=UsuarioResponse,
	summary="Crear nuevo usuario",
	description="Registra un nuevo usuario en el sistema. Requiere privilegios de administrador.",
)
async def create_user(
	usuario_data: UsuarioCreate, 
	db: AsyncSession = Depends(get_db), 
	current_user=Depends(RoleChecker([RolEnum.ADMIN]))
):
	"""Crea un usuario validando unicidad de correo/username y existencia del rol."""
	try:
		return await UsuarioService.create_user(db, usuario_data)
	except UsernameAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except EmailAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except RoleDoesNotExistError as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
	"/", 
	status_code=status.HTTP_200_OK, 
	response_model=list[UsuarioResponse], 
	dependencies=[Depends(get_current_active_user)],
	summary="Listar / Buscar usuarios",
	description="Retorna la lista de todos los usuarios registrados o permite filtrar por coincidencia parcial de username.",
)
async def get_users(username: str | None = None, db: AsyncSession = Depends(get_db)):
	"""Obtiene colecciones de usuarios aplicando filtros de búsqueda opcionales."""
	usuarios = await UsuarioRepository.get_or_search(db, username)
	return usuarios


@router.delete(
	"/{id_usuario}", 
	status_code=status.HTTP_200_OK,
	summary="Eliminar usuario",
	description="Elimina de forma permanente a un usuario del sistema mediante su ID. Requiere rol de administrador.",
)
async def delete_user(
	id_usuario: int, 
	db: AsyncSession = Depends(get_db), 
	current_user=Depends(RoleChecker([RolEnum.ADMIN]))
):
	"""Elimina un usuario validando que el administrador no intente eliminarse a sí mismo."""
	if id_usuario == current_user.id_usuario:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST, 
			detail="No puedes eliminar tu propio usuario"
		)
	
	try:
		nombre_usuario_eliminado = await UsuarioService.delete_user(db, id_usuario)
		return {"detail": f"Usuario {nombre_usuario_eliminado} eliminado exitosamente"}
	except UserDoesNotExistError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
	
	
@router.patch(
	"/{id_usuario}", 
	response_model=UsuarioResponse,
	status_code=status.HTTP_200_OK,
	summary="Actualizar usuario parcialmente",
	description="Modifica campos específicos de un usuario existente (PATCH). Requiere rol de administrador.",
	)
async def update_user(
	id_usuario: int, 
    datos_nuevos: UsuarioUpdate, 
	db: AsyncSession = Depends(get_db), 
	current_user=Depends(RoleChecker([RolEnum.ADMIN]))
):
	"""Actualiza de forma parcial los datos de un usuario tras validar reglas de negocio."""
	try:
		return await UsuarioService.update_user(db, id_usuario, datos_nuevos)
	except UsernameAlreadyExistsError as exc:
			raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except UserDoesNotExistError as exc:
				raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
	except EmailAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except RoleDoesNotExistError as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
	

@router.get(
	"/me", 
	response_model=UsuarioResponse,
	summary="Obtener perfil propio",
	description="Retorna la información del usuario autenticado actualmente en la sesión.",
)
async def get_my_user( current_user: Annotated[Usuario,Depends(get_current_active_user)]):
	"""Retorna el modelo del usuario extraído directamente del token Bearer actual."""
	return current_user