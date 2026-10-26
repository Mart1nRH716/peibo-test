"""Configuración de la conexión a la base de datos utilizando SQLAlchemy.

Este módulo establece el motor de conexión (engine), la fábrica de sesiones (SessionLocal),
el generador para la inyección de dependencias en los endpoints (`get_db`) y la clase
base declarativa para los modelos ORM.
"""

from app.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Configuración del motor de base de datos con manejo de conexiones concurrentes
engine = create_async_engine(
	settings.DATABASE_URL,
	pool_size=5,
	max_overflow=10,
	pool_pre_ping=True,
)

# Generador de sesiones para interactuar con la base de datos
SessionLocal = async_sessionmaker(autoflush=False, bind=engine, expire_on_commit=False)


async def get_db():
	"""Generador de sesiones de base de datos para inyección de dependencias.

	Crea una nueva sesión para cada petición HTTP y se asegura de cerrarla
	automáticamente al finalizar, incluso si ocurren excepciones.
	"""
	db = SessionLocal()
	try:
		yield db
	finally:
		await db.close()


class Base(DeclarativeBase):
	"""Clase base declarativa para definir los modelos ORM de la base de datos."""
	
	pass