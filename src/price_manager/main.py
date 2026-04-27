# %%writefile price_manager/main.py

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from price_manager.preload_data.preload_data import (  # noqa: E402
    cargar_datos_iniciales,
    guardar_datos,
)
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

    Inicializa dependencias, precarga datos semilla y lanza la UI de consola.
    """
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

    if import_default_data:
        cargar_datos_iniciales(
            servicio_categoria,
            servicio_proveedor,
            servicio_precio,
            servicio_cotizacion,
            servicio_producto,
            servicio_stock,
        )

    console = PriceManagerConsole(
        servicio_producto,
        servicio_stock,
        servicio_precio,
        servicio_cotizacion,
        servicio_competencia,
        servicio_categoria,
        servicio_proveedor,
    )

    try:
        console.run()
    finally:
        guardar_datos(
            servicio_categoria,
            servicio_proveedor,
            servicio_precio,
            servicio_cotizacion,
            servicio_producto,
            servicio_stock,
        )


if __name__ == "__main__":
    main()