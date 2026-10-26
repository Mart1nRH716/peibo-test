from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
	"""Configuración global de la aplicación utilizando variables de entorno.

    Maneja las variables principales del proyecto, prefijos de rutas,
	cadena de conexión a la base de datos, etc. desde un archivo .env.
    """
	PROJECT_NAME:str = "Usuarios API"
	API_V1_STR:str = "/api/v1"
	ACCESS_TOKEN_EXPIRE_MINUTES:int
	SECRET_KEY: str
	ALGORITHM: str
	DATABASE_URL:str
	TEST_DATABASE_URL: str 

	model_config = SettingsConfigDict(env_file=".env")


settings = Settings()