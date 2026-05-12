import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dotación | Talent Hub", layout="wide", initial_sidebar_state="collapsed")

# 2. INYECCIÓN DE CSS (DISEÑO CORPORATIVO NEUTRO)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        color: #1e293b !important; 
    }
    .main-title {
        color: #0f172a;
        font-weight: 700;
        font-size: 28px;
        margin-bottom: -5px;
    }
    .sub-title {
        color: #64748b;
        font-weight: 600;
        font-size: 12px;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    [data-testid="metric-container"] label {
        color: #64748b !important;
        font-weight: 500;
    }
    [data-testid="metric-container"] div {
        color: #1e293b !important;
    }
    hr {
        border-color: #e2e8f0;
    }
    .stExpander {
        background-color: #ffffff;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }
    /* Estilo del icono corporativo superior */
    .corp-logo {
        background-color: #0f172a; 
        width: 48px; 
        height: 48px; 
        border-radius: 10px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        color: white; 
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# PALETA DE COLORES NEUTRA PARA GRÁFICOS (Tonos Pizarra, Acero y Gris)
paleta_corporativa = ['#1e293b', '#475569', '#64748b', '#94a3b8', '#334155', '#cbd5e1', '#0f172a', '#e2e8f0']

# 3. LECTURA Y LIMPIEZA DE DATOS
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
    hoy = datetime.now()

    # 4. ENCABEZADO PERSONALIZADO
    col_icon, col_text = st.columns([0.5, 11.5])
    with col_icon:
        st.markdown("<div class='corp-logo'>TH</div>", unsafe_allow_html=True)
    with col_text:
        st.markdown("<div class='main-title'>Dotación</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Estructura Organizacional</div>", unsafe_allow_html=True)

    # 5. BARRA DE FILTROS SUPERIOR
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    
    df_filt = df_raw.copy()
    
    with f4:
        anio_analisis = st.selectbox("AÑO", [2026, 2025, 2024], index=0)
    with f5:
        mes_analisis = st.selectbox("MES", range(1, 13), index=hoy.month-1, format_func=lambda x: calendar.month_abbr[x].upper())
        
    ultimo_dia = calendar.monthrange(anio_analisis, mes_analisis)[1]
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_analisis:02d}-{ultimo_dia}")

    def get_opts(col, df): 
        if col in df.columns: return sorted([x for x in df[col].unique() if pd.notna(x)])
        return []

    with f1:
        sel_emp = st.multiselect("EMPRESA", get_opts('EMPRESA', df_filt), placeholder="Todas")
        if sel_emp: df_filt = df_filt[df_filt['EMPRESA'].isin(sel_emp)]
        
    with f2:
        sel_loc = st.multiselect("LOCALIDAD", get_opts('LOCALIDAD', df_filt), placeholder="Todas")
        if sel_loc: df_filt = df_filt[df_filt['LOCALIDAD'].isin(sel_loc)]
        
    with f3:
        sel_area = st.multiselect("ÁREA", get_opts('AREA', df_filt), placeholder="Todas")
        if sel_area: df_filt = df_filt[df_filt['AREA'].isin(sel_area)]

    with st.expander("Filtros Avanzados (Sub Área y Puesto)", expanded=False):
        fa1, fa2 = st.columns(2)
        with fa1:
            sel_subarea = st.multiselect("SUB ÁREA", get_opts('SUB AREA', df_filt), placeholder="Todas")
            if sel_subarea: df_filt = df_filt[df_filt['SUB AREA'].isin(sel_subarea)]
        with fa2:
            sel_puesto = st.multiselect("PUESTO", get_opts('PUESTO', df_filt), placeholder="Todos")
            if sel_puesto: df_filt = df_filt[df_filt['PUESTO'].isin(sel_puesto)]

    df_universo = df_filt.copy()

    def get_dotacion_a_fecha(df, fecha):
        return df[(df['FECHA_ING_DT'] <= fecha) & ((df['FECHA_EGR_DT'].isna()) | (df['FECHA_EGR_DT'] > fecha))]

    df_periodo = get_dotacion_a_fecha(df_universo, fecha_corte)
    dot_actual = len(df_periodo)

    # 6. CÁLCULO DE KPIS
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

    fecha_limite_prueba = fecha_corte - pd.DateOffset(months=6)
    df_prueba = df_periodo[df_periodo['FECHA_ING_DT'] > fecha_limite_prueba].copy()
    en_prueba = len(df_prueba)
    pct_prueba = (en_prueba / dot_actual * 100) if dot_actual > 0 else 0

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dotación en Periodo", dot_actual)
    c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=f"{dif_mes} ({pct_mes:+.1f}%)")
    c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=f"{dif_anio} ({pct_anio:+.1f}%)")
    c4.metric("En Período de Prueba", f"{en_prueba}", delta=f"{pct_prueba:.1f}% de la estructura", delta_color="off")

    # 7. NÓMINAS DESPLEGABLES
    posibles_nombres = ['APELLIDO Y NOMBRE', 'APELLIDOS Y NOMBRES', 'NOMBRE Y APELLIDO', 'NOMBRE', 'COLABORADOR']
    col_nombre = next((c for c in posibles_nombres if c in df_periodo.columns), None)

    if en_prueba > 0:
        with st.expander(f"Detalle: {en_prueba} colaboradores en Período de Prueba", expanded=False):
            df_prueba['VENCIMIENTO PRUEBA'] = df_prueba['FECHA_ING_DT'] + pd.DateOffset(months=6)
            df_prueba['DÍAS RESTANTES'] = (df_prueba['VENCIMIENTO PRUEBA'] - fecha_corte).dt.days
            df_prueba['VENCIMIENTO PRUEBA'] = df_prueba['VENCIMIENTO PRUEBA'].dt.strftime('%d/%m/%Y')
            
            cols_prueba_base = ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'FECHA DE INGRESO', 'VENCIMIENTO PRUEBA', 'DÍAS RESTANTES']
            if col_nombre: cols_prueba_base.insert(1, col_nombre)
            cols_prueba = [c for c in cols_prueba_base if c in df_prueba.columns]
            
            df_prueba_show = df_prueba[cols_prueba].sort_values(by='DÍAS RESTANTES', ascending=True)
            
            def highlight_urgent(row):
                if row['DÍAS RESTANTES'] < 30:
                    return ['background-color: #f1f5f9; color: #b91c1c; font-weight: 600'] * len(row)
                return [''] * len(row)
                
            st.dataframe(df_prueba_show.style.apply(highlight_urgent, axis=1), use_container_width=True)

    with st.expander(f"Nómina completa: {dot_actual} colaboradores activos", expanded=False):
        if not df_periodo.empty:
            cols_base = ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'FECHA DE INGRESO']
            if col_nombre: cols_base.insert(1, col_nombre)
            cols_nomina = [c for c in cols_base if c in df_periodo.columns]
            sort_cols = [c for c in ['EMPRESA', 'AREA', col_nombre] if c and c in df_periodo.columns]
            
            st.dataframe(df_periodo[cols_nomina].sort_values(by=sort_cols), use_container_width=True)

    st.divider()

    # 8. GRÁFICOS DINÁMICOS
    st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Evolución de Crecimiento Neto</h3>", unsafe_allow_html=True)
    
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
        
        # Gráfica de línea sobria
        fig_evol = px.line(df_historia, x='Fecha', y='Dotación', markers=True, text='Dotación')
        fig_evol.update_traces(textposition="top center", textfont_size=11, marker=dict(size=7, color="#1e293b"), line=dict(color="#475569", width=2))
        fig_evol.update_xaxes(title="", tickmode='array', tickvals=df_historia['Fecha'], ticktext=df_historia['Mes_Esp'], tickangle=-45, showgrid=False)
        fig_evol.update_yaxes(title="Colaboradores", showgrid=True, gridcolor='#f1f5f9')
        fig_evol.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60), font=dict(color="#475569")) 
        
        st.plotly_chart(fig_evol, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Análisis Profundo de Variación</h3>", unsafe_allow_html=True)
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
        cm3.metric("Crecimiento Neto", crec_neto, delta=crec_neto)

        if len(altas_mes) > 0 or len(bajas_mes) > 0:
            tab_altas, tab_bajas = st.tabs(["Ingresos del Mes", "Bajas del Mes"])
            
            with tab_altas:
                if len(altas_mes) > 0:
                    altas_mes['UBICACION'] = altas_mes['EMPRESA'] + " - " + altas_mes['LOCALIDAD']
                    res_a = altas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='Cant')
                    total_a = res_a['Cant'].sum()
                    res_a['Etiqueta'] = res_a['Cant'].astype(str) + " (" + (res_a['Cant']/total_a*100).round(1).astype(str) + "%)"
                    
                    fig_a = px.bar(res_a, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', color_discrete_sequence=paleta_corporativa)
                    fig_a.update_layout(xaxis_title="", yaxis_title="Altas", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                    st.plotly_chart(fig_a, use_container_width=True)
                    
                    # RESTAURADO: Expander de Ingresantes
                    with st.expander("Ver nómina de colaboradores ingresantes"):
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
                    
                    fig_b = px.bar(res_b, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', color_discrete_sequence=paleta_corporativa)
                    fig_b.update_layout(xaxis_title="", yaxis_title="Bajas", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                    st.plotly_chart(fig_b, use_container_width=True)
                    
                    # RESTAURADO: Expander de Bajas
                    with st.expander("Ver nómina de colaboradores dados de baja"):
                        cols_b = [c for c in ['CUIL', col_nombre, 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'FECHA DE EGRESO', 'MOTIVO DE EGRESO'] if c and c in bajas_mes.columns]
                        st.dataframe(bajas_mes[cols_b], use_container_width=True)
                else:
                    st.info("No se registraron bajas en este periodo.")

    st.divider()

    # 9. APERTURAS ESTRUCTURALES
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='font-size: 16px; font-weight: 600;'>Estructura General por Empresa</h3>", unsafe_allow_html=True)
        df_emp = df_periodo.groupby('EMPRESA').size().reset_index(name='Cant')
        if not df_emp.empty:
            total_emp = df_emp['Cant'].sum()
            df_emp['Etiqueta'] = df_emp['Cant'].astype(str) + " (" + (df_emp['Cant']/total_emp*100).round(1).astype(str) + "%)"
            fig_emp = px.bar(df_emp, x='EMPRESA', y='Cant', text='Etiqueta', color='EMPRESA', color_discrete_sequence=paleta_corporativa)
            fig_emp.update_layout(xaxis_title="", yaxis_title="Dotación", plot_bgcolor='#ffffff', showlegend=False, font=dict(color="#475569"))
            st.plotly_chart(fig_emp, use_container_width=True)
        
    with col2:
        st.markdown("<h3 style='font-size: 16px; font-weight: 600;'>Corte por Localidad</h3>", unsafe_allow_html=True)
        if not df_periodo.empty:
            fig_loc = px.pie(df_periodo, names='LOCALIDAD', hole=0.4, color_discrete_sequence=paleta_corporativa)
            fig_loc.update_traces(textinfo='value+percent')
            fig_loc.update_layout(font=dict(color="#475569"))
            st.plotly_chart(fig_loc, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
