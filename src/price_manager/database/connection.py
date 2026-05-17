from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class ConexionDB:
    """Administra la conexion a la base de datos mediante SQLAlchemy."""

    def __init__(
        self,
        url: str = "sqlite:///price_manager.db",
        echo: bool = False,
    ) -> None:
        self._engine: Engine = create_engine(url, echo=echo, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def crear_sesion(self) -> Session:
        """Devuelve una nueva sesion para operar con la base."""
        return self._session_factory()

    @contextmanager
    def transaccion(self) -> Iterator[Session]:
        """Maneja una transaccion con commit/rollback automatico."""
        sesion = self.crear_sesion()
        try:
            yield sesion
            sesion.commit()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    def probar_conexion(self) -> bool:
        """Ejecuta un SELECT simple para validar conectividad."""
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def cerrar(self) -> None:
        """Libera conexiones abiertas del engine."""
        self._engine.dispose()
