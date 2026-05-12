import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar

st.set_page_config(page_title="HC Analytics | Grupo Cenoa", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL, dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={
        'ÁREA': 'AREA', 
        'F. INGR': 'FECHA DE INGRESO',
        'FECHA INGRESO': 'FECHA DE INGRESO',
        'F. EGRESO': 'FECHA DE EGRESO',
        'FECHA EGRESO': 'FECHA DE EGRESO'
    })
    
    # Normalización de Fechas
    df['FECHA_ING_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    df['FECHA_EGR_DT'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')
    
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract(r'(\d+)').astype(float)
    
    # Normalización de textos
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'ESTADO', 'PUESTO']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], np.nan)
            
    # 1. FILTRO ESTRUCTURAL: Eliminar Practicantes de todo el análisis
    if 'PUESTO' in df.columns:
        df = df[~df['PUESTO'].str.contains('PRACTICANTE', na=False)]
        
    return df

try:
    df_raw = load_data()

    # --- SIDEBAR (CONFIGURACIÓN) ---
    st.sidebar.title("📈 Configuración")
    
    hoy = datetime.now()
    anio_analisis = st.sidebar.selectbox("Año de Corte", [2026, 2025, 2024], index=0)
    mes_analisis = st.sidebar.slider("Mes de Corte", 1, 12, hoy.month)
    
    ultimo_dia = calendar.monthrange(anio_analisis, mes_analisis)[1]
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_analisis:02d}-{ultimo_dia}")

    st.sidebar.divider()
    
    def get_opts(col): return sorted([x for x in df_raw[col].unique() if pd.notna(x)])
    sel_emp = st.sidebar.multiselect("Empresa", get_opts('EMPRESA'), default=get_opts('EMPRESA'))
    sel_area = st.sidebar.multiselect("Área", get_opts('AREA'), default=get_opts('AREA'))

    # --- FILTRADO ESTRUCTURAL PREVIO ---
    df_universo = df_raw.copy()
    if sel_emp: df_universo = df_universo[df_universo['EMPRESA'].isin(sel_emp)]
    if sel_area: df_universo = df_universo[df_universo['AREA'].isin(sel_area)]

    # --- RECONSTRUCCIÓN EXACTA ---
    def get_dotacion_a_fecha(df, fecha):
        return df[(df['FECHA_ING_DT'] <= fecha) & ((df['FECHA_EGR_DT'].isna()) | (df['FECHA_EGR_DT'] > fecha))]

    df_periodo = get_dotacion_a_fecha(df_universo, fecha_corte)

    # --- DASHBOARD PRINCIPAL ---
    st.title(f"👥 Análisis de Dotación: Fin de {mes_analisis}/{anio_analisis}")
    st.caption(f"Excluye puestos de 'Practicantes'. Cálculo exacto al {ultimo_dia}/{mes_analisis:02d}/{anio_analisis}")
    
    dot_actual = len(df_periodo)
    
    mes_ant = mes_analisis - 1 if mes_analisis > 1 else 12
    anio_ant_calc = anio_analisis if mes_analisis > 1 else anio_analisis - 1
    ult_dia_ant = calendar.monthrange(anio_ant_calc, mes_ant)[1]
    fecha_mes_ant = pd.to_datetime(f"{anio_ant_calc}-{mes_ant:02d}-{ult_dia_ant}")
    dot_mes_ant = len(get_dotacion_a_fecha(df_universo, fecha_mes_ant))
    
    ult_dia_inter = calendar.monthrange(anio_analisis - 1, mes_analisis)[1]
    fecha_anio_ant = pd.to_datetime(f"{anio_analisis - 1}-{mes_analisis:02d}-{ult_dia_inter}")
    dot_anio_ant = len(get_dotacion_a_fecha(df_universo, fecha_anio_ant))

    c1, c2, c3 = st.columns(3)
    c1.metric("Dotación en Periodo", dot_actual)
    c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=int(dot_actual - dot_mes_ant))
    c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=int(dot_actual - dot_anio_ant))

    st.divider()

    # --- GRÁFICO DINÁMICO ---
    st.subheader("📈 Evolución de Crecimiento Neto")
    
    fecha_inicio_grafico = pd.to_datetime('2025-01-01')
    if fecha_corte >= fecha_inicio_grafico:
        rango_fechas = pd.date_range(start=fecha_inicio_grafico, end=fecha_corte, freq='ME')
    else:
        rango_fechas = pd.date_range(start=fecha_corte.replace(month=1, day=1), end=fecha_corte, freq='ME')
        
    historia = []
    for f in rango_fechas:
        historia.append({'Fecha': f, 'Dotación': len(get_dotacion_a_fecha(df_universo, f))})
    
    if historia:
        df_historia = pd.DataFrame(historia)
        meses_es = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        df_historia['Mes_Esp'] = df_historia['Fecha'].dt.month.map(meses_es) + " " + df_historia['Fecha'].dt.year.astype(str)
        
        fig_evol = px.line(df_historia, x='Fecha', y='Dotación', markers=True, text='Dotación')
        fig_evol.update_traces(textposition="top center", textfont_size=12, marker=dict(size=8))
        fig_evol.update_xaxes(title="", tickmode='array', tickvals=df_historia['Fecha'], ticktext=df_historia['Mes_Esp'], tickangle=-45, showgrid=False)
        fig_evol.update_yaxes(title="Colaboradores", showgrid=True, gridcolor='lightgray')
        fig_evol.update_layout(plot_bgcolor='white', margin=dict(b=80)) 
        
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- NUEVO: ANÁLISIS DRILL-DOWN MENSUAL ---
        st.subheader("🔍 Análisis Profundo de Variación")
        st.markdown("¿Notaste un pico en el gráfico? Selecciona el mes para descubrir qué áreas o empresas impulsaron el crecimiento.")
        
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            mes_drill = st.selectbox("Seleccione un mes para auditar:", df_historia['Mes_Esp'].tolist(), index=len(df_historia)-1)
            
        # Obtenemos la fecha exacta del mes seleccionado en el combo
        fecha_elegida = df_historia.loc[df_historia['Mes_Esp'] == mes_drill, 'Fecha'].iloc[0]
        
        # Filtramos quién ingresó (Alta) y quién se fue (Baja) exactamente en ese mes y año
        altas_mes = df_universo[(df_universo['FECHA_ING_DT'].dt.year == fecha_elegida.year) & 
                                (df_universo['FECHA_ING_DT'].dt.month == fecha_elegida.month)]
                                
        bajas_mes = df_universo[(df_universo['FECHA_EGR_DT'].dt.year == fecha_elegida.year) & 
                                (df_universo['FECHA_EGR_DT'].dt.month == fecha_elegida.month)]
        
        crec_neto = len(altas_mes) - len(bajas_mes)

        # Mini-métricas del mes auditado
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric(f"Altas en {mes_drill}", len(altas_mes))
        cm2.metric(f"Bajas en {mes_drill}", len(bajas_mes))
        cm3.metric("Crecimiento Neto del Mes", crec_neto, delta=crec_neto)

        # Gráficos detallados por pestaña
        if len(altas_mes) > 0 or len(bajas_mes) > 0:
            tab_altas, tab_bajas = st.tabs(["🟢 Dónde hubo Ingresos", "🔴 Dónde hubo Bajas"])
            
            with tab_altas:
                if len(altas_mes) > 0:
                    fig_a = px.histogram(altas_mes, x='EMPRESA', color='AREA', text_auto=True, title=f"Altas por Empresa y Área ({mes_drill})")
                    st.plotly_chart(fig_a, use_container_width=True)
                else:
                    st.info("No se registraron ingresos en este periodo.")
                    
            with tab_bajas:
                if len(bajas_mes) > 0:
                    fig_b = px.histogram(bajas_mes, x='EMPRESA', color='AREA', text_auto=True, title=f"Bajas por Empresa y Área ({mes_drill})")
                    st.plotly_chart(fig_b, use_container_width=True)
                else:
                    st.info("No se registraron bajas en este periodo.")
    else:
        st.info("No hay datos históricos para graficar en este periodo.")

    st.divider()

    # --- APERTURAS ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Estructura General por Empresa")
        df_emp = df_periodo.groupby('EMPRESA').size().reset_index(name='Cant')
        st.plotly_chart(px.bar(df_emp, x='EMPRESA', y='Cant', text_auto=True, color='EMPRESA'), use_container_width=True)
    with col2:
        st.subheader("Corte por Localidad")
        st.plotly_chart(px.pie(df_periodo, names='LOCALIDAD', hole=0.3), use_container_width=True)

    st.subheader("Explorador de Estructura (Activos en el mes)")
    st.plotly_chart(px.sunburst(df_periodo, path=['EMPRESA', 'AREA', 'PUESTO'], color='EMPRESA'), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
