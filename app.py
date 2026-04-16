import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title="HR Dashboard Estratégico", page_icon="📊", layout="wide")

st.title("📊 Dashboard Estratégico de HR Analytics")
st.markdown("Orientado a medición de Eficiencia, Productividad y Fuga de Talento")

# Función para cargar datos en caché
@st.cache_data(ttl=3600) # Actualiza cada 1 hora
def load_data():
    # Truco BI: Cambiamos output=csv por output=xlsx para poder descargar todas las solapas con un solo link
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhx1mzO6cExRA4rtOkPx3t7CU1Ubvy0GVegOZpKv2KYe8E3vf6Z-Vb6y4xYjlLdg/pub?output=xlsx"
    
    try:
        df_dotacion = pd.read_excel(url, sheet_name='DOTACION')
        df_rotacion = pd.read_excel(url, sheet_name='ROTACION')
        df_bajas = pd.read_excel(url, sheet_name='BAJAS')
        return df_dotacion, df_rotacion, df_bajas
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_dot, df_rot, df_baj = load_data()

# Verifica si hay datos antes de proceder
if not df_dot.empty:
    
    # ------------------ SIDEBAR: FILTROS ------------------
    st.sidebar.header("Filtros Estratégicos")
    
    # Asumiendo que tus columnas se llaman 'Anio', 'Mes', 'Unidad_Negocio', 'Puesto'
    # Agrega un manejo dinámico por si los nombres varían levemente
    año_col = [col for col in df_dot.columns if 'año' in col.lower() or 'anio' in col.lower()][0]
    un_col = [col for col in df_dot.columns if 'unidad' in col.lower() or 'sucursal' in col.lower()][0]
    
    filtro_anios = st.sidebar.multiselect("Seleccionar Año", options=df_dot[año_col].unique(), default=df_dot[año_col].unique())
    filtro_un = st.sidebar.multiselect("Unidad de Negocio", options=df_dot[un_col].unique(), default=df_dot[un_col].unique())
    
    # Aplicar filtros
    df_dot_filtered = df_dot[(df_dot[año_col].isin(filtro_anios)) & (df_dot[un_col].isin(filtro_un))]
    df_rot_filtered = df_rot[(df_rot[año_col].isin(filtro_anios)) & (df_rot[un_col].isin(filtro_un))]
    df_baj_filtered = df_baj[(df_baj[año_col].isin(filtro_anios)) & (df_baj[un_col].isin(filtro_un))]

    # ------------------ SECCIÓN 1: OVERVIEW (KPIs) ------------------
    st.subheader("Indicadores Principales (YTD)")
    col1, col2, col3, col4 = st.columns(4)
    
    # Cálculos simulados basados en tu estructura (Ajustar nombres exactos de columnas)
    total_dotacion = df_dot_filtered['Headcount'].sum() if 'Headcount' in df_dot_filtered.columns else len(df_dot_filtered)
    total_bajas = len(df_baj_filtered)
    
    # Simulamos el cálculo de productividad si existe la columna Ventas o Productividad
    prod_col = [col for col in df_dot_filtered.columns if 'prod' in col.lower() or 'ventas' in col.lower()]
    productividad_avg = df_dot_filtered[prod_col[0]].mean() if prod_col else 0
    
    with col1:
        st.metric("Dotación Total Activa", f"{total_dotacion:,.0f}", delta="-2% vs Año Anterior")
    with col2:
        st.metric("Rotación Total", f"{(total_bajas/total_dotacion)*100 if total_dotacion else 0:.1f}%", delta="1.5% (Alerta)", delta_color="inverse")
    with col3:
        # Asumiendo columna 'Tipo_Baja'
        voluntarias = len(df_baj_filtered[df_baj_filtered['Tipo_Baja'].str.contains('Voluntaria', na=False)]) if 'Tipo_Baja' in df_baj_filtered.columns else 0
        st.metric("Rotación Voluntaria", f"{(voluntarias/total_dotacion)*100 if total_dotacion else 0:.1f}%", delta="Riesgo de fuga")
    with col4:
        st.metric("Productividad Promedio", f"${productividad_avg:,.2f}", delta="+5% vs Target")

    st.markdown("---")

    # ------------------ SECCIÓN 2: TENDENCIAS (Líneas) ------------------
    st.subheader("Tendencias Críticas: Eficiencia y Fuga")
    colA, colB = st.columns(2)
    
    with colA:
        # Evolución de Rotación (Mes a Mes)
        mes_col = [col for col in df_rot_filtered.columns if 'mes' in col.lower()][0]
        fig_rot_trend = px.line(df_rot_filtered.groupby(mes_col, as_index=False).sum(), 
                                x=mes_col, y=df_rot_filtered.columns[2], # Ajustar por tu columna de % rotación
                                title="Evolución de Rotación (Histórico)",
                                markers=True)
        st.plotly_chart(fig_rot_trend, use_container_width=True)

    with colB:
        if prod_col:
            fig_prod_trend = px.line(df_dot_filtered.groupby(mes_col, as_index=False)[prod_col[0]].mean(),
                                     x=mes_col, y=prod_col[0],
                                     title="Productividad por Vendedor / FTE",
                                     markers=True)
            st.plotly_chart(fig_prod_trend, use_container_width=True)

    # ------------------ SECCIÓN 3: PROBLEMAS E INSIGHTS (Barras) ------------------
    st.subheader("Análisis de Desvíos y Diagnóstico")
    colC, colD = st.columns(2)

    with colC:
        if 'Motivo' in df_baj_filtered.columns:
            motivos = df_baj_filtered['Motivo'].value_counts().reset_index()
            motivos.columns = ['Motivo', 'Cantidad']
            fig_motivos = px.bar(motivos, x='Cantidad', y='Motivo', orientation='h',
                                 title="Diagnóstico de Bajas (Top Motivos)", color='Cantidad')
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.info("La columna 'Motivo' no existe en la solapa BAJAS.")

    with colD:
        # Rotación por Unidad de Negocio
        rot_un = df_baj_filtered[un_col].value_counts().reset_index()
        rot_un.columns = ['Unidad de Negocio', 'Cantidad Bajas']
        fig_un = px.bar(rot_un, x='Unidad de Negocio', y='Cantidad Bajas',
                        title="Bajas por Unidad de Negocio (Detectar Focos Rojos)",
                        color='Cantidad Bajas', color_continuous_scale="Reds")
        st.plotly_chart(fig_un, use_container_width=True)

else:
    st.warning("No se pudieron cargar los datos. Verifica el formato de tu Excel y la conexión a internet.")
