import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Mapeo de columnas clave
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA INGRESO': 'FECHA DE INGRESO',
        'F. EGRESO': 'FECHA DE EGRESO',
        'FECHA EGRESO': 'FECHA DE EGRESO'
    })

    # Limpieza y conversión de fechas
    df['FECHA_ING_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    df['FECHA_EGR_DT'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')
    
    # Edad numérica
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)
    
    # Normalizar textos
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'ESTADO', 'SEXO']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], np.nan)
            
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL ---
    st.sidebar.title("📈 Gestión Human Capital")
    
    # Selector de Mes y Año de Corte (Para ver la dotación en ese momento exacto)
    st.sidebar.subheader("Punto en el Tiempo")
    hoy = datetime.now()
    mes_analisis = st.sidebar.slider("Mes de Corte", 1, 12, hoy.month)
    anio_analisis = st.sidebar.selectbox("Año de Corte", [2026, 2025, 2024], index=0)
    fecha_corte = pd.to_datetime(datetime(anio_analisis, mes_analisis, 1))

    st.sidebar.divider()
    
    # Filtros de estructura
    def get_opts(col): return sorted([x for x in df_raw[col].unique() if pd.notna(x)])
    sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
    sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))

    # --- LÓGICA DE RECONSTRUCCIÓN HISTÓRICA ---
    # Un empleado estaba activo en la fecha de corte si:
    # 1. Ingresó antes o el mismo día de la fecha de corte.
    # 2. No tiene fecha de egreso O su fecha de egreso es posterior a la fecha de corte.
    
    mask_historica = (
        (df_raw['FECHA_ING_DT'] <= fecha_corte) & 
        ((df_raw['FECHA_EGR_DT'].isna()) | (df_raw['FECHA_EGR_DT'] > fecha_corte))
    )
    
    df_periodo = df_raw[mask_historica].copy()
    
    # Aplicar filtros de empresa y área sobre ese histórico
    if sel_emp: df_periodo = df_periodo[df_periodo['EMPRESA'].isin(sel_emp)]
    if sel_area: df_periodo = df_periodo[df_periodo['AREA'].isin(sel_area)]

    # --- DASHBOARD ---
    st.title(f"📊 Análisis de Dotación: {mes_analisis}/{anio_analisis}")
    st.caption("Considera empleados activos a la fecha, incluyendo 'Inactivos' actuales que estaban presentes en este periodo.")

    # KPIs
    dot_total = len(df_periodo)
    c1, c2, c3 = st.columns(3)
    c1.metric("Dotación en Periodo", dot_total)
    
    # Comparativa vs mes anterior (simplificada)
    fecha_ant = fecha_corte - pd.DateOffset(months=1)
    dot_ant = len(df_raw[(df_raw['FECHA_ING_DT'] <= fecha_ant) & ((df_raw['FECHA_EGR_DT'].isna()) | (df_raw['FECHA_EGR_DT'] > fecha_ant))])
    c2.metric("Variación vs Mes Ant.", dot_total, delta=int(dot_total - dot_ant))
    
    edad_p = df_periodo['EDAD_NUM'].mean()
    c3.metric("Edad Promedio", f"{edad_p:.1f}" if pd.notna(edad_p) else "S/D")

    st.divider()

    # --- GRÁFICO DE EVOLUCIÓN MENSUAL ---
    st.subheader("📈 Evolución Histórica de la Dotación")
    
    fechas_rango = pd.date_range(start='2024-01-01', end=datetime.now(), freq='MS')
    evolucion = []
    for f in fechas_rango:
        conteo = len(df_raw[(df_raw['FECHA_ING_DT'] <= f) & ((df_raw['FECHA_EGR_DT'].isna()) | (df_raw['FECHA_EGR_DT'] > f))])
        evolucion.append({'Fecha': f, 'Dotación': conteo})
    
    df_evolucion = pd.DataFrame(evolucion)
    fig_linea = px.line(df_evolucion, x='Fecha', y='Dotación', markers=True, title="Crecimiento Neto Grupo Cenoa")
    st.plotly_chart(fig_linea, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Dotación por Empresa")
        st.plotly_chart(px.bar(df_periodo.groupby('EMPRESA').size().reset_index(name='Cant'), x='EMPRESA', y='Cant', text_auto=True), use_container_width=True)
    with col2:
        st.subheader("Distribución por Área")
        st.plotly_chart(px.pie(df_periodo, names='AREA', hole=0.4), use_container_width=True)

    st.subheader("Estructura en este Periodo")
    fig_sun = px.sunburst(df_periodo, path=['EMPRESA', 'AREA', 'PUESTO'], color='EMPRESA')
    st.plotly_chart(fig_sun, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
