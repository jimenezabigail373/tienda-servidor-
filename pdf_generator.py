"""
=============================================================
  PDF_GENERATOR.PY  -  Genera proformas en PDF con FPDF2
=============================================================
"""

from fpdf import FPDF
from datetime import datetime


class ProformaPDF(FPDF):
    """PDF con cabecera y pie de pagina personalizados."""

    def header(self):
        # Barra superior
        self.set_fill_color(30, 90, 150)
        self.rect(0, 0, 210, 28, "F")

        self.set_y(7)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "TIENDA ONLINE", align="C", ln=True)

        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "www.tiendaonline.com  |  ventas@tiendaonline.com", align="C", ln=True)
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, "Este documento es una proforma. Gracias por su compra.", align="C", ln=True)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")


def generar_proforma_pdf(orden: dict) -> bytes:
    """
    Genera un PDF con los datos de la orden y retorna los bytes.
    orden = {
        numero_orden, cliente_nombre, cliente_email, fecha,
        items: [{nombre, cantidad, precio_unit, subtotal}, ...],
        subtotal, impuesto, total
    }
    """
    pdf = ProformaPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Titulo del documento ───────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(30, 90, 150)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 10, "PROFORMA DE COMPRA", border="B", align="C", ln=True, fill=True)
    pdf.ln(4)

    # ── Info de la orden y del cliente ────────────────────
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    col_w = 95
    # Columna izquierda
    y_ini = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w, 7, "DATOS DEL CLIENTE", ln=False)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w, 7, "DATOS DE LA ORDEN", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w, 6, f"Nombre:  {orden['cliente_nombre']}", ln=False)
    pdf.cell(col_w, 6, f"No. Orden:  {orden['numero_orden']}", ln=True)
    pdf.cell(col_w, 6, f"Correo:  {orden['cliente_email']}", ln=False)
    pdf.cell(col_w, 6, f"Fecha:      {orden['fecha']}", ln=True)
    pdf.cell(col_w, 6, "", ln=False)
    pdf.cell(col_w, 6, "Estado:     CONFIRMADA", ln=True)
    pdf.ln(6)

    # ── Tabla de productos ─────────────────────────────────
    # Cabecera tabla
    pdf.set_fill_color(30, 90, 150)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(80, 9, "Producto",     border=1, fill=True)
    pdf.cell(25, 9, "Cant.",        border=1, fill=True, align="C")
    pdf.cell(40, 9, "Precio Unit.", border=1, fill=True, align="R")
    pdf.cell(40, 9, "Subtotal",     border=1, fill=True, align="R", ln=True)

    # Filas alternadas
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    colores = [(255, 255, 255), (235, 242, 255)]

    for i, item in enumerate(orden["items"]):
        pdf.set_fill_color(*colores[i % 2])
        pdf.cell(80, 8, item["nombre"][:38], border=1, fill=True)
        pdf.cell(25, 8, str(item["cantidad"]), border=1, fill=True, align="C")
        pdf.cell(40, 8, f"$ {item['precio_unit']:.2f}", border=1, fill=True, align="R")
        pdf.cell(40, 8, f"$ {item['subtotal']:.2f}",   border=1, fill=True, align="R", ln=True)

    pdf.ln(4)

    # ── Totales ────────────────────────────────────────────
    x_tot = 110
    pdf.set_x(x_tot)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(55, 7, "Subtotal:", align="R")
    pdf.cell(35, 7, f"$ {orden['subtotal']:.2f}", align="R", ln=True)

    pdf.set_x(x_tot)
    pdf.cell(55, 7, "IVA (12%):", align="R")
    pdf.cell(35, 7, f"$ {orden['impuesto']:.2f}", align="R", ln=True)

    # Linea separadora
    y_sep = pdf.get_y()
    pdf.set_draw_color(30, 90, 150)
    pdf.line(x_tot, y_sep, 200, y_sep)
    pdf.ln(1)

    # Total
    pdf.set_x(x_tot)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(30, 90, 150)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(55, 9, "TOTAL:", fill=True, align="R")
    pdf.cell(35, 9, f"$ {orden['total']:.2f}", fill=True, align="R", ln=True)

    pdf.ln(10)

    # ── Nota de agradecimiento ─────────────────────────────
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0, 6,
        "Estimado/a cliente: gracias por su compra. Esta proforma tiene validez de 48 horas. "
        "Para consultas comuniquese con ventas@tiendaonline.com.",
        align="C"
    )

    return bytes(pdf.output())
