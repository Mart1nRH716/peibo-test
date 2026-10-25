from app.models.usuario_model import Usuario
from app.schemas.enum import RolEnum
from fastapi import Depends, HTTPException, status
from app.utils.security_utils import get_current_active_user



class RoleChecker:

	def __init__(self, allowed_roles: list[RolEnum]):
		# Guardamos los IDs permitidos (ej: [1])
		self.allowed_role_ids = [role.value for role in allowed_roles]

	def __call__(self, current_user: Usuario = Depends(get_current_active_user)):
		# Validamos directamente contra la llave foránea del rol en la BD
		if current_user.id_rol not in self.allowed_role_ids:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="No tienes los permisos necesarios para realizar esta acción.",
			)
		return current_user