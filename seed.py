# seed.py
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import engine, SessionLocal, Base
from app.models.usuario_model import Rol, Usuario
from app.utils.usuario_utils import hash_password

async def seed_data():	
	# Crea las tablas si aún no existen en la base de datos local
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

	async with SessionLocal() as db:
		async with db.begin():
			# 1. Crear los Roles base si no existen
			roles_a_crear = [ "admin", "films", "people", "locations", "species", "vehicles"]
			roles_db = {}

			for nombre_rol in roles_a_crear:
				# Verificar si el rol ya existe
				stmt_rol = select(Rol).where(Rol.rol_nombre == nombre_rol)
				result_rol = await db.execute(stmt_rol)
				rol_existente = result_rol.scalar_one_or_none()

				if not rol_existente:
					nuevo_rol = Rol(rol_nombre=nombre_rol)
					db.add(nuevo_rol)
					# Forzamos el flush para que la DB le asigne un ID antes del commit final
					await db.flush() 
					roles_db[nombre_rol] = nuevo_rol
					print(f"Rol '{nombre_rol}' creado con ID {nuevo_rol.id_rol}")
				else:
					roles_db[nombre_rol] = rol_existente
					print(f"El rol '{nombre_rol}' ya existe.")

			# 2. Crear los Usuarios base asignados a sus respectivos roles
			usuarios_a_crear = [
				{
					"username": "admin_user",
					"email": "admin@example.com",
					"password": "admin1234",  
					"rol": roles_db["admin"]
				},
				{
					"username": "films_user",
					"email": "films@example.com",
					"password": "films1234",
					"rol": roles_db["films"]
				},
				{
					"username": "people_user",
					"email": "people@example.com",
					"password": "people1234",
					"rol": roles_db["people"]
				},
				{
					"username": "locations_user",
					"email": "locations@example.com",
					"password": "locations1234",
					"rol": roles_db["locations"]
				},
				{
					"username": "species_user",
					"email": "species@example.com",
					"password": "species1234",
					"rol": roles_db["species"]
				},
				{
					"username": "vehicles_user",
					"email": "vehicles@example.com",
					"password": "vehicles1234",
					"rol": roles_db["vehicles"]
				}
			]

			for user_data in usuarios_a_crear:
				stmt_user = select(Usuario).where(Usuario.username == user_data["username"])
				result_user = await db.execute(stmt_user)
				user_existente = result_user.scalar_one_or_none()

				if not user_existente:
					nuevo_usuario = Usuario(
						username=user_data["username"],
						email=user_data["email"],
						password_hashed=hash_password(user_data["password"]),
						id_rol=user_data["rol"].id_rol,
						is_active=True
					)
					db.add(nuevo_usuario)
					print(f"Usuario '{user_data['username']}' creado asignado al rol '{user_data['rol'].rol_nombre}'")
				else:
					print(f"El usuario '{user_data['username']}' ya existe.")

	print("Datos creados")

if __name__ == "__main__":
	asyncio.run(seed_data())