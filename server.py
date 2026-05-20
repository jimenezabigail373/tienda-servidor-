"""
=============================================================
  SERVIDOR DE SOCKETS - TIENDA ONLINE
  Protocolo: TCP  |  Puerto: 9000
  Comunicacion: JSON
=============================================================
"""

import socket
import threading
import json
import logging
from datetime import datetime
from handlers import manejar_peticion
from database import inicializar_base_de_datos

# ── Configuracion ──────────────────────────────────────────
HOST = "0.0.0.0"   # Escucha en todas las interfaces de red
PORT = 9000
MAX_CONEXIONES = 10
BUFFER_SIZE = 65536  # 64 KB por mensaje

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("servidor.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def manejar_cliente(conn, addr):
    """Hilo dedicado a cada cliente conectado."""
    log.info(f"Cliente conectado: {addr[0]}:{addr[1]}")
    try:
        while True:
            datos = conn.recv(BUFFER_SIZE)
            if not datos:
                break  # Cliente desconectado

            try:
                peticion = json.loads(datos.decode("utf-8"))
                log.info(f"[{addr[0]}] Accion: {peticion.get('action', 'desconocida')}")
                respuesta = manejar_peticion(peticion)
            except json.JSONDecodeError:
                respuesta = {"status": "ERROR", "mensaje": "JSON invalido"}
            except Exception as e:
                log.error(f"Error procesando peticion de {addr}: {e}")
                respuesta = {"status": "ERROR", "mensaje": str(e)}

            conn.sendall(json.dumps(respuesta).encode("utf-8"))

    except ConnectionResetError:
        log.info(f"Cliente {addr} cerro la conexion abruptamente")
    finally:
        conn.close()
        log.info(f"Conexion cerrada: {addr[0]}:{addr[1]}")


def iniciar_servidor():
    """Arranca el servidor TCP y acepta conexiones."""
    inicializar_base_de_datos()
    log.info("Base de datos lista.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(MAX_CONEXIONES)
        log.info(f"Servidor escuchando en {HOST}:{PORT}")
        print(f"\n{'='*50}")
        print(f"  TIENDA ONLINE - SERVIDOR ACTIVO")
        print(f"  Puerto: {PORT}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        while True:
            conn, addr = srv.accept()
            hilo = threading.Thread(
                target=manejar_cliente,
                args=(conn, addr),
                daemon=True
            )
            hilo.start()
            log.info(f"Hilos activos: {threading.active_count() - 1}")


if __name__ == "__main__":
    iniciar_servidor()
