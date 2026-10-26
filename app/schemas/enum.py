"""Definición de enumeraciones (Enums) para los roles del sistema.

Este módulo mapea los roles internos de la base de datos (`cat_rol`) con identificadores
numéricos estables, facilitando la validación de permisos mediante dependencias y
el enrutamiento hacia la API de Studio Ghibli según corresponda.
"""
from enum import Enum


class RolEnum(int, Enum):
	"""Enumeración que representa los roles permitidos en el sistema y sus respectivos IDs en la BD."""
	ADMIN = 1
	FILMS = 2
	PEOPLE = 3
	LOCATIONS = 4
	SPECIES = 5
	VEHICLES = 6