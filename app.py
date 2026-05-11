import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Human Capital Analytics | Grupo Cenoa", layout="wide")

# CORRECCIÓN DE ESTILO (unsafe_allow_html=True)
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
    df = pd.read_csv(CSV_URL)
    
    # Normalización de columnas
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'ANTIGÜEDAD': 'ANTIGUEDAD',
        'F. INGR': 'FECHA DE INGRESO'
    })
    
    # Limpieza de ESTADO y EMPRESA para evitar el error de "0" dotación
    for col in ['ESTADO', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SEXO', 'JERARQUIA', 'SUB AREA']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    
    # Eliminar filas basura
    df = df[~df['EMPRESA'].isin(['NAN', '0', ''])]
    
    # --- LIMPIEZA DE FECHAS (Solución al TypeError) ---
    def clean_date(date_val):
        # Si es un número o texto que no es fecha, lo hace NaT (No es una fecha)
        return pd.to_datetime(date_val, errors='coerce')

    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA DE INGRESO'] = df['FECHA DE INGRESO'].apply(clean_date)
        df['AÑO_INGRESO'] = df['FECHA DE INGRESO'].dt.year.fillna(0).astype(int)
    
    if 'FECHA DE EGRESO' in df.columns:
        df['FECHA DE EGRESO'] = df['FECHA DE EGRESO'].apply(clean_date)
        
    # Limpieza de EDAD
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
        
        # Filtros con listas limpias
        list_emp = sorted([x for x in df['EMPRESA'].unique() if x not in ['NAN', '0']])
        emp_sel = st.sidebar.multiselect("Empresa", list_emp, default=list_emp)
        
        list_loc = sorted([x for x in df['LOCALIDAD'].unique() if x not in ['NAN', '0']])
        loc_sel = st.sidebar.multiselect("Localidad", list_loc, default=list_loc)
        
        list_area = sorted([x for x in df['AREA'].unique() if x not in ['NAN', '0']])
        area_sel = st.sidebar.multiselect("Área", list_area, default=list_area)
        
        list_anio = sorted([x for x in df['AÑO_INGRESO'].unique() if x > 0], reverse=True)
        anio_sel = st.sidebar.multiselect("Año de Ingreso", list_anio, default=list_anio)

        # Aplicar Filtros (SOLO ACTIVO)
        df_activos = df[
            (df['ESTADO'] == 'ACTIVO') &
            (df['EMPRESA'].isin(emp_sel)) &
            (df['LOCALIDAD'].isin(loc_sel)) &
            (df['AREA'].isin(area_sel)) &
            (df['AÑO_INGRESO'].isin(anio_sel))
        ].copy()

        # --- INTERFAZ VISUAL ---
        st.title("👥 Análisis de Dotación (Headcount)")
        
        total_pax = len(df_activos)
        
        if total_pax > 0:
            # Tarjetas de KPI
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Dotación Activa", f"{total_pax}", "Colaboradores")
            k2.metric("Edad Promedio", f"{df_activos['EDAD_NUM'].mean():.1f}" if 'EDAD_NUM' in df_activos.columns else "N/A")
            mujeres = len(df_activos[df_activos['SEXO'] == 'F'])
            k3.metric("Género", f"{(mujeres/total_pax*100):.1f}% Muj.", f"{mujeres} F")
            k4.metric("Sedes", df_activos['LOCALIDAD'].nunique())

            st.divider()

            # Gráficos
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Por Empresa")
                st.plotly_chart(px.bar(df_activos.groupby('EMPRESA').size().reset_index(name='T'), 
                                       x='EMPRESA', y='T', text_auto=True), use_container_width=True)
            with c2:
                st.subheader("Por Localidad")
                st.plotly_chart(px.pie(df_activos, names='LOCALIDAD', hole=0.4), use_container_width=True)

            st.subheader("Explorador de Estructura")
            st.plotly_chart(px.sunburst(df_activos, path=['EMPRESA', 'AREA', 'SUB AREA'], color='EMPRESA'), use_container_width=True)

            with st.expander("Ver Datos Detallados"):
                st.dataframe(df_activos[['CUIL', 'APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO']], use_container_width=True)
        else:
            st.warning("No hay datos para los filtros seleccionados.")

    # Módulos 2 y 3 (Estructura base)
    elif categoria == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo en desarrollo.")
    elif categoria == "3- AUSENTISMO":
        st.title("🤒 Control de Ausentismo")
        st.info("Módulo en desarrollo.")

except Exception as e:
    st.error(f"Error al procesar la Base de Datos: {e}")
