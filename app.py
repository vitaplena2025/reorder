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

# Paso 1: subir archivo
st.header("1️⃣ Sube tu archivo CSV")
uploaded_file = st.file_uploader("Selecciona tu CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    # Renombrar columnas internas
    rename_map = {
        'SKU or Item Code': 'Producto',
        'Inventario hoy': 'Inventario_actual_cajas',
        'Ventas (en cajas)': 'Ventas_totales_ultimos_meses',
        'Periodo de las ventas (en días)': 'Periodo_dias',
        'Lead Time(días)': 'Lead_time_dias',
        'Safety Stock': 'Factor_seguridad',
        'Tamaño Paleta': 'Pallet_size'
    }
    df.rename(columns=rename_map, inplace=True)
    # Validación de datos
    numeric_cols = ['Inventario_actual_cajas', 'Ventas_totales_ultimos_meses', 'Periodo_dias', 'Lead_time_dias', 'Factor_seguridad', 'Pallet_size']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    st.success("✔️ Datos cargados")
    st.dataframe(df, height=200)

    # Paso 2: calcular sugerencia de orden
    if st.button("2️⃣ Calcular Sugerencia de Orden"):
        # Cálculo de demanda diaria y punto de reposición
        df['ventasDiarias'] = df['Ventas_totales_ultimos_meses'] / df['Periodo_dias']
        df['puntoReposicion'] = (
            df['ventasDiarias'] * df['Lead_time_dias'] * df['Factor_seguridad']
        ).round(0)
        df['reordenar'] = df['Inventario_actual_cajas'] <= df['puntoReposicion']

        # Sugerencia de orden con pallets variables
        df['diferencia'] = df['puntoReposicion'] - df['Inventario_actual_cajas']
        df['diferencia'] = df['diferencia'].clip(lower=0)
        df['Orden_sugerida_cajas'] = df.apply(
            lambda r: math.ceil(r['diferencia']/r['Pallet_size']) * r['Pallet_size'] if r['Pallet_size'] > 0 else 0,
            axis=1
        )

        # Mostrar resultados
        st.subheader("📈 Resultados de Sugerencia")
        st.dataframe(
            df[['Producto','ventasDiarias','puntoReposicion','reordenar','Pallet_size','Orden_sugerida_cajas']],
            height=300
        )

        # Explicación breve
        st.markdown("---")
        st.write(
            "**Cómo se calcula:**\n"
            "1. ventasDiarias = Ventas_totales_ultimos_meses / Periodo_dias.\n"
            "2. puntoReposicion = ventasDiarias × Lead_time_dias × Factor_seguridad.\n"
            "3. reordenar = Inventario_actual_cajas ≤ puntoReposicion.\n"
            "4. diferencia = max(puntoReposicion - Inventario_actual_cajas, 0).\n"
            "5. Orden_sugerida_cajas = ceil(diferencia / Pallet_size) × Pallet_size."
        )

        # Botón para descargar resultados
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Resultados",
            data=csv,
            file_name="sugerencia_orden.csv",
            mime="text/csv"
        )
