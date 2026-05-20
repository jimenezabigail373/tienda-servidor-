"""
=============================================================
  DATABASE.PY  -  Gestion de base de datos SQLite
=============================================================
"""

import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "tienda.db"


def obtener_conexion():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Resultados como diccionarios
    return conn


def inicializar_base_de_datos():
    """Crea tablas e inserta productos de ejemplo si no existen."""
    conn = obtener_conexion()
    cur = conn.cursor()

    # Tabla clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT NOT NULL,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telefono TEXT,
            creado   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla productos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            descripcion TEXT,
            precio      REAL NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0,
            categoria   TEXT,
            imagen_url  TEXT
        )
    """)

    # Tabla ordenes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_orden TEXT UNIQUE NOT NULL,
            cliente_id   INTEGER,
            cliente_email TEXT,
            cliente_nombre TEXT,
            subtotal     REAL,
            impuesto     REAL,
            total        REAL,
            estado       TEXT DEFAULT 'PENDIENTE',
            fecha        TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    # Tabla detalle de ordenes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_orden (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id    INTEGER,
            producto_id INTEGER,
            nombre_prod TEXT,
            cantidad    INTEGER,
            precio_unit REAL,
            subtotal    REAL,
            FOREIGN KEY (orden_id) REFERENCES ordenes(id)
        )
    """)

    conn.commit()
    _insertar_productos_ejemplo(cur, conn)
    conn.close()


def _insertar_productos_ejemplo(cur, conn):
    """Inserta productos de muestra si la tabla esta vacia."""
    cur.execute("SELECT COUNT(*) FROM productos")
    if cur.fetchone()[0] > 0:
        return

    productos = [
        ("Laptop ProMax 15",    "Intel i7, 16GB RAM, 512GB SSD", 1299.99, 10, "Electronica"),
        ("Mouse Inalambrico",   "Ergonomico, 2.4GHz, bateria AAA", 35.00,  50, "Accesorios"),
        ("Teclado Mecanico",    "RGB, switches azules, USB-C",    89.99,  25, "Accesorios"),
        ("Monitor 27 pulgadas", "FHD 144Hz, 1ms, HDMI/DP",       299.00, 15, "Electronica"),
        ("Auriculares BT Pro",  "ANC, 30h bateria, plegables",    149.99, 30, "Audio"),
        ("Webcam HD 1080p",     "Con microfono, clip universal",  59.99,  40, "Accesorios"),
        ("SSD Externo 1TB",     "USB 3.2, 1050MB/s lectura",      109.99, 20, "Almacenamiento"),
        ("Hub USB-C 7en1",      "HDMI 4K, USB-A x3, SD, PD 100W", 45.00, 35, "Accesorios"),
        ("Silla Gamer ErgoX",   "Lumbar ajustable, reclinable",   399.00,  8, "Mobiliario"),
        ("Pad Mouse XL",        "900x400mm, antideslizante",       19.99, 60, "Accesorios"),
    ]

    cur.executemany(
        "INSERT INTO productos (nombre, descripcion, precio, stock, categoria) VALUES (?,?,?,?,?)",
        productos
    )
    conn.commit()


# ── CLIENTES ───────────────────────────────────────────────

def registrar_cliente(nombre, email, password, telefono=""):
    conn = obtener_conexion()
    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn.execute(
            "INSERT INTO clientes (nombre, email, password, telefono) VALUES (?,?,?,?)",
            (nombre, email, pwd_hash, telefono)
        )
        conn.commit()
        return {"ok": True, "mensaje": "Cliente registrado correctamente"}
    except sqlite3.IntegrityError:
        return {"ok": False, "mensaje": "El correo ya esta registrado"}
    finally:
        conn.close()


def autenticar_cliente(email, password):
    conn = obtener_conexion()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    row = conn.execute(
        "SELECT id, nombre, email FROM clientes WHERE email=? AND password=?",
        (email, pwd_hash)
    ).fetchone()
    conn.close()
    if row:
        return {"ok": True, "cliente": dict(row)}
    return {"ok": False, "mensaje": "Credenciales incorrectas"}


# ── PRODUCTOS ──────────────────────────────────────────────

def obtener_catalogo():
    conn = obtener_conexion()
    rows = conn.execute(
        "SELECT id, nombre, descripcion, precio, stock, categoria FROM productos WHERE stock > 0"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_producto(producto_id):
    conn = obtener_conexion()
    row = conn.execute(
        "SELECT * FROM productos WHERE id=?", (producto_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── ORDENES ────────────────────────────────────────────────

def crear_orden(cliente_email, cliente_nombre, carrito):
    """
    carrito = [{"producto_id": 1, "cantidad": 2}, ...]
    Retorna el numero de orden y el total.
    """
    conn = obtener_conexion()
    try:
        # Validar stock y calcular totales
        items = []
        subtotal = 0.0
        for item in carrito:
            prod = conn.execute(
                "SELECT id, nombre, precio, stock FROM productos WHERE id=?",
                (item["producto_id"],)
            ).fetchone()
            if not prod:
                return {"ok": False, "mensaje": f"Producto {item['producto_id']} no encontrado"}
            if prod["stock"] < item["cantidad"]:
                return {"ok": False, "mensaje": f"Stock insuficiente para '{prod['nombre']}'"}
            sub = prod["precio"] * item["cantidad"]
            subtotal += sub
            items.append({
                "producto_id": prod["id"],
                "nombre":      prod["nombre"],
                "cantidad":    item["cantidad"],
                "precio_unit": prod["precio"],
                "subtotal":    sub
            })

        impuesto = round(subtotal * 0.12, 2)  # IVA 12%
        total    = round(subtotal + impuesto, 2)

        # Numero de orden unico
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        numero_orden = f"ORD-{ts}"

        # Insertar orden
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ordenes
               (numero_orden, cliente_email, cliente_nombre, subtotal, impuesto, total, estado)
               VALUES (?,?,?,?,?,?,'CONFIRMADA')""",
            (numero_orden, cliente_email, cliente_nombre, subtotal, impuesto, total)
        )
        orden_id = cur.lastrowid

        # Insertar detalle y actualizar stock
        for it in items:
            cur.execute(
                """INSERT INTO detalle_orden
                   (orden_id, producto_id, nombre_prod, cantidad, precio_unit, subtotal)
                   VALUES (?,?,?,?,?,?)""",
                (orden_id, it["producto_id"], it["nombre"],
                 it["cantidad"], it["precio_unit"], it["subtotal"])
            )
            cur.execute(
                "UPDATE productos SET stock = stock - ? WHERE id=?",
                (it["cantidad"], it["producto_id"])
            )

        conn.commit()
        return {
            "ok": True,
            "numero_orden":   numero_orden,
            "orden_id":       orden_id,
            "items":          items,
            "subtotal":       subtotal,
            "impuesto":       impuesto,
            "total":          total,
            "cliente_nombre": cliente_nombre,
            "cliente_email":  cliente_email,
            "fecha":          datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        conn.rollback()
        return {"ok": False, "mensaje": str(e)}
    finally:
        conn.close()
