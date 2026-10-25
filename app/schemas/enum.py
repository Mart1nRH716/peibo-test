from enum import Enum


class RolEnum(int, Enum):
	ADMIN = 1
	FILMS = 2
	PEOPLE = 3
	LOCATIONS = 4
	SPECIES = 5
	VEHICLES = 6