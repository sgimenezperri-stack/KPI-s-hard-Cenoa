import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (LECTURA SEGURA)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    # Todo como texto para evitar el error de float vs str
    df = pd.read_csv(CSV_URL, dtype=str)
    
    # Normalizar encabezados
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA INGRESO': 'FECHA DE INGRESO',
        'ANTIGÜEDAD': 'ANTIGUEDAD'
    })
    
    # Limpieza masiva de basura
    df = df.replace(['-', ' -', '- ', '0', '0.0', 'NAN', 'NONE', ''], np.nan)
    
    # Normalizar textos y extraer datos numéricos
    for col in df.columns:
        if col not in ['FECHA DE INGRESO', 'FECHA DE EGRESO']:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Edad: Extraer solo número de "XX AÑOS"
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)

    # Fechas: Procesar para cálculos de crecimiento y filtros
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        df['ANIO_ING'] = df['FECHA_DT'].dt.year.fillna(0).astype(int).astype(str)
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL: NAVEGACIÓN ---
    st.sidebar.title("📈 Gestión Human Capital")
    modulo = st.sidebar.radio("Dimensión de Análisis:", ["1- DOTACION", "2- ROTACION", "3- AUSENTISMO"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Dotación")

        def get_opts(col):
            return sorted([x for x in df_raw[col].unique() if pd.notna(x) and x not in ['NAN', '0']])

        sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
        sel_loc = st.sidebar.multiselect("Localidad", get_opts('LOCALIDAD'), default=get_opts('LOCALIDAD'))
        sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))
        
        # FILTRO DE AÑO (Para analizar 2025, 2026, etc.)
        anios_disp = sorted([x for x in df_raw['ANIO_ING'].unique() if x != '0'], reverse=True)
        sel_anio = st.sidebar.multiselect("Año de Ingreso (Análisis Periodo)", anios_disp, default=anios_disp)

        # --- APLICACIÓN DE FILTROS ---
        df_act = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
        
        if sel_emp: df_act = df_act[df_act['EMPRESA'].isin(sel_emp)]
        if sel_loc: df_act = df_act[df_act['LOCALIDAD'].isin(sel_loc)]
        if sel_area: df_act = df_act[df_act['AREA'].isin(sel_area)]
        if sel_anio: df_act = df_act[df_act['ANIO_ING'].isin(sel_anio)]

        # --- CÁLCULO DE CRECIMIENTO ---
        f_ini_2026 = pd.to_datetime('2026-01-01')
        f_ini_2025 = pd.to_datetime('2025-01-01')
        
        dot_hoy = len(df_act)
        dot_ini_2026 = len(df_act[df_act['FECHA_DT'] < f_ini_2026])
        dot_ini_2025 = len(df_act[df_act['FECHA_DT'] < f_ini_2025])
        
        crec_2026 = ((dot_hoy - dot_ini_2026) / dot_ini_2026 * 100) if dot_ini_2026 > 0 else 100
        crec_2025 = ((dot_hoy - dot_ini_2025) / dot_ini_2025 * 100) if dot_ini_2025 > 0 else 100

        # --- DASHBOARD VISUAL ---
        st.title("👥 Análisis de Dotación y Crecimiento")
        
        # Fila 1: Métricas de Crecimiento
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Dotación Actual", dot_hoy)
        m2.metric("Crecimiento 2026", f"{crec_2026:.1f}%", f"{dot_hoy - dot_ini_2026} netos")
        m3.metric("Crecimiento vs 2025", f"{crec_2025:.1f}%")
        edad_p = df_act['EDAD_NUM'].mean()
        m4.metric("Edad Promedio", f"{edad_p:.1f}" if pd.notna(edad_p) else "S/D")

        st.divider()

        # Fila 2: Distribución
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Headcount por Empresa")
            fig_emp = px.bar(df_act.groupby('EMPRESA').size().reset_index(name='Cant'), 
                             x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA')
            st.plotly_chart(fig_emp, use_container_width=True)
        with c2:
            st.subheader("Distribución Geográfica")
            fig_loc = px.pie(df_act, names='LOCALIDAD', hole=0.4)
            st.plotly_chart(fig_loc, use_container_width=True)

        st.divider()

        # Fila 3: Crecimiento Detallado por Área
        st.subheader("📊 Índice de Crecimiento por Empresa y Área")
        res_crec = df_act.groupby(['EMPRESA', 'AREA']).agg(
            Actual=('ESTADO', 'count'),
            Inicio_2026=('FECHA_DT', lambda x: (x < f_ini_2026).sum())
        ).reset_index()
        res_crec['Variacion_%'] = ((res_crec['Actual'] - res_crec['Inicio_2026']) / res_crec['Inicio_2026'] * 100).replace([np.inf, -np.inf], 100).fillna(0)
        
        st.dataframe(res_crec.sort_values(by='Variacion_%', ascending=False), use_container_width=True)

        st.divider()

        # Fila 4: Estructura Sunburst (Explorador)
        st.subheader("Explorador Organizacional (Área > Sub Área > Puesto)")
        fig_sun = px.sunburst(df_act, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
        fig_sun.update_layout(height=600)
        st.plotly_chart(fig_sun, use_container_width=True)

        # Fila 5: Tabla Maestra
        with st.expander("Ver Nómina Completa Filtrada"):
            st.dataframe(df_act[['CUIL', 'APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'FECHA DE INGRESO']], use_container_width=True)

    elif modulo == "2- ROTACION":
        st.title("🔄 Análisis de Rotación e Índice de Bajas")
        st.info("Módulo configurado para procesar motivos de egreso.")

except Exception as e:
    st.error(f"Error detectado: {e}")
