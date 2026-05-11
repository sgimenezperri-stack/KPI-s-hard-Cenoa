import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# 2. CARGA DE DATOS
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'ÁREA': 'AREA', 'F. INGR': 'FECHA DE INGRESO', 'FECHA INGRESO': 'FECHA DE INGRESO'})
    
    # Limpieza de textos
    for col in ['EMPRESA', 'LOCALIDAD', 'AREA', 'ESTADO', 'FECHA DE INGRESO']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['-', 'NAN', 'NONE', '0', ''], np.nan)
    
    # Procesar Fecha de Ingreso para cálculos de crecimiento
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL ---
    st.sidebar.title("📈 Gestión Human Capital")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        def get_opts(col): return sorted([x for x in df_raw[col].unique() if pd.notna(x)])

        sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
        sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))

        # FILTRADO BASE
        df_act = df_raw[(df_raw['ESTADO'] == 'ACTIVO')].copy()
        if sel_emp: df_act = df_act[df_act['EMPRESA'].isin(sel_emp)]
        if sel_area: df_act = df_act[df_act['AREA'].isin(sel_area)]

        # --- LÓGICA DE CRECIMIENTO ---
        f_inicio_2026 = pd.to_datetime('2026-01-01')
        f_inicio_2025 = pd.to_datetime('2025-01-01')

        # Dotaciones de referencia
        dot_hoy = len(df_act)
        dot_ini_2026 = len(df_act[df_act['FECHA_DT'] < f_inicio_2026])
        dot_ini_2025 = len(df_act[df_act['FECHA_DT'] < f_inicio_2025])

        # % Crecimiento
        crec_2026 = ((dot_hoy - dot_ini_2026) / dot_ini_2026 * 100) if dot_ini_2026 > 0 else 0
        crec_2025 = ((dot_hoy - dot_ini_2025) / dot_ini_2025 * 100) if dot_ini_2025 > 0 else 0

        # --- DASHBOARD ---
        st.title("👥 Análisis de Dotación e Índice de Crecimiento")
        
        # Métricas de Crecimiento
        m1, m2, m3 = st.columns(3)
        m1.metric("Dotación Actual", dot_hoy)
        m2.metric("Crecimiento 2026 (YTD)", f"{crec_2026:.1f}%", f"{dot_hoy - dot_ini_2026} ingresos netos")
        m3.metric("Interanual (vs 2025)", f"{crec_2025:.1f}%", delta=None)

        st.divider()

        # --- TABLA DE CRECIMIENTO POR ÁREA / EMPRESA ---
        st.subheader("📊 Apertura de Crecimiento por Estructura")
        
        # Agrupamos por Empresa y Área para ver dónde creció más el equipo
        res = df_act.groupby(['EMPRESA', 'AREA']).agg(
            Dot_Hoy=('ESTADO', 'count'),
            Dot_Ini_2026=('FECHA_DT', lambda x: (x < f_inicio_2026).sum())
        ).reset_index()
        
        res['Crecimiento_%'] = ((res['Dot_Hoy'] - res['Dot_Ini_2026']) / res['Dot_Ini_2026'] * 100).replace(np.inf, 100).fillna(100)
        
        c1, c2 = st.columns([1.2, 0.8])
        with c1:
            st.dataframe(res.sort_values(by='Crecimiento_%', ascending=False), use_container_width=True)
        with c2:
            fig_crec = px.bar(res, x='AREA', y='Crecimiento_%', color='EMPRESA', 
                             title="% Crecimiento por Área", text_auto='.1f')
            st.plotly_chart(fig_crec, use_container_width=True)

        st.divider()
        st.subheader("Estructura Organizacional")
        st.plotly_chart(px.sunburst(df_act, path=['EMPRESA', 'AREA', 'PUESTO'], color='EMPRESA'), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
