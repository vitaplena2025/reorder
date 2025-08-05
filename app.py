import streamlit as st
import pandas as pd
import math
from datetime import date, timedelta

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
    .stApp { background: #f5f7fa; color: #333333; }
    .css-1lcbmh3o3 { background-color: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """,
    unsafe_allow_html=True
)

# Título y descripción
st.title("🚀 ReorderPro: Calculadora de Punto de Reorden")
st.write("Calcula cuándo pedir de cada SKU considerando inventario, demanda histórica, lead time y días de safety stock.")

# Ejemplo de archivo a subir
st.subheader("📊 Ejemplo de archivo a subir (CSV o Excel)")
example_df = pd.DataFrame({
    'SKU or Item Code': ['4387', '4417'],
    'Inventario hoy': [892, 1174],
    'Ventas (en cajas)': [2189, 1810],
    'Periodo de las ventas (en días)': [210, 210],
    'Lead Time (días)': [60, 60],
    'Días de Safety Stock': [15, 15],
    'Tamaño Paleta': [225, 225]
})
st.table(example_df)
st.write(
    "**Columnas necesarias:**\n"
    "- SKU or Item Code: Código del producto.\n"
    "- Inventario hoy: Stock actual en cajas.\n"
    "- Ventas (en cajas): Total de ventas en el periodo.\n"
    "- Periodo de las ventas (en días): Días del histórico de ventas.\n"
    "- Lead Time (días): Plazo de entrega medio.\n"
    "- Días de Safety Stock: Días de inventario adicional como buffer.\n"
    "- Tamaño Paleta: Cajas por pallet para redondeo."
)

st.markdown("---")

# Descarga de plantilla
st.markdown("### 📥 Descarga tu plantilla de Excel antes de cargar datos")
with open('template.xlsx', 'rb') as f:
    template_bytes = f.read()
st.download_button(
    label='Descargar plantilla (template.xlsx)',
    data=template_bytes,
    file_name='plantilla_reorder.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Paso 1: subir archivo
st.header("1️⃣ Sube tu archivo CSV o Excel")
uploaded = st.file_uploader("Selecciona tu archivo", type=['csv','xls','xlsx'])

if uploaded:
    # Leer según extensión
    if uploaded.name.lower().endswith(('xls','xlsx')):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    # Mapeo interno de columnas
    expected = {
        'SKU or Item Code': 'SKU',
        'Inventario hoy': 'Inventario_cajas',
        'Ventas (en cajas)': 'Ventas_cajas',
        'Periodo de las ventas (en días)': 'Periodo_dias',
        'Lead Time (días)': 'Lead_time',
        'Días de Safety Stock': 'Safety_days',
        'Tamaño Paleta': 'Pallet_size'
    }
    missing = [col for col in expected if col not in df.columns]
    if missing:
        st.error(f"❌ Faltan estas columnas en tu archivo: {missing}")
        st.stop()
    df = df.rename(columns=expected)

    # Asegurar columnas numéricas
    for col in ['Inventario_cajas', 'Ventas_cajas', 'Periodo_dias', 'Lead_time', 'Safety_days', 'Pallet_size']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Paso 2: calcular punto de reposición y fecha de orden
    if st.button("2️⃣ Calcular Sugerencia de Orden"):
        df['ventasDiarias'] = (df['Ventas_cajas'] / df['Periodo_dias']).round(2)
        df['puntoReposicion'] = (df['ventasDiarias'] * (df['Lead_time'] + df['Safety_days'])).round(2)
        df['reordenar'] = df['Inventario_cajas'] <= df['puntoReposicion']
        df['reordenar'] = df['reordenar'].map({True: 'Ordenar', False: 'No ordenar'})
        def calc_order_date(row):
            if row['ventasDiarias'] > 0:
                days_until = (row['Inventario_cajas'] - row['puntoReposicion']) / row['ventasDiarias']
                days_until = math.floor(days_until) if days_until > 0 else 0
                return (date.today() + timedelta(days=days_until)).strftime('%d/%m/%Y')
            return date.today().strftime('%d/%m/%Y')
        df['Fecha_para_orden'] = df.apply(calc_order_date, axis=1)

        # Mostrar resultados en tabla estilizada
        st.subheader("📈 Resultados de Sugerencia de Orden")
        result = df[['SKU', 'ventasDiarias', 'puntoReposicion', 'reordenar', 'Fecha_para_orden']].copy()
        result.columns = ['SKU', 'Ventas Diarias 🌟', 'Punto de Reposición 📦', '¿Reordenar?', 'Fecha de Orden 🗓']
        st.table(result)

        st.markdown("---")
        st.write(
            "**Cómo se calcula:**  \n"
            "1) ventasDiarias = Ventas_cajas / Periodo_dias (2 decimales).  \n"
            "2) puntoReposicion = ventasDiarias × (Lead_time + Safety_days) (2 decimales).  \n"
            "3) reordenar = Inventario_cajas ≤ puntoReposicion.  \n"
            "4) Fecha_para_orden = hoy + floor((Inventario_cajas - puntoReposicion)/ventasDiarias) días."
        )

        # Descargar todo el df original con columnas nuevas
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='📥 Descargar archivo con análisis',
            data=csv,
            file_name='datos_con_analisis.csv',
            mime='text/csv'
        )
