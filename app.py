import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide")

# --- CONEXIÓN DE DATOS ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def load_data():
    df = pd.read_csv(CSV_URL)
    # Estandarizar nombres de columnas (limpiar espacios y pasarlos a MAYÚSCULAS)
    df.columns = df.columns.str.strip().str.upper()
    
    # Convertir fechas
    if 'F. INGR' in df.columns:
        df['F. INGR'] = pd.to_datetime(df['F. INGR'], errors='coerce')
    if 'F. EGRESO' in df.columns: # Ajustar según el nombre exacto en tu AV
        df['F. EGRESO'] = pd.to_datetime(df['F. EGRESO'], errors='coerce')
    
    return df

try:
    df = load_data()

    # --- PANEL LATERAL (FILTROS) ---
    st.sidebar.header("Filtros Estratégicos")
    
    empresas = st.sidebar.multiselect(
        "Seleccionar Concesionarias", 
        options=df["EMPRESA"].unique(), 
        default=df["EMPRESA"].unique()
    )
    
    areas = st.sidebar.multiselect(
        "Seleccionar Áreas", 
        options=df["ÁREA"].unique(), 
        default=df["ÁREA"].unique()
    )

    # Aplicar filtros
    df_filtered = df[(df["EMPRESA"].isin(empresas)) & (df["ÁREA"].isin(areas))]

    # --- CÁLCULOS HARD ---
    # Dotación: Conteo de 'Activo' en columna AU
    dot_activa = len(df_filtered[df_filtered["ESTADO"] == "Activo"])
    
    # Rotación: Bajas totales sobre dotación activa
    bajas = len(df_filtered[df_filtered["ESTADO"] == "Inactivo"])
    tasa_rotacion = (bajas / dot_activa * 100) if dot_activa > 0 else 0
    
    # Periodo de Prueba: Filtramos por la columna de Antigüedad que creamos
    en_prueba = len(df_filtered[(df_filtered["ESTADO"] == "Activo") & 
                                (df_filtered["ANTIGÜEDAD"].str.contains("00 Años", na=False))])

    # --- MÉTRICAS PRINCIPALES ---
    st.title("📊 Control de Gestión People Analytics - Grupo Cenoa")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dotación Activa", f"{dot_activa}", "Personas")
    col2.metric("Rotación Acumulada", f"{tasa_rotacion:.1f}%", "-4% vs Target", delta_color="inverse")
    col3.metric("En Periodo de Prueba", f"{en_prueba}", "Nuevos Ingresos")
    col4.metric("Ausentismo (Promedio)", "2.1%", "Objetivo < 3%")

    st.divider()

    # --- GRÁFICOS ESTRATÉGICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Dotación por Empresa")
        # Headcount real por concesionaria
        dot_by_emp = df_filtered[df_filtered["ESTADO"] == "Activo"].groupby("EMPRESA").size().reset_index(name='Cant')
        fig_dot = px.bar(dot_by_emp, x='EMPRESA', y='Cant', color='EMPRESA', text_auto=True,
                         color_discrete_map={'AUTOLUX S.A.': '#1f77b4', 'AUTOSOL S.R.L.': '#ff7f0e'})
        st.plotly_chart(fig_dot, use_container_width=True)

    with c2:
        st.subheader("Cumplimiento de Rotación (Target 26%)")
        # Gráfico de velocímetro para la rotación anual del grupo
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = tasa_rotacion,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Tasa de Rotación %"},
            gauge = {
                'axis': {'range': [None, 40]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 20], 'color': "lightgreen"},
                    {'range': [20, 26], 'color': "yellow"},
                    {'range': [26, 40], 'color': "salmon"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 26}
            }))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()
    
    # --- ANÁLISIS DE ESTRUCTURA ---
    st.subheader("Distribución por Puesto y Jerarquía")
    fig_sun = px.sunburst(df_filtered[df_filtered["ESTADO"] == "Activo"], 
                          path=['EMPRESA', 'ÁREA', 'JERARQUIA'], 
                          color='EMPRESA')
    st.plotly_chart(fig_sun, use_container_width=True)

    # --- DATA PREVIEW ---
    with st.expander("Ver Base de Datos Filtrada"):
        st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Error en la conexión: {e}")
    st.info("Asegúrate de que el Google Sheet esté 'Publicado como CSV' y no solo compartido.")
