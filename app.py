import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN BÁSICA
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# 2. CARGA DE DATOS SIN RIESGOS
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    # Forzamos a que TODO sea texto desde el primer segundo
    df = pd.read_csv(CSV_URL, dtype=str)
    
    # Limpiamos los nombres de las columnas de cualquier símbolo extraño
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Mapeo manual para asegurar que las columnas clave se llamen igual siempre
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA INGRESO': 'FECHA DE INGRESO',
        'ANTIGÜEDAD': 'ANTIGUEDAD'
    })
    
    # Limpiamos los datos: quitamos espacios y convertimos guiones en vacíos
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace(['-', 'NAN', 'NONE', '0', '0.0', ''], np.nan)
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL ---
    st.sidebar.title("📈 Gestión Human Capital")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        
        # Función ultra-segura para obtener opciones de filtros
        def get_safe_opts(col_name):
            if col_name in df_raw.columns:
                return sorted([x for x in df_raw[col_name].unique() if pd.notna(x)])
            return []

        # Creamos los selectores
        sel_emp = st.sidebar.multiselect("Empresa", get_safe_opts('EMPRESA'), default=get_safe_opts('EMPRESA'))
        sel_loc = st.sidebar.multiselect("Localidad", get_safe_opts('LOCALIDAD'), default=get_safe_opts('LOCALIDAD'))
        sel_area = st.sidebar.multiselect("Área", get_safe_opts('AREA'), default=get_safe_opts('AREA'))

        # FILTRADO PASO A PASO (SIN COMPARACIONES < o > QUE DAN ERROR)
        # 1. Filtro de Estado
        df_f = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
        
        # 2. Filtros de usuario (Solo si hay columnas y selecciones)
        if sel_emp and 'EMPRESA' in df_f.columns:
            df_f = df_f[df_f['EMPRESA'].isin(sel_emp)]
        if sel_loc and 'LOCALIDAD' in df_f.columns:
            df_f = df_f[df_f['LOCALIDAD'].isin(sel_loc)]
        if sel_area and 'AREA' in df_f.columns:
            df_f = df_f[df_f['AREA'].isin(sel_area)]

        # --- DASHBOARD ---
        st.title("👥 Panel de Dotación Activa")
        
        total = len(df_f)
        
        if total > 0:
            c1, c2, c3 = st.columns(3)
            c1.metric("Dotación Total", total)
            c2.metric("Sedes Activas", df_f['LOCALIDAD'].nunique() if 'LOCALIDAD' in df_f.columns else 0)
            c3.metric("Áreas", df_f['AREA'].nunique() if 'AREA' in df_f.columns else 0)

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Por Empresa")
                if 'EMPRESA' in df_f.columns:
                    res_emp = df_f.groupby('EMPRESA').size().reset_index(name='Cant')
                    st.plotly_chart(px.bar(res_emp, x='EMPRESA', y='Cant', text_auto=True), use_container_width=True)
            
            with col_b:
                st.subheader("Por Localidad")
                if 'LOCALIDAD' in df_f.columns:
                    st.plotly_chart(px.pie(df_f, names='LOCALIDAD', hole=0.3), use_container_width=True)

            st.subheader("Estructura Organizacional")
            # El Sunburst es lo que más falla si hay datos raros, así que lo protegemos
            cols_sun = [c for c in ['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'] if c in df_f.columns]
            if len(cols_sun) > 1:
                st.plotly_chart(px.sunburst(df_f, path=cols_sun, color='EMPRESA'), use_container_width=True)
        else:
            st.warning("No se encontraron colaboradores activos con los filtros seleccionados.")

except Exception as e:
    st.error(f"Error Crítico: {e}")
    st.info("Recomendación: Si ves este mensaje, es probable que el link del Sheets haya cambiado o no tenga permisos de lectura pública.")
