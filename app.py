import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Human Capital Analytics | Grupo Cenoa", layout="wide")

# Diseño estético
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN Y CARGA DE DATOS
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    # Leer el CSV
    df = pd.read_csv(CSV_URL)
    
    # 1. Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'ANTIGÜEDAD': 'ANTIGUEDAD',
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA DE EGRESO': 'FECHA_EGRESO'
    })
    
    # 2. Limpieza de Guiones y Vacíos en TODA la base
    # Reemplazamos "-" por NaN (Not a Number) para que no rompa los filtros
    df = df.replace(['-', ' -', '- ', 'nan', 'NAN', '0'], np.nan)
    
    # 3. Limpieza de columnas de texto (Mayúsculas y quitar espacios)
    columnas_texto = ['ESTADO', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SEXO', 'JERARQUIA', 'SUB AREA', 'PUESTO']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # 4. Procesamiento de FECHAS (Blindado)
    # pd.to_datetime con errors='coerce' convierte los "-" o vacíos en NaT automáticamente
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA DE INGRESO'] = pd.to_datetime(df['FECHA DE INGRESO'], errors='coerce')
        # Extraer año solo si la fecha es válida, sino poner 0
        df['AÑO_INGRESO'] = df['FECHA DE INGRESO'].dt.year.fillna(0).astype(int)
    
    if 'FECHA_EGRESO' in df.columns:
        df['FECHA_EGRESO'] = pd.to_datetime(df['FECHA_EGRESO'], errors='coerce')
        
    # 5. Limpieza de EDAD (Extraer solo el número)
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].astype(str).str.extract(r'(\d+)').astype(float)
        
    return df

try:
    df = load_data()

    # --- PANEL IZQUIERDO: NAVEGACIÓN ---
    st.sidebar.title("Módulos RRHH")
    categoria = st.sidebar.radio("Seleccione Dimensión:", ["1- DOTACION", "2- ROTACION", "3- AUSENTISMO"])

    if categoria == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Dotación")
        
        # Listas para filtros (excluyendo 'NAN')
        def get_clean_list(column):
            return sorted([x for x in df[column].unique() if x not in ['NAN', 'NONE', 'nan', None]])

        list_emp = get_clean_list('EMPRESA')
        emp_sel = st.sidebar.multiselect("Empresa", list_emp, default=list_emp)
        
        list_loc = get_clean_list('LOCALIDAD')
        loc_sel = st.sidebar.multiselect("Localidad", list_loc, default=loc_sel if 'loc_sel' in locals() else list_loc)
        
        list_area = get_clean_list('AREA')
        area_sel = st.sidebar.multiselect("Área", list_area, default=area_sel if 'area_sel' in locals() else list_area)
        
        list_anio = sorted([int(x) for x in df['AÑO_INGRESO'].unique() if x > 0], reverse=True)
        anio_sel = st.sidebar.multiselect("Año de Ingreso", list_anio, default=list_anio)

        # APLICAR FILTROS (Solo Activos)
        # Usamos .query o filtros directos asegurando que no haya conflictos de tipos
        df_f = df[
            (df['ESTADO'] == 'ACTIVO') &
            (df['EMPRESA'].isin(emp_sel)) &
            (df['LOCALIDAD'].isin(loc_sel)) &
            (df['AREA'].isin(area_sel)) &
            (df['AÑO_INGRESO'].isin(anio_sel))
        ].copy()

        # --- INTERFAZ VISUAL ---
        st.title("👥 Análisis de Dotación (Headcount)")
        
        total = len(df_f)
        
        if total > 0:
            # Métricas Principales
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Dotación Activa", f"{total}", "Personas")
            
            promedio_edad = df_f['EDAD_NUM'].mean()
            k2.metric("Edad Promedio", f"{promedio_edad:.1f}" if not np.isnan(promedio_edad) else "N/D")
            
            mujeres = len(df_f[df_f['SEXO'] == 'F'])
            k3.metric("Género", f"{(mujeres/total*100):.1f}% Mujeres", f"{mujeres} F")
            
            k4.metric("Localidades", df_f['LOCALIDAD'].nunique())

            st.divider()

            # Gráficos Profesionales
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Distribución por Empresa")
                fig_emp = px.bar(df_f.groupby('EMPRESA').size().reset_index(name='Cant'), 
                                 x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA')
                st.plotly_chart(fig_emp, use_container_width=True)
                
            with c2:
                st.subheader("Dotación por Localidad")
                fig_loc = px.pie(df_f, names='LOCALIDAD', hole=0.4)
                st.plotly_chart(fig_loc, use_container_width=True)

            st.subheader("Estructura Jerárquica y Puestos")
            fig_sun = px.sunburst(df_f, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            st.plotly_chart(fig_sun, use_container_width=True)

            with st.expander("Ver Listado Detallado"):
                st.dataframe(df_f[['CUIL', 'APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'JEFE DIRECTO']], use_container_width=True)
        else:
            st.warning("No se encontraron colaboradores activos con los filtros seleccionados.")

    elif categoria == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo listo para recibir lógica de bajas.")

    elif categoria == "3- AUSENTISMO":
        st.title("🤒 Control de Ausentismo")
        st.info("Módulo listo para recibir datos de novedades.")

except Exception as e:
    st.error(f"Se produjo un error en la carga: {e}")
    st.info("Sugerencia: Revisa que las columnas de fechas no tengan textos largos o errores de carga en el Excel.")
