"""Esquemas de validación y serialización de datos (Pydantic).

Este módulo define los modelos Pydantic utilizados para validar las peticiones
de entrada (creación y actualización de usuarios), así como para estructurar las
respuestas JSON de salida (perfiles de usuario, roles y tokens de autenticación JWT),
aprovechando la configuración moderna de Pydantic v2 (`ConfigDict`).
"""
from pydantic import BaseModel, ConfigDict, Field, EmailStr

class RolResponse(BaseModel):
	"""Esquema de respuesta para representar los datos de un rol en el sistema."""
	model_config = ConfigDict(from_attributes=True)
	
	id_rol: int
	rol_nombre: str

class UsuarioCreate(BaseModel):
	"""Esquema de validación para los datos requeridos al registrar un nuevo usuario."""
	username: str = Field(min_length=2, max_length=200)
	password: str = Field(min_length=8, max_length=200)
	email: EmailStr = Field(min_length=1, max_length=200)
	id_rol: int

class UsuarioUpdate(BaseModel):
	"""Esquema de validación para la actualización parcial de un usuario (PATCH).

	Todos los campos son opcionales para permitir modificar únicamente los atributos deseados.
	"""
	username: str | None = Field(default=None, min_length=2, max_length=200)
	password: str | None = Field(default=None, min_length=6, max_length=200)
	email: EmailStr | None= Field(default=None, min_length=1, max_length=200)
	id_rol: int | None = Field(default=None)
	is_active: bool | None = Field(default=None)

class UsuarioResponse(BaseModel):
	"""Esquema de respuesta que estructura los datos públicos de un usuario, incluyendo su rol anidado."""
	model_config = ConfigDict(from_attributes=True)

	id_usuario: int
	username: str
	email: EmailStr
	rol: RolResponse 
	is_active: bool

class Token(BaseModel):
	"""Esquema de respuesta que encapsula el token de acceso JWT generado tras la autenticación."""
	access_token: str
	token_type: str

class TokenData(BaseModel):
	"""Esquema para almacenar los datos decodificados extraídos del payload del token JWT."""
	username: str | None = None