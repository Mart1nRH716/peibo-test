"""Modelos(tablas de la base de datos)

EStá sección se declaran los modelos que se mapearan a tablas en la bd por medio de alembic
"""

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, func, ForeignKey
from datetime import datetime
from typing import List

class Rol(Base):
	__tablename__= "cat_rol"
	id_rol: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
	rol_nombre: Mapped[str] = mapped_column(String(20), nullable=False)
	usuarios: Mapped[List["Usuario"]] = relationship(back_populates="rol")

class Usuario(Base):
	__tablename__ = "tb_usuario"
	id_usuario: Mapped[int] = mapped_column(primary_key=True, autoincrement="auto")
	username: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
	email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
	id_rol: Mapped[int] = mapped_column(ForeignKey("cat_rol.id_rol"))
	rol: Mapped["Rol"] = relationship(back_populates="usuarios")
	password_hashed: Mapped[str] = mapped_column(String(255), nullable=False)
	created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
	is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

