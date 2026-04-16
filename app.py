import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración inicial
st.set_page_config(page_title="HR Dashboard Estratégico", page_icon="📊", layout="wide")
st.title("📊 Dashboard Estratégico de HR Analytics")
st.markdown("Orientado a medición de Eficiencia, Productividad y Fuga de Talento")

# 2. Conexión de Datos
@st.cache_data(ttl=3600) 
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhx1mzO6cExRA4rtOkPx3t7CU1Ubvy0GVegOZpKv2KYe8E3vf6Z-Vb6y4xYjlLdg/pub?output=xlsx"
    try:
        xls = pd.ExcelFile(url)
        nombres_solapas = xls.sheet_names
        
        # Búsqueda flexible de solapas
        nombre_dot = next((s for s in nombres_solapas if 'DOTACION' in s.upper()), None)
        nombre_rot = next((s for s in nombres_solapas if 'ROTACION' in s.upper()), None)
        nombre_baj = next((s for s in nombres_solapas if 'BAJAS' in s.upper()), None)

        if not nombre_dot:
            st.error(f"Falta solapa 'DOTACION'. Solapas leídas: {nombres_solapas}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        df_dotacion = pd.read_excel(url, sheet_name=nombre_dot)
        df_rotacion = pd.read_excel(url, sheet_name=nombre_rot)
        df_bajas = pd.read_excel(url, sheet_name=nombre_baj)
        
        # SOLUCIÓN DEL ERROR: Forzamos a que todos los encabezados sean texto
        df_dotacion.columns = df_dotacion.columns.astype(str)
        df_rotacion.columns = df_rotacion.columns.astype(str)
        df_bajas.columns = df_bajas.columns.astype(str)
        
        return df_dotacion, df_rotacion, df_bajas
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_dot, df_rot, df_baj = load_data()

# 3. Construcción del Dashboard
if not df_dot.empty:
    st.sidebar.header("Filtros Estratégicos")
    
    # Búsqueda de columnas dinámicas para evitar errores
    cols_dot = [c.lower() for c in df_dot.columns]
    
    # Detectamos la columna de Año y Unidad dinámicamente
    año_col = df_dot.columns[cols_dot.index(next(c for c in cols_dot if 'año' in c or 'anio' in c))] if any('año' in c or 'anio' in c for c in cols_dot) else None
    un_col = df_dot.columns[cols_dot.index(next(c for c in cols_dot if 'unidad' in c or 'sucursal' in c))] if any('unidad' in c or 'sucursal' in c for c in cols_dot) else None
    
    # Filtros
    if año_col and un_col:
        filtro_anios = st.sidebar.multiselect("Año", options=df_dot[año_col].dropna().unique(), default=df_dot[año_col].dropna().unique())
        filtro_un = st.sidebar.multiselect("Unidad de Negocio", options=df_dot[un_col].dropna().unique(), default=df_dot[un_col].dropna().unique())
        
        # Aplicamos filtros
        df_dot = df_dot[(df_dot[año_col].isin(filtro_anios)) & (df_dot[un_col].isin(filtro_un))]
        if not df_baj.empty and año_col in df_baj.columns and un_col in df_baj.columns:
            df_baj = df_baj[(df_baj[año_col].isin(filtro_anios)) & (df_baj[un_col].isin(filtro_un))]
            
    # Overview
    st.subheader("Indicadores Principales")
    col1, col2, col3, col4 = st.columns(4)
    
    # Cálculos puros
    total_dotacion = len(df_dot)
    total_bajas = len(df_baj) if not df_baj.empty else 0
    rotacion_total = (total_bajas / total_dotacion * 100) if total_dotacion > 0 else 0
    
    with col1: st.metric("Dotación Total Activa", f"{total_dotacion:,.0f}")
    with col2: st.metric("Rotación Total", f"{rotacion_total:.1f}%")
    
    st.markdown("---")
    
    # Diagnóstico de datos limpios
    st.success("✅ Conexión exitosa. Mostrando vista previa de las columnas para armar los gráficos finales:")
    st.write("**Columnas detectadas en Dotación:**", list(df_dot.columns))
    st.write("**Columnas detectadas en Bajas:**", list(df_baj.columns) if not df_baj.empty else "Sin datos")

else:
    st.warning("Esperando datos...")
