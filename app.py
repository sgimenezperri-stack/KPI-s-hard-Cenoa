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
        'FECHA EGRESO': 'FECHA DE EGRESO',
        'MOTIVO EGRESO': 'MOTIVO DE EGRESO',
        'MOTIVOS DE EGRESO': 'MOTIVO DE EGRESO',
        'MOTIVO': 'MOTIVO DE EGRESO'
    })
    
    df['FECHA_ING_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    df['FECHA_EGR_DT'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')
    
    if 'EDAD' in df.columns:
        df['EDAD_NUM'] = df['EDAD'].str.extract(r'(\d+)').astype(float)
    
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'ESTADO', 'PUESTO', 'MOTIVO DE EGRESO']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], np.nan)
            
    if 'PUESTO' in df.columns:
        df = df[~df['PUESTO'].str.contains('PRACTICANTE', na=False)]
        
    return df

try:
    df_raw = load_data()

    # --- SIDEBAR ---
    st.sidebar.title("📈 Configuración")
    
    hoy = datetime.now()
    anio_analisis = st.sidebar.selectbox("Año de Corte", [2026, 2025, 2024], index=0)
    mes_analisis = st.sidebar.slider("Mes de Corte", 1, 12, hoy.month)
    
    ultimo_dia = calendar.monthrange(anio_analisis, mes_analisis)[1]
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_analisis:02d}-{ultimo_dia}")

    st.sidebar.divider()
    st.sidebar.markdown("**Filtros Estructurales**\n*(Dejar en blanco para incluir todas las opciones)*")
    
    # --- LÓGICA DE FILTROS EN CASCADA ---
    df_filt = df_raw.copy()
    
    # 1. Empresa
    opts_emp = sorted([x for x in df_filt['EMPRESA'].unique() if pd.notna(x)])
    sel_emp = st.sidebar.multiselect("Empresa", opts_emp)
    if sel_emp: 
        df_filt = df_filt[df_filt['EMPRESA'].isin(sel_emp)]
        
    # 2. Localidad (Las opciones dependen de la empresa elegida arriba)
    opts_loc = sorted([x for x in df_filt['LOCALIDAD'].unique() if pd.notna(x)])
    sel_loc = st.sidebar.multiselect("Localidad", opts_loc)
    if sel_loc: 
        df_filt = df_filt[df_filt['LOCALIDAD'].isin(sel_loc)]
        
    # 3. Área
    opts_area = sorted([x for x in df_filt['AREA'].unique() if pd.notna(x)])
    sel_area = st.sidebar.multiselect("Área", opts_area)
    if sel_area: 
        df_filt = df_filt[df_filt['AREA'].isin(sel_area)]
        
    # 4. Sub Área
    if 'SUB AREA' in df_filt.columns:
        opts_sub = sorted([x for x in df_filt['SUB AREA'].unique() if pd.notna(x)])
        sel_subarea = st.sidebar.multiselect("Sub Área", opts_sub)
        if sel_subarea: 
            df_filt = df_filt[df_filt['SUB AREA'].isin(sel_subarea)]
    
    # 5. Puesto
    if 'PUESTO' in df_filt.columns:
        opts_puesto = sorted([x for x in df_filt['PUESTO'].unique() if pd.notna(x)])
        sel_puesto = st.sidebar.multiselect("Puesto", opts_puesto)
        if sel_puesto: 
            df_filt = df_filt[df_filt['PUESTO'].isin(sel_puesto)]

    df_universo = df_filt.copy()

    def get_dotacion_a_fecha(df, fecha):
        return df[(df['FECHA_ING_DT'] <= fecha) & ((df['FECHA_EGR_DT'].isna()) | (df['FECHA_EGR_DT'] > fecha))]

    df_periodo = get_dotacion_a_fecha(df_universo, fecha_corte)

    # --- DASHBOARD PRINCIPAL ---
    st.title(f"👥 Análisis de Dotación: Fin de {mes_analisis}/{anio_analisis}")
    st.caption(f"Excluye puestos de 'Practicantes'. Cálculo exacto al {ultimo_dia}/{mes_analisis:02d}/{anio_analisis}")
    
    dot_actual = len(df_periodo)
    
    # Cálculos KPIs
    mes_ant = mes_analisis - 1 if mes_analisis > 1 else 12
    anio_ant_calc = anio_analisis if mes_analisis > 1 else anio_analisis - 1
    ult_dia_ant = calendar.monthrange(anio_ant_calc, mes_ant)[1]
    fecha_mes_ant = pd.to_datetime(f"{anio_ant_calc}-{mes_ant:02d}-{ult_dia_ant}")
    dot_mes_ant = len(get_dotacion_a_fecha(df_universo, fecha_mes_ant))
    dif_mes = int(dot_actual - dot_mes_ant)
    pct_mes = (dif_mes / dot_mes_ant * 100) if dot_mes_ant > 0 else 0
    
    ult_dia_inter = calendar.monthrange(anio_analisis - 1, mes_analisis)[1]
    fecha_anio_ant = pd.to_datetime(f"{anio_analisis - 1}-{mes_analisis:02d}-{ult_dia_inter}")
    dot_anio_ant = len(get_dotacion_a_fecha(df_universo, fecha_anio_ant))
    dif_anio = int(dot_actual - dot_anio_ant)
    pct_anio = (dif_anio / dot_anio_ant * 100) if dot_anio_ant > 0 else 0

    # CÁLCULO PERIODO DE PRUEBA (Menos de 6 meses de antigüedad)
    fecha_limite_prueba = fecha_corte - pd.DateOffset(months=6)
    en_prueba = len(df_periodo[df_periodo['FECHA_ING_DT'] > fecha_limite_prueba])
    pct_prueba = (en_prueba / dot_actual * 100) if dot_actual > 0 else 0

    # 4 Columnas para incluir el nuevo KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dotación en Periodo", dot_actual)
    c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=f"{dif_mes} ({pct_mes:+.1f}%)")
    c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=f"{dif_anio} ({pct_anio:+.1f}%)")
    c4.metric("En Período de Prueba", f"{en_prueba}", delta=f"{pct_prueba:.1f}% de la estructura", delta_color="off")

    # --- NÓMINA DESPLEGABLE ---
    with st.expander(f"📋 Ver nómina detallada de los {dot_actual} colaboradores activos", expanded=False):
        if not df_periodo.empty:
            posibles_nombres = ['APELLIDO Y NOMBRE', 'APELLIDOS Y NOMBRES', 'NOMBRE Y APELLIDO', 'NOMBRE', 'COLABORADOR']
            col_nombre = next((c for c in posibles_nombres if c in df_periodo.columns), None)
            
            cols_base = ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'FECHA DE INGRESO']
            if col_nombre:
                cols_base.insert(1, col_nombre)
                
            cols_nomina = [c for c in cols_base if c in df_periodo.columns]
            sort_cols = [c for c in ['EMPRESA', 'AREA', col_nombre] if c and c in df_periodo.columns]
            
            st.dataframe(df_periodo[cols_nomina].sort_values(by=sort_cols), use_container_width=True)
        else:
            st.info("No hay colaboradores activos para los filtros seleccionados.")

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

        # --- ANÁLISIS DRILL-DOWN MENSUAL ---
        st.subheader("🔍 Análisis Profundo de Variación")
        st.markdown("Selecciona el mes en el menú desplegable para auditar las altas y bajas por Sede y Área.")
        
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            mes_drill = st.selectbox("Seleccione un mes para auditar:", df_historia['Mes_Esp'].tolist(), index=len(df_historia)-1)
            
        fecha_elegida = df_historia.loc[df_historia['Mes_Esp'] == mes_drill, 'Fecha'].iloc[0]
        
        altas_mes = df_universo[(df_universo['FECHA_ING_DT'].dt.year == fecha_elegida.year) & 
                                (df_universo['FECHA_ING_DT'].dt.month == fecha_elegida.month)].copy()
                                
        bajas_mes = df_universo[(df_universo['FECHA_EGR_DT'].dt.year == fecha_elegida.year) & 
                                (df_universo['FECHA_EGR_DT'].dt.month == fecha_elegida.month)].copy()
        
        crec_neto = len(altas_mes) - len(bajas_mes)

        cm1, cm2, cm3 = st.columns(3)
        cm1.metric(f"Altas en {mes_drill}", len(altas_mes))
        cm2.metric(f"Bajas en {mes_drill}", len(bajas_mes))
        cm3.metric("Crecimiento Neto del Mes", crec_neto, delta=crec_neto)

        if len(altas_mes) > 0 or len(bajas_mes) > 0:
            tab_altas, tab_bajas = st.tabs(["🟢 Análisis de Ingresos", "🔴 Análisis de Bajas"])
            
            with tab_altas:
                if len(altas_mes) > 0:
                    altas_mes['UBICACION'] = altas_mes['EMPRESA'] + " - " + altas_mes['LOCALIDAD']
                    res_a = altas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='Cant')
                    total_a = res_a['Cant'].sum()
                    res_a['Etiqueta'] = res_a['Cant'].astype(str) + " (" + (res_a['Cant']/total_a*100).round(1).astype(str) + "%)"
                    
                    fig_a = px.bar(res_a, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', 
                                   title=f"Distribución de Ingresos por Sede ({mes_drill})")
                    fig_a.update_layout(xaxis_title="", yaxis_title="Cantidad de Altas")
                    st.plotly_chart(fig_a, use_container_width=True)
                    
                    with st.expander("Ver detalle de colaboradores ingresantes"):
                        cols_a = [c for c in ['CUIL', col_nombre, 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'FECHA DE INGRESO'] if c and c in altas_mes.columns]
                        st.dataframe(altas_mes[cols_a], use_container_width=True)
                else:
                    st.info("No se registraron ingresos en este periodo.")
                    
            with tab_bajas:
                if len(bajas_mes) > 0:
                    bajas_mes['UBICACION'] = bajas_mes['EMPRESA'] + " - " + bajas_mes['LOCALIDAD']
                    res_b = bajas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='Cant')
                    total_b = res_b['Cant'].sum()
                    res_b['Etiqueta'] = res_b['Cant'].astype(str) + " (" + (res_b['Cant']/total_b*100).round(1).astype(str) + "%)"
                    
                    fig_b = px.bar(res_b, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', 
                                   title=f"Distribución de Bajas por Sede ({mes_drill})")
                    fig_b.update_layout(xaxis_title="", yaxis_title="Cantidad de Bajas")
                    st.plotly_chart(fig_b, use_container_width=True)
                    
                    with st.expander("Ver detalle de colaboradores dados de baja"):
                        cols_b = [c for c in ['CUIL', col_nombre, 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'FECHA DE EGRESO', 'MOTIVO DE EGRESO'] if c and c in bajas_mes.columns]
                        st.dataframe(bajas_mes[cols_b], use_container_width=True)
                else:
                    st.info("No se registraron bajas en este periodo.")
    else:
        st.info("No hay datos históricos para graficar en este periodo.")

    st.divider()

    # --- APERTURAS ESTRUCTURALES ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Estructura General por Empresa")
        df_emp = df_periodo.groupby('EMPRESA').size().reset_index(name='Cant')
        if not df_emp.empty:
            total_emp = df_emp['Cant'].sum()
            df_emp['Etiqueta'] = df_emp['Cant'].astype(str) + " (" + (df_emp['Cant']/total_emp*100).round(1).astype(str) + "%)"
            fig_emp = px.bar(df_emp, x='EMPRESA', y='Cant', text='Etiqueta', color='EMPRESA')
            fig_emp.update_layout(xaxis_title="", yaxis_title="Dotación")
            st.plotly_chart(fig_emp, use_container_width=True)
        
    with col2:
        st.subheader("Corte por Localidad")
        if not df_periodo.empty:
            fig_loc = px.pie(df_periodo, names='LOCALIDAD', hole=0.3)
            fig_loc.update_traces(textinfo='value+percent')
            st.plotly_chart(fig_loc, use_container_width=True)

    st.subheader("Explorador de Estructura (Activos en el mes)")
    if not df_periodo.empty:
        path_sun = ['EMPRESA', 'LOCALIDAD', 'AREA']
        if 'SUB AREA' in df_periodo.columns: path_sun.append('SUB AREA')
        if 'PUESTO' in df_periodo.columns: path_sun.append('PUESTO')
        
        fig_sun = px.sunburst(df_periodo, path=path_sun, color='EMPRESA')
        fig_sun.update_traces(textinfo='label+value+percent entry')
        st.plotly_chart(fig_sun, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
