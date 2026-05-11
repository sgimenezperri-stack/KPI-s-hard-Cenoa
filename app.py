import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Human Capital Analytics | Grupo Cenoa", layout="wide")

# CORRECCIÓN: unsafe_allow_html=True
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
    
    # Normalización estricta de columnas
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'ANTIGÜEDAD': 'ANTIGUEDAD',
        'F. INGR': 'FECHA DE INGRESO'
    })
    
    # Limpieza profunda: Quitar espacios en blanco al inicio y final de los textos clave
    if 'ESTADO' in df.columns:
        df['ESTADO'] = df['ESTADO'].astype(str).str.strip().str.upper()
    if 'EMPRESA' in df.columns:
        df['EMPRESA'] = df['EMPRESA'].astype(str).str.strip()
    
    # Eliminar filas basura (vacías)
    df = df[df['EMPRESA'] != 'nan']
    df = df[df['EMPRESA'] != '0']
    
    # Procesamiento de Fechas
    if 'FECHA DE INGRESO' in df.columns:
        df['FECHA DE INGRESO'] = pd.to_datetime(df['FECHA DE INGRESO'], errors='coerce')
        df['AÑO_INGRESO'] = df['FECHA DE INGRESO'].dt.year.fillna(0).astype(int)
        
    # Limpieza de EDAD
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].astype(str).str.extract(r'(\d+)').astype(float)
        
    return df

try:
    df = load_data()

    # --- PANEL IZQUIERDO: NAVEGACIÓN ---
    st.sidebar.image("https://via.placeholder.com/200x80?text=GRUPO+CENOA", use_column_width=True)
    st.sidebar.title("Módulos RRHH")
    categoria = st.sidebar.radio("Seleccione Dimensión:", ["1- DOTACION", "2- ROTACION", "3- AUSENTISMO"])

    # --- LÓGICA DEL MÓDULO 1: DOTACIÓN ---
    if categoria == "1- DOTACION":
        st.sidebar.divider()
        st.sidebar.subheader("Filtros de Dotación")
        
        # Filtros Dinámicos limpios
        list_emp = sorted(df['EMPRESA'].unique())
        emp_sel = st.sidebar.multiselect("Empresa", list_emp, default=list_emp)
        
        list_loc = sorted([x for x in df['LOCALIDAD'].astype(str).str.strip().unique() if x != 'nan' and x != '0'])
        loc_sel = st.sidebar.multiselect("Localidad", list_loc, default=list_loc)
        
        list_area = sorted([x for x in df['AREA'].astype(str).str.strip().unique() if x != 'nan' and x != '0'])
        area_sel = st.sidebar.multiselect("Área", list_area, default=list_area)
        
        list_anio = sorted([x for x in df['AÑO_INGRESO'].unique() if x > 0], reverse=True)
        anio_sel = st.sidebar.multiselect("Año de Ingreso", list_anio, default=list_anio)

        # Aplicar Filtros (Solo Activos) - Ya normalizados a 'ACTIVO' sin espacios
        df_activos = df[
            (df['ESTADO'] == 'ACTIVO') &
            (df['EMPRESA'].isin(emp_sel)) &
            (df['LOCALIDAD'].str.strip().isin(loc_sel)) &
            (df['AREA'].str.strip().isin(area_sel)) &
            (df['AÑO_INGRESO'].isin(anio_sel))
        ].copy()

        # --- INTERFAZ VISUAL: DOTACIÓN ---
        st.title("👥 Análisis de Dotación (Headcount)")
        
        # 1. TARJETAS DE KPIs
        total_pax = len(df_activos)
        edad_promedio = df_activos['EDAD_NUM'].mean() if 'EDAD_NUM' in df_activos.columns else 0
        hombres = len(df_activos[df_activos['SEXO'].astype(str).str.strip().str.upper() == 'M'])
        mujeres = len(df_activos[df_activos['SEXO'].astype(str).str.strip().str.upper() == 'F'])
        pct_mujeres = (mujeres / total_pax * 100) if total_pax > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Dotación Activa", f"{total_pax}", "Colaboradores")
        k2.metric("Edad Promedio", f"{edad_promedio:.1f} años")
        k3.metric("Diversidad de Género", f"{pct_mujeres:.1f}% Mujeres", f"{mujeres} F / {hombres} M")
        k4.metric("Convenios Activos", df_activos['CONVENIO'].nunique(), "Tipos de Contrato")

        st.divider()

        # Si hay datos para mostrar, dibuja los gráficos
        if total_pax > 0:
            # 2. GRÁFICOS ESTRUCTURALES
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.subheader("Por Empresa")
                fig_emp = px.bar(df_activos.groupby('EMPRESA').size().reset_index(name='Total'),
                                 x='EMPRESA', y='Total', color='EMPRESA', text_auto=True,
                                 color_discrete_sequence=px.colors.qualitative.Bold)
                fig_emp.update_layout(showlegend=False, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_emp, use_container_width=True)

            with c2:
                st.subheader("Por Localidad")
                fig_loc = px.pie(df_activos, names='LOCALIDAD', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig_loc, use_container_width=True)
                
            with c3:
                st.subheader("Por Generación")
                fig_gen = px.pie(df_activos, names='GENERACION', 
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_gen, use_container_width=True)

            # 3. ANÁLISIS DE PUESTOS Y JERARQUÍA
            st.divider()
            c4, c5 = st.columns([1.5, 1])

            with c4:
                st.subheader("Top Puestos por Volumen")
                puestos = df_activos.groupby('PUESTO').size().reset_index(name='Total').sort_values('Total', ascending=False).head(12)
                fig_puesto = px.bar(puestos, x='Total', y='PUESTO', orientation='h', 
                                    color='Total', color_continuous_scale='Blues', text_auto=True)
                fig_puesto.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_puesto, use_container_width=True)

            with c5:
                st.subheader("Pirámide Jerárquica")
                jerarquia = df_activos.groupby('JERARQUIA').size().reset_index(name='Total').sort_values('Total', ascending=False)
                fig_jer = px.funnel(jerarquia, y='JERARQUIA', x='Total', color_discrete_sequence=['#1f77b4'])
                st.plotly_chart(fig_jer, use_container_width=True)

            # 4. EXPLORADOR ORGANIZACIONAL
            st.subheader("Explorador de Estructura: Área y Sub Área")
            st.info("Gráfico interactivo: Clic en el centro para expandir la estructura.")
            fig_sun = px.sunburst(df_activos, path=['EMPRESA', 'AREA', 'SUB AREA'], 
                                 color='EMPRESA', color_discrete_sequence=px.colors.qualitative.Vivid)
            fig_sun.update_layout(height=500, margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig_sun, use_container_width=True)
            
            # 5. VISTA DE DATOS
            with st.expander("Ver Maestro de Colaboradores Filtrado"):
                st.dataframe(df_activos[['CUIL', 'APELLIDO Y NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO']], use_container_width=True)
        else:
            st.warning("No hay colaboradores activos que coincidan con los filtros seleccionados.")

    # --- LÓGICA DEL MÓDULO 2: ROTACIÓN ---
    elif categoria == "2- ROTACION":
        st.title("🔄 Análisis de Rotación")
        st.info("Módulo en construcción.")

    # --- LÓGICA DEL MÓDULO 3: AUSENTISMO ---
    elif categoria == "3- AUSENTISMO":
        st.title("🤒 Control de Ausentismo")
        st.info("Módulo en construcción.")

except Exception as e:
    st.error(f"Error al procesar la Base de Datos: {e}")
