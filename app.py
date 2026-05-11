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
    # Cargamos todo como string para evitar choques de tipos (número vs texto)
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={'ÁREA': 'AREA', 'F. INGR': 'FECHA DE INGRESO'})
    
    # Limpieza de basura
    df = df.replace(['-', ' -', '- ', '0', 'nan', 'NAN', ''], np.nan)
    
    # Normalización de textos y eliminación de espacios laterales
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
    
    # Procesar años de ingreso (convertimos a texto para que coincida con los filtros)
    if 'FECHA DE INGRESO' in df.columns:
        # Intentamos leer la fecha, si falla queda como NaT
        fechas = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        # Extraemos el año y lo convertimos a string (ej: "2024")
        df['AÑO_INGRESO_STR'] = fechas.dt.year.fillna(0).astype(int).astype(str)
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL (FILTROS) ---
    st.sidebar.title("Módulos RRHH")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Precisión")

        # Función para obtener opciones limpias
        def get_options(col):
            opts = sorted([x for x in df_raw[col].unique() if x not in ['NAN', 'NONE', '0', '0.0']])
            return opts

        # Selectores
        selected_emp = st.sidebar.multiselect("Empresa", get_options('EMPRESA'), default=get_options('EMPRESA'))
        selected_loc = st.sidebar.multiselect("Localidad", get_options('LOCALIDAD'), default=get_options('LOCALIDAD'))
        selected_area = st.sidebar.multiselect("Área", get_options('AREA'), default=get_options('AREA'))
        
        # Filtro de Año (usando la columna de texto que creamos)
        anios_disponibles = sorted([x for x in df_raw['AÑO_INGRESO_STR'].unique() if x != '0'], reverse=True)
        selected_anio = st.sidebar.multiselect("Año de Ingreso", anios_disponibles, default=anios_disponibles)

        # --- LÓGICA DE FILTRADO (UNIFICADA EN TEXTO) ---
        # 1. Empezamos con los activos
        df_filtrado = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
        
        # 2. Aplicamos cada filtro de forma secuencial
        if selected_emp:
            df_filtrado = df_filtrado[df_filtrado['EMPRESA'].isin(selected_emp)]
        if selected_loc:
            df_filtrado = df_filtrado[df_filtrado['LOCALIDAD'].isin(selected_loc)]
        if selected_area:
            df_filtrado = df_filtrado[df_filtrado['AREA'].isin(selected_area)]
        if selected_anio:
            df_filtrado = df_filtrado[df_filtrado['AÑO_INGRESO_STR'].isin(selected_anio)]

        # --- DASHBOARD ---
        st.title("👥 Análisis de Dotación")
        
        total = len(df_filtrado)
        
        if total > 0:
            c1, c2, c3 = st.columns(3)
            c1.metric("Dotación Actual", f"{total}")
            c2.metric("Sedes Activas", df_filtrado['LOCALIDAD'].nunique())
            c3.metric("Áreas", df_filtrado['AREA'].nunique())

            st.divider()

            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("Headcount por Empresa")
                res_emp = df_filtrado.groupby('EMPRESA').size().reset_index(name='Cant')
                st.plotly_chart(px.bar(res_emp, x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA'), use_container_width=True)
            
            with col_right:
                st.subheader("Distribución por Localidad")
                st.plotly_chart(px.pie(df_filtrado, names='LOCALIDAD', hole=0.3), use_container_width=True)

            st.subheader("Explorador de Estructura Organizacional")
            fig_sun = px.sunburst(df_filtrado, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.warning("No se encontraron resultados para los filtros seleccionados.")

except Exception as e:
    st.error(f"Error en el sistema: {e}")
