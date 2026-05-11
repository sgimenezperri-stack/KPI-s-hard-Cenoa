import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

# Estilo profesional corregido
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA Y LIMPIEZA PROFUNDA
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    # Cargar datos tratando todo como texto inicialmente para evitar errores de tipo automáticos
    df = pd.read_csv(CSV_URL, dtype=str)
    
    # Normalizar títulos
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={'ÁREA': 'AREA', 'F. INGR': 'FECHA DE INGRESO'})

    # REEMPLAZO CRÍTICO: Convertir guiones y ceros de texto en valores Nulos reales (NaN)
    df = df.replace(['-', ' -', '- ', '0', 'nan', 'NAN', 'None', ''], np.nan)

    # Limpiar espacios en blanco en columnas de texto
    for col in df.columns:
        df[col] = df[col].str.strip()

    # PROCESAMIENTO SEGURO DE FECHAS
    # errors='coerce' transformará cualquier "-" que haya sobrevivido en NaT (Not a Time), que no rompe comparaciones
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA DE INGRESO'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
        df['AÑO_INGRESO'] = df['FECHA DE INGRESO'].dt.year.fillna(0).astype(int)
    
    if 'FECHA DE EGRESO' in df.columns:
        df['FECHA DE EGRESO'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')

    # PROCESAMIENTO DE EDAD
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)

    return df

try:
    df = load_data()

    # --- NAVEGACIÓN ---
    st.sidebar.title("Módulos RRHH")
    modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION", "3- AUSENTISMO"])

    if modulo == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros")

        # Función para obtener listas de filtros sin valores nulos
        def clean_options(col):
            return sorted([x for x in df[col].unique() if pd.notna(x)])

        list_emp = clean_options('EMPRESA')
        emp_sel = st.sidebar.multiselect("Empresa", list_emp, default=list_emp)

        list_loc = clean_options('LOCALIDAD')
        loc_sel = st.sidebar.multiselect("Localidad", list_loc, default=list_loc)

        list_area = clean_options('AREA')
        area_sel = st.sidebar.multiselect("Área", list_area, default=list_area)

        # FILTRADO SEGURO (Solo Activos)
        # Forzamos comparación de strings para evitar el TypeError
        df_activos = df[
            (df['ESTADO'].str.upper() == 'ACTIVO') &
            (df['EMPRESA'].isin(emp_sel)) &
            (df['LOCALIDAD'].isin(loc_sel)) &
            (df['AREA'].isin(area_sel))
        ].copy()

        # --- INTERFAZ ---
        st.title("👥 Análisis de Dotación (Headcount)")
        
        total = len(df_activos)
        
        if total > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dotación Activa", f"{total}", "Personas")
            
            # Cálculo seguro de promedio ignorando nulos
            edad_prom = df_activos['EDAD_NUM'].mean()
            c2.metric("Edad Promedio", f"{edad_prom:.1f}" if pd.notna(edad_prom) else "S/D")
            
            mujeres = len(df_activos[df_activos['SEXO'].str.upper() == 'F'])
            c3.metric("Género", f"{(mujeres/total*100):.1f}% Muj.", f"{mujeres} F")
            c4.metric("Localidades", df_activos['LOCALIDAD'].nunique())

            st.divider()

            # Gráficos de barras y torta
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Distribución por Empresa")
                fig_emp = px.bar(df_activos.groupby('EMPRESA').size().reset_index(name='Cant'), 
                                 x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA')
                st.plotly_chart(fig_emp, use_container_width=True)
            with g2:
                st.subheader("Dotación por Localidad")
                fig_loc = px.pie(df_activos, names='LOCALIDAD', hole=0.4)
                st.plotly_chart(fig_loc, use_container_width=True)

            st.subheader("Estructura Organizacional (Área > Sub Área > Puesto)")
            fig_sun = px.sunburst(df_activos, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
            st.plotly_chart(fig_sun, use_container_width=True)

        else:
            st.warning("No se encontraron colaboradores con los filtros actuales.")

    elif modulo == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo configurado. Pendiente lógica de bajas.")

except Exception as e:
    st.error(f"Error detectado: {e}")
    st.info("Sugerencia: Si el error persiste, verifica que la columna 'ESTADO' no contenga fórmulas de Excel rotas.")
