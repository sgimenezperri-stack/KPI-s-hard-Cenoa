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
    
    /* Pestañas superiores destacadas */
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
# 2. CONEXIÓN A BASES DE DATOS
# =====================================================================
CSV_URL_DOTACION = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"
CSV_URL_MOVIMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?gid=176641150&single=true&output=csv" 

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
    
    cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'ESTADO', 'PUESTO', 'MOTIVO DE EGRESO', 'CATEGORIA', 'CATEGORIA DE VARIABLE', 'FRECUENCIA DEL VARIABLE']
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
    
    if 'FECHA_MOV' in df.columns:
        df['FECHA_MOV_DT'] = pd.to_datetime(df['FECHA_MOV'], dayfirst=True, errors='coerce')
        
    cols_txt = ['EMP_ORIGEN', 'LOC_ORIGEN', 'PUESTO_ORIGEN', 'EMP_DESTINO', 'LOC_DESTINO', 'AREA_DESTINO', 'PUESTO_DESTINO', 'TIPO_MOV', 'POTENCIAL']
    for c in cols_txt:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], 'NO DECLARADO')
    return df

try:
    df_raw = load_data()
    hoy = datetime.now()

    # =====================================================================
    # 3. ENCABEZADO Y BOTÓN GRIS (SECONDARY)
    # =====================================================================
    col_icon, col_text, col_btn = st.columns([0.5, 9.5, 2])
    with col_icon:
        st.markdown("<div style='background-color: #0f172a; width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; letter-spacing: 1px; margin-top: 5px;'>GC</div>", unsafe_allow_html=True)
    with col_text:
        st.markdown("<div class='main-title'>People Analytics & HR Hard Metrics</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Grupo Cenoa | Panel de Control de Dotación y Rotación</div>", unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        # Cambio a botón secundario (Gris)
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    df_filt = df_raw.copy()
    
    with f4: anio_analisis = st.selectbox("AÑO", [2026, 2025, 2024], index=0)
    with f5: 
        meses_nombres = {1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'}
        mes_sel = st.selectbox("MES", ["Todos"] + list(range(1, 13)), index=hoy.month, format_func=lambda x: "TODOS (Acumulado)" if x == "Todos" else meses_nombres[x])
        
    if mes_sel == "Todos":
        mes_calc = hoy.month if anio_analisis == hoy.year else 12
        es_acumulado = True
    else:
        mes_calc = mes_sel
        es_acumulado = False

    ultimo_dia = calendar.monthrange(anio_analisis, mes_calc)[1]
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_calc:02d}-{ultimo_dia}")

    df_filt['ANTIGUEDAD_AÑOS'] = (fecha_corte - df_filt['FECHA_ING_DT']).dt.days / 365.25
    bins_ant = [-1, 1, 3, 5, 10, 100]
    labels_ant = ['< 1 año', '1 a 3 años', '3 a 5 años', '5 a 10 años', '+ 10 años']
    df_filt['RANGO_ANTIGUEDAD'] = pd.cut(df_filt['ANTIGUEDAD_AÑOS'], bins=bins_ant, labels=labels_ant)
    
    posibles_lideres = ['LIDER', 'JEFE', 'SUPERVISOR', 'REPORTA A', 'ENCARGADO', 'GERENTE']
    col_lider = next((c for c in df_filt.columns if c in posibles_lideres), None)

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

    with st.expander("Filtros Avanzados (Sub Área, Puesto, Antigüedad, Líder)", expanded=False):
        fa1, fa2, fa3, fa4 = st.columns(4)
        with fa1:
            sel_subarea = st.multiselect("SUB ÁREA", get_opts('SUB AREA', df_filt), placeholder="Todas")
            if sel_subarea: df_filt = df_filt[df_filt['SUB AREA'].isin(sel_subarea)]
        with fa2:
            sel_puesto = st.multiselect("PUESTO", get_opts('PUESTO', df_filt), placeholder="Todos")
            if sel_puesto: df_filt = df_filt[df_filt['PUESTO'].isin(sel_puesto)]
        with fa3:
            sel_antig = st.multiselect("ANTIGÜEDAD", labels_ant, placeholder="Todas")
            if sel_antig: df_filt = df_filt[df_filt['RANGO_ANTIGUEDAD'].isin(sel_antig)]
        with fa4:
            if col_lider:
                sel_lider = st.multiselect("LÍDER", get_opts(col_lider, df_filt), placeholder="Todos")
                if sel_lider: df_filt = df_filt[df_filt[col_lider].isin(sel_lider)]

    df_periodo = df_filt[(df_filt['FECHA_ING_DT'] <= fecha_corte) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_corte))].copy()
    dot_actual = len(df_periodo)

    posibles_nombres = ['APELLIDO Y NOMBRE', 'APELLIDOS Y NOMBRES', 'NOMBRE Y APELLIDO', 'NOMBRE', 'COLABORADOR']
    col_nombre = next((c for c in posibles_nombres if c in df_periodo.columns), None)
    
    cols_base = ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'CATEGORIA', 'CATEGORIA DE VARIABLE', 'FRECUENCIA DEL VARIABLE', 'FECHA DE INGRESO']
    if col_nombre: cols_base.insert(1, col_nombre)
    cols_nomina = [c for c in cols_base if c in df_periodo.columns]
    
    def draw_safe_interactive_chart(fig, unique_key):
        try: return st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=unique_key)
        except TypeError: return st.plotly_chart(fig, use_container_width=True)

    if es_acumulado:
        fecha_inicio_historia = pd.to_datetime('2025-01-01')
    else:
        fecha_inicio_historia = pd.to_datetime(f"{anio_analisis - 1}-{mes_calc:02d}-01")
        
    rango_fechas_historia = pd.date_range(start=fecha_inicio_historia, end=fecha_corte, freq='ME')
    historia_datos = [{'Fecha': f, 'Dotación': len(df_filt[(df_filt['FECHA_ING_DT'] <= f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > f))])} for f in rango_fechas_historia]
    df_historia = pd.DataFrame(historia_datos) if historia_datos else pd.DataFrame()
    if not df_historia.empty:
        meses_es = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        df_historia['Mes_Esp'] = df_historia['Fecha'].dt.month.map(meses_es) + " " + df_historia['Fecha'].dt.year.astype(str)

    # =====================================================================
    # 4. PESTAÑAS MAESTRAS
    # =====================================================================
    tab_dotacion, tab_rotacion = st.tabs(["📊 Análisis de Dotación y Estructura", "📉 Análisis de Rotación y Retención"])

    # ---------------------------------------------------------------------
    # TAB 1: DOTACIÓN
    # ---------------------------------------------------------------------
    with tab_dotacion:
        mes_ant_calc = mes_calc - 1 if mes_calc > 1 else 12
        anio_ant_calc = anio_analisis if mes_calc > 1 else anio_analisis - 1
        ult_dia_ant = calendar.monthrange(anio_ant_calc, mes_ant_calc)[1]
        fecha_mes_ant = pd.to_datetime(f"{anio_ant_calc}-{mes_ant_calc:02d}-{ult_dia_ant}")
        dot_mes_ant = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_mes_ant) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_mes_ant))])
        dif_mes = int(dot_actual - dot_mes_ant)
        pct_mes = (dif_mes / dot_mes_ant * 100) if dot_mes_ant > 0 else 0
        
        ult_dia_inter = calendar.monthrange(anio_analisis - 1, mes_calc)[1]
        fecha_anio_ant = pd.to_datetime(f"{anio_analisis - 1}-{mes_calc:02d}-{ult_dia_inter}")
        dot_anio_ant = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_anio_ant) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_anio_ant))])
        dif_anio = int(dot_actual - dot_anio_ant)
        pct_anio = (dif_anio / dot_anio_ant * 100) if dot_anio_ant > 0 else 0

        fecha_limite_prueba = fecha_corte - pd.DateOffset(months=6)
        df_prueba = df_periodo[df_periodo['FECHA_ING_DT'] > fecha_limite_prueba].copy()
        en_prueba = len(df_prueba)
        pct_prueba = (en_prueba / dot_actual * 100) if dot_actual > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dotación en Periodo", dot_actual)
        c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=f"{dif_mes} ({pct_mes:+.1f}%)")
        c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=f"{dif_anio} ({pct_anio:+.1f}%)")
        c4.metric("En Período de Prueba", f"{en_prueba}", delta=f"{pct_prueba:.1f}% de la estructura", delta_color="off")

        with st.expander(f"Nómina completa y Búsqueda: {dot_actual} colaboradores", expanded=False):
            col_b1, col_b2 = st.columns([1, 3])
            with col_b1: search_name = st.text_input("🔍 Buscar por Nombre:", placeholder="Ej: Perez...", key="busq_1")
            df_show_nomina = df_periodo.copy()
            if search_name and col_nombre: df_show_nomina = df_show_nomina[df_show_nomina[col_nombre].str.contains(search_name, case=False, na=False)]
            st.dataframe(df_show_nomina[cols_nomina].sort_values(by=[c for c in ['EMPRESA', 'AREA', col_nombre] if c in df_show_nomina.columns]), use_container_width=True)

        st.divider()

        sel_click_empresa, sel_click_localidad, sel_click_antiguedad, sel_click_lider, sel_click_categoria = None, None, None, None, None
        if 'k_emp' in st.session_state and isinstance(st.session_state.k_emp, dict) and st.session_state.k_emp.get('selection', {}).get('points'): sel_click_empresa = st.session_state.k_emp['selection']['points'][0].get('x')
        if 'k_loc' in st.session_state and isinstance(st.session_state.k_loc, dict) and st.session_state.k_loc.get('selection', {}).get('points'): pt = st.session_state.k_loc['selection']['points'][0]; sel_click_localidad = pt.get('label', pt.get('x'))
        if 'k_ant' in st.session_state and isinstance(st.session_state.k_ant, dict) and st.session_state.k_ant.get('selection', {}).get('points'): sel_click_antiguedad = st.session_state.k_ant['selection']['points'][0].get('x')
        if 'k_lid' in st.session_state and isinstance(st.session_state.k_lid, dict) and st.session_state.k_lid.get('selection', {}).get('points'): sel_click_lider = st.session_state.k_lid['selection']['points'][0].get('y')
        if 'k_cat' in st.session_state and isinstance(st.session_state.k_cat, dict) and st.session_state.k_cat.get('selection', {}).get('points'): sel_click_categoria = st.session_state.k_cat['selection']['points'][0].get('y')

        def cross_filter(exclude_chart):
            df_x = df_periodo.copy()
            if exclude_chart != 'emp' and sel_click_empresa: df_x = df_x[df_x['EMPRESA'] == sel_click_empresa]
            if exclude_chart != 'loc' and sel_click_localidad: df_x = df_x[df_x['LOCALIDAD'] == sel_click_localidad]
            if exclude_chart != 'ant' and sel_click_antiguedad: df_x = df_x[df_x['RANGO_ANTIGUEDAD'] == sel_click_antiguedad]
            if exclude_chart != 'lid' and sel_click_lider and col_lider: df_x = df_x[df_x[col_lider] == sel_click_lider]
            if exclude_chart != 'cat' and sel_click_categoria and 'CATEGORIA' in df_x.columns: df_x = df_x[df_x['CATEGORIA'] == sel_click_categoria]
            return df_x

        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Evolución de la Dotación</h4>", unsafe_allow_html=True)
            if not df_historia.empty:
                fig_evol = px.line(df_historia, x='Fecha', y='Dotación', markers=True, text='Dotación')
                fig_evol.update_traces(textposition="top center", textfont_size=11, marker=dict(size=7, color="#1e293b"), line=dict(color="#475569", width=2))
                fig_evol.update_xaxes(tickvals=df_historia['Fecha'], ticktext=df_historia['Mes_Esp'], tickangle=-45)
                fig_evol.update_layout(plot_bgcolor='#ffffff', height=350, margin=dict(b=60, t=10))
                st.plotly_chart(fig_evol, use_container_width=True)
        with col_top2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Categoría</h4>", unsafe_allow_html=True)
            df_chart_cat = cross_filter('cat')
            if not df_chart_cat.empty and 'CATEGORIA' in df_chart_cat.columns:
                df_cat = df_chart_cat.groupby('CATEGORIA').size().reset_index(name='CANT')
                fig_cat = px.bar(df_cat.sort_values('CANT', ascending=True), y='CATEGORIA', x='CANT', text='CANT', orientation='h', color_discrete_sequence=[paleta_neutra[3]])
                fig_cat.update_layout(height=350, plot_bgcolor='#ffffff', margin=dict(t=10))
                draw_safe_interactive_chart(fig_cat, "k_cat")

        st.markdown("<br>", unsafe_allow_html=True)
        col_x1, col_x2 = st.columns(2)
        with col_x1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Empresa</h4>", unsafe_allow_html=True)
            df_chart_emp = cross_filter('emp')
            if not df_chart_emp.empty:
                df_emp = df_chart_emp.groupby('EMPRESA').size().reset_index(name='Cant')
                fig_emp = px.bar(df_emp, x='EMPRESA', y='Cant', text='Cant', color_discrete_sequence=[paleta_neutra[0]])
                fig_emp.update_layout(plot_bgcolor='#ffffff')
                draw_safe_interactive_chart(fig_emp, "k_emp")
        with col_x2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Corte por Localidad</h4>", unsafe_allow_html=True)
            df_chart_loc = cross_filter('loc')
            if not df_chart_loc.empty:
                fig_loc = px.pie(df_chart_loc, names='LOCALIDAD', hole=0.4, color_discrete_sequence=paleta_neutra)
                draw_safe_interactive_chart(fig_loc, "k_loc")

    # ---------------------------------------------------------------------
    # TAB 2: ROTACIÓN
    # ---------------------------------------------------------------------
    with tab_rotacion:
        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Indicadores Clave de Rotación (Egresos / Dotación Promedio)</h3>", unsafe_allow_html=True)
        
        fecha_inicio_rot = pd.to_datetime(f"{anio_analisis}-01-01") if es_acumulado else pd.to_datetime(f"{anio_analisis}-{mes_calc:02d}-01")
        dot_inicial_rot = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_inicio_rot) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= fecha_inicio_rot))])
        dot_promedio_rot = (dot_inicial_rot + dot_actual) / 2
        dot_promedio_calc = dot_promedio_rot if dot_promedio_rot > 0 else 1
        
        bajas_periodo_rot = df_filt[(df_filt['FECHA_EGR_DT'] >= fecha_inicio_rot) & (df_filt['FECHA_EGR_DT'] <= fecha_corte)].copy()
        tot_bajas_rot = len(bajas_periodo_rot)
        rot_total_pct = (tot_bajas_rot / dot_promedio_calc) * 100
        
        bajas_voluntarias_rot = bajas_periodo_rot[bajas_periodo_rot['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False)].copy()
        tot_bajas_vol_rot = len(bajas_voluntarias_rot)
        rot_vol_pct = (tot_bajas_vol_rot / dot_promedio_calc) * 100
        
        if not bajas_voluntarias_rot.empty:
            bajas_voluntarias_rot['ANT_DIAS'] = (bajas_voluntarias_rot['FECHA_EGR_DT'] - bajas_voluntarias_rot['FECHA_ING_DT']).dt.days
            bajas_vol_temp_rot = bajas_voluntarias_rot[bajas_voluntarias_rot['ANT_DIAS'] <= 365].copy()
            tot_bajas_vol_temp_rot = len(bajas_vol_temp_rot)
        else:
            bajas_vol_temp_rot = pd.DataFrame(); tot_bajas_vol_temp_rot = 0
        rot_vol_temp_pct = (tot_bajas_vol_temp_rot / dot_promedio_calc) * 100
        
        # STAFF vs OPERACIÓN
        df_staff = df_filt[df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        df_op = df_filt[~df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        
        def calc_rot_seg(df_seg):
            d_ini = len(df_seg[(df_seg['FECHA_ING_DT'] <= fecha_inicio_rot) & ((df_seg['FECHA_EGR_DT'].isna()) | (df_seg['FECHA_EGR_DT'] >= fecha_inicio_rot))])
            d_fin = len(df_seg[(df_seg['FECHA_ING_DT'] <= fecha_corte) & ((df_seg['FECHA_EGR_DT'].isna()) | (df_seg['FECHA_EGR_DT'] > fecha_corte))])
            prom = (d_ini + d_fin) / 2
            bajas = len(bajas_periodo_rot[bajas_periodo_rot['EMPRESA'].isin(df_seg['EMPRESA'].unique())])
            return (bajas / (prom if prom > 0 else 1)) * 100

        cr1, cr2, cr3 = st.columns(3)
        cr1.metric("Rotación Total", f"{rot_total_pct:.1f}%", f"{tot_bajas_rot} egresos")
        cr2.metric("Rotación Voluntaria", f"{rot_vol_pct:.1f}%", f"{tot_bajas_vol_rot} renuncias")
        cr3.metric("Rot. Voluntaria Temprana", f"{rot_vol_temp_pct:.1f}%", f"{tot_bajas_vol_temp_rot} renuncias < 1 año")
        
        st.markdown("<br>", unsafe_allow_html=True)
        cr4, cr5, cr6 = st.columns(3)
        cr4.metric("Dotación Promedio", f"{dot_promedio_rot:.1f}", f"Inicial: {dot_inicial_rot} | Final: {dot_actual}", delta_color="off")
        cr5.metric("Rotación STAFF (La Luz)", f"{calc_rot_seg(df_staff):.1f}%")
        cr6.metric("Rotación OPERACIÓN", f"{calc_rot_seg(df_op):.1f}%")
        
        st.divider()
        
        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Evolución Mensual de Rotación</h4>", unsafe_allow_html=True)
        if not df_historia.empty:
            t_tot, t_vol, t_temp = [], [], []
            for f in df_historia['Fecha']:
                ini_f = pd.to_datetime(f"{f.year}-{f.month:02d}-01")
                d_i = len(df_filt[(df_filt['FECHA_ING_DT'] <= ini_f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= ini_f))])
                d_f = len(df_filt[(df_filt['FECHA_ING_DT'] <= f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > f))])
                p = (d_i + d_f) / 2
                p_c = p if p > 0 else 1
                b_m = df_filt[(df_filt['FECHA_EGR_DT'] >= ini_f) & (df_filt['FECHA_EGR_DT'] <= f)]
                b_v = b_m[b_m['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False)]
                b_t = b_v[(b_v['FECHA_EGR_DT'] - b_v['FECHA_ING_DT']).dt.days <= 365]
                t_tot.append((len(b_m)/p_c)*100); t_vol.append((len(b_v)/p_c)*100); t_temp.append((len(b_t)/p_c)*100)
                
            df_hist_rot = df_historia.copy()
            df_hist_rot['T_TOT'], df_hist_rot['T_VOL'], df_hist_rot['T_TEMP'] = t_tot, t_vol, t_temp
            
            sub_t1, sub_t2, sub_t3 = st.tabs(["Total (%)", "Voluntaria (%)", "Temprana (%)"])
            with sub_t1:
                fig = px.line(df_hist_rot, x='Fecha', y='T_TOT', markers=True, text='T_TOT')
                fig.update_traces(texttemplate='%{text:.1f}%', textposition="top center", line_color="#ef4444")
                fig.update_xaxes(tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            with sub_t2:
                fig = px.line(df_hist_rot, x='Fecha', y='T_VOL', markers=True, text='T_VOL')
                fig.update_traces(texttemplate='%{text:.1f}%', textposition="top center", line_color="#f97316")
                fig.update_xaxes(tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            with sub_t3:
                fig = px.line(df_hist_rot, x='Fecha', y='T_TEMP', markers=True, text='T_TEMP')
                fig.update_traces(texttemplate='%{text:.1f}%', textposition="top center", line_color="#eab308")
                fig.update_xaxes(tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Composición de la Rotación</h4>", unsafe_allow_html=True)
            if tot_bajas_rot > 0:
                bajas_periodo_rot['TIPO'] = np.where(bajas_periodo_rot['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False), 'Renuncia Voluntaria', 'Otras Bajas')
                fig_tipo = px.pie(bajas_periodo_rot, names='TIPO', hole=0.4, color_discrete_sequence=['#ef4444', paleta_neutra[2]])
                draw_safe_interactive_chart(fig_tipo, "k_rot_tipo")
        with col_r2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Top Áreas con Renuncias</h4>", unsafe_allow_html=True)
            if tot_bajas_vol_rot > 0:
                res_area = bajas_voluntarias_rot.groupby('AREA').size().reset_index(name='CANT').sort_values('CANT', ascending=False).head(7)
                fig_area = px.bar(res_area, x='CANT', y='AREA', orientation='h', text='CANT', color_discrete_sequence=[paleta_neutra[1]])
                draw_safe_interactive_chart(fig_area, "k_rot_area")

        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>↳ Detalle Interactivo de Bajas</h4>", unsafe_allow_html=True)
        sel_rt = st.session_state.get('k_rot_tipo', {}).get('selection', {}).get('points', [{}])[0].get('label')
        sel_ra = st.session_state.get('k_rot_area', {}).get('selection', {}).get('points', [{}])[0].get('y')
        df_show_bajas = bajas_periodo_rot.copy()
        if sel_rt: df_show_bajas = df_show_bajas[df_show_bajas['TIPO'] == sel_rt]
        if sel_ra: df_show_bajas = df_show_bajas[df_show_bajas['AREA'] == sel_ra]
        st.dataframe(df_show_bajas[cols_rot_show].rename(columns={'FECHA_EGR_STR': 'FECHA EGRESO'}), use_container_width=True)

except Exception as e:
    st.error(f"Error técnico general: {e}")
