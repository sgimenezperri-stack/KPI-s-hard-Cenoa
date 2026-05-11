import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# 2. CARGA DE DATOS (URL DE TU GOOGLE SHEETS)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    # Cargamos TODO como objeto (texto) para evitar el error de float vs str
    df = pd.read_csv(CSV_URL, dtype=object)
    
    # Limpiar nombres de columnas (Quitar espacios y a Mayúsculas)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    
    # Reemplazo de guiones y vacíos por Nulo Real (NaN)
    df = df.replace(['-', ' -', '- ', '0', '0.0', 'NAN', 'NONE', ''], np.nan)
    
    # Normalizar contenidos de texto
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()

    # TRATAMIENTO DE EDAD: Extraer solo el número
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)

    # TRATAMIENTO DE FECHA DE INGRESO (Para el filtro de Año)
    if 'FECHA DE INGRESO' in df.columns:
        # Convertimos a fecha, si falla queda como NaT (vacio)
        fechas_temp = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        # Guardamos el año como texto plano para evitar el error de comparación
        df['ANIO_FILTRO'] = fechas_temp.dt.year.fillna(0).astype(int).astype(str)
    else:
        df['ANIO_FILTRO'] = "0"
    
    return df

try:
    df_raw = load_data()

    # --- PANEL LATERAL ---
    st.sidebar.title("📈 Gestión Human Capital")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Dotación")

        # Función para listas de filtros sin basura
        def get_clean_opts(col):
            return sorted([x for x in df_raw[col].unique() if x not in ['NAN', '0', 'NONE', '0.0']])

        # Selectores
        f_emp = st.sidebar.multiselect("Empresa", get_clean_opts('EMPRESA'), default=get_clean_opts('EMPRESA'))
        f_loc = st.sidebar.multiselect("Localidad", get_clean_opts('LOCALIDAD'), default=get_clean_opts('LOCALIDAD'))
        f_area = st.sidebar.multiselect("Área", get_clean_opts('AREA'), default=get_clean_opts('AREA'))
        
        # Filtro de Año (usando nuestra columna de texto)
        anios_disponibles = sorted([x for x in df_raw['ANIO_FILTRO'].unique() if x != '0'], reverse=True)
        f_anio = st.sidebar.multiselect("Año de Ingreso", anios_disponibles, default=anios_disponibles)

        # --- APLICACIÓN DE FILTROS ---
        # Filtramos secuencialmente para evitar errores lógicos
        df_f = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
        
        if f_emp: df_f = df_f[df_f['EMPRESA'].isin(f_emp)]
        if f_loc: df_f = df_f[df_f['LOCALIDAD'].isin(f_loc)]
        if f_area: df_f = df_f[df_f['AREA'].isin(f_area)]
        if f_anio: df_f = df_f[df_f['ANIO_FILTRO'].isin(f_anio)]

        # --- INTERFAZ ---
        st.title("👥 Panel de Dotación Activa")
        
        if not df_f.empty:
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Dotación Total", len(df_f))
            c2.metric("Sedes", df_f['LOCALIDAD'].nunique())
            
            # Promedio de edad ignorando errores
            edad_prom = df_f['EDAD_NUM'].mean() if 'EDAD_NUM' in df_f.columns else 0
            c3.metric("Edad Promedio", f"{edad_prom:.1f} años" if not np.isnan(edad_prom) else "S/D")

            st.divider()

            # Gráficos
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Por Empresa")
                res_emp = df_f.groupby('EMPRESA').size().reset_index(name='Cant')
                st.plotly_chart(px.bar(res_emp, x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA'), use_container_width=True)
            with col2:
                st.subheader("Por Localidad")
                st.plotly_chart(px.pie(df_f, names='LOCALIDAD', hole=0.4), use_container_width=True)

            st.subheader("Estructura Organizacional")
            fig_sun = px.sunburst(df_f, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.warning("No hay datos para los filtros seleccionados.")

    elif modulo == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo configurado para usar 'INACTIVO' en columna AU.")

except Exception as e:
    st.error(f"Error detectado: {e}")
