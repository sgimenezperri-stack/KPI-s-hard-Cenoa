import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página y Estilo
st.set_page_config(page_title="Cenoa HR Analytics", page_icon="📈", layout="wide")

# Forzamos un poco de estilo para que el menú lateral sea claro
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. Función de Carga de Datos Blindada
@st.cache_data(ttl=600)
def load_all_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhx1mzO6cExRA4rtOkPx3t7CU1Ubvy0GVegOZpKv2KYe8E3vf6Z-Vb6y4xYjlLdg/pub?output=xlsx"
    try:
        xls = pd.ExcelFile(url)
        sheets = xls.sheet_names
        
        # Identificar solapas ignorando mayúsculas/minúsculas
        s_dot = next((s for s in sheets if 'DOTACION' in s.upper()), None)
        s_rot = next((s for s in sheets if 'ROTACION' in s.upper()), None)
        s_baj = next((s for s in sheets if 'BAJAS' in s.upper()), None)

        # Carga y limpieza de columnas (Conversión a string para evitar AttributeError)
        df_dot = pd.read_excel(url, sheet_name=s_dot) if s_dot else pd.DataFrame()
        df_rot = pd.read_excel(url, sheet_name=s_rot) if s_rot else pd.DataFrame()
        df_baj = pd.read_excel(url, sheet_name=s_baj) if s_baj else pd.DataFrame()

        for df in [df_dot, df_rot, df_baj]:
            if not df.empty:
                df.columns = [str(c).strip().upper() for c in df.columns]

        return df_dot, df_rot, df_baj
    except Exception as e:
        st.error(f"Error crítico de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_dot, df_rot, df_baj = load_all_data()

# 3. Menú de Navegación Lateral
st.sidebar.image("https://www.cenoa.com.ar/wp-content/uploads/2021/05/logo-cenoa.png", width=150) # Logo genérico o de la empresa
st.sidebar.title("Panel de Control")
categoria = st.sidebar.radio(
    "Seleccione Categoría:",
    ["📊 Dotación", "🔄 Rotación", "🚪 Bajas"],
    index=0
)

# Filtros Globales (Año y Unidad)
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globales")

# Lógica de filtros dinámicos
if not df_dot.empty:
    # Detectar columnas de filtrado
    col_anio = next((c for c in df_dot.columns if 'AÑO' in c or 'ANIO' in c), None)
    col_un = next((c for c in df_dot.columns if 'UNIDAD' in c or 'SUCURSAL' in c or 'EMPRESA' in c), None)

    selected_anio = st.sidebar.multiselect("Año", options=df_dot[col_anio].unique()) if col_anio else []
    selected_un = st.sidebar.multiselect("Unidad de Negocio", options=df_dot[col_un].unique()) if col_un else []

    # Aplicar Filtros
    if selected_anio:
        df_dot = df_dot[df_dot[col_anio].isin(selected_anio)]
        if not df_rot.empty and col_anio in df_rot.columns: df_rot = df_rot[df_rot[col_anio].isin(selected_anio)]
        if not df_baj.empty and col_anio in df_baj.columns: df_baj = df_baj[df_baj[col_anio].isin(selected_anio)]
    if selected_un:
        df_dot = df_dot[df_dot[col_un].isin(selected_un)]
        if not df_rot.empty and col_un in df_rot.columns: df_rot = df_rot[df_rot[col_un].isin(selected_un)]
        if not df_baj.empty and col_un in df_baj.columns: df_baj = df_baj[df_baj[col_un].isin(selected_un)]

# 4. Renderizado de Secciones
if "Dotación" in categoria:
    st.header("📋 Gestión de Dotación")
    if not df_dot.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Headcount Actual", f"{len(df_dot)}")
        
        # Gráfico por Unidad
        if col_un:
            fig_un = px.pie(df_dot, names=col_un, title="Distribución por Unidad de Negocio", hole=0.4)
            st.plotly_chart(fig_un, use_container_width=True)
        
        st.subheader("Detalle de Personal")
        st.dataframe(df_dot, use_container_width=True)
    else:
        st.warning("No hay datos disponibles en la solapa DOTACION.")

elif "Rotación" in categoria:
    st.header("🔄 Indicadores de Rotación")
    if not df_rot.empty:
        # Aquí implementamos la lógica de omitir meses vacíos (0)
        col_tasa = next((c for c in df_rot.columns if 'TASA' in c or 'INDICE' in c or 'ROTACION' in c), df_rot.columns[-1])
        df_rot_clean = df_rot[df_rot[col_tasa] > 0] # Solo meses que ya ocurrieron
        
        avg_rot = df_rot_clean[col_tasa].mean()
        st.metric("Promedio Rotación Mensual", f"{avg_rot:.2f}%")
        
        fig_line = px.line(df_rot, x=df_rot.columns[0], y=col_tasa, title="Evolución de la Rotación", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No hay datos en la solapa ROTACION.")

elif "Bajas" in categoria:
    st.header("🚪 Análisis de Bajas")
    if not df_baj.empty:
        st.metric("Total Egresos en Periodo", len(df_baj))
        
        col_motivo = next((c for c in df_baj.columns if 'MOTIVO' in c), None)
        if col_motivo:
            fig_bar = px.bar(df_baj[col_motivo].value_counts().reset_index(), 
                             x='count', y=col_motivo, orientation='h', title="Principales Motivos de Egreso")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.subheader("Registro de Bajas")
        st.table(df_baj.head(10))
    else:
        st.warning("No hay datos en la solapa BAJAS.")
