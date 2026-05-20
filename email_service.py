"""
=============================================================
  EMAIL_SERVICE.PY  -  Envio de correo con Gmail + smtplib
=============================================================
  CONFIGURACION:
    1. Activa verificacion en 2 pasos en tu cuenta Gmail
    2. Ve a: Cuenta Google > Seguridad > Contrasenas de aplicacion
    3. Crea una contrasena para "Correo" en "Otro dispositivo"
    4. Pega esa contrasena de 16 caracteres en EMAIL_PASSWORD
=============================================================
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

log = logging.getLogger(__name__)

# ── CONFIGURA ESTOS DATOS ──────────────────────────────────
import os
EMAIL_REMITENTE = os.environ.get("EMAIL_REMITENTE", "morenoabi250401@gmail.com")
EMAIL_PASSWORD  = os.environ.get("EMAIL_PASSWORD", "tkrr kmwj psrq ywve")   # <-- Contrasena de aplicacion
EMAIL_NOMBRE    = "Tienda Online"
SMTP_HOST       = "smtp.gmail.com"
SMTP_PORT       = 587


def enviar_proforma_correo(
    destinatario: str,
    nombre_cliente: str,
    numero_orden: str,
    pdf_bytes: bytes
):
    """Envia un correo con la proforma PDF adjunta."""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Proforma de compra - {numero_orden}"
    msg["From"]    = f"{EMAIL_NOMBRE} <{EMAIL_REMITENTE}>"
    msg["To"]      = destinatario

    # ── Cuerpo HTML del correo ─────────────────────────────
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f6f9; margin:0; padding:20px;">
      <div style="max-width:600px; margin:auto; background:#fff;
                  border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.1);">

        <!-- Cabecera -->
        <div style="background:#1e5a96; padding:28px; text-align:center;">
          <h1 style="color:#fff; margin:0; font-size:24px;">TIENDA ONLINE</h1>
          <p style="color:#aac8ef; margin:6px 0 0;">Confirmacion de compra</p>
        </div>

        <!-- Cuerpo -->
        <div style="padding:32px;">
          <h2 style="color:#1e5a96; margin-top:0;">Hola, {nombre_cliente}!</h2>
          <p style="color:#444; line-height:1.6;">
            Tu compra ha sido procesada exitosamente.
            Encontraras la proforma detallada en el archivo adjunto a este correo.
          </p>

          <div style="background:#f0f5ff; border-left:4px solid #1e5a96;
                      border-radius:6px; padding:16px; margin:20px 0;">
            <p style="margin:0; color:#333;">
              <strong>Numero de orden:</strong> {numero_orden}<br>
              <strong>Fecha:</strong> {fecha}
            </p>
          </div>

          <p style="color:#444; line-height:1.6;">
            Si tienes alguna pregunta, respondenos a este correo o escribe a
            <a href="mailto:ventas@tiendaonline.com" style="color:#1e5a96;">
              ventas@tiendaonline.com
            </a>.
          </p>

          <p style="color:#444;">Gracias por tu compra!</p>
          <p style="color:#444;">— El equipo de Tienda Online</p>
        </div>

        <!-- Pie -->
        <div style="background:#f0f0f0; padding:16px; text-align:center;">
          <p style="color:#999; font-size:12px; margin:0;">
            Este correo fue generado automaticamente. Por favor no respondas directamente.
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    # ── Adjuntar PDF ───────────────────────────────────────
    adjunto = MIMEBase("application", "octet-stream")
    adjunto.set_payload(pdf_bytes)
    encoders.encode_base64(adjunto)
    adjunto.add_header(
        "Content-Disposition",
        f"attachment; filename=\"Proforma_{numero_orden}.pdf\""
    )
    msg.attach(adjunto)

    # ── Enviar via SMTP ────────────────────────────────────
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_REMITENTE, destinatario, msg.as_string())

    log.info(f"Proforma enviada a {destinatario}")
