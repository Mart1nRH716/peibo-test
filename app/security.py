"""Módulo de seguridad, permisos y control de acceso basado en roles (RBAC).

Este módulo implementa dependencias reutilizables para FastAPI encargadas de verificar
la autenticación del usuario actual y validar si sus privilegios (IDs de roles)
coinciden con los permisos requeridos para ejecutar una acción específica.
"""
from app.models.usuario_model import Usuario
from app.schemas.enum import RolEnum
from fastapi import Depends, HTTPException, status
from app.utils.security_utils import get_current_active_user



class RoleChecker:
	"""Verificador de roles basado en dependencias (Callable Class).

    Comprueba si el usuario autenticado posee al menos uno de los roles permitidos
    para acceder a un recurso protegido, evaluando directamente su `id_rol` frente
    a los identificadores del catálogo de roles.
    """

	def __init__(self, allowed_roles: list[RolEnum]):
		"""Inicializa el verificador recibiendo una lista de roles permitidos y extrayendo sus IDs."""
        # Guardamos los IDs permitidos (ej: [1])
		self.allowed_role_ids = [role.value for role in allowed_roles]

	def __call__(self, current_user: Usuario = Depends(get_current_active_user)):
		"""Ejecuta la validación de permisos al invocar la dependencia en una ruta.

        Lanza una excepción HTTP 403 Forbidden si el rol del usuario no está autorizado.
        """
		# Validamos directamente contra la llave foránea del rol en la BD
		if current_user.id_rol not in self.allowed_role_ids:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="No tienes los permisos necesarios para realizar esta acción.",
			)
		return current_user