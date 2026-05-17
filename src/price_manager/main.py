# %%writefile price_manager/main.py

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from price_manager.migrations.migrations import migrar_datos  # noqa: E402
from price_manager.repositories.repositories import (  # noqa: E402
    RepositorioCategoria,
    RepositorioCotizacionDolar,
    RepositorioPrecio,
    RepositorioProducto,
    RepositorioProveedor,
    RepositorioStock,
)
from price_manager.services.services import (  # noqa: E402
    ServicioCategoria,
    ServicioCompetenciaWeb,
    ServicioCotizacionDolar,
    ServicioPrecio,
    ServicioProducto,
    ServicioProveedor,
    ServicioStock,
)
from price_manager.ui.console import PriceManagerConsole  # noqa: E402


def main(import_default_data: bool = True) -> None:
    """Punto de entrada de la aplicacion.

    Inicializa dependencias y lanza la UI de consola.
    Si import_default_data=True, migra CSV->DB antes de iniciar.
    """
    if import_default_data:
        base_dir = Path(__file__).resolve().parent
        migrar_datos(
            str(base_dir / "migrations" / "csv"),
            str(base_dir / "migrations" / "sql"),
        )

    repo_categoria = RepositorioCategoria()
    repo_proveedor = RepositorioProveedor()
    repo_precio = RepositorioPrecio()
    repo_cotizacion = RepositorioCotizacionDolar()
    repo_producto = RepositorioProducto()
    repo_stock = RepositorioStock()

    servicio_categoria = ServicioCategoria(repo_categoria)
    servicio_proveedor = ServicioProveedor(repo_proveedor)
    servicio_precio = ServicioPrecio(repo_precio)
    servicio_cotizacion = ServicioCotizacionDolar(repo_cotizacion)
    servicio_competencia = ServicioCompetenciaWeb()
    servicio_producto = ServicioProducto(
        repo_producto,
        servicio_categoria,
        servicio_proveedor,
    )
    servicio_stock = ServicioStock(repo_stock, servicio_producto)

    console = PriceManagerConsole(
        servicio_producto,
        servicio_stock,
        servicio_precio,
        servicio_cotizacion,
        servicio_competencia,
        servicio_categoria,
        servicio_proveedor,
    )

    console.run()


if __name__ == "__main__":
    main()
