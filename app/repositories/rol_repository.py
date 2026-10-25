from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.usuario_model import Rol
from sqlalchemy import select

class RolRepository:
	@staticmethod
	async def get_by_id(db: AsyncSession, id_rol: int) -> Rol | None:
		stmt = select(Rol).where(Rol.id_rol == id_rol)
		result = await db.execute(stmt)
		return result.scalar_one_or_none()
