"""Punto de entrada principal de la aplicación FastAPI.

Este módulo inicializa la instancia de la aplicación, configura los metadatos
globales obtenidos desde las variables de entorno, registra los enrutadores (routers)
bajo el prefijo de la versión de la API y expone un endpoint de diagnóstico (health check).
"""
from fastapi import FastAPI
from app.config import settings
from app.routers.usuarios_router import router as usuarios_router

# Inicialización de la aplicación FastAPI con metadatos globales
app= FastAPI(
	title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API REST de usuarios con integración a la API de Studio Ghibli según roles.",
)

# Registro de enrutadores de la API (versión 1)
app.include_router(usuarios_router, prefix=f"{settings.API_V1_STR}/usuarios", tags=["usuarios"],)


@app.get(
	"/health", 
	include_in_schema=False,
	summary="Verificación de estado",
	description="Endpoint interno para comprobar la disponibilidad y versión actual del servicio.",
)
async def health_check():
	"""Valida que la API esté activa y respondiendo correctamente."""
	return {"status": "ok", "service": f"{settings.PROJECT_NAME}", "version": "1.0.0"}
