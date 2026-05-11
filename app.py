import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la interfaz profesional
st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide", initial_sidebar_state="expanded")

# --- CONEXIÓN DE DATOS ---
# Link de publicación CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    # Leer CSV directamente desde la publicación web
    df = pd.read_csv(CSV_URL)
    
    # Limpieza de nombres de columnas (quitar espacios y pasar a MAYÚSCULAS)
    df.columns = df.columns.str.strip().str.upper()
    
    # Procesamiento de Fechas (Ingreso en W y Egreso en AV)
    if 'F. INGR' in df.columns:
        df['F. INGR'] = pd.to_datetime(df['F. INGR'], errors='coerce')
    if 'F. EGRESO' in df.columns:
        df['F. EGRESO'] = pd.to_datetime(df['F. EGRESO'], errors='coerce')
    
    return df

try:
    df = load_data()

    # --- LÓGICA DE TIEMPO (Año actual para Rotación OIT) ---
    anio_actual = datetime.now().year
    inicio_anio = pd.to_datetime(f"{anio_actual}-01-01")
    hoy = pd.to_datetime(datetime.now())

    # --- PANEL LATERAL (FILTROS) ---
    st.sidebar.title("Filtros de Gestión")
    
    # Filtro por Empresa
    list_empresas = sorted(df['EMPRESA'].dropna().unique())
    empresa_sel = st.sidebar.multiselect("Seleccionar Concesionaria", list_empresas, default=list_empresas)
    
    # Filtro por Localidad
    list_localidades = sorted(df['LOCALIDAD'].dropna().unique())
    localidad_sel = st.sidebar.multiselect("Seleccionar Localidad", list_localidades, default=list_localidades)
    
    # Filtro por Áreas
    list_areas = sorted(df['ÁREA'].dropna().unique())
    area_sel = st.sidebar.multiselect("Seleccionar Área", list_areas, default=list_areas)

    # Aplicación de filtros cruzados
    mask = (df['EMPRESA'].isin(empresa_sel)) & \
           (df['LOCALIDAD'].isin(localidad_sel)) & \
           (df['ÁREA'].isin(area_sel))
    df_f = df[mask].copy()

    # --- CÁLCULOS KPI HARD (ROTACIÓN OIT) ---
    
    # 1. Dotación Inicial (Estaban activos al inicio del año)
    dot_inicial = len(df_f[
        (df_f['F. INGR'] < inicio_anio) & 
        ((df_f['ESTADO'].str.upper() == 'ACTIVO') | (df_f['F. EGRESO'] >= inicio_anio))
    ])

    # 2. Dotación Final (Activos hoy)
    dot_final = len(df_f[df_f['ESTADO'].str.upper() == 'ACTIVO'])

    # 3. Bajas del periodo (Inactivos con egresos ocurridos este año)
    bajas_periodo = len(df_f[
        (df_f['ESTADO'].str.upper() == 'INACTIVO') & 
        (df_f['F. EGRESO'] >= inicio_anio) & 
        (df_f['F. EGRESO'] <= hoy)
    ])

    # 4. Cálculo Rotación: Bajas / ((Dot. Inicial + Dot. Final) / 2)
    dot_promedio = (dot_inicial + dot_final) / 2
    tasa_rotacion = (bajas_periodo / dot_promedio * 100) if dot_promedio > 0 else 0

    # Periodo de Prueba
    en_prueba = len(df_f[
        (df_f['ESTADO'].str.upper() == 'ACTIVO') & 
        (df_f['ANTIGÜEDAD'].str.contains('00 Años', na=False))
    ])

    # --- DISEÑO DEL DASHBOARD ---
    st.title("📊 DashBoard People Analytics - Grupo Cenoa")
    st.markdown(f"**Periodo:** {inicio_anio.strftime('%d/%m/%Y')} al {hoy.strftime('%d/%m/%Y')}")

    # Fila superior de métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Dotación Actual", f"{dot_final} pers.", help="Colaboradores con estado 'Activo'")
    m2.metric("Rotación OIT (YTD)", f"{tasa_rotacion:.1f}%", f"{bajas_periodo} bajas", delta_color="inverse")
    m3.metric("Dotación Promedio", f"{dot_promedio:.1f}")
    m4.metric("Periodo de Prueba", f"{en_prueba}", "Ingresos < 1 año")

    st.divider()

    # Fila de Gráficos
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Dotación por Localidad")
        dot_loc = df_f[df_f['ESTADO'].str.upper() == 'ACTIVO'].groupby('LOCALIDAD').size().reset_index(name='Cant')
        fig_loc = px.bar(dot_loc, x='LOCALIDAD', y='Cant', color='LOCALIDAD', text_auto=True,
                         color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_loc, use_container_width=True)

    with c2:
        st.subheader("Distribución por Áreas")
        dot_area = df_f[df_f['ESTADO'].str.upper() == 'ACTIVO'].groupby('ÁREA').size().reset_index(name='Cant')
        fig_area = px.pie(dot_area, values='Cant', names='ÁREA', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_area, use_container_width=True)

    # Gráfico de Desempeño por Concesionaria
    st.subheader("Análisis de Dotación por Empresa")
    dot_emp = df_f[df_f['ESTADO'].str.upper() == 'ACTIVO'].groupby('EMPRESA').size().reset_index(name='Cant')
    fig_emp = px.bar(dot_emp, x='EMPRESA', y='Cant', color='EMPRESA', text_auto=True)
    st.plotly_chart(fig_emp, use_container_width=True)

    # Vista de Tabla Detallada
    with st.expander("Ver Nómina Filtrada (Detalle)"):
        st.dataframe(df_f[['APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'ÁREA', 'PUESTO', 'ESTADO', 'ANTIGÜEDAD']], 
                     use_container_width=True)

except Exception as e:
    st.error(f"Se detectó un error al procesar la BDD: {e}")
    st.info("Recomendación: Verifica que no haya celdas combinadas en las filas de encabezado de Google Sheets.")
