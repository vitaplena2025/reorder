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
    .stApp { background: #f5f7fa; color: #333; }
    .css-1lcbmhc.e1fqkh3o3 { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True
)

# Título y descripción
st.title("🚀 ReorderPro: Calculadora de Punto de Reorden")
st.write("Determina cuándo y cuánto pedir de cada SKU según inventario, demanda histórica, lead time y días de safety stock.")

# Ejemplo de archivo\st.subheader("📊 Ejemplo de archivo a subir (CSV o Excel)")
example_df = pd.DataFrame({
    'SKU': ['4387', '4417'],
    'Inventario hoy': [892, 1174],
    'Ventas (cajas)': [2189, 1810],
    'Periodo días': [210, 210],
    'Lead Time días': [60, 60],
    'Días Safety Stock': [15, 15],
    'Tamaño Paleta': [225, 225]
})
st.table(example_df)

st.write(
    "**Columnas necesarias:**\n"
    "- SKU: Código del producto.\n"
    "- Inventario hoy: Stock actual en cajas.\n"
    "- Ventas (cajas): Ventas del periodo.\n"
    "- Periodo días: Días de histórico.\n"
    "- Lead Time días: Días de entrega.\n"
    "- Días Safety Stock: Días adicionales de inventario como buffer.\n"
    "- Tamaño Paleta: Cajas por paleta para redondeo."
)

st.markdown("---")
# Descarga plantilla
st.markdown("### 📥 Descarga plantilla de Excel antes de cargar datos")
with open('template.xlsx','rb') as f:
    tmpl = f.read()
st.download_button(label='Descargar plantilla', data=tmpl, file_name='plantilla.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Subir archivo
st.header("1️⃣ Sube tu CSV o Excel")
uploaded = st.file_uploader("Selecciona tu archivo", type=['csv','xls','xlsx'])
if uploaded:
    if uploaded.name.lower().endswith(('xls','xlsx')):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)
    # Renombrar internamente
df.rename(columns={
    'SKU':'SKU','Inventario hoy':'Inventario_cajas','Ventas (cajas)':'Ventas_cajas',
    'Periodo días':'Periodo_dias','Lead Time días':'Lead_time','Días Safety Stock':'Safety_days',
    'Tamaño Paleta':'Pallet_size'
}, inplace=True)
    # Tipar
    for col in ['Inventario_cajas','Ventas_cajas','Periodo_dias','Lead_time','Safety_days','Pallet_size']:
        df[col]=pd.to_numeric(df[col],errors='coerce')
    st.success("✔️ Datos cargados")
    st.dataframe(df, height=200)

    # Calcular
    if st.button("2️⃣ Calcular Sugerencia"):
        df['ventasDiarias']=df['Ventas_cajas']/df['Periodo_dias']
        # punto = D*(L + Safety_days)
        df['puntoReposicion']=(df['ventasDiarias']*(df['Lead_time']+df['Safety_days'])).round(0)
        df['reordenar']=df['Inventario_cajas']<=df['puntoReposicion']
        # diferencia y redondeo
        df['diferencia']= (df['puntoReposicion']-df['Inventario_cajas']).clip(lower=0)
        df['Orden_cajas']=df.apply(lambda r: math.ceil(r['diferencia']/r['Pallet_size'])*r['Pallet_size'] if r['Pallet_size']>0 else 0, axis=1)
        st.subheader("📈 Resultados")
        st.dataframe(df[['SKU','ventasDiarias','puntoReposicion','reordenar','Orden_cajas']],height=300)
        # explicación
        st.markdown("---")
        st.write(
            "**Cálculo:**  "
            "1) ventasDiarias = Ventas_cajas/Periodo_dias.  "
            "2) puntoReposicion = ventasDiarias * (Lead_time + Safety_days).  "
            "3) reordenar = Inventario_cajas ≤ puntoReposicion.  "
            "4) Orden_cajas = ceil(max(puntoReposicion-Inventario_cajas,0)/Pallet_size)*Pallet_size."
        )
        # descarga
        csv=df.to_csv(index=False).encode('utf-8')
        st.download_button(label='📥 Descargar',data=csv,file_name='sugerencia.csv',mime='text/csv')
```
