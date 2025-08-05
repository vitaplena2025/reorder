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

st.title("🚀 ReorderPro: Calculadora de Punto de Reorden")
st.write("Calcula cuándo pedir de cada SKU, mostrando tu tabla original más las columnas de análisis al final.")

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
st.markdown("---")

st.markdown("### 📥 Descarga tu plantilla de Excel antes de cargar datos")
with open('template.xlsx', 'rb') as f:
    st.download_button(
        label='Descargar plantilla (template.xlsx)',
        data=f.read(),
        file_name='plantilla_reorder.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

st.header("1️⃣ Sube tu archivo CSV o Excel")
uploaded = st.file_uploader("Selecciona tu archivo", type=['csv','xls','xlsx'])

if uploaded:
    # Leemos y guardamos copia original
    if uploaded.name.lower().endswith(('xls','xlsx')):
        raw = pd.read_excel(uploaded)
    else:
        raw = pd.read_csv(uploaded)
    df = raw.copy()

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
    missing = [c for c in expected if c not in df.columns]
    if missing:
        st.error(f"❌ Faltan columnas: {missing}")
        st.stop()
    df = df.rename(columns=expected)

    # Convertir numéricas
    for col in ['Inventario_cajas','Ventas_cajas','Periodo_dias','Lead_time','Safety_days','Pallet_size']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    st.success("Datos cargados, procede a calcular.")

    if st.button("2️⃣ Calcular Sugerencia de Orden"):
        # Cálculos
        df['ventasDiarias'] = (df['Ventas_cajas']/df['Periodo_dias']).round(2)
        df['puntoReposicion'] = (df['ventasDiarias']*(df['Lead_time']+df['Safety_days'])).round(2)
        df['reordenar'] = df['Inventario_cajas'] <= df['puntoReposicion']
        df['reordenar'] = df['reordenar'].map({True:'Ordenar', False:'No ordenar'})
        def calc_date(r):
            if r['ventasDiarias']>0:
                dias = (r['Inventario_cajas']-r['puntoReposicion'])/r['ventasDiarias']
                dias = math.floor(dias) if dias>0 else 0
                return (date.today()+timedelta(days=dias)).strftime('%d/%m/%Y')
            return date.today().strftime('%d/%m/%Y')
        df['Fecha_para_orden'] = df.apply(calc_date, axis=1)

        # Unir análisis al final de la tabla original
        analysis_cols = ['ventasDiarias','puntoReposicion','reordenar','Fecha_para_orden']
        # renombrar para claridad
        df_display = raw.copy()
        df_display['Ventas Diarias'] = df['ventasDiarias']
        df_display['Punto de Reposición'] = df['puntoReposicion']
        df_display['¿Reordenar?'] = df['reordenar']
        df_display['Fecha de Orden'] = df['Fecha_para_orden']

        st.subheader("📈 Tu tabla original con análisis agregado")
        st.table(df_display)

        # Descarga de archivo completo
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='📥 Descargar tu archivo con análisis',
            data=csv,
            file_name='datos_con_analisis.csv',
            mime='text/csv'
        )
