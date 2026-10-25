from pydantic import BaseModel, ConfigDict, Field, EmailStr

class RolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id_rol: int
    rol_nombre: str

class UsuarioCreate(BaseModel):
	username: str = Field(min_length=2, max_length=200)
	password: str = Field(min_length=8, max_length=200)
	email: EmailStr = Field(min_length=1, max_length=200)
	id_rol: int = Field(default=None)

class UsuarioUpdate(BaseModel):
	username: str | None = Field(default=None, min_length=2, max_length=200)
	password: str | None = Field(default=None, min_length=6, max_length=200)
	email: EmailStr | None= Field(default=None, min_length=1, max_length=200)
	id_rol: int | None = Field(default=None)
	is_active: bool | None = Field(default=None)

class UsuarioResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id_usuario: int
	username: str
	email: EmailStr
	rol: RolResponse 
	is_active: bool

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: str | None = None