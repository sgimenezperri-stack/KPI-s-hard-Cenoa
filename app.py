import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CSS
# =====================================================================
st.set_page_config(page_title="HR Metrics | Grupo Cenoa", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #1e293b !important; }
    .main-title { color: #0f172a; font-weight: 800; font-size: 30px; margin-bottom: -5px; letter-spacing: -0.5px; }
    .sub-title { color: #2563eb; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 20px; }
    [data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    [data-testid="metric-container"] label { color: #64748b !important; font-weight: 600; font-size: 13px;}
    [data-testid="metric-container"] div { color: #0f172a !important; font-weight: 700; }
    hr { border-color: #e2e8f0; }
    .stExpander { background-color: #ffffff; border: 1px solid #e2e8f0 !important; border-radius: 6px !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 30px;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 15px;
        padding-bottom: 15px;
        font-size: 20px; 
        font-weight: 700; 
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        color: #1e293b !important;
        border-bottom: 4px solid #2563eb !important;
    }
    </style>
""", unsafe_allow_html=True)

paleta_neutra = ['#2563eb', '#64748b', '#94a3b8', '#334155', '#cbd5e1', '#0f172a', '#e2e8f0']

# =====================================================================
# 2. CONEXIÓN A LAS 3 FUENTES DE DATOS
# =====================================================================
CSV_URL_DOTACION = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"
CSV_URL_MOVIMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?gid=176641150&single=true&output=csv" 
CSV_URL_AUSENTISMO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?gid=966031933&single=true&output=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(CSV_URL_DOTACION, dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={
        'ÁREA': 'AREA', 'F. INGR': 'FECHA DE INGRESO', 'FECHA INGRESO': 'FECHA DE INGRESO',
        'F. EGRESO': 'FECHA DE EGRESO', 'FECHA EGRESO': 'FECHA DE EGRESO',
        'MOTIVO EGRESO': 'MOTIVO DE EGRESO', 'MOTIVOS DE EGRESO': 'MOTIVO DE EGRESO', 'MOTIVO': 'MOTIVO DE EGRESO'
    })
    df['FECHA_ING_DT'] = pd.to_datetime(df['FECHA DE INGRESO'], dayfirst=True, errors='coerce')
    df['FECHA_EGR_DT'] = pd.to_datetime(df['FECHA DE EGRESO'], dayfirst=True, errors='coerce')
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'ESTADO', 'PUESTO', 'MOTIVO DE EGRESO', 'CATEGORIA', 'CATEGORIA DE VARIABLE']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], np.nan)
    if 'PUESTO' in df.columns: df = df[~df['PUESTO'].str.contains('PRACTICANTE', na=False)]
    return df

@st.cache_data(ttl=600)
def load_data_mov():
    df = pd.read_csv(CSV_URL_MOVIMIENTOS, dtype=str)
    df.columns = [str(c).strip().upper().replace('Ó','O').replace('Í','I').replace('Á','A') for c in df.columns]
    mapeo = {}
    for col in df.columns:
        if 'FECHA' in col and ('MOV' in col or 'EFE' in col): mapeo[col] = 'FECHA_MOV'
        elif 'TIPO' in col and 'MOV' in col: mapeo[col] = 'TIPO_MOV'
        elif 'POTENCIAL' in col or 'EVALUAC' in col: mapeo[col] = 'POTENCIAL'
        elif 'NOMBRE' in col or 'COLAB' in col or 'APELLIDO' in col: mapeo[col] = 'NOMBRE'
        elif 'ORIGEN' in col:
            if 'EMP' in col: mapeo[col] = 'EMP_ORIGEN'
            elif 'LOC' in col: mapeo[col] = 'LOC_ORIGEN'
            elif 'PUEST' in col: mapeo[col] = 'PUESTO_ORIGEN'
        elif 'DESTINO' in col:
            if 'EMP' in col: mapeo[col] = 'EMP_DESTINO'
            elif 'LOC' in col: mapeo[col] = 'LOC_DESTINO'
            elif 'AREA' in col or 'ÁREA' in col: mapeo[col] = 'AREA_DESTINO'
            elif 'PUEST' in col: mapeo[col] = 'PUESTO_DESTINO'
    df = df.rename(columns=mapeo)
    if 'FECHA_MOV' in df.columns: df['FECHA_MOV_DT'] = pd.to_datetime(df['FECHA_MOV'], dayfirst=True, errors='coerce')
    return df

@st.cache_data(ttl=600)
def load_data_ausentismo():
    try:
        df = pd.read_csv(CSV_URL_AUSENTISMO, dtype=str)
        df.columns = [str(c).strip().upper().replace('Ó','O').replace('Í','I').replace('Á','A') for c in df.columns]
        mapeo = {}
        for col in df.columns:
            if 'FECHA' in col and ('INICIO' in col or 'AUS' in col): mapeo[col] = 'FECHA_AUSENTISMO'
            elif 'MOTIVO' in col or 'RAZON' in col: mapeo[col] = 'MOTIVO_AUSENCIA'
            elif 'DIAS' in col or 'DÍAS' in col: mapeo[col] = 'DIAS_AUSENCIA'
            elif 'NOMBRE' in col or 'COLAB' in col: mapeo[col] = 'NOMBRE'
            elif 'EMP' in col: mapeo[col] = 'EMPRESA'
            elif 'LOC' in col: mapeo[col] = 'LOCALIDAD'
            elif 'AREA' in col or 'ÁREA' in col: mapeo[col] = 'AREA'
            elif 'PUEST' in col: mapeo[col] = 'PUESTO'
        df = df.rename(columns=mapeo)
        if 'FECHA_AUSENTISMO' in df.columns: df['FECHA_AUS_DT'] = pd.to_datetime(df['FECHA_AUSENTISMO'], dayfirst=True, errors='coerce')
        if 'DIAS_AUSENCIA' in df.columns: df['DIAS_AUSENCIA'] = pd.to_numeric(df['DIAS_AUSENCIA'].str.replace(',','.'), errors='coerce').fillna(1)
        else: df['DIAS_AUSENCIA'] = 1
        return df
    except Exception: return pd.DataFrame()

try:
    df_raw = load_data()
    hoy = datetime.now()

    # =====================================================================
    # 3. INTERFAZ DE FILTROS GLOBALES
    # =====================================================================
    col_h1, col_h2, col_btn = st.columns([0.5, 9.5, 2])
    with col_h1:
        st.markdown("<div style='background-color: #0f172a; width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; letter-spacing: 1px; margin-top: 5px;'>GC</div>", unsafe_allow_html=True)
    with col_h2:
        st.markdown("<div class='main-title'>People Analytics & HR Hard Metrics</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Grupo Cenoa | Gestión Estratégica de Capital Humano</div>", unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar Datos", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    df_filt = df_raw.copy()
    
    with f4: anio_analisis = st.selectbox("AÑO", [2026, 2025, 2024], index=0)
    with f5: 
        meses_nombres = {1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'}
        if anio_analisis == hoy.year: ops_m = list(range(1, hoy.month + 1))
        else: ops_m = list(range(1, 13))
        meses_sel = st.multiselect("MESES", ops_m, default=ops_m, format_func=lambda x: meses_nombres[x])
        if not meses_sel: meses_sel = ops_m
            
    mes_max = max(meses_sel); mes_min = min(meses_sel)
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_max:02d}-{calendar.monthrange(anio_analisis, mes_max)[1]}")
    fecha_inicio_periodo = pd.to_datetime(f"{anio_analisis}-{mes_min:02d}-01")

    def get_opts(col, df): return sorted([x for x in df[col].unique() if pd.notna(x)]) if col in df.columns else []

    with f1:
        sel_emp = st.multiselect("EMPRESA", get_opts('EMPRESA', df_filt), placeholder="Todas")
        if sel_emp: df_filt = df_filt[df_filt['EMPRESA'].isin(sel_emp)]
    with f2:
        sel_loc = st.multiselect("LOCALIDAD", get_opts('LOCALIDAD', df_filt), placeholder="Todas")
        if sel_loc: df_filt = df_filt[df_filt['LOCALIDAD'].isin(sel_loc)]
    with f3:
        sel_area = st.multiselect("ÁREA", get_opts('AREA', df_filt), placeholder="Todas")
        if sel_area: df_filt = df_filt[df_filt['AREA'].isin(sel_area)]

    with st.expander("Filtros Avanzados (Puesto, Antigüedad, Líder)", expanded=False):
        fa1, fa2, fa3 = st.columns(3)
        with fa1:
            sel_puesto = st.multiselect("PUESTO", get_opts('PUESTO', df_filt), placeholder="Todos")
            if sel_puesto: df_filt = df_filt[df_filt['PUESTO'].isin(sel_puesto)]
        with fa2:
            bins_ant = [-1, 1, 3, 5, 10, 100]; labels_ant = ['< 1 año', '1 a 3 años', '3 a 5 años', '5 a 10 años', '+ 10 años']
            df_filt['ANTIGUEDAD_AÑOS'] = (fecha_corte - df_filt['FECHA_ING_DT']).dt.days / 365.25
            df_filt['RANGO_ANTIGUEDAD'] = pd.cut(df_filt['ANTIGUEDAD_AÑOS'], bins=bins_ant, labels=labels_ant)
            sel_antig = st.multiselect("ANTIGÜEDAD", labels_ant, placeholder="Todas")
            if sel_antig: df_filt = df_filt[df_filt['RANGO_ANTIGUEDAD'].isin(sel_antig)]
        with fa3:
            posibles_lideres = ['LIDER', 'JEFE', 'SUPERVISOR', 'REPORTA A', 'ENCARGADO', 'GERENTE']
            col_lider = next((c for c in df_filt.columns if c in posibles_lideres), None)
            if col_lider:
                sel_lider = st.multiselect("LÍDER", get_opts(col_lider, df_filt), placeholder="Todos")
                if sel_lider: df_filt = df_filt[df_filt[col_lider].isin(sel_lider)]

    df_periodo = df_filt[(df_filt['FECHA_ING_DT'] <= fecha_corte) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_corte))].copy()
    dot_actual = len(df_periodo)
    posibles_nombres = ['APELLIDO Y NOMBRE', 'APELLIDOS Y NOMBRES', 'NOMBRE Y APELLIDO', 'NOMBRE', 'COLABORADOR']
    col_nombre = next((c for c in posibles_nombres if c in df_periodo.columns), None)
    cols_nomina = [c for c in ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'CATEGORIA', 'CATEGORIA DE VARIABLE', 'FRECUENCIA DEL VARIABLE', 'FECHA DE INGRESO'] if c in df_periodo.columns]
    if col_nombre: cols_nomina.insert(1, col_nombre)
    
    def draw_safe_interactive_chart(fig, unique_key):
        try: return st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=unique_key)
        except TypeError: return st.plotly_chart(fig, use_container_width=True)
            # =====================================================================
    # 4. PESTAÑAS MAESTRAS
    # =====================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    tab_dot, tab_rot, tab_aus = st.tabs(["📊 Análisis de Dotación", "📉 Análisis de Rotación", "🤒 Análisis de Ausentismo"])

    # ---------------------------------------------------------------------
    # TAB 1: DOTACIÓN
    # ---------------------------------------------------------------------
    with tab_dot:
        mes_ant_val = mes_max - 1 if mes_max > 1 else 12
        anio_ant_val = anio_analisis if mes_max > 1 else anio_analisis - 1
        fecha_ant = pd.to_datetime(f"{anio_ant_val}-{mes_ant_val:02d}-{calendar.monthrange(anio_ant_val, mes_ant_val)[1]}")
        dot_ant = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_ant) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_ant))])
        dif_mes = int(dot_actual - dot_ant); pct_mes = (dif_mes / dot_ant * 100) if dot_ant > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dotación Actual", dot_actual)
        c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=f"{dif_mes} ({pct_mes:+.1f}%)")
        c3.metric("En Periodo de Prueba", len(df_periodo[df_periodo['FECHA_ING_DT'] > (fecha_corte - pd.DateOffset(months=6))]))
        c4.metric("Promedio Antigüedad", f"{df_periodo['ANTIGUEDAD_AÑOS'].mean():.1f} años")

        st.divider()
        sel_c_emp, sel_c_loc, sel_c_area = None, None, None
        if 'k_e' in st.session_state and st.session_state.k_e.get('selection', {}).get('points'): sel_c_emp = st.session_state.k_e['selection']['points'][0].get('x')
        if 'k_l' in st.session_state and st.session_state.k_l.get('selection', {}).get('points'): sel_c_loc = st.session_state.k_l['selection']['points'][0].get('label')
        if 'k_a' in st.session_state and st.session_state.k_a.get('selection', {}).get('points'): sel_c_area = st.session_state.k_a['selection']['points'][0].get('label')

        def cf_dot(exc):
            df_x = df_periodo.copy()
            if exc != 'e' and sel_c_emp: df_x = df_x[df_x['EMPRESA'] == sel_c_emp]
            if exc != 'l' and sel_c_loc: df_x = df_x[df_x['LOCALIDAD'] == sel_c_loc]
            if exc != 'a' and sel_c_area: df_x = df_x[df_x['AREA'] == sel_c_area]
            return df_x

        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Evolución de la Dotación</h4>", unsafe_allow_html=True)
            if len(meses_sel) > 1: f_ini_hist = pd.to_datetime(f"{anio_analisis}-01-01")
            else: f_ini_hist = pd.to_datetime(f"{anio_analisis - 1}-{mes_max:02d}-01")
            r_fechas = pd.date_range(start=f_ini_hist, end=fecha_corte, freq='ME')
            hist_d = [{'Fecha': f, 'Dotación': len(df_filt[(df_filt['FECHA_ING_DT'] <= f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > f))])} for f in r_fechas]
            df_h = pd.DataFrame(hist_d) if hist_d else pd.DataFrame()
            if not df_h.empty:
                df_h['Mes_Esp'] = df_h['Fecha'].dt.month.map(meses_nombres) + " " + df_h['Fecha'].dt.year.astype(str)
                fig_ev = px.line(df_h, x='Fecha', y='Dotación', markers=True, text='Dotación')
                fig_ev.update_traces(textposition="top center", line_color="#475569")
                fig_ev.update_xaxes(tickvals=df_h['Fecha'], ticktext=df_h['Mes_Esp'], tickangle=-45)
                fig_ev.update_layout(height=350, plot_bgcolor='#ffffff', margin=dict(b=60, t=10))
                st.plotly_chart(fig_ev, use_container_width=True)
        with col_top2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Categoría</h4>", unsafe_allow_html=True)
            df_cat = cf_dot('none')
            if 'CATEGORIA' in df_cat.columns:
                res_c = df_cat.groupby('CATEGORIA').size().reset_index(name='C')
                fig_c = px.bar(res_c.sort_values('C'), y='CATEGORIA', x='C', orientation='h', color_discrete_sequence=[paleta_neutra[3]])
                fig_c.update_layout(height=350, plot_bgcolor='#ffffff', margin=dict(t=10))
                st.plotly_chart(fig_c, use_container_width=True)

        col_x1, col_x2, col_x3 = st.columns(3)
        with col_x1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Empresa</h4>", unsafe_allow_html=True)
            df_e = cf_dot('e'); res_e = df_e.groupby('EMPRESA').size().reset_index(name='Cant')
            fig_e = px.bar(res_e, x='EMPRESA', y='Cant', text='Cant', color_discrete_sequence=[paleta_neutra[0]])
            fig_e.update_layout(plot_bgcolor='#ffffff')
            draw_safe_interactive_chart(fig_e, "k_e")
        with col_x2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Corte por Localidad</h4>", unsafe_allow_html=True)
            df_l = cf_dot('l'); fig_l = px.pie(df_l, names='LOCALIDAD', hole=0.4, color_discrete_sequence=paleta_neutra)
            draw_safe_interactive_chart(fig_l, "k_l")
        with col_x3:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Distribución por Área (%)</h4>", unsafe_allow_html=True)
            df_a = cf_dot('a'); fig_a = px.pie(df_a, names='AREA', hole=0.4, color_discrete_sequence=paleta_neutra)
            fig_a.update_traces(textinfo='percent')
            draw_safe_interactive_chart(fig_a, "k_a")

        df_t = cf_dot('none')
        filt_act = [f for f in [sel_c_emp, sel_c_loc, sel_c_area] if f]
        if filt_act:
            st.markdown(f"<div style='background:#f1f5f9; padding:15px; border-radius:8px; border-left: 4px solid #2563eb;'><b>↳ Nómina Filtrada ({len(df_t)} resultados)</b></div><br>", unsafe_allow_html=True)
            st.dataframe(df_t[cols_nomina].sort_values(by=[col_nombre] if col_nombre else []), use_container_width=True)

        st.divider()
        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Análisis de Ingresos y Egresos (Múltiples Meses)</h3>", unsafe_allow_html=True)
        
        altas_mes = df_filt[(df_filt['FECHA_ING_DT'].dt.year == anio_analisis) & (df_filt['FECHA_ING_DT'].dt.month.isin(meses_sel))].copy()
        bajas_mes = df_filt[(df_filt['FECHA_EGR_DT'].dt.year == anio_analisis) & (df_filt['FECHA_EGR_DT'].dt.month.isin(meses_sel))].copy()
        
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric(f"Altas en el Periodo", len(altas_mes))
        cm2.metric(f"Bajas en el Periodo", len(bajas_mes))
        cm3.metric("Crecimiento Neto", len(altas_mes) - len(bajas_mes))

        if len(altas_mes) > 0 or len(bajas_mes) > 0:
            tab_alt, tab_baj = st.tabs(["Altas", "Bajas"])
            with tab_alt:
                if not altas_mes.empty:
                    altas_mes['UBICACION'] = altas_mes['EMPRESA'] + " - " + altas_mes['LOCALIDAD']
                    fig_al = px.bar(altas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='C'), x='UBICACION', y='C', color='AREA')
                    fig_al.update_layout(plot_bgcolor='#ffffff')
                    st.plotly_chart(fig_al, use_container_width=True)
            with tab_baj:
                if not bajas_mes.empty:
                    c_b1, c_b2 = st.columns(2)
                    with c_b1:
                        bajas_mes['UBICACION'] = bajas_mes['EMPRESA'] + " - " + bajas_mes['LOCALIDAD']
                        fig_bj = px.bar(bajas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='C'), x='UBICACION', y='C', color='AREA')
                        fig_bj.update_layout(plot_bgcolor='#ffffff')
                        st.plotly_chart(fig_bj, use_container_width=True)
                    with c_b2:
                        fig_m = px.pie(bajas_mes.groupby('MOTIVO DE EGRESO').size().reset_index(name='C'), names='MOTIVO DE EGRESO', values='C', hole=0.4)
                        st.plotly_chart(fig_m, use_container_width=True)

        st.divider()
        try:
            df_mov = load_data_mov()
            if 'FECHA_MOV_DT' in df_mov.columns:
                df_mov_p = df_mov[(df_mov['FECHA_MOV_DT'].dt.year == anio_analisis) & (df_mov['FECHA_MOV_DT'].dt.month.isin(meses_sel))].copy()
                if not df_mov_p.empty:
                    st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Movilidad Interna</h3>", unsafe_allow_html=True)
                    m1, m2 = st.columns(2)
                    with m1:
                        fig_tm = px.pie(df_mov_p.groupby('TIPO_MOV').size().reset_index(name='C'), names='TIPO_MOV', values='C', hole=0.4)
                        draw_safe_interactive_chart(fig_tm, "k_tm")
                    with m2:
                        s_tm = st.session_state.get('k_tm', {}).get('selection', {}).get('points', [{}])[0].get('label')
                        df_ev = df_mov_p[df_mov_p['TIPO_MOV'] == s_tm] if s_tm else df_mov_p
                        if 'POTENCIAL' in df_ev.columns:
                            fig_p = px.bar(df_ev.groupby('POTENCIAL').size().reset_index(name='C'), x='POTENCIAL', y='C')
                            fig_p.update_layout(plot_bgcolor='#ffffff')
                            st.plotly_chart(fig_p, use_container_width=True)
        except Exception: pass

    # ---------------------------------------------------------------------
    # TAB 2: ROTACIÓN
    # ---------------------------------------------------------------------
    with tab_rot:
        bajas_r = df_filt[(df_filt['FECHA_EGR_DT'] >= fecha_inicio_periodo) & (df_filt['FECHA_EGR_DT'] <= fecha_corte)].copy()
        dot_ini_r = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= fecha_inicio_periodo))])
        dot_prom_r = (dot_ini_r + dot_actual) / 2; dot_prom_c = dot_prom_r if dot_prom_r > 0 else 1
        
        tot_bajas = len(bajas_r); rot_total = (tot_bajas / dot_prom_c) * 100
        bajas_v = bajas_r[bajas_r['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False)]
        tot_v = len(bajas_v); rot_vol = (tot_v / dot_prom_c) * 100
        tot_vt = len(bajas_v[(bajas_v['FECHA_EGR_DT'] - bajas_v['FECHA_ING_DT']).dt.days <= 365]) if not bajas_v.empty else 0
        rot_vt = (tot_vt / dot_prom_c) * 100
        
        # Efectividad Selección
        ingresos_p = len(df_filt[(df_filt['FECHA_ING_DT'] >= fecha_inicio_periodo) & (df_filt['FECHA_ING_DT'] <= fecha_corte) & (df_filt['FECHA_ING_DT'].dt.month.isin(meses_sel))])
        bajas_p = len(bajas_r[(bajas_r['FECHA_EGR_DT'] - bajas_r['FECHA_ING_DT']).dt.days <= 180])
        sob_p = len(df_periodo[(fecha_corte - df_periodo['FECHA_ING_DT']).dt.days <= 180])
        pob_p = sob_p + bajas_p
        ef_sel = 100 - ((bajas_p / pob_p * 100) if pob_p > 0 else 0)
        
        # Efectividad Comercial
        b_p_com = len(bajas_r[(bajas_r['AREA'] == 'COMERCIAL') & ((bajas_r['FECHA_EGR_DT'] - bajas_r['FECHA_ING_DT']).dt.days <= 180)])
        s_p_com = len(df_periodo[(df_periodo['AREA'] == 'COMERCIAL') & ((fecha_corte - df_periodo['FECHA_ING_DT']).dt.days <= 180)])
        pob_c = s_p_com + b_p_com
        ef_com = 100 - ((b_p_com / pob_c * 100) if pob_c > 0 else 0)

        # Staff vs Op
        df_st = df_filt[df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        df_op = df_filt[~df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        
        def calc_rot(dff):
            d_i = len(dff[(dff['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((dff['FECHA_EGR_DT'].isna()) | (dff['FECHA_EGR_DT'] >= fecha_inicio_periodo))])
            d_f = len(dff[(dff['FECHA_ING_DT'] <= fecha_corte) & ((dff['FECHA_EGR_DT'].isna()) | (dff['FECHA_EGR_DT'] > fecha_corte))])
            p = (d_i + d_f) / 2; pc = p if p > 0 else 1
            b = len(bajas_r[bajas_r['EMPRESA'].isin(dff['EMPRESA'].unique())])
            return (b / pc) * 100, b, p

        rot_st_pct, b_st, p_st = calc_rot(df_st)
        rot_op_pct, b_op, p_op = calc_rot(df_op)

        def get_kpi_html(label, val, low_txt):
            c = "#15803d" if val >= 90 else "#dc2626"; b = "#f0fdf4" if val >= 90 else "#fef2f2"
            return f"<div style='background-color:{b};border:1px solid {c};border-radius:8px;padding:20px;height:100%;min-height:115px;display:flex;flex-direction:column;justify-content:center;'><div style='color:#64748b;font-weight:600;font-size:13px;'>{label}</div><div style='color:{c};font-weight:700;font-size:28px;'>{val:.1f}%</div><div style='color:{c};font-size:12px;'>Obj: ≥90% | {low_txt}</div></div>"

        rk1, rk2, rk3, rk4, rk5 = st.columns(5)
        rk1.metric("Rotación Total", f"{(len(bajas_r)/dot_prom_c*100):.1f}%", f"{len(bajas_r)} bajas")
        rk2.metric("Rotación Voluntaria", f"{(len(bajas_r[bajas_r['MOTIVO DE EGRESO'].str.contains('RENUNCIA', na=False)])/dot_prom_c*100):.1f}%")
        rk3.metric("Rotación STAFF", f"{(len(bajas_r[bajas_r['EMPRESA'].str.contains('LA LUZ', na=False)])/((len(df_filt[df_filt['EMPRESA'].str.contains('LA LUZ', na=False)])+1)/2)*100):.1f}%")
        with rk4: st.markdown(get_kpi_html("Efectividad Selección", ef_sel, f"Bajas: {bajas_p}"), unsafe_allow_html=True)
        with rk5: st.markdown(get_kpi_html("Efec. Sel. Comercial", ef_com, f"Bajas: {b_p_com}"), unsafe_allow_html=True)

        st.divider()
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Composición de la Rotación</h4>", unsafe_allow_html=True)
            if not bajas_r.empty:
                bajas_r['T'] = np.where(bajas_r['MOTIVO DE EGRESO'].str.contains('RENUNCIA', na=False), 'Voluntaria', 'Involuntaria')
                fig_tr = px.pie(bajas_r, names='T', hole=0.4, color_discrete_sequence=['#ef4444', paleta_neutra[1]])
                draw_safe_interactive_chart(fig_tr, "k_rt")
        with col_r2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Áreas con mayor fuga voluntaria</h4>", unsafe_allow_html=True)
            res_av = bajas_r[bajas_r['T']=='Voluntaria'].groupby('AREA').size().reset_index(name='C').sort_values('C', ascending=False)
            fig_av = px.bar(res_av.head(7), x='C', y='AREA', orientation='h', color_discrete_sequence=[paleta_neutra[0]])
            draw_safe_interactive_chart(fig_av, "k_ra")

        def fmt_ant(d):
            if pd.isna(d) or d<0: return "N/D"
            a = int(d//365.25); m = int((d%365.25)//30.4)
            res = []
            if a>0: res.append(f"{a} año{'s' if a>1 else ''}")
            if m>0: res.append(f"{m} mes{'es' if m>1 else ''}")
            return " y ".join(res) if res else "Menos de 1 mes"

        st.markdown("**↳ Detalle Interactivo de Bajas**")
        s_rt = st.session_state.get('k_rt', {}).get('selection', {}).get('points', [{}])[0].get('label')
        s_ra = st.session_state.get('k_ra', {}).get('selection', {}).get('points', [{}])[0].get('y')
        df_sb = bajas_r.copy()
        if s_rt: df_sb = df_sb[df_sb['T'] == s_rt]
        if s_ra: df_sb = df_sb[df_sb['AREA'] == s_ra]
        df_sb['ANTIGÜEDAD'] = (df_sb['FECHA_EGR_DT'] - df_sb['FECHA_ING_DT']).dt.days.apply(fmt_ant)
        st.dataframe(df_sb[[col_nombre, 'EMPRESA', 'LOCALIDAD', 'AREA', 'ANTIGÜEDAD', 'MOTIVO DE EGRESO']], use_container_width=True)

    # ---------------------------------------------------------------------
    # TAB 3: AUSENTISMO (NUEVO)
    # ---------------------------------------------------------------------
    with tab_aus:
        df_aus = load_data_ausentismo()
        if not df_aus.empty and 'FECHA_AUS_DT' in df_aus.columns:
            df_aus_p = df_aus[(df_aus['FECHA_AUS_DT'] >= fecha_inicio_periodo) & (df_aus['FECHA_AUS_DT'] <= fecha_corte)].copy()
            # Filtros Cruzados de Dotación aplicados al Ausentismo
            if sel_emp: df_aus_p = df_aus_p[df_aus_p['EMPRESA'].isin(sel_emp)]
            if sel_loc: df_aus_p = df_aus_p[df_aus_p['LOCALIDAD'].isin(sel_loc)]
            if sel_area: df_aus_p = df_aus_p[df_aus_p['AREA'].isin(sel_area)]
            
            tot_dias = df_aus_p['DIAS_AUSENCIA'].sum()
            dias_t = dot_prom_c * 22 * len(meses_sel)
            ind_aus = (tot_dias / dias_t * 100) if dias_t > 0 else 0
            
            ak1, ak2, ak3, ak4 = st.columns(4)
            ak1.metric("Índice de Ausentismo", f"{ind_aus:.2f}%", f"{tot_dias:.1f} días totales")
            ak2.metric("Total Eventos", len(df_aus_p))
            if not df_aus_p.empty:
                ak3.metric("Motivo Líder", df_aus_p['MOTIVO_AUSENCIA'].value_counts().index[0])
                ak4.metric("Máximo Ausente", df_aus_p.groupby('NOMBRE')['DIAS_AUSENCIA'].sum().idxmax())

            st.divider()
            ca1, ca2 = st.columns(2)
            with ca1:
                st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Días perdidos por Motivo</h4>", unsafe_allow_html=True)
                res_am = df_aus_p.groupby('MOTIVO_AUSENCIA')['DIAS_AUSENCIA'].sum().reset_index()
                fig_am = px.pie(res_am, names='MOTIVO_AUSENCIA', values='DIAS_AUSENCIA', hole=0.4, color_discrete_sequence=paleta_neutra)
                st.plotly_chart(fig_am, use_container_width=True)
            with ca2:
                st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Top Áreas (Días Ausentes)</h4>", unsafe_allow_html=True)
                res_aa = df_aus_p.groupby('AREA')['DIAS_AUSENCIA'].sum().reset_index().sort_values('DIAS_AUSENCIA', ascending=False)
                fig_aa = px.bar(res_aa.head(10), x='DIAS_AUSENCIA', y='AREA', orientation='h', color_discrete_sequence=[paleta_neutra[2]])
                st.plotly_chart(fig_aa, use_container_width=True)
                
            with st.expander("↳ Ver Listado Detallado de Ausencias"):
                st.dataframe(df_aus_p[['FECHA_AUSENTISMO', 'NOMBRE', 'EMPRESA', 'AREA', 'MOTIVO_AUSENCIA', 'DIAS_AUSENCIA']].sort_values('FECHA_AUSENTISMO', ascending=False), use_container_width=True)
        else:
            st.info("No hay datos cargados en la solapa Hechos_Ausentismo para este periodo.")

except Exception as e:
    st.error(f"Error crítico en el dashboard: {e}")
