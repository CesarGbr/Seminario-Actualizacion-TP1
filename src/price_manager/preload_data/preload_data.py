# %%writefile price_manager/preload_data/preload_data.py

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


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
) -> None:
    """Escribe filas en un archivo CSV."""
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
    csv_path = (
        base_path
        or Path(__file__).resolve().parents[1] / "migrations" / "csv"
    )

    for row in _read_csv(csv_path / "categorias.csv"):
        servicio_categoria.crear(
            Categoria(
                id=int(row["id"]),
                nombre=row["nombre"],
            )
        )

    for row in _read_csv(csv_path / "proveedores.csv"):
        servicio_proveedor.crear(
            Proveedor(
                id=int(row["id"]),
                nombre=row["nombre_legal"],
                contacto=row["contacto"],
            )
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
        categoria = servicio_categoria.buscar_por_id(
            int(row["categoria_id"])
        )
        proveedor = servicio_proveedor.buscar_por_id(
            int(row["proveedor_id"])
        )

        if categoria is None or proveedor is None:
            raise ValueError(
                "Producto con categoria o proveedor inexistente en "
                "datos iniciales"
            )

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
        producto = servicio_producto.buscar_por_id(
            int(row["producto_id"])
        )

        if producto is None:
            raise ValueError(
                "Stock con producto inexistente en datos iniciales"
            )

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
    csv_path = (
        base_path
        or Path(__file__).resolve().parents[1] / "migrations" / "csv"
    )

    categorias = [
        {
            "id": str(categoria.id),
            "nombre": categoria.nombre,
        }
        for categoria in sorted(
            servicio_categoria.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "categorias.csv",
        categorias,
        ["id", "nombre"],
    )

    proveedores = [
        {
            "id": str(proveedor.id),
            "nombre_legal": proveedor.nombre_legal,
            "contacto": proveedor.contacto,
        }
        for proveedor in sorted(
            servicio_proveedor.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "proveedores.csv",
        proveedores,
        ["id", "nombre_legal", "contacto"],
    )

    cotizaciones = [
        {
            "id": str(cotizacion.id),
            "valor": f"{cotizacion.valor:.4f}",
            "fecha": cotizacion.fecha.isoformat(),
            "tipo": cotizacion.tipo,
        }
        for cotizacion in sorted(
            servicio_cotizacion.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "cotizaciones.csv",
        cotizaciones,
        ["id", "valor", "fecha", "tipo"],
    )

    precios = [
        {
            "id": str(precio.id),
            "valor": f"{precio.valor:.4f}",
            "moneda": precio.moneda,
            "fecha_actualizacion": precio.fecha_actualizacion.isoformat(),
        }
        for precio in sorted(
            servicio_precio.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "precios.csv",
        precios,
        ["id", "valor", "moneda", "fecha_actualizacion"],
    )

    productos = [
        {
            "id": str(producto.id),
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio_id": str(producto.precio.id),
            "categoria_id": str(producto.categoria.id),
            "proveedor_id": str(producto.proveedor.id),
        }
        for producto in sorted(
            servicio_producto.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "productos.csv",
        productos,
        [
            "id",
            "nombre",
            "descripcion",
            "precio_id",
            "categoria_id",
            "proveedor_id",
        ],
    )

    stock = [
        {
            "id": str(item.id),
            "producto_id": str(item.producto.id),
            "almacen": item.almacen,
            "cantidad": str(item.cantidad),
        }
        for item in sorted(
            servicio_stock.listar_todos(),
            key=lambda item: item.id,
        )
    ]
    _write_csv(
        csv_path / "stock.csv",
        stock,
        ["id", "producto_id", "almacen", "cantidad"],
    )