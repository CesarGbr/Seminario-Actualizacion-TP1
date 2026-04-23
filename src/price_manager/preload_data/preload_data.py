from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from price_manager.entities.entities import (
  Categoria,
  CotizacionDolar,
  Precio,
  Producto,
  Proveedor,
  Stock,
)
from price_manager.services.services import (
  ServicioCategoria,
  ServicioCotizacionDolar,
  ServicioPrecio,
  ServicioProducto,
  ServicioProveedor,
  ServicioStock,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
  """Lee un CSV y devuelve filas como diccionarios por columna."""
  with path.open("r", encoding="utf-8-sig", newline="") as file:
    return list(csv.DictReader(file))


def cargar_datos_iniciales(
  servicio_categoria: ServicioCategoria,
  servicio_proveedor: ServicioProveedor,
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacionDolar,
  servicio_producto: ServicioProducto,
  servicio_stock: ServicioStock,
  base_path: Path | None = None,
) -> None:
  """Carga datos semilla desde CSV respetando dependencias entre entidades.

  Orden de carga:
  1) catalogos base (categorias/proveedores/cotizaciones/precios)
  2) productos (requieren categoria, proveedor y precio)
  3) stock (requiere producto existente)
  """
  csv_path = base_path or Path(__file__).resolve().parents[1] / "migrations" / "csv"

  # Entidades base sin dependencias externas.
  for row in _read_csv(csv_path / "categorias.csv"):
    servicio_categoria.crear(Categoria(int(row["id"]), row["nombre"]))

  for row in _read_csv(csv_path / "proveedores.csv"):
    servicio_proveedor.crear(Proveedor(int(row["id"]), row["nombre_legal"], row["contacto"]))

  for row in _read_csv(csv_path / "cotizaciones.csv"):
    servicio_cotizacion.crear(
      CotizacionDolar(
        int(row["id"]),
        float(row["valor"]),
        date.fromisoformat(row["fecha"]),
        row["tipo"],
      )
    )

  # Se cachean por id para resolver referencias desde productos.csv.
  precios_por_id: dict[int, Precio] = {}
  for row in _read_csv(csv_path / "precios.csv"):
    precio = servicio_precio.crear(
      Precio(
        int(row["id"]),
        float(row["valor"]),
        row["moneda"],
        date.fromisoformat(row["fecha_actualizacion"]),
      )
    )
    precios_por_id[int(row["id"])] = precio

  for row in _read_csv(csv_path / "productos.csv"):
    categoria = servicio_categoria.buscar_por_id(int(row["categoria_id"]))
    proveedor = servicio_proveedor.buscar_por_id(int(row["proveedor_id"]))
    # Valida integridad referencial antes de crear producto.
    if categoria is None or proveedor is None:
      raise ValueError("Producto con categoria o proveedor inexistente en datos iniciales")

    servicio_producto.crear(
      Producto(
        int(row["id"]),
        row["nombre"],
        row["descripcion"],
        precios_por_id[int(row["precio_id"])],
        categoria,
        proveedor,
      )
    )

  for row in _read_csv(csv_path / "stock.csv"):
    producto = servicio_producto.buscar_por_id(int(row["producto_id"]))
    # Valida que el stock siempre apunte a un producto existente.
    if producto is None:
      raise ValueError("Stock con producto inexistente en datos iniciales")

    servicio_stock.crear(
      Stock(
        int(row["id"]),
        producto,
        row["almacen"],
        int(row["cantidad"]),
      )
    )
