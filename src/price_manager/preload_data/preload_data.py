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


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


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
    servicio_categoria.crear(Categoria(id=int(row["id"]), nombre=row["nombre"]))

  for row in _read_csv(csv_path / "proveedores.csv"):
    servicio_proveedor.crear(
      Proveedor(id=int(row["id"]), nombre=row["nombre_legal"], contacto=row["contacto"])
    )

  for row in _read_csv(csv_path / "cotizaciones.csv"):
    servicio_cotizacion.crear(
      CotizacionDolar(
        id=int(row["id"]),
        valor=float(row["valor"]),
        fecha=date.fromisoformat(row["fecha"]),
        tipo=row["tipo"],
      )
    )

  # Se cachean por id para resolver referencias desde productos.csv.
  precios_por_id: dict[int, Precio] = {}
  for row in _read_csv(csv_path / "precios.csv"):
    precio = servicio_precio.crear(
      Precio(
        id=int(row["id"]),
        valor=float(row["valor"]),
        moneda=row["moneda"],
        fecha=date.fromisoformat(row["fecha_actualizacion"]),
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
        id=int(row["id"]),
        nombre=row["nombre"],
        descripcion=row["descripcion"],
        precio=precios_por_id[int(row["precio_id"])],
        categoria=categoria,
        proveedor=proveedor,
      )
    )

  for row in _read_csv(csv_path / "stock.csv"):
    producto = servicio_producto.buscar_por_id(int(row["producto_id"]))
    # Valida que el stock siempre apunte a un producto existente.
    if producto is None:
      raise ValueError("Stock con producto inexistente en datos iniciales")

    servicio_stock.crear(
      Stock(
        id=int(row["id"]),
        producto=producto,
        almacen=row["almacen"],
        cantidad=int(row["cantidad"]),
      )
    )


def guardar_datos(
  servicio_categoria: ServicioCategoria,
  servicio_proveedor: ServicioProveedor,
  servicio_precio: ServicioPrecio,
  servicio_cotizacion: ServicioCotizacionDolar,
  servicio_producto: ServicioProducto,
  servicio_stock: ServicioStock,
  base_path: Path | None = None,
) -> None:
  """Persistencia de salida: serializa estado en memoria a CSV."""
  csv_path = base_path or Path(__file__).resolve().parents[1] / "migrations" / "csv"

  categorias = [
    {"id": str(c.id), "nombre": c.nombre}
    for c in sorted(servicio_categoria.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(csv_path / "categorias.csv", categorias, ["id", "nombre"])

  proveedores = [
    {"id": str(p.id), "nombre_legal": p.nombre_legal, "contacto": p.contacto}
    for p in sorted(servicio_proveedor.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(csv_path / "proveedores.csv", proveedores, ["id", "nombre_legal", "contacto"])

  cotizaciones = [
    {
      "id": str(c.id),
      "valor": f"{c.valor:.4f}",
      "fecha": c.fecha.isoformat(),
      "tipo": c.tipo,
    }
    for c in sorted(servicio_cotizacion.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(csv_path / "cotizaciones.csv", cotizaciones, ["id", "valor", "fecha", "tipo"])

  precios = [
    {
      "id": str(p.id),
      "valor": f"{p.valor:.4f}",
      "moneda": p.moneda,
      "fecha_actualizacion": p.fecha_actualizacion.isoformat(),
    }
    for p in sorted(servicio_precio.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(csv_path / "precios.csv", precios, ["id", "valor", "moneda", "fecha_actualizacion"])

  productos = [
    {
      "id": str(p.id),
      "nombre": p.nombre,
      "descripcion": p.descripcion,
      "precio_id": str(p.precio.id),
      "categoria_id": str(p.categoria.id),
      "proveedor_id": str(p.proveedor.id),
    }
    for p in sorted(servicio_producto.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(
    csv_path / "productos.csv",
    productos,
    ["id", "nombre", "descripcion", "precio_id", "categoria_id", "proveedor_id"],
  )

  stock = [
    {
      "id": str(s.id),
      "producto_id": str(s.producto.id),
      "almacen": s.almacen,
      "cantidad": str(s.cantidad),
    }
    for s in sorted(servicio_stock.listar_todos(), key=lambda x: x.id)
  ]
  _write_csv(csv_path / "stock.csv", stock, ["id", "producto_id", "almacen", "cantidad"])
