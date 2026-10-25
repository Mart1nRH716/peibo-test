from fastapi import FastAPI
from app.config import settings
from app.routers.usuarios_router import router as usuarios_router

app= FastAPI(title=settings.PROJECT_NAME)

app.include_router(usuarios_router, prefix=f"{settings.API_V1_STR}/usuarios", tags=["usuarios"],)


@app.get("/health", include_in_schema=False)
async def health_check():
	return {"status": "ok", "service": f"{settings.PROJECT_NAME}", "version": "1.0.0"}
