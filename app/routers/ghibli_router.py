"""Endpoints de la API para la integración y consumo de datos de Studio Ghibli."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.security import GhibliRoleChecker
from app.services.ghibli_service import (
	GhibliItemNotFoundError,
	GhibliService,
	GhibliUpstreamError,
	InvalidGhibliResourceError,
)

router = APIRouter(tags=["Studio Ghibli"])


@router.get(
	"/{resource}",
	response_model=Any,
	summary="Consultar API de Studio Ghibli por rol",
	description="Permite a los usuarios consultar recursos de Ghibli estrictamente en función de su rol asignado.",
)
async def get_ghibli_data_by_role(
	resource: str,
	item_id: str | None = None,
	current_user=Depends(GhibliRoleChecker()),
):
	"""Consulta la API externa de Ghibli validando los permisos del rol del usuario autenticado."""
	try:
		return await GhibliService.get_ghibli_data(resource, item_id)
	except InvalidGhibliResourceError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
	except GhibliItemNotFoundError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
	except GhibliUpstreamError as exc:
		raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc