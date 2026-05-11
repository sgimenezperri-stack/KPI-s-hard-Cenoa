import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la interfaz
st.set_page_config(page_title="People Analytics | Grupo Cenoa", layout="wide")

# --- CONEXIÓN DE DATOS ---
# Tu link de Google Sheets publicado como CSV
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL)
    # Limpieza de nombres de columnas
    df.columns = df.columns.str.strip().str.upper()
    
    # Conversión de fechas (Columnas W y AV en tu sheet)
    if 'F. INGR' in df.columns:
        df['F. INGR'] = pd.to_datetime(df['F. INGR'], errors='coerce')
    if 'F. EGRESO' in df.columns:
        df['F. EGRESO'] = pd.to_datetime(df['F. EGRESO'], errors='coerce')
    
    return df

try:
    df = load_data()

    # --- LÓGICA DE FECHAS PARA ROTACIÓN OIT ---
    anio_actual = datetime.now().year
    inicio_anio = pd.to_datetime(f"{anio_actual}-01-01")
    hoy = pd.to_datetime(datetime.now())

    # --- SIDEBAR / FILTROS ---
    st.sidebar.header("Filtros Globales")
    empresas = st.sidebar.multiselect("Concesionarias", df["EMPRESA"].unique(), df["EMPRESA"].unique())
    areas = st.sidebar.multiselect("Áreas", df["ÁREA"].unique(), df["ÁREA"].unique())

    # Filtrado del DataFrame
    df_f = df[(df["EMPRESA"].isin(empresas)) & (df["ÁREA"].isin(areas))]

    # --- CÁLCULOS TÉCNICOS (KPI HARD) ---
    
    # 1. Dotación Inicial (Estaban activos al 01/01)
    dot_inicial = len(df_f[
        (df_f['F. INGR'] < inicio_anio) & 
        ((df_f['ESTADO'] == 'Activo') | (df_f['F. EGRESO'] >= inicio_anio))
    ])

    # 2. Dotación Final (Activos hoy)
    dot_final = len(df_f[df_f["ESTADO"] == "Activo"])

    # 3. Bajas del Periodo (Egreso dentro del año actual)
    bajas = len(df_f[
        (df_f['F. EGRESO'] >= inicio_anio) & 
        (df_f['F. EGRESO'] <= hoy)
    ])

    # 4. Fórmula OIT: Bajas / Promedio de Dotación
    dot_promedio = (dot_inicial + dot_final) / 2
    tasa_rotacion = (bajas / dot_promedio * 100) if dot_promedio > 0 else 0

    # --- INTERFAZ DEL DASHBOARD ---
    st.title("📊 Dashboard de Gestión Human Capital - Cenoa")
    st.markdown(f"**Periodo de Análisis:** {inicio_anio.strftime('%d/%m/%Y')} al {hoy.strftime('%d/%m/%Y')}")

    # Tarjetas de Métricas
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dotación Actual", f"{dot_final}", "Colaboradores")
    k2.metric("Rotación (OIT)", f"{tasa_rotacion:.1f}%", f"Bajas: {bajas}", delta_color="inverse")
    k3.metric("Dotación Promedio", f"{dot_promedio:.1f}")
    k4.metric("Ausentismo (Target)", "2.1%", "Meta < 3%")

    st.divider()

    # Gráficos Principales
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribución por Concesionaria")
        fig_bar = px.bar(df_f[df_f["ESTADO"]=="Activo"].groupby("EMPRESA").size().reset_index(name='Cant'),
                         x='EMPRESA', y='Cant', color='EMPRESA', text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        st.subheader("Control de Bajas vs Meta Anual (26%)")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = tasa_rotacion,
            gauge = {'axis': {'range': [0, 40]},
                     'bar': {'color': "#1f77b4"},
                     'steps': [
                         {'range': [0, 20], 'color': "lightgreen"},
                         {'range': [20, 26], 'color': "yellow"},
                         {'range': [26, 40], 'color': "salmon"}],
                     'threshold': {'line': {'color': "red", 'width': 4}, 'value': 26}}))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Detalle de la Base
    with st.expander("Ver nómina filtrada"):
        st.dataframe(df_f[['APELLIDO Y NOMBRE', 'EMPRESA', 'ÁREA', 'PUESTO', 'ANTIGÜEDAD', 'ESTADO']], use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión: {e}")
