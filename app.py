import streamlit as st
import pandas as pd
import math

# Configuración de la página
st.set_page_config(
    page_title="ReorderPro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fa;
        color: #333333;
    }
    .css-1lcbmhc.e1fqkh3o3 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título y descripción
st.title("🚀 ReorderPro: Calculadora de Punto de Reorden")
st.write(
    "Esta aplicación determina cuándo y cuánto pedir de cada SKU según su inventario, demanda histórica y lead time, usando pallet sizes variables por SKU."
)

# Ejemplo visual del CSV
st.subheader("📊 Ejemplo de archivo CSV a subir")
example_df = pd.DataFrame({
    'SKU or Item Code': ['4387', '4417'],
    'Inventario hoy': [892, 1174],
    'Ventas (en cajas)': [2189, 1810],
    'Periodo de las ventas (en días)': [210, 210],
    'Lead Time(días)': [60, 60],
    'Safety Stock': [1.3, 1.3],
    'Tamaño Paleta': [225, 150]  # cajas por pallet distintas
})
st.table(example_df)

st.write(
    "**Columnas del CSV:**\n"
    "- SKU or Item Code: Código o identificador del artículo.\n"
    "- Inventario hoy: Stock actual en cajas.\n"
    "- Ventas (en cajas): Total de ventas en el periodo.\n"
    "- Periodo de las ventas (en días): Duración del histórico.\n"
    "- Lead Time(días): Tiempo de reposición en días.\n"
    "- Safety Stock: Coeficiente >1 para margen de seguridad.\n"
    "- Tamaño Paleta: Cajas por pallet para cada SKU, para sugerir orden múltiplo de éste."
)

st.markdown("---")

# Botón destacado para descargar plantilla de Excel antes de comenzar
st.markdown("### 📥 **Descarga aquí tu plantilla de Excel antes de cargar datos**")
with open('template.xlsx', 'rb') as f:
    data = f.read()
st.download_button(
    label='Descargar plantilla de Excel (template.xlsx)',
    data=data,
    file_name='plantilla_reorder.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Paso 1: subir archivo
st.header("1️⃣ Sube tu archivo CSV")
uploaded_file = st.file_uploader("Selecciona tu CSV", type="csv")
