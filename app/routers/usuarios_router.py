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
from app.services.usuario_service import UsuarioService, UsernameAlreadyExistsError, EmailAlreadyExistsError, UserDoesNotExistError
from app.utils.security_utils import create_access_token, get_current_active_user

router = APIRouter()

@router.post("/token", status_code=status.HTTP_200_OK, response_model=Token,)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: AsyncSession = Depends(get_db)):
	usuario = await autenticar_usuario(db, form_data.username, form_data.password)
	if not usuario:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nombre de usuario o contraseña incorrectos", headers={"WWW-Authenticate": "Bearer"})

	token = create_access_token(data={"sub": usuario.username})

	return {"access_token": token, "token_type": "bearer"}


@router.post("/crear-usuario", status_code=status.HTTP_201_CREATED, response_model=UsuarioResponse)
async def create_user(
		usuario_data: UsuarioCreate, 
		db: AsyncSession = Depends(get_db), 
		current_user: Usuario = Depends(get_current_active_user)
	):

	if current_user.rol.rol_nombre != "admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para crear usuarios")

	try:
		nuevo_usuario = await UsuarioService.create_user(db, usuario_data)
		return nuevo_usuario
	except UsernameAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except EmailAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) 

@router.get("/", status_code=status.HTTP_200_OK, response_model=list[UsuarioResponse], dependencies=[Depends(get_current_active_user)])
async def get_users(username: str | None = None, db: AsyncSession = Depends(get_db)):
	usuarios = await UsuarioRepository.get_or_search(db, username)
	return usuarios



@router.delete("/{id_usuario}", status_code=status.HTTP_200_OK)
async def delete_user(
		id_usuario: int, 
		db: AsyncSession = Depends(get_db), 
		current_user: Usuario = Depends(get_current_active_user)
	):

	if current_user.rol.rol_nombre != "admin":
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para eliminar usuarios")
	
	if id_usuario == current_user.id_usuario:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes eliminar tu propio usuario")
	
	try:
		nombre_usuario_eliminado = await UsuarioService.delete_user(db, id_usuario)
		return {"detail": f"Usuario {nombre_usuario_eliminado} eliminado exitosamente"}
	except UserDoesNotExistError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
	
	
@router.patch("/{id_usuario}", response_model=UsuarioResponse,status_code=status.HTTP_200_OK)
async def update_user(id_usuario: int, datos_nuevos: UsuarioUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(RoleChecker([RolEnum.ADMIN]))):
	try:
		return await UsuarioService.update_user(db, id_usuario, datos_nuevos)
	except UsernameAlreadyExistsError as exc:
			raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	except UserDoesNotExistError as exc:
				raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
	except EmailAlreadyExistsError as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
	

	
	
@router.get("/me", response_model=UsuarioResponse)
async def get_my_user( current_user: Annotated[Usuario,Depends(get_current_active_user)]):
	return current_user