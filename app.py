import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# Estilo para tarjetas de métricas
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #efefef; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (CONEXIÓN DIRECTA)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    # Cargamos como texto para evitar errores de tipo
    df = pd.read_csv(CSV_URL, dtype=str)
    
    # Normalizar encabezados (quitar espacios y a Mayúsculas)
    df.columns = df.columns.str.strip().str.upper()
    
    # Limpieza masiva de basura (guiones, ceros de texto, etc.)
    df = df.replace(['-', ' -', '- ', '0', '0.0', 'NAN', 'NONE', ''], np.nan)
    
    # Normalizar contenidos de texto para que los filtros no fallen
    columnas_texto = ['ESTADO', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'SEXO', 'GENERACION', 'JERARQUIA']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # TRATAMIENTO DE EDAD: Extraer número de "XX Años"
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)

    # TRATAMIENTO DE FECHA DE INGRESO
    if 'FECHA DE INGRESO' in df.columns:
        # errors='coerce' convierte lo que no es fecha (como guiones) en NaT (vacío legal)
        fechas = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        df['ANIO_ING_STR'] = fechas.dt.year.fillna(0).astype(int).astype(str)
    
    return df

try:
    df_raw = load_data()

    # --- MENÚ LATERAL ---
    st.sidebar.title("📈 Gestión Human Capital")
    modulo = st.sidebar.radio("Dimensión de Análisis:", ["1- DOTACION", "2- ROTACION", "3- AUSENTISMO"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Dotación")

        # Función para obtener listas de filtros sin nulos
        def get_opts(col):
            return sorted([x for x in df_raw[col].unique() if pd.notna(x) and x not in ['NAN', '0', 'NONE']])

        sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
        sel_loc = st.sidebar.multiselect("Localidad", get_opts('LOCALIDAD'), default=get_opts('LOCALIDAD'))
        sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))
        
        anios = sorted([x for x in df_raw['ANIO_ING_STR'].unique() if x != '0'], reverse=True)
        sel_anio = st.sidebar.multiselect("Año de Ingreso", anios, default=anios)

        # --- APLICACIÓN DE FILTROS PASO A PASO ---
        # 1. Solo ACTIVO (según tu requerimiento)
        df_f = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
        
        # 2. Filtros de usuario
        if sel_emp: df_f = df_f[df_f['EMPRESA'].isin(sel_emp)]
        if sel_loc: df_f = df_f[df_f['LOCALIDAD'].isin(sel_loc)]
        if sel_area: df_f = df_f[df_f['AREA'].isin(sel_area)]
        if sel_anio: df_f = df_f[df_f['ANIO_ING_STR'].isin(sel_anio)]

        # --- VISUALIZACIÓN ---
        st.title("👥 Panel de Dotación Activa")
        
        if not df_f.empty:
            # Métricas principales
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dotación Total", len(df_f), "Colaboradores")
            
            prom_edad = df_f['EDAD_NUM'].mean()
            c2.metric("Edad Promedio", f"{prom_edad:.1f} años" if pd.notna(prom_edad) else "S/D")
            
            mujeres = len(df_f[df_f['SEXO'] == 'F'])
            c3.metric("Género", f"{(mujeres/len(df_f)*100):.1f}% Muj.", f"{mujeres} F")
            c4.metric("Sedes", df_f['LOCALIDAD'].nunique())

            st.divider()

            # Distribución Geográfica y por Empresa
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Headcount por Concesionaria")
                fig_emp = px.bar(df_f.groupby('EMPRESA').size().reset_index(name='Cant'), 
                                 x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA')
                st.plotly_chart(fig_emp, use_container_width=True)
            with col2:
                st.subheader("Distribución por Localidad")
                fig_loc = px.pie(df_f, names='LOCALIDAD', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_loc, use_container_width=True)

            # Estructura Organizacional
            st.subheader("Explorador de Estructura: Área > Sub Área > Puesto")
            fig_sun = px.sunburst(df_f, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            fig_sun.update_layout(height=600)
            st.plotly_chart(fig_sun, use_container_width=True)

            # Detalle de datos
            with st.expander("Ver nómina completa filtrada"):
                st.dataframe(df_f[['CUIL', 'APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'JERARQUIA']], use_container_width=True)
        else:
            st.warning("⚠️ No se encontraron colaboradores activos con los filtros seleccionados.")

    elif modulo == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo configurado. Utilizará 'INACTIVO' en columna AU y 'FECHA DE EGRESO' en columna AV.")

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
