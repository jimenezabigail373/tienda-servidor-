"""
=============================================================
  HANDLERS.PY  -  Logica de negocio por accion
=============================================================
  Acciones disponibles:
    REGISTER   - Registrar nuevo cliente
    LOGIN      - Autenticar cliente
    GET_CATALOG - Obtener lista de productos
    PURCHASE   - Realizar compra y generar proforma
=============================================================
"""

import threading
import logging
from database import (
    registrar_cliente,
    autenticar_cliente,
    obtener_catalogo,
    crear_orden
)
from pdf_generator import generar_proforma_pdf
from email_service import enviar_proforma_correo

log = logging.getLogger(__name__)


def manejar_peticion(peticion: dict) -> dict:
    """Enruta la peticion al handler correspondiente."""
    accion = peticion.get("action", "").upper()

    handlers = {
        "REGISTER":    _handler_register,
        "LOGIN":       _handler_login,
        "GET_CATALOG": _handler_catalogo,
        "PURCHASE":    _handler_compra,
    }

    handler = handlers.get(accion)
    if handler:
        return handler(peticion)

    return {"status": "ERROR", "mensaje": f"Accion desconocida: '{accion}'"}


# ── Handlers individuales ──────────────────────────────────

def _handler_register(p):
    resultado = registrar_cliente(
        nombre   = p.get("nombre", ""),
        email    = p.get("email", ""),
        password = p.get("password", ""),
        telefono = p.get("telefono", "")
    )
    status = "OK" if resultado["ok"] else "ERROR"
    return {"status": status, "mensaje": resultado["mensaje"]}


def _handler_login(p):
    resultado = autenticar_cliente(
        email    = p.get("email", ""),
        password = p.get("password", "")
    )
    if resultado["ok"]:
        return {"status": "OK", "cliente": resultado["cliente"]}
    return {"status": "ERROR", "mensaje": resultado["mensaje"]}


def _handler_catalogo(_p):
    productos = obtener_catalogo()
    return {"status": "OK", "productos": productos}


def _handler_compra(p):
    carrito        = p.get("carrito", [])
    cliente_email  = p.get("email", "")
    cliente_nombre = p.get("nombre", "")

    if not carrito:
        return {"status": "ERROR", "mensaje": "El carrito esta vacio"}
    if not cliente_email:
        return {"status": "ERROR", "mensaje": "Email del cliente requerido"}

    # Crear orden en la base de datos
    orden = crear_orden(cliente_email, cliente_nombre, carrito)
    if not orden["ok"]:
        return {"status": "ERROR", "mensaje": orden["mensaje"]}

    # Generar PDF de la proforma
    try:
        pdf_bytes = generar_proforma_pdf(orden)
        pdf_b64   = _bytes_a_base64(pdf_bytes)
    except Exception as e:
        log.error(f"Error generando PDF: {e}")
        pdf_b64 = None

    # Enviar correo en segundo plano (no bloquea la respuesta al cliente)
    if pdf_bytes and cliente_email:
        threading.Thread(
            target=_enviar_correo_seguro,
            args=(cliente_email, cliente_nombre, orden["numero_orden"], pdf_bytes),
            daemon=True
        ).start()

    return {
        "status":       "OK",
        "numero_orden": orden["numero_orden"],
        "subtotal":     orden["subtotal"],
        "impuesto":     orden["impuesto"],
        "total":        orden["total"],
        "items":        orden["items"],
        "fecha":        orden["fecha"],
        "pdf_base64":   pdf_b64,
        "mensaje":      f"Compra exitosa. Se enviara la proforma a {cliente_email}"
    }


def _enviar_correo_seguro(email, nombre, numero_orden, pdf_bytes):
    try:
        enviar_proforma_correo(email, nombre, numero_orden, pdf_bytes)
        log.info(f"Correo enviado a {email} para orden {numero_orden}")
    except Exception as e:
        log.error(f"Error enviando correo a {email}: {e}")


def _bytes_a_base64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("utf-8")
