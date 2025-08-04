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

# Título
st.title("🚀 ReorderPro: Calculadora de Punto de Reorden")

# Descripción breve
st.markdown(
    "Esta aplicación te ayuda a determinar cuándo y cuánto pedir de cada SKU según tu inventario actual, histórico de ventas y tiempos de reposición."
)

# Ejemplo visual del Excel
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

st.markdown(
    "Cada columna debe contener lo siguiente:"
)
st.markdown(
    "- **Producto**: Código o SKU.
    \n- **Inventario_actual_cajas**: Unidades en stock (en cajas).
    \n- **Ventas_totales_ultimos_meses**: Suma de ventas en el periodo analizado (cajas).
    \n- **Periodo_dias**: Días totales del histórico (ej. 210 para enero-julio).
    \n- **Lead_time_dias**: Tiempo que tarda un pedido en llegar.
    \n- **Factor_seguridad**: Coeficiente (>1) para cubrir variabilidad (ej. 1.3 para +30%).
    \n- **Minimo_paletas**: Número mínimo de paletas a ordenar (1 paleta = 225 cajas)."
)

st.markdown("---")

# Sidebar configuración
with st.sidebar:
    st.header("⚙️ Parámetros")
    min_paletas = st.number_input(
        "Mínimo de paletas global:",
        min_value=1,
        value=10,
        help="Número mínimo total de paletas a asignar entre los SKUs."
    )
    st.markdown(
        "La asignación final se distribuirá según el mix de ventas y urgencia de reposición."
    )

st.header("1️⃣ Sube tu archivo CSV")
uploaded_file = st.file_uploader("Selecciona aquí tu archivo CSV", type="csv")

if uploaded_file:
    # Lectura y validación
    df = pd.read_csv(uploaded_file)
    numeric_cols = [
        'Inventario_actual_cajas', 'Ventas_totales_ultimos_meses',
        'Periodo_dias', 'Lead_time_dias', 'Factor_seguridad'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Minimo_paletas' in df.columns:
        min_paletas = int(df['Minimo_paletas'].iloc[0])

    st.success("✔️ Datos cargados correctamente")
    st.dataframe(df, height=200)

    if st.button("2️⃣ Calcular Reorden"):
        # Cálculos principales
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
        df['paletas'] = (
            df['peso'] / total_peso * min_paletas
        ).round().astype(int)
        diff = min_paletas - df['paletas'].sum()
        if diff != 0:
            idx = df['peso'].idxmax()
            df.at[idx, 'paletas'] += diff

        df['cajasOrdenar'] = df['paletas'] * 225

        # Mostrar resultados
        st.subheader("📈 Resultados de Reorden")
        st.dataframe(df, height=300)

        # Explicación breve
        st.markdown("---")
        st.markdown(
            "**Explicación del cálculo:**
            \n- *ventasDiarias*: Ventas totales / periodo.
            \n- *puntoReposicion*: ventasDiarias × lead_time × factor_seguridad.
            \n- *reordenar*: True si stock ≤ punto de reposición.
            \n- *urgencia*: 1.3 para SKUs que quedan sin stock antes del lead_time, 1.0 para el resto.
            \n- *peso*: ventasDiarias × urgencia, usado para distribuir el mínimo de paletas.
            \n- *paletas*: (peso / suma de pesos) × mínimo global, ajustado a enteros.
            \n- *cajasOrdenar*: paletas × 225."
        )

        # Descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='📥 Descargar CSV Sugerido',
            data=csv,
            file_name='reorder_sugerido.csv',
            mime='text/csv'
        )
```
