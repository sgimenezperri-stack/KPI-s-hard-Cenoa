import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Dotación - Grupo Cenoa", layout="wide")

# Título y estilos
st.title("📊 Panel Histórico de Dotación - Grupo Cenoa")
st.markdown("---")

# URL del Google Sheets publicado (pubhtml)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQeYlPH-NwPQdPU4tLiOXlC_oUsvQJZAQ1rFYP9TahnaUQyYJkKaNsSldk5spBg-20iUej669ln9luI/pubhtml"

@st.cache_data(ttl=600) # El cache se limpia cada 10 minutos automáticamente
def load_all_data(url):
    try:
        # Leemos todas las tablas del HTML publicado
        # Nota: Google Sheets publica las solapas como tablas diferentes en el HTML
        all_tables = pd.read_html(url, header=1)
        
        historial_df = []
        
        # Procesamos cada tabla (asumiendo que cada una es un mes)
        for i, df in enumerate(all_tables):
            # Limpieza básica de columnas
            df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
            
            # Intentamos identificar el periodo (mes/año) 
            # Si el link pubhtml no trae los nombres de las pestañas, 
            # buscamos una celda que contenga fechas o usamos un índice.
            if 'EMPRESA' in df.columns and 'APELLIDO Y NOMBRE' in df.columns:
                # Filtrar filas vacías o de prueba según tus registros
                df = df[df['APELLIDO Y NOMBRE'].notna()]
                
                # Agregar columna de periodo si existe en el encabezado o datos
                # (Aquí puedes ajustar la lógica según cómo aparezca el mes en el HTML)
                historial_df.append(df)
        
        if not historial_df:
            return pd.DataFrame()
            
        return pd.concat(historial_df, ignore_index=True)
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

# --- LÓGICA DE ACTUALIZACIÓN CON BOTÓN ---
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.success("¡Datos actualizados!")

# Carga de datos
df_raw = load_all_data(SHEET_URL)

if df_raw.empty:
    st.warning("No se pudieron cargar los datos. Verifica que el Google Sheets esté publicado correctamente en la web.")
else:
    # --- FILTROS EN SIDEBAR ---
    st.sidebar.header("Filtros de Análisis")
    
    empresas = st.sidebar.multiselect("Seleccionar Empresa", options=df_raw["EMPRESA"].unique(), default=df_raw["EMPRESA"].unique())
    sucursales = st.sidebar.multiselect("Seleccionar Sucursal", options=df_raw["SUCURSAL"].unique(), default=df_raw["SUCURSAL"].unique())
    areas = st.sidebar.multiselect("Seleccionar Área", options=df_raw["ÁREA"].unique(), default=df_raw["ÁREA"].unique())

    # Aplicar filtros
    mask = (df_raw["EMPRESA"].isin(empresas)) & (df_raw["SUCURSAL"].isin(sucursales)) & (df_raw["ÁREA"].isin(areas))
    df_filtered = df_raw[mask]

    # --- MÉTRICAS PRINCIPALES ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Dotación Total", len(df_filtered))
    with m2:
        # Ejemplo basado en tus datos de RRHH: Total histórico esperado 529
        st.metric("Empresas Activas", df_filtered["EMPRESA"].nunique())
    with m3:
        st.metric("Promedio Edad", round(pd.to_numeric(df_filtered["EDAD"], errors='coerce').mean(), 1))
    with m4:
        st.metric("Sucursales", df_filtered["SUCURSAL"].nunique())

    st.markdown("---")

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Distribución por Empresa")
        fig_emp = px.pie(df_filtered, names="EMPRESA", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_emp, use_container_width=True)

    with c2:
        st.subheader("Dotación por Sucursal")
        fig_suc = px.bar(df_filtered.groupby("SUCURSAL").size().reset_index(name='Cantidad'), 
                         x="SUCURSAL", y="Cantidad", color="SUCURSAL", text_auto=True)
        st.plotly_chart(fig_suc, use_container_width=True)

    st.subheader("Análisis por Áreas y Puestos")
    fig_area = px.treemap(df_filtered, path=['ÁREA', 'SUB ÁREA', 'PUESTO'], 
                          title="Jerarquía de Dotación por Sector")
    st.plotly_chart(fig_area, use_container_width=True)

    # --- TABLA DE DATOS ---
    with st.expander("Ver detalle de la nómina"):
        st.dataframe(df_filtered[["APELLIDO Y NOMBRE", "DNI", "EMPRESA", "SUCURSAL", "ÁREA", "PUESTO", "F. INGR"]])
