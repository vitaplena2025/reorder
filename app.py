```python
# app.py
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="ReorderPro", layout="wide")

st.title('ReorderPro 🚀')

with st.sidebar:
    st.header("Configuración")
    min_paletas = st.number_input(
        "Mínimo de paletas:", min_value=1, value=10, step=1
    )
    st.markdown("---")
    st.markdown("### Ejemplo de CSV esperado:")
    st.code(
        "Producto,Inventario_actual_cajas,Ventas_totales_ultimos_meses,Periodo_dias,Lead_time_dias,Factor_seguridad,Minimo_paletas\n"
        "4387,892,2189,210,60,1.3,10\n"
        "4417,1174,1810,210,60,1.3,10",
        language='csv'
    )

st.header('Sube tu archivo CSV')
uploaded_file = st.file_uploader("Selecciona un CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    # Convertir columnas numéricas
    for col in ['Inventario_actual_cajas','Ventas_totales_ultimos_meses','Periodo_dias','Lead_time_dias','Factor_seguridad']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Usar minimo paletas del CSV si existe
    if 'Minimo_paletas' in df.columns:
        min_paletas = int(df['Minimo_paletas'].iloc[0])

    st.success('Datos cargados correctamente')
    st.dataframe(df.head())

    if st.button('Calcular Reorden'):
        # Cálculos
        df['ventasDiarias'] = df['Ventas_totales_ultimos_meses'] / df['Periodo_dias']
        df['puntoReposicion'] = (df['ventasDiarias'] * df['Lead_time_dias'] * df['Factor_seguridad']).round(0)
        df['reordenar'] = df['Inventario_actual_cajas'] <= df['puntoReposicion']

        # Peso y urgencia
        df['diasHasta'] = (df['Inventario_actual_cajas'] - df['puntoReposicion']) / df['ventasDiarias']
        df['urgencia'] = df.apply(lambda r: 1.3 if r['diasHasta'] <= r['Lead_time_dias'] else 1.0, axis=1)
        df['peso'] = df['ventasDiarias'] * df['urgencia']

        total_peso = df['peso'].sum()
        df['paletas'] = (df['peso'] / total_peso * min_paletas).round().astype(int)
        diff = min_paletas - df['paletas'].sum()
        if diff != 0:
            idx = df['peso'].idxmax()
            df.at[idx, 'paletas'] += diff

        df['cajasOrdenar'] = df['paletas'] * 225

        # Mostrar resultados
        st.subheader('Resultados de Reorden')
        st.dataframe(df)

        # Botón para descargar
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label='📥 Descargar CSV',
            data=csv,
            file_name='reorder_sugerido.csv',
            mime='text/csv'
        )
```
