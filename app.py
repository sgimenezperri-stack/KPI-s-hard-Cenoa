import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Configuración de página y Estilo
st.set_page_config(page_title="Cenoa HR Analytics", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. Función de Carga y Transformación de Datos
@st.cache_data(ttl=600)
def load_and_transform_dotacion():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhx1mzO6cExRA4rtOkPx3t7CU1Ubvy0GVegOZpKv2KYe8E3vf6Z-Vb6y4xYjlLdg/pub?output=xlsx"
    try:
        # Búsqueda flexible de la solapa
        xls = pd.ExcelFile(url)
        nombres_solapas = xls.sheet_names
        nombre_dot = next((s for s in nombres_solapas if 'DOTACION' in s.upper()), None)

        if not nombre_dot:
            st.error(f"Falta solapa de Dotación. Solapas leídas: {nombres_solapas}")
            return pd.DataFrame()

        df_raw = pd.read_excel(url, sheet_name=nombre_dot)
        
        # Limpieza inicial: Forzar nombres de columnas a string en mayúsculas
        df_raw.columns = [str(c).strip().upper() for c in df_raw.columns]
        
        # Eliminar filas vacías
        df_raw = df_raw.dropna(subset=[df_raw.columns[0]]) 
        
        df_raw = df_raw.rename(columns={
            df_raw.columns[0]: 'AÑO',
            df_raw.columns[1]: 'EMPRESA',
            df_raw.columns[2]: 'LOCALIDAD'
        })
        
        columnas_base = ['AÑO', 'EMPRESA', 'LOCALIDAD']
        
        # --- NUEVA LÓGICA DE FILTRADO DE MESES ---
        columnas_meses = []
        for c in df_raw.columns:
            # Debe tener un guion y no ser el promedio
            if '-' in c and 'PROMEDIO' not in c:
                
                # REGLA 1: Descartar si empieza con "1-" o "01-" (Ej: 1-10, 01-10)
                if c.startswith('1-') or c.startswith('01-'):
                    continue
                    
                # REGLA 2: Descartar si Pandas lo convirtió a fecha y es el día 01 (Ej: 2025-10-01 00:00:00)
                if '-01 00:' in c:
                    continue
                
                # Si sobrevive a los filtros, es el final del periodo. Lo guardamos.
                columnas_meses.append(c)
        
        df_filtrado = df_raw[columnas_base + columnas_meses].copy()
        
        # Transformar (Unpivot)
        df_melted = pd.melt(
            df_filtrado, 
            id_vars=columnas_base, 
            var_name='MES_PERIODO', 
            value_name='HEADCOUNT'
        )
        
        df_melted['AÑO'] = pd.to_numeric(df_melted['AÑO'], errors='coerce')
        df_melted['HEADCOUNT'] = pd.to_numeric(df_melted['HEADCOUNT'], errors='coerce').fillna(0)
        df_melted = df_melted.dropna(subset=['AÑO'])
        
        # Limpiar visualmente el nombre del mes si Pandas lo convirtió a fecha larga
        df_melted['MES_PERIODO'] = df_melted['MES_PERIODO'].apply(lambda x: x.split(' ')[0] if ' 00:00:00' in x else x)
        
        return df_melted

    except Exception as e:
        st.error(f"Error procesando Dotación: {e}")
        return pd.DataFrame()

# Cargar los datos transformados
df_dot = load_and_transform_dotacion()

# 3. Menú de Navegación Lateral
st.sidebar.image("https://www.cenoa.com.ar/wp-content/uploads/2021/05/logo-cenoa.png", width=150)
st.sidebar.title("Panel de Control")
categoria = st.sidebar.radio(
    "Seleccione Categoría:",
    ["📊 Dotación", "🔄 Rotación", "🚪 Bajas"],
    index=0
)

# 4. Filtros Globales
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globales")

if not df_dot.empty:
    anios_disponibles = sorted(df_dot['AÑO'].unique())
    selected_anio = st.sidebar.multiselect("Año", options=anios_disponibles, default=anios_disponibles)
    
    empresas_disponibles = sorted(df_dot['EMPRESA'].astype(str).unique())
    selected_empresa = st.sidebar.multiselect("Empresa", options=empresas_disponibles, default=empresas_disponibles)
    
    df_dot_filtered = df_dot[
        (df_dot['AÑO'].isin(selected_anio)) & 
        (df_dot['EMPRESA'].isin(selected_empresa))
    ]
    
    meses_disponibles = df_dot_filtered['MES_PERIODO'].unique()

# 5. Renderizado de la Sección Dotación
if "Dotación" in categoria:
    st.header("📋 Gestión de Dotación")
    
    if not df_dot.empty:
        st.markdown("### Seleccione el Mes de Análisis")
        mes_seleccionado = st.selectbox("Mes", options=meses_disponibles, index=len(meses_disponibles)-1)
        
        df_mes_actual = df_dot_filtered[df_dot_filtered['MES_PERIODO'] == mes_seleccionado]
        
        c1, c2, c3 = st.columns(3)
        total_headcount = df_mes_actual['HEADCOUNT'].sum()
        c1.metric("Headcount Total (Mes Seleccionado)", f"{total_headcount:,.0f}")
        
        st.markdown("---")
        colA, colB = st.columns(2)
        
        with colA:
            if total_headcount > 0:
                fig_empresa = px.pie(
                    df_mes_actual, 
                    values='HEADCOUNT', 
                    names='EMPRESA', 
                    title=f"Distribución por Empresa ({mes_seleccionado})",
                    hole=0.4
                )
                st.plotly_chart(fig_empresa, use_container_width=True)
            else:
                st.info(f"No hay headcount registrado para {mes_seleccionado}.")
                
        with colB:
            if total_headcount > 0:
                df_loc = df_mes_actual.groupby('LOCALIDAD')['HEADCOUNT'].sum().reset_index()
                df_loc = df_loc.sort_values(by='HEADCOUNT', ascending=True) 
                fig_loc = px.bar(
                    df_loc, 
                    x='HEADCOUNT', 
                    y='LOCALIDAD', 
                    orientation='h',
                    title=f"Headcount por Localidad ({mes_seleccionado})"
                )
                st.plotly_chart(fig_loc, use_container_width=True)

        st.markdown("---")
        st.markdown("### Evolución Histórica")
        df_tendencia = df_dot_filtered.groupby(['MES_PERIODO', 'AÑO'], sort=False)['HEADCOUNT'].sum().reset_index()
        fig_trend = px.line(
            df_tendencia, 
            x='MES_PERIODO', 
            y='HEADCOUNT', 
            title="Evolución de Dotación", 
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        with st.expander("Auditoría de Datos: Ver tabla procesada"):
            st.dataframe(df_dot_filtered)
            
    else:
        st.warning("No se pudieron cargar los datos de la solapa DOTACION. Verifique el formato.")

elif "Rotación" in categoria:
    st.header("🔄 Indicadores de Rotación")
    st.info("Sección en construcción. Pasaremos a esta solapa cuando confirmemos Dotación.")

elif "Bajas" in categoria:
    st.header("🚪 Análisis de Bajas")
    st.info("Sección en construcción. Pasaremos a esta solapa cuando confirmemos Rotación.")
