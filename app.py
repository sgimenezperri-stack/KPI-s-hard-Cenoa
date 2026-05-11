import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# 2. CARGA DE DATOS
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60) # Bajamos el cache a 1 min para que los cambios en el Excel se vean rápido
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={'ÁREA': 'AREA', 'F. INGR': 'FECHA DE INGRESO'})
    
    # LIMPIEZA TOTAL: Guiones, ceros y espacios
    df = df.replace(['-', ' -', '- ', '0', 'nan', 'NAN', ''], np.nan)
    
    # Normalizamos todas las columnas de texto para que los filtros coincidan siempre
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
    
    # Procesar fechas para filtros de año
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        df['AÑO_INGRESO'] = df['FECHA_DT'].dt.year.fillna(0).astype(int)
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL (FILTROS) ---
    st.sidebar.title("Módulos RRHH")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Precisión")

        # Función para opciones de filtro sin basura
        def get_options(col):
            opts = sorted([x for x in df_raw[col].unique() if x not in ['NAN', 'NONE', '0']])
            return opts

        # Creación de filtros
        selected_emp = st.sidebar.multiselect("Filtrar Empresa", get_options('EMPRESA'), default=get_options('EMPRESA'))
        selected_loc = st.sidebar.multiselect("Filtrar Localidad", get_options('LOCALIDAD'), default=get_options('LOCALIDAD'))
        selected_area = st.sidebar.multiselect("Filtrar Área", get_options('AREA'), default=get_options('AREA'))
        
        anios_validos = sorted([x for x in df_raw['AÑO_INGRESO'].unique() if x > 0], reverse=True)
        selected_anio = st.sidebar.multiselect("Año de Ingreso", anios_validos, default=anios_validos)

        # --- APLICACIÓN CRÍTICA DE FILTROS ---
        # Paso 1: Solo activos
        mask_activos = (df_raw['ESTADO'] == 'ACTIVO')
        
        # Paso 2: Aplicar multiselects uno por uno
        mask_final = (
            mask_activos &
            (df_raw['EMPRESA'].isin(selected_emp)) &
            (df_raw['LOCALIDAD'].isin(selected_loc)) &
            (df_raw['AREA'].isin(selected_area)) &
            (df_raw['AÑO_INGRESO'].isin(selected_anio))
        )
        
        df_final = df_raw[mask_final].copy()

        # --- VISUALIZACIÓN ---
        st.title("👥 Análisis de Dotación")
        
        total = len(df_final)
        
        if total > 0:
            c1, c2, c3 = st.columns(3)
            c1.metric("Dotación Filtrada", f"{total} pers.")
            c2.metric("Empresas Seleccionadas", f"{len(selected_emp)}")
            c3.metric("Localidades", df_final['LOCALIDAD'].nunique())

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Headcount por Empresa")
                res_emp = df_final.groupby('EMPRESA').size().reset_index(name='Cant')
                st.plotly_chart(px.bar(res_emp, x='EMPRESA', y='Cant', text_auto=True), use_container_width=True)
            
            with col_b:
                st.subheader("Distribución por Localidad")
                st.plotly_chart(px.pie(df_final, names='LOCALIDAD', hole=0.3), use_container_width=True)

            st.subheader("Estructura Jerárquica")
            # El Sunburst ahora solo mostrará lo que esté en df_final
            fig_sun = px.sunburst(df_final, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.error("⚠️ No hay datos para esta combinación de filtros.")
            st.info("Prueba seleccionando todas las empresas o áreas en el panel izquierdo.")

except Exception as e:
    st.error(f"Error: {e}")
