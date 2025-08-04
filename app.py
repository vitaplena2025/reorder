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
st.write("Esta aplicación determina cuándo y cuánto pedir de cada SKU según inventario, ventas históricas y lead time.")

# Ejemplo visual del CSV
st.subheader("📊 Ejemplo de archivo CSV a subir")
example_df = pd.DataFrame({
    'Producto': ['4387', '4417'],
    'Inventario_actual_cajas': [892, 1174],
    'Ventas_totales_ultimos_meses': [2189, 1810],
    'Periodo_dias': [210, 210],
    'Lead_time_dias': [60, 60],
    'Factor_seguridad': [1.3, 1.3],
    'Minimo_paletas': [10, 10]
})
st.table(example_df)

st.write(
    "**Columnas del CSV:**\n"
    "- Producto: Código o SKU.\n"
    "- Inventario_actual_cajas: Stock actual en cajas.\n"
    "- Ventas_totales_ultimos_meses: Ventas en el periodo.\n"
    "- Periodo_dias: Días del histórico (ej. 210).\n"
    "- Lead_time_dias: Tiempo de reposición en días.\n"
    "- Factor_seguridad: Coeficiente >1 para buffer (ej. 1.3).\n"
    "- Minimo_paletas: Paletas mínimas totales (1 paleta=225 cajas)."
)

st.markdown("---")

# Sidebar de parámetros
with st.sidebar:
    st.header("⚙️ Parámetros")
    min_paletas = st.number_input(
        "Mínimo de paletas global:",
        min_value=1,
        value=10,
        help="Total mínimo de paletas a asignar."
    )
    st.write("La asignación se reparte según mix de ventas y urgencia.")

# Paso 1: subir archivo
st.header("1️⃣ Sube tu archivo CSV")
uploaded_file = st.file_uploader("Selecciona tu CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    # Validación de datos numéricos
    for col in [
        'Inventario_actual_cajas',
        'Ventas_totales_ultimos_meses',
        'Periodo_dias',
        'Lead_time_dias',
        'Factor_seguridad'
    ]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'Minimo_paletas' in df.columns:
        min_paletas = int(df['Minimo_paletas'].iloc[0])

    st.success("✔️ Datos cargados")
    st.dataframe(df, height=200)

    # Paso 2: calcular reorden
    if st.button("2️⃣ Calcular Reorden"):
        df['ventasDiarias'] = df['Ventas_totales_ultimos_meses'] / df['Periodo_dias']
        df['puntoReposicion'] = (
            df['ventasDiarias'] *
            df['Lead_time_dias'] *
            df['Factor_seguridad']
        ).round(0)
        df['reordenar'] = df['Inventario_actual_cajas'] <= df['puntoReposicion']

        # Urgencia y peso
        df['diasHasta'] = (
            df['Inventario_actual_cajas'] - df['puntoReposicion']
        ) / df['ventasDiarias']
        df['urgencia'] = df.apply(
            lambda r: 1.3 if r['diasHasta'] <= r['Lead_time_dias'] else 1.0,
            axis=1
        )
        df['peso'] = df['ventasDiarias'] * df['urgencia']

        # Asignación de paletas
        total_peso = df['peso'].sum()
        df['paletas'] = (df['peso'] / total_peso * min_paletas).round().astype(int)
        diff = min_paletas - df['paletas'].sum()
        if diff != 0:
            idx = df['peso'].idxmax()
            df.at[idx, 'paletas'] += diff

        df['cajasOrdenar'] = df['paletas'] * 225

        # Mostrar resultados
        st.subheader("📈 Resultados de Reorden")
        st.dataframe(df, height=300)

        # Explicación del cálculo
        st.markdown("---")
        st.write(
            "**Cómo se calcula:**\n"
            "1. ventasDiarias = Ventas_totales_ultimos_meses / Periodo_dias.\n"
            "2. puntoReposicion = ventasDiarias × Lead_time_dias × Factor_seguridad.\n"
            "3. reordenar = Inventario_actual_cajas ≤ puntoReposicion.\n"
            "4. urgencia = 1.3 si stock termina antes del Lead_time, sino 1.0.\n"
            "5. peso = ventasDiarias × urgencia.\n"
            "6. paletas = (peso / suma de pesos) × min_paletas (redondeo).\n"
            "7. cajasOrdenar = paletas × 225."
        )

        # Botón para descargar
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV Sugerido",
            data=csv,
            file_name="reorder_sugerido.csv",
            mime="text/csv"
        )
