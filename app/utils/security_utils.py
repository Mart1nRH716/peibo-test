# app/utils/security.py
import datetime

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database import get_db
from app.models.usuario_model import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_eschema import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/usuarios/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.now(timezone.utc) + expires_delta
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
	return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
		username = payload.get("sub")
		if username is None:
			raise credentials_exception
		token_data = TokenData(username=username)
	except InvalidTokenError:
		raise credentials_exception
	user =  await UsuarioRepository.get_by_username(db, token_data.username)
	if user is None:
		raise credentials_exception
	return user


async def get_current_active_user(current_user: Annotated[Usuario, Depends(get_current_user)],):
	if not current_user.is_active:
		raise HTTPException(status_code=400, detail="Inactive user")
	return current_user