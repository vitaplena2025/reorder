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
    'SKU or Item Code': ['4387', '4417'],
    'Inventario hoy': [892, 1174],
    'Ventas (en cajas)': [2189, 1810],
    'Periodo de las ventas (en días)': [210, 210],
    'Lead Time(días)': [60, 60],
    'Safety Stock': [1.3, 1.3],
    'Mínimo Paleta': [10, 10]
})
st.table(example_df)

st.markdown(
    """
**Columnas del CSV:**
- **SKU or Item Code**: Código o identificador del artículo.
- **Inventario hoy**: Stock actual en cajas.
- **Ventas (en cajas)**: Total de ventas en el periodo.
- **Periodo de las ventas (en días)**: Duración del histórico de ventas.
- **Lead Time(días)**: Tiempo de reposición en días.
- **Safety Stock**: Coeficiente >1 para margen de seguridad.
- **Mínimo Paleta**: Paletas mínimas totales (1 paleta = 225 cajas).
    """
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
    # Renombrar columnas a internos para cálculo
    rename_map = {
        'SKU or Item Code': 'Producto',
        'Inventario hoy': 'Inventario_actual_cajas',
        'Ventas (en cajas)': 'Ventas_totales_ultimos_meses',
        'Periodo de las ventas (en días)': 'Periodo_dias',
        'Lead Time(días)': 'Lead_time_dias',
        'Safety Stock': 'Factor_seguridad',
        'Mínimo Paleta': 'Minimo_paletas'
    }
    df.rename(columns=rename_map, inplace=True)
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
            df['ventasDiarias'] * df['Lead_time_dias'] * df['Factor_seguridad']
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
            "**Cómo se calcula:**  "
            "ventasDiarias = Ventas_totales_ultimos_meses / Periodo_dias.  "
            "puntoReposicion = ventasDiarias × Lead_time_dias × Factor_seguridad.  "
            "reordenar = Inventario_actual_cajas ≤ puntoReposicion.  "
            "urgencia = 1.3 si stock termina antes del Lead_time, sino 1.0.  "
            "peso = ventasDiarias × urgencia.  "
            "paletas = (peso / suma de pesos) × min_paletas (redondeo).  "
            "cajasOrdenar = paletas × 225."
        )

        # Botón para descargar
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV Sugerido",
            data=csv,
            file_name="reorder_sugerido.csv",
            mime="text/csv"
        )
