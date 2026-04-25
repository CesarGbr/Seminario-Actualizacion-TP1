from __future__ import annotations

import sys
from pathlib import Path

# Si se ejecuta este archivo directamente (python src/price_manager/main.py),
# agrega la raiz del proyecto para que funcionen los imports `src.price_manager`.
if __package__ is None or __package__ == "":
  sys.path.append(str(Path(__file__).resolve().parents[2]))

from price_manager.preload_data.preload_data import cargar_datos_iniciales, guardar_datos
from price_manager.repositories.repositories import (
  RepositorioCategoria,
  RepositorioCotizacionDolar,
  RepositorioPrecio,
  RepositorioProducto,
  RepositorioProveedor,
  RepositorioStock,
)
from price_manager.services.services import (
  ServicioCategoria,
  ServicioCompetenciaWeb,
  ServicioCotizacionDolar,
  ServicioPrecio,
  ServicioProducto,
  ServicioProveedor,
  ServicioStock,
)
from price_manager.ui.console import PriceManagerConsole


def main(import_default_data: bool = True) -> None:
  """Punto de entrada de la aplicacion.

  Inicializa dependencias, precarga datos semilla y lanza la UI de consola.
  """
  # Repositorios en memoria (capa de persistencia).
  repo_categoria = RepositorioCategoria()
  repo_proveedor = RepositorioProveedor()
  repo_precio = RepositorioPrecio()
  repo_cotizacion = RepositorioCotizacionDolar()
  repo_producto = RepositorioProducto()
  repo_stock = RepositorioStock()

  # Servicios (capa de negocio) con inyeccion de repositorios.
  servicio_categoria = ServicioCategoria(repo_categoria)
  servicio_proveedor = ServicioProveedor(repo_proveedor)
  servicio_precio = ServicioPrecio(repo_precio)
  servicio_cotizacion = ServicioCotizacionDolar(repo_cotizacion)
  servicio_competencia = ServicioCompetenciaWeb()
  servicio_producto = ServicioProducto(repo_producto, servicio_categoria, servicio_proveedor)
  servicio_stock = ServicioStock(repo_stock, servicio_producto)

  # Carga inicial opcional desde CSV para disponer de datos al iniciar la app.
  if import_default_data:
    cargar_datos_iniciales(
      servicio_categoria,
      servicio_proveedor,
      servicio_precio,
      servicio_cotizacion,
      servicio_producto,
      servicio_stock,
    )

  # Interfaz de usuario por consola.
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
  # Ejecuta main solo cuando el archivo se corre como script principal.
  main()
