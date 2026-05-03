import streamlit as st
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# --- Configuración de la Página ---
st.set_page_config(page_title="TramiTRUJILLO - Sistema de Ventas", page_icon="📄")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if 'productos' not in st.session_state:
    st.session_state.productos = []

# --- Funciones de Apoyo ---
def total_a_letras(total):
    enteros = int(total)
    centimos = int(round((total - enteros) * 100))
    return f"SON: {enteros} CON {centimos:02d}/100 SOLES"

def crear_pdf(n_nota, caja, vendedor, cliente, metodo, productos):
    pdf = FPDF('P', 'mm', (105, 220)) 
    pdf.add_page()
    pdf.set_margins(7, 7, 7)
    
    # ENCABEZADO
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 7, "TramiTRUJILLO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "SIMPLIFICANDO TUS GESTIONES TRIBUTARIAS", ln=True, align="C")
    pdf.cell(0, 4, "Psj. Pasaje San Agustín N° 110 - Trujillo", ln=True, align="C")
    pdf.cell(0, 4, "acarlosa@unitru.edu.pe", ln=True, align="C")
    pdf.cell(0, 4, "Cel: 935534706", ln=True, align="C")
    pdf.ln(4)
    
    # INFO NOTA
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"NOTA DE VENTA N°: {n_nota}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Caja: {caja}", ln=True)
    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True)
    pdf.cell(0, 5, f"Vendedor: {vendedor}", ln=True)
    pdf.cell(0, 5, f"Cliente: {cliente if cliente else 'Clientes Varios'}", ln=True)
    pdf.ln(2)
    
    # TABLA
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(45, 6, "Descripción", border="TB")
    pdf.cell(12, 6, "Cant.", border="TB", align="C")
    pdf.cell(15, 6, "P.Unit", border="TB", align="R")
    pdf.cell(18, 6, "Total", border="TB", align="R")
    pdf.ln(7)
    
    pdf.set_font("Helvetica", "", 8)
    total_acumulado = 0
    for p in productos:
        pdf.cell(45, 5, p['desc'])
        pdf.cell(12, 5, str(p['cant']), align="C")
        pdf.cell(15, 5, f"{p['precio']:.2f}", align="R")
        pdf.cell(18, 5, f"{p['subtotal']:.2f}", align="R")
        pdf.ln()
        total_acumulado += p['subtotal']
    
    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(7, pdf.get_y(), 98, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(72, 6, "Total:", align="R")
    pdf.cell(18, 6, f"{total_acumulado:.2f}", align="R", ln=True)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 5, total_a_letras(total_acumulado), ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Método de pago: {metodo}", ln=True)
    pdf.ln(4)
    
    # PIE CON WHATSAPP FUNCIONAL
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "¡Gracias por su preferencia!", ln=True, align="C")
    pdf.set_text_color(0, 0, 255)
    pdf.set_font("Helvetica", "U", 8)
    wa_url = "https://wa.me/51935534706"
    pdf.cell(0, 4, "Presiona aquí para WhatsApp", ln=True, align="C", link=wa_url)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 3, "Documento no válido como comprobante de pago ante SUNAT. Uso Informativo", align="C")
    
    return bytes(pdf.output())

# --- Interfaz Principal ---
st.title("📄 Generador TramiTRUJILLO")

with st.form("datos_venta"):
    col1, col2 = st.columns(2)
    with col1:
        n_nota = st.text_input("Nota de Venta N°", value="NV-000052")
        vendedor = st.text_input("Vendedor", value="Carlos Daniel")
    with col2:
        cliente = st.text_input("Cliente", value="Clientes Varios")
        metodo = st.selectbox("Método de Pago", ["Yape", "Efectivo", "Plin", "Transferencia"])
    
    submit_button = st.form_submit_button("Generar PDF y Registrar Venta")

st.subheader("Añadir Productos")
c1, c2, c3 = st.columns([3, 1, 1])
p_desc = c1.text_input("Descripción")
p_cant = c2.number_input("Cant", min_value=1.0, value=1.0)
p_prec = c3.number_input("P.Unit", min_value=0.0, value=0.0)

if st.button("Añadir a la lista ➕"):
    if p_desc:
        st.session_state.productos.append({
            "desc": p_desc, "cant": p_cant, "precio": p_prec, "subtotal": p_cant * p_prec
        })
        st.rerun()

if st.session_state.productos:
    st.table(st.session_state.productos)
    if st.button("Limpiar Productos 🗑️"):
        st.session_state.productos = []
        st.rerun()

# --- Lógica de Salida ---
if submit_button:
    if not st.session_state.productos:
        st.error("No hay productos en la nota.")
    else:
        total_f = sum(p['subtotal'] for p in st.session_state.productos)
        
        # 1. Registrar en Google Sheets (Orden idéntico a tu Excel)
        try:
            nueva_venta = pd.DataFrame([{
                "Nota": n_nota,
                "Fecha": datetime.now().strftime('%d-%m-%Y %H:%M'),
                "Metodo": metodo,
                "Cliente": cliente,
                "Vendedor": vendedor,
                "Total": total_f
            }])
            
            data_actual = conn.read()
            updated_df = pd.concat([data_actual, nueva_venta], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ Venta registrada en Google Sheets.")
        except Exception as e:
            st.error(f"Error al conectar con la nube: {e}")

        # 2. Generar PDF
        pdf_bytes = crear_pdf(n_nota, "1", vendedor, cliente, metodo, st.session_state.productos)
        st.download_button(
            label="⬇️ Descargar Nota en PDF",
            data=pdf_bytes,
            file_name=f"{n_nota}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
