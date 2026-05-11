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
    try:
        # Cargamos todo como texto
        df = pd.read_csv(CSV_URL, dtype=str)
        
        # LIMPIEZA CRÍTICA DE ENCABEZADOS: Quita espacios, saltos de línea y pasa a MAYÚSCULAS
        df.columns = df.columns.astype(str).str.strip().str.replace('\n', ' ').str.upper()
        
        # Mapeo de nombres (Aseguramos que 'FECHA DE INGRESO' y 'AREA' existan)
        df = df.rename(columns={
            'ÁREA': 'AREA', 
            'F. INGR': 'FECHA DE INGRESO',
            'FECHA INGRESO': 'FECHA DE INGRESO'
        })
        
        # Reemplazo de basura
        df = df.replace(['-', ' -', '- ', '0', '0.0', 'NAN', 'NONE', ''], np.nan)
        
        # Normalización de contenidos
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

        # Limpieza de EDAD
        if 'EDAD' in df.columns:
            df['EDAD_NUM'] = df['EDAD'].str.extract('(\d+)').astype(float)

        # Procesamiento de FECHA DE INGRESO
        if 'FECHA DE INGRESO' in df.columns:
            fechas = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
            df['ANIO_ING_STR'] = fechas.dt.year.fillna(0).astype(int).astype(str)
        else:
            df['ANIO_ING_STR'] = "0"

        return df
    except Exception as e:
        st.error(f"Error al leer el CSV: {e}")
        return pd.DataFrame()

try:
    df_raw = load_data()

    if not df_raw.empty:
        # --- VERIFICACIÓN DE COLUMNAS ---
        columnas_necesarias = ['EMPRESA', 'LOCALIDAD', 'AREA', 'ESTADO']
        columnas_faltantes = [c for c in columnas_necesarias if c not in df_raw.columns]

        if columnas_faltantes:
            st.error(f"⚠️ No se encuentran las columnas: {', '.join(columnas_faltantes)}")
            st.info(f"Columnas detectadas en tu Excel: {list(df_raw.columns)}")
        else:
            # --- PANEL LATERAL ---
            st.sidebar.title("📈 Gestión Human Capital")
            modulo = st.sidebar.radio("Dimensión:", ["1- DOTACION", "2- ROTACION"])

            if modulo == "1- DOTACION":
                st.sidebar.divider()
                
                def get_opts(col):
                    return sorted([x for x in df_raw[col].unique() if x not in ['NAN', '0', 'NONE']])

                sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
                sel_loc = st.sidebar.multiselect("Localidad", get_opts('LOCALIDAD'), default=get_opts('LOCALIDAD'))
                sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))
                
                anios = sorted([x for x in df_raw.get('ANIO_ING_STR', ['0']).unique() if x != '0'], reverse=True)
                sel_anio = st.sidebar.multiselect("Año de Ingreso", anios, default=anios)

                # FILTRADO
                df_f = df_raw[df_raw['ESTADO'] == 'ACTIVO'].copy()
                
                if sel_emp: df_f = df_f[df_f['EMPRESA'].isin(sel_emp)]
                if sel_loc: df_f = df_f[df_f['LOCALIDAD'].isin(sel_loc)]
                if sel_area: df_f = df_f[df_f['AREA'].isin(sel_area)]
                if sel_anio: df_f = df_f[df_f['ANIO_ING_STR'].isin(sel_anio)]

                # DASHBOARD
                st.title("👥 Panel de Dotación Activa")
                
                if not df_f.empty:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Dotación", len(df_f))
                    m2.metric("Sedes", df_f['LOCALIDAD'].nunique())
                    m3.metric("Edad Promedio", f"{df_f['EDAD_NUM'].mean():.1f}" if 'EDAD_NUM' in df_f.columns else "S/D")

                    st.divider()
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("Por Empresa")
                        st.plotly_chart(px.bar(df_f.groupby('EMPRESA').size().reset_index(name='Cant'), x='EMPRESA', y='Cant', text_auto=True), use_container_width=True)
                    with c2:
                        st.subheader("Por Localidad")
                        st.plotly_chart(px.pie(df_f, names='LOCALIDAD', hole=0.4), use_container_width=True)

                    st.subheader("Estructura Organizacional")
                    fig_sun = px.sunburst(df_f, path=['EMPRESA', 'AREA', 'SUB AREA', 'PUESTO'], color='EMPRESA')
                    st.plotly_chart(fig_sun, use_container_width=True)
                else:
                    st.warning("No hay datos para los filtros seleccionados.")
    else:
        st.error("El archivo está vacío o no se pudo cargar.")

except Exception as e:
    st.error(f"Error crítico: {e}")
