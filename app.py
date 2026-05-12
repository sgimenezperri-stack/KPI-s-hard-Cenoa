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
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA INGRESO': 'FECHA DE INGRESO',
        'F. EGRESO': 'FECHA DE EGRESO',
        'FECHA EGRESO': 'FECHA DE EGRESO'
    })
    df['FECHA_ING_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    df['FECHA_EGR_DT'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')
    
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)
    
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'ESTADO']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], np.nan)
    return df

try:
    df_raw = load_data()

    # --- SIDEBAR ---
    st.sidebar.title("📈 Configuración")
    
    # Selectores de Tiempo
    hoy = datetime.now()
    anio_analisis = st.sidebar.selectbox("Año de Corte", [2026, 2025, 2024], index=0)
    mes_analisis = st.sidebar.slider("Mes de Corte", 1, 12, hoy.month)
    fecha_corte = pd.to_datetime(datetime(anio_analisis, mes_analisis, 1))

    st.sidebar.divider()
    
    # Filtros de Estructura
    def get_opts(col): return sorted([x for x in df_raw[col].unique() if pd.notna(x)])
    sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
    sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))

    # --- FILTRADO ESTRUCTURAL PREVIO ---
    # Filtramos el universo total por empresa y área antes de calcular la historia
    df_universo = df_raw.copy()
    if sel_emp: df_universo = df_universo[df_universo['EMPRESA'].isin(sel_emp)]
    if sel_area: df_universo = df_universo[df_universo['AREA'].isin(sel_area)]

    # --- RECONSTRUCCIÓN DE DOTACIÓN ---
    def get_dotacion_a_fecha(df, fecha):
        return df[(df['FECHA_ING_DT'] <= fecha) & ((df['FECHA_EGR_DT'].isna()) | (df['FECHA_EGR_DT'] > fecha))]

    df_periodo = get_dotacion_a_fecha(df_universo, fecha_corte)

    # --- DASHBOARD ---
    st.title(f"👥 Análisis de Dotación: {mes_analisis}/{anio_analisis}")
    
    # KPIs con Variaciones
    dot_actual = len(df_periodo)
    
    # Variación vs Mes Anterior
    fecha_mes_ant = fecha_corte - pd.DateOffset(months=1)
    dot_mes_ant = len(get_dotacion_a_fecha(df_universo, fecha_mes_ant))
    
    # Variación vs Año Anterior (Interanual)
    fecha_anio_ant = fecha_corte - pd.DateOffset(years=1)
    dot_anio_ant = len(get_dotacion_a_fecha(df_universo, fecha_anio_ant))

    c1, c2, c3 = st.columns(3)
    c1.metric("Dotación en Periodo", dot_actual)
    c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=int(dot_actual - dot_mes_ant))
    c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=int(dot_actual - dot_anio_ant), help="Comparación con el mismo mes del año anterior")

    st.divider()

    # --- GRÁFICO DINÁMICO DE CRECIMIENTO ---
    st.subheader("📈 Evolución de Crecimiento Neto (Filtrado)")
    
    # Generamos la serie histórica basada solo en el universo filtrado
    rango_fechas = pd.date_range(start='2024-01-01', end=datetime.now(), freq='MS')
    historia = []
    for f in rango_fechas:
        historia.append({'Fecha': f, 'Dotación': len(get_dotacion_a_fecha(df_universo, f))})
    
    df_historia = pd.DataFrame(historia)
    
    fig_evol = px.line(df_historia, x='Fecha', y='Dotación', markers=True, text='Dotación')
    fig_evol.update_traces(textposition="top center") # Muestra etiquetas de datos
    st.plotly_chart(fig_evol, use_container_width=True)

    # --- APERTURAS ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Corte por Empresa")
        df_emp = df_periodo.groupby('EMPRESA').size().reset_index(name='Cant')
        st.plotly_chart(px.bar(df_emp, x='EMPRESA', y='Cant', text_auto=True), use_container_width=True)
    with col2:
        st.subheader("Corte por Localidad")
        st.plotly_chart(px.pie(df_periodo, names='LOCALIDAD', hole=0.3), use_container_width=True)

    st.subheader("Explorador de Estructura")
    st.plotly_chart(px.sunburst(df_periodo, path=['EMPRESA', 'AREA', 'PUESTO'], color='EMPRESA'), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
