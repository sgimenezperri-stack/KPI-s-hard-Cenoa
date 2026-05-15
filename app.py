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
# 2. CONEXIÓN A BASES DE DATOS
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
    return df

@st.cache_data(ttl=600)
def load_data_ausentismo():
    try:
        df = pd.read_csv(CSV_URL_AUSENTISMO, dtype=str)
        df.columns = [str(c).strip().upper().replace('Ó','O').replace('Í','I').replace('Á','A').replace('É','E') for c in df.columns]
        mapeo = {}
        # Nuevo mapeo adaptado a las columnas específicas de Hechos_Ausentismo
        for col in df.columns:
            if 'DESDE' in col or ('FECHA' in col and ('INICIO' in col or 'AUS' in col)): mapeo[col] = 'FECHA_AUSENTISMO'
            elif 'LICENCIA' in col or 'MOTIVO' in col or 'RAZON' in col: mapeo[col] = 'MOTIVO_AUSENCIA'
            elif 'TIEMPO' in col or 'DIAS' in col or 'DÍAS' in col or 'CANTIDAD' in col: mapeo[col] = 'DIAS_AUSENCIA'
            elif 'NOMBRE' in col or 'COLAB' in col or 'APELLIDO' in col: mapeo[col] = 'NOMBRE'
            elif 'EMP' in col: mapeo[col] = 'EMPRESA'
            elif 'LOC' in col: mapeo[col] = 'LOCALIDAD'
            elif 'AREA' in col or 'ÁREA' in col: mapeo[col] = 'AREA'
            elif 'PUEST' in col: mapeo[col] = 'PUESTO'

        df = df.rename(columns=mapeo)
        
        # Resguardo: si no encontró FECHA_AUSENTISMO, busca cualquier columna que diga FECHA
        if 'FECHA_AUSENTISMO' not in df.columns:
            for col in df.columns:
                if 'FECHA' in col:
                    df = df.rename(columns={col: 'FECHA_AUSENTISMO'})
                    break

        if 'FECHA_AUSENTISMO' in df.columns:
            df['FECHA_AUS_DT'] = pd.to_datetime(df['FECHA_AUSENTISMO'], dayfirst=True, errors='coerce')
            
        if 'DIAS_AUSENCIA' in df.columns:
            # Extrae solo los números en caso de que diga "5 días", y reemplaza comas por puntos
            df['DIAS_AUSENCIA'] = pd.to_numeric(df['DIAS_AUSENCIA'].astype(str).str.replace(',','.').str.extract(r'(\d+\.?\d*)', expand=False), errors='coerce').fillna(1)
        else:
            df['DIAS_AUSENCIA'] = 1 
            
        cols_txt = ['EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'MOTIVO_AUSENCIA']
        for c in cols_txt:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip().str.upper().replace(['NAN', 'NONE', '0', ''], 'NO DECLARADO')
        return df
    except Exception:
        return pd.DataFrame()

try:
    df_raw = load_data()
    hoy = datetime.now()

    # =====================================================================
    # 3. ENCABEZADO Y BOTÓN GRIS
    # =====================================================================
    col_icon, col_text, col_btn = st.columns([0.5, 9.5, 2])
    with col_icon:
        st.markdown("<div style='background-color: #0f172a; width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; letter-spacing: 1px; margin-top: 5px;'>GC</div>", unsafe_allow_html=True)
    with col_text:
        st.markdown("<div class='main-title'>People Analytics & HR Hard Metrics</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Grupo Cenoa | Panel de Control de Dotación y Rotación</div>", unsafe_allow_html=True)
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
        if anio_analisis == hoy.year:
            opciones_meses = list(range(1, hoy.month + 1))
        else:
            opciones_meses = list(range(1, 13))
            
        meses_sel = st.multiselect("MESES", opciones_meses, default=opciones_meses, format_func=lambda x: meses_nombres[x])
        if not meses_sel:
            meses_sel = opciones_meses
            st.warning("Debe seleccionar al menos un mes.")
            
    mes_fin = max(meses_sel)
    mes_inicio = min(meses_sel)

    ultimo_dia = calendar.monthrange(anio_analisis, mes_fin)[1]
    fecha_corte = pd.to_datetime(f"{anio_analisis}-{mes_fin:02d}-{ultimo_dia}")
    fecha_inicio_periodo = pd.to_datetime(f"{anio_analisis}-{mes_inicio:02d}-01")

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

    if len(meses_sel) > 1:
        fecha_inicio_historia = pd.to_datetime(f"{anio_analisis}-01-01")
    else:
        fecha_inicio_historia = pd.to_datetime(f"{anio_analisis - 1}-{mes_fin:02d}-01")
        
    rango_fechas_historia = pd.date_range(start=fecha_inicio_historia, end=fecha_corte, freq='ME')
    historia_datos = [{'Fecha': f, 'Dotación': len(df_filt[(df_filt['FECHA_ING_DT'] <= f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > f))])} for f in rango_fechas_historia]
    df_historia = pd.DataFrame(historia_datos) if historia_datos else pd.DataFrame()
    if not df_historia.empty:
        meses_es = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        df_historia['Mes_Esp'] = df_historia['Fecha'].dt.month.map(meses_es) + " " + df_historia['Fecha'].dt.year.astype(str)

    # =====================================================================
    # 4. PESTAÑAS MAESTRAS
    # =====================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    tab_dotacion, tab_rotacion, tab_ausentismo = st.tabs(["📊 Análisis de Dotación y Estructura", "📉 Análisis de Rotación y Retención", "🤒 Análisis de Ausentismo"])

    # ---------------------------------------------------------------------
    # TAB 1: DOTACIÓN Y ESTRUCTURA
    # ---------------------------------------------------------------------
    with tab_dotacion:
        mes_ant_calc = mes_fin - 1 if mes_fin > 1 else 12
        anio_ant_calc = anio_analisis if mes_fin > 1 else anio_analisis - 1
        ult_dia_ant = calendar.monthrange(anio_ant_calc, mes_ant_calc)[1]
        fecha_mes_ant = pd.to_datetime(f"{anio_ant_calc}-{mes_ant_calc:02d}-{ult_dia_ant}")
        dot_mes_ant = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_mes_ant) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_mes_ant))])
        dif_mes = int(dot_actual - dot_mes_ant)
        pct_mes = (dif_mes / dot_mes_ant * 100) if dot_mes_ant > 0 else 0
        
        ult_dia_inter = calendar.monthrange(anio_analisis - 1, mes_fin)[1]
        fecha_anio_ant = pd.to_datetime(f"{anio_analisis - 1}-{mes_fin:02d}-{ult_dia_inter}")
        dot_anio_ant = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_anio_ant) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > fecha_anio_ant))])
        dif_anio = int(dot_actual - dot_anio_ant)
        pct_anio = (dif_anio / dot_anio_ant * 100) if dot_anio_ant > 0 else 0

        fecha_limite_prueba = fecha_corte - pd.DateOffset(months=6)
        df_prueba = df_periodo[df_periodo['FECHA_ING_DT'] > fecha_limite_prueba].copy()
        en_prueba = len(df_prueba)
        pct_prueba = (en_prueba / dot_actual * 100) if dot_actual > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dotación Actual", dot_actual)
        c2.metric("Vs. Mes Anterior", f"{dot_actual}", delta=f"{dif_mes} ({pct_mes:+.1f}%)")
        c3.metric("Vs. Año Anterior", f"{dot_actual}", delta=f"{dif_anio} ({pct_anio:+.1f}%)")
        c4.metric("En Período de Prueba", f"{en_prueba}", delta=f"{pct_prueba:.1f}% de la estructura", delta_color="off")

        if en_prueba > 0:
            with st.expander(f"Detalle: {en_prueba} colaboradores en Período de Prueba", expanded=False):
                df_prueba['VENCIMIENTO PRUEBA'] = df_prueba['FECHA_ING_DT'] + pd.DateOffset(months=6)
                df_prueba['DÍAS RESTANTES'] = (df_prueba['VENCIMIENTO PRUEBA'] - fecha_corte).dt.days
                df_prueba['VENCIMIENTO PRUEBA'] = df_prueba['VENCIMIENTO PRUEBA'].dt.strftime('%d/%m/%Y')
                cols_prueba = [c for c in cols_base + ['VENCIMIENTO PRUEBA', 'DÍAS RESTANTES'] if c in df_prueba.columns]
                df_prueba_show = df_prueba[cols_prueba].sort_values(by='DÍAS RESTANTES', ascending=True)
                st.dataframe(df_prueba_show.style.apply(lambda r: ['background-color: #fee2e2; color: #991b1b; font-weight: bold'] * len(r) if r['DÍAS RESTANTES'] < 30 else [''] * len(r), axis=1), use_container_width=True)

        with st.expander(f"Nómina completa y Búsqueda: {dot_actual} colaboradores activos", expanded=False):
            if not df_periodo.empty:
                col_b1, col_b2 = st.columns([1, 3])
                with col_b1:
                    search_name = st.text_input("🔍 Buscar por Nombre:", placeholder="Ej: Perez...", key="busq_1")
                
                df_show_nomina = df_periodo.copy()
                if search_name and col_nombre:
                    df_show_nomina = df_show_nomina[df_show_nomina[col_nombre].str.contains(search_name, case=False, na=False)]
                    
                sort_cols = [c for c in ['EMPRESA', 'AREA', col_nombre] if c in df_show_nomina.columns]
                st.dataframe(df_show_nomina[cols_nomina].sort_values(by=sort_cols), use_container_width=True)

        st.divider()

        sel_click_empresa, sel_click_localidad, sel_click_antiguedad, sel_click_lider, sel_click_categoria, sel_click_area = None, None, None, None, None, None
        
        if 'k_emp' in st.session_state and isinstance(st.session_state.k_emp, dict) and st.session_state.k_emp.get('selection', {}).get('points'): 
            sel_click_empresa = st.session_state.k_emp['selection']['points'][0].get('x')
        if 'k_loc' in st.session_state and isinstance(st.session_state.k_loc, dict) and st.session_state.k_loc.get('selection', {}).get('points'): 
            pt = st.session_state.k_loc['selection']['points'][0]
            sel_click_localidad = pt.get('label', pt.get('x'))
        if 'k_area' in st.session_state and isinstance(st.session_state.k_area, dict) and st.session_state.k_area.get('selection', {}).get('points'): 
            pt_a = st.session_state.k_area['selection']['points'][0]
            sel_click_area = pt_a.get('label', pt_a.get('x'))
        if 'k_ant' in st.session_state and isinstance(st.session_state.k_ant, dict) and st.session_state.k_ant.get('selection', {}).get('points'): 
            sel_click_antiguedad = st.session_state.k_ant['selection']['points'][0].get('x')
        if 'k_lid' in st.session_state and isinstance(st.session_state.k_lid, dict) and st.session_state.k_lid.get('selection', {}).get('points'): 
            sel_click_lider = st.session_state.k_lid['selection']['points'][0].get('y')
        if 'k_cat' in st.session_state and isinstance(st.session_state.k_cat, dict) and st.session_state.k_cat.get('selection', {}).get('points'): 
            sel_click_categoria = st.session_state.k_cat['selection']['points'][0].get('y')

        def cross_filter(exclude_chart):
            df_x = df_periodo.copy()
            if exclude_chart != 'emp' and sel_click_empresa: df_x = df_x[df_x['EMPRESA'] == sel_click_empresa]
            if exclude_chart != 'loc' and sel_click_localidad: df_x = df_x[df_x['LOCALIDAD'] == sel_click_localidad]
            if exclude_chart != 'area' and sel_click_area: df_x = df_x[df_x['AREA'] == sel_click_area]
            if exclude_chart != 'ant' and sel_click_antiguedad: df_x = df_x[df_x['RANGO_ANTIGUEDAD'] == sel_click_antiguedad]
            if exclude_chart != 'lid' and sel_click_lider and col_lider: df_x = df_x[df_x[col_lider] == sel_click_lider]
            if exclude_chart != 'cat' and sel_click_categoria and 'CATEGORIA' in df_x.columns: df_x = df_x[df_x['CATEGORIA'] == sel_click_categoria]
            return df_x

        col_top1, col_top2 = st.columns([2, 1])
        
        with col_top1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Evolución de la Dotación</h4>", unsafe_allow_html=True)
            if not df_historia.empty:
                fig_evol = px.line(df_historia, x='Fecha', y='Dotación', markers=True, text='Dotación')
                fig_evol.update_traces(textposition="top center", textfont_size=11, marker=dict(size=7, color="#1e293b"), 
                                       line=dict(color="#475569", width=2), hovertemplate="<b>%{text} Colaboradores</b><extra></extra>")
                fig_evol.update_xaxes(title="", tickmode='array', tickvals=df_historia['Fecha'], ticktext=df_historia['Mes_Esp'], tickangle=-45, showgrid=False)
                fig_evol.update_yaxes(title="Colaboradores", showgrid=True, gridcolor='#f1f5f9')
                fig_evol.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60, t=10, l=10, r=10), font=dict(color="#475569"), height=350) 
                st.plotly_chart(fig_evol, use_container_width=True)
                
        with col_top2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Categoría</h4>", unsafe_allow_html=True)
            df_chart_cat = cross_filter('cat')
            if not df_chart_cat.empty and 'CATEGORIA' in df_chart_cat.columns:
                df_cat = df_chart_cat.groupby('CATEGORIA').size().reset_index(name='CANTIDAD')
                df_cat['CATEGORIA'] = df_cat['CATEGORIA'].replace('NAN', 'NO DECLARADA')
                df_cat['ETIQUETA'] = df_cat['CANTIDAD'].astype(str) + " (" + (df_cat['CANTIDAD']/df_cat['CANTIDAD'].sum()*100).round(1).astype(str) + "%)"
                df_cat = df_cat.sort_values('CANTIDAD', ascending=True)
                
                fig_cat = px.bar(df_cat, y='CATEGORIA', x='CANTIDAD', text='ETIQUETA', orientation='h', color_discrete_sequence=[paleta_neutra[3]])
                fig_cat.update_traces(hovertemplate="<b>Categoría: %{y}</b><br>Colaboradores: %{text}<extra></extra>", textposition='outside')
                fig_cat.update_layout(height=350, xaxis_title="Cantidad", yaxis_title="", plot_bgcolor='#ffffff', font=dict(color="#475569"), margin=dict(t=10, l=10, r=10))
                draw_safe_interactive_chart(fig_cat, "k_cat")

        st.markdown("<br>", unsafe_allow_html=True)

        col_x1, col_x2, col_x3 = st.columns(3)
        with col_x1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Empresa</h4>", unsafe_allow_html=True)
            df_chart_emp = cross_filter('emp')
            if not df_chart_emp.empty:
                df_emp = df_chart_emp.groupby('EMPRESA').size().reset_index(name='Cant')
                df_emp['Etiqueta'] = df_emp['Cant'].astype(str) + " (" + (df_emp['Cant']/df_emp['Cant'].sum()*100).round(1).astype(str) + "%)"
                fig_emp = px.bar(df_emp, x='EMPRESA', y='Cant', text='Etiqueta', color_discrete_sequence=[paleta_neutra[0]])
                fig_emp.update_traces(hovertemplate="<b>%{x}</b><br>Dotación: %{text}<extra></extra>")
                fig_emp.update_layout(xaxis_title="", yaxis_title="Dotación", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                draw_safe_interactive_chart(fig_emp, "k_emp")

        with col_x2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Corte por Localidad</h4>", unsafe_allow_html=True)
            df_chart_loc = cross_filter('loc')
            if not df_chart_loc.empty:
                fig_loc = px.pie(df_chart_loc, names='LOCALIDAD', hole=0.4, color_discrete_sequence=paleta_neutra)
                fig_loc.update_traces(textinfo='value+percent', hovertemplate="<b>%{label}</b><br>Dotación: %{value} (%{percent})<extra></extra>")
                fig_loc.update_layout(font=dict(color="#475569"))
                draw_safe_interactive_chart(fig_loc, "k_loc")
                
        with col_x3:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Distribución por Área</h4>", unsafe_allow_html=True)
            df_chart_area = cross_filter('area')
            if not df_chart_area.empty:
                fig_area = px.pie(df_chart_area, names='AREA', hole=0.4, color_discrete_sequence=paleta_neutra)
                fig_area.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Dotación: %{value} (%{percent})<extra></extra>")
                fig_area.update_layout(font=dict(color="#475569"))
                draw_safe_interactive_chart(fig_area, "k_area")

        col_x4, col_x5 = st.columns(2)
        with col_x4:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Distribución por Antigüedad</h4>", unsafe_allow_html=True)
            df_chart_ant = cross_filter('ant')
            if not df_chart_ant.empty:
                res_ant = df_chart_ant['RANGO_ANTIGUEDAD'].value_counts().reindex(labels_ant).reset_index(name='CANTIDAD')
                res_ant['ETIQUETA'] = res_ant['CANTIDAD'].astype(str) + " (" + (res_ant['CANTIDAD']/res_ant['CANTIDAD'].sum()*100).round(1).astype(str) + "%)"
                fig_ant = px.bar(res_ant, x='RANGO_ANTIGUEDAD', y='CANTIDAD', text='ETIQUETA', color_discrete_sequence=[paleta_neutra[1]])
                fig_ant.update_traces(hovertemplate="<b>Rango: %{x}</b><br>Colaboradores: %{text}<extra></extra>")
                fig_ant.update_layout(xaxis_title="", yaxis_title="Cantidad", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                draw_safe_interactive_chart(fig_ant, "k_ant")

        with col_x5:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Top 10 Colaboradores por Líder</h4>", unsafe_allow_html=True)
            if col_lider:
                df_chart_lid = cross_filter('lid')
                if not df_chart_lid.empty:
                    df_lider = df_chart_lid.groupby(col_lider).size().reset_index(name='CANTIDAD')
                    df_lider = df_lider[df_lider[col_lider] != 'NO DECLARADO'].sort_values('CANTIDAD', ascending=False).head(10)
                    fig_lid = px.bar(df_lider, y=col_lider, x='CANTIDAD', text='CANTIDAD', orientation='h', color_discrete_sequence=[paleta_neutra[2]])
                    fig_lid.update_traces(hovertemplate="<b>Líder: %{y}</b><br>Personas a cargo: %{x}<extra></extra>")
                    fig_lid.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title="", xaxis_title="Personas", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                    draw_safe_interactive_chart(fig_lid, "k_lid")

        df_tabla_final = cross_filter('none')
        filtros_activos = [f for f in [f"Empresa: {sel_click_empresa}" if sel_click_empresa else "", f"Localidad: {sel_click_localidad}" if sel_click_localidad else "", f"Área: {sel_click_area}" if sel_click_area else "", f"Antigüedad: {sel_click_antiguedad}" if sel_click_antiguedad else "", f"Líder: {sel_click_lider}" if sel_click_lider else "", f"Categoría: {sel_click_categoria}" if sel_click_categoria else ""] if f]
        if filtros_activos:
            st.markdown(f"<div style='background:#f1f5f9; padding:15px; border-radius:8px; border-left: 4px solid #2563eb;'><b>↳ Nómina Interactiva ({len(df_tabla_final)} filtrados):</b> {' | '.join(filtros_activos)}</div><br>", unsafe_allow_html=True)
            st.dataframe(df_tabla_final[cols_nomina].sort_values(by=[c for c in ['EMPRESA', 'AREA', col_nombre] if c in df_tabla_final.columns]), use_container_width=True)

        st.divider()

        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Análisis Mensual de Ingresos y Egresos</h3>", unsafe_allow_html=True)
        
        if not df_historia.empty:
            opciones_drill = df_historia['Mes_Esp'].tolist()
            
            col_sel, _ = st.columns([1, 2])
            with col_sel: 
                meses_drill = st.multiselect("Seleccione uno o más periodos para auditar:", opciones_drill, default=opciones_drill)
                
            if not meses_drill:
                meses_drill = opciones_drill
                
            fechas_elegidas = df_historia[df_historia['Mes_Esp'].isin(meses_drill)]['Fecha']
            meses_num = fechas_elegidas.dt.month.tolist()
            anios_num = fechas_elegidas.dt.year.tolist()
            
            mask_altas = (df_filt['FECHA_ING_DT'].dt.year.isin(anios_num)) & (df_filt['FECHA_ING_DT'].dt.month.isin(meses_num))
            mask_bajas = (df_filt['FECHA_EGR_DT'].dt.year.isin(anios_num)) & (df_filt['FECHA_EGR_DT'].dt.month.isin(meses_num))
            
            altas_mes = df_filt[mask_altas].copy()
            bajas_mes = df_filt[mask_bajas].copy()
            label_periodo = f"{len(meses_drill)} Mes(es) Seleccionados"
            
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric(f"Altas en {label_periodo}", len(altas_mes))
            cm2.metric(f"Bajas en {label_periodo}", len(bajas_mes))
            cm3.metric("Crecimiento Neto", len(altas_mes) - len(bajas_mes), delta=len(altas_mes) - len(bajas_mes))

            if len(altas_mes) > 0 or len(bajas_mes) > 0:
                tab_altas, tab_bajas = st.tabs(["Análisis de Ingresos", "Análisis de Bajas"])
                
                with tab_altas:
                    if len(altas_mes) > 0:
                        altas_mes['UBICACION'] = altas_mes['EMPRESA'] + " - " + altas_mes['LOCALIDAD']
                        res_a = altas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='Cant')
                        res_a['Etiqueta'] = res_a['Cant'].astype(str) + " (" + (res_a['Cant']/res_a['Cant'].sum()*100).round(1).astype(str) + "%)"
                        fig_a = px.bar(res_a, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', color_discrete_sequence=paleta_neutra)
                        fig_a.update_traces(hovertemplate="<b>%{x}</b><br>Altas: %{text}<extra></extra>")
                        fig_a.update_layout(xaxis_title="", yaxis_title="Altas", plot_bgcolor='#ffffff', font=dict(color="#475569"))
                        st.plotly_chart(fig_a, use_container_width=True)
                        with st.expander("Ver detalle de colaboradores ingresantes"):
                            st.dataframe(altas_mes[[c for c in cols_base if c in altas_mes.columns]], use_container_width=True)
                
                with tab_bajas:
                    if len(bajas_mes) > 0:
                        bajas_mes['ANTIGÜEDAD AL EGRESO'] = (bajas_mes['FECHA_EGR_DT'] - bajas_mes['FECHA_ING_DT']).dt.days / 365.25
                        bajas_mes['< 1 AÑO'] = np.where(bajas_mes['ANTIGÜEDAD AL EGRESO'] < 1, '⚠️ Sí', 'No')
                        bajas_tempranas = len(bajas_mes[bajas_mes['ANTIGÜEDAD AL EGRESO'] < 1])
                        
                        if bajas_tempranas > 0:
                            st.markdown(f"<div style='background-color: #fef2f2; border-left: 4px solid #b91c1c; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><p style='color: #991b1b; font-weight: 600; font-size: 14px; margin: 0;'>Atención: {bajas_tempranas} colaborador(es) se dieron de baja con menos de 1 año de antigüedad. Esto representa el <b>{(bajas_tempranas / len(bajas_mes) * 100):.1f}%</b> del total de egresos en el periodo.</p></div>", unsafe_allow_html=True)
                        
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.markdown("<h4 style='font-size: 14px; font-weight: 600; color: #475569;'>Bajas por Sede y Área</h4>", unsafe_allow_html=True)
                            bajas_mes['UBICACION'] = bajas_mes['EMPRESA'] + " - " + bajas_mes['LOCALIDAD']
                            res_b = bajas_mes.groupby(['UBICACION', 'AREA']).size().reset_index(name='Cant')
                            res_b['Etiqueta'] = res_b['Cant'].astype(str) + " (" + (res_b['Cant']/res_b['Cant'].sum()*100).round(1).astype(str) + "%)"
                            fig_b = px.bar(res_b, x='UBICACION', y='Cant', color='AREA', text='Etiqueta', color_discrete_sequence=paleta_neutra)
                            fig_b.update_traces(hovertemplate="<b>%{x}</b><br>Bajas: %{text}<extra></extra>")
                            fig_b.update_layout(xaxis_title="", yaxis_title="Bajas", plot_bgcolor='#ffffff', font=dict(color="#475569"), margin=dict(t=10))
                            st.plotly_chart(fig_b, use_container_width=True)
                            
                        with col_b2:
                            st.markdown("<h4 style='font-size: 14px; font-weight: 600; color: #475569;'>Motivos de Baja</h4>", unsafe_allow_html=True)
                            res_mot = bajas_mes.groupby('MOTIVO DE EGRESO').size().reset_index(name='Cant')
                            fig_mot = px.pie(res_mot, names='MOTIVO DE EGRESO', values='Cant', hole=0.4, color_discrete_sequence=paleta_neutra)
                            fig_mot.update_traces(textinfo='value+percent', hovertemplate="<b>%{label}</b><br>Cantidad: %{value} (%{percent})<extra></extra>")
                            fig_mot.update_layout(font=dict(color="#475569"), margin=dict(t=10))
                            st.plotly_chart(fig_mot, use_container_width=True)

                        with st.expander("Ver detalle de colaboradores dados de baja"):
                            st.dataframe(bajas_mes[[c for c in cols_base + ['FECHA DE EGRESO', 'MOTIVO DE EGRESO', '< 1 AÑO'] if c in bajas_mes.columns]], use_container_width=True)

        st.divider()

        try:
            df_mov = load_data_mov()
            
            if 'FECHA_MOV_DT' in df_mov.columns:
                df_mov_periodo = df_mov[
                    (df_mov['FECHA_MOV_DT'].dt.year == anio_analisis) & 
                    (df_mov['FECHA_MOV_DT'].dt.month.isin(meses_sel))
                ].copy()
                
                if not df_mov_periodo.empty:
                    st.markdown(f"<h3 style='font-size: 18px; font-weight: 600;'>Movilidad Interna y Desarrollo de Talento</h3>", unsafe_allow_html=True)
                    st.markdown("<p style='font-size: 13px; color: #64748b;'>💡 <b>Consejo:</b> Haz clic en el gráfico de torta para auditar los resultados de las evaluaciones de potencial.</p>", unsafe_allow_html=True)

                    total_movs = len(df_mov_periodo)
                    df_mov_kpi = df_mov_periodo.merge(df_raw[[col_nombre, 'FECHA_EGR_DT']], left_on='NOMBRE', right_on=col_nombre, how='left')
                    df_mov_kpi['DIAS_POST_MOV'] = (df_mov_kpi['FECHA_EGR_DT'] - df_mov_kpi['FECHA_MOV_DT']).dt.days
                    
                    df_bajas_riesgo = df_mov_kpi[(df_mov_kpi['DIAS_POST_MOV'] >= 0) & (df_mov_kpi['DIAS_POST_MOV'] <= 365)].copy()
                    bajas_temp_mov = len(df_bajas_riesgo)
                    
                    if bajas_temp_mov > 0:
                        pct_fracaso = (bajas_temp_mov / total_movs) * 100
                        st.markdown(f"<div style='background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><p style='color: #b45309; font-weight: 600; font-size: 14px; margin: 0;'>⚠️ <b>Riesgo de Retención post-Movimiento:</b> {bajas_temp_mov} de los {total_movs} colaboradores movidos/promovidos (<b>{pct_fracaso:.1f}%</b>) se dieron de baja antes de cumplir 12 meses en su nuevo rol.</p></div>", unsafe_allow_html=True)
                        
                        with st.expander("Ver colaboradores que se dieron de baja tras movimiento/promoción", expanded=False):
                            df_bajas_riesgo['FECHA_EGR'] = df_bajas_riesgo['FECHA_EGR_DT'].dt.strftime('%d/%m/%Y')
                            df_bajas_riesgo['FECHA_MOV_STR'] = df_bajas_riesgo['FECHA_MOV_DT'].dt.strftime('%d/%m/%Y')
                            cols_show_riesgo = ['NOMBRE', 'TIPO_MOV', 'FECHA_MOV_STR', 'PUESTO_ORIGEN', 'PUESTO_DESTINO', 'FECHA_EGR', 'DIAS_POST_MOV']
                            st.dataframe(df_bajas_riesgo[cols_show_riesgo].rename(columns={'FECHA_MOV_STR': 'FECHA MOV.', 'FECHA_EGR': 'FECHA EGRESO', 'DIAS_POST_MOV': 'DÍAS DURACIÓN'}).sort_values('DÍAS DURACIÓN'), use_container_width=True)
                    else:
                        st.markdown(f"<div style='background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><p style='color: #15803d; font-weight: 600; font-size: 14px; margin: 0;'>✅ Excelente retención: Ningún talento promovido o reubicado en este periodo se ha dado de baja.</p></div>", unsafe_allow_html=True)

                    sel_click_tipo_mov = None
                    if 'k_tipo_mov' in st.session_state and isinstance(st.session_state.k_tipo_mov, dict) and st.session_state.k_tipo_mov.get('selection', {}).get('points'):
                        sel_click_tipo_mov = st.session_state.k_tipo_mov['selection']['points'][0].get('label')

                    col_m1, col_m2 = st.columns(2)
                    
                    with col_m1:
                        st.markdown("<h4 style='font-size: 14px; font-weight: 600; color: #475569;'>Distribución de Movimientos</h4>", unsafe_allow_html=True)
                        if 'TIPO_MOV' in df_mov_periodo.columns:
                            res_tipo_mov = df_mov_periodo.groupby('TIPO_MOV').size().reset_index(name='CANTIDAD')
                            fig_tipo_mov = px.pie(res_tipo_mov, names='TIPO_MOV', values='CANTIDAD', hole=0.4, color_discrete_sequence=paleta_neutra)
                            fig_tipo_mov.update_traces(textinfo='value+percent', hovertemplate="<b>%{label}</b><br>Cantidad: %{value} (%{percent})<extra></extra>")
                            fig_tipo_mov.update_layout(font=dict(color="#475569"), margin=dict(t=10))
                            draw_safe_interactive_chart(fig_tipo_mov, "k_tipo_mov")
                    
                    with col_m2:
                        if sel_click_tipo_mov:
                            df_eval = df_mov_periodo[df_mov_periodo['TIPO_MOV'] == sel_click_tipo_mov].copy()
                            titulo_eval = f"Evaluación de Potencial en: {sel_click_tipo_mov}"
                        else:
                            df_promo_default = df_mov_periodo[df_mov_periodo['TIPO_MOV'].str.contains('PROMOC', na=False, case=False)]
                            if not df_promo_default.empty:
                                df_eval = df_promo_default.copy()
                                titulo_eval = "Evaluación de Potencial en: PROMOCIONES"
                            else:
                                df_eval = df_mov_periodo.copy()
                                titulo_eval = "Evaluación de Potencial (Global)"

                        st.markdown(f"<h4 style='font-size: 14px; font-weight: 600; color: #475569;'>{titulo_eval}</h4>", unsafe_allow_html=True)
                        
                        if not df_eval.empty and 'POTENCIAL' in df_eval.columns:
                            df_eval['POTENCIAL'] = df_eval['POTENCIAL'].replace(['NAN', 'NO APLICA', 'NO DECLARADO', ''], 'SIN EVALUAR')
                            res_pot = df_eval.groupby('POTENCIAL').size().reset_index(name='CANTIDAD')
                            res_pot['ETIQUETA'] = res_pot['CANTIDAD'].astype(str) + " (" + (res_pot['CANTIDAD']/res_pot['CANTIDAD'].sum()*100).round(1).astype(str) + "%)"
                            
                            fig_pot = px.bar(res_pot, x='POTENCIAL', y='CANTIDAD', text='ETIQUETA', color='POTENCIAL', color_discrete_sequence=paleta_neutra)
                            fig_pot.update_traces(hovertemplate="<b>Potencial: %{x}</b><br>Cantidad: %{text}<extra></extra>")
                            fig_pot.update_layout(xaxis_title="Resultado de Evaluación", yaxis_title="Cantidad", plot_bgcolor='#ffffff', font=dict(color="#475569"), margin=dict(t=10), showlegend=False)
                            st.plotly_chart(fig_pot, use_container_width=True)
                        else:
                            st.info("No hay datos de evaluación para graficar en esta categoría.")
                
                    with st.expander("Ver detalle histórico de movimientos y promociones"):
                        cols_mov = [c for c in ['NOMBRE', 'TIPO_MOV', 'FECHA_MOV', 'EMP_ORIGEN', 'PUESTO_ORIGEN', 'EMP_DESTINO', 'AREA_DESTINO', 'PUESTO_DESTINO', 'POTENCIAL'] if c in df_mov_periodo.columns]
                        df_show_mov = df_mov_periodo.copy()
                        
                        if sel_click_tipo_mov:
                            df_show_mov = df_show_mov[df_show_mov['TIPO_MOV'] == sel_click_tipo_mov]
                            st.markdown(f"<div style='font-size:13px; color:#2563eb; margin-bottom:10px;'><b>Filtro activo:</b> Mostrando solo {sel_click_tipo_mov}</div>", unsafe_allow_html=True)
                            
                        st.dataframe(df_show_mov.sort_values(by='FECHA_MOV_DT', ascending=False)[cols_mov], use_container_width=True)
                else:
                    st.info("No hay registros de movimientos internos en el periodo seleccionado.")
            else:
                st.warning("No se detectó la columna de Fechas en la pestaña de Movimientos.")
        except Exception as e:
            st.error(f"Error al cargar módulo de movimientos. Detalle técnico: {e}")

    # ---------------------------------------------------------------------
    # TAB 2: ROTACIÓN Y RETENCIÓN
    # ---------------------------------------------------------------------
    with tab_rotacion:
        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Indicadores Clave de Rotación y Selección</h3>", unsafe_allow_html=True)
        
        dot_inicial_rot = len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= fecha_inicio_periodo))])
        dot_final_rot = dot_actual 
        dot_promedio_rot = (dot_inicial_rot + dot_final_rot) / 2
        dot_promedio_calc = dot_promedio_rot if dot_promedio_rot > 0 else 1
        
        bajas_periodo_rot = df_filt[
            (df_filt['FECHA_EGR_DT'] >= fecha_inicio_periodo) & 
            (df_filt['FECHA_EGR_DT'] <= fecha_corte) &
            (df_filt['FECHA_EGR_DT'].dt.month.isin(meses_sel))
        ].copy()
        
        tot_bajas_rot = len(bajas_periodo_rot)
        rot_total_pct = (tot_bajas_rot / dot_promedio_calc) * 100
        
        bajas_voluntarias_rot = bajas_periodo_rot[bajas_periodo_rot['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False)].copy()
        tot_bajas_vol_rot = len(bajas_voluntarias_rot)
        rot_vol_pct = (tot_bajas_vol_rot / dot_promedio_calc) * 100
        
        if not bajas_voluntarias_rot.empty:
            bajas_voluntarias_rot['ANTIGUEDAD_DIAS_EGR'] = (bajas_voluntarias_rot['FECHA_EGR_DT'] - bajas_voluntarias_rot['FECHA_ING_DT']).dt.days
            bajas_vol_temp_rot = bajas_voluntarias_rot[bajas_voluntarias_rot['ANTIGUEDAD_DIAS_EGR'] <= 365].copy()
            tot_bajas_vol_temp_rot = len(bajas_vol_temp_rot)
        else:
            bajas_vol_temp_rot = pd.DataFrame()
            tot_bajas_vol_temp_rot = 0
            
        rot_vol_temp_pct = (tot_bajas_vol_temp_rot / dot_promedio_calc) * 100

        # KPI EFECTIVIDAD SELECCIÓN GLOBAL
        if not bajas_periodo_rot.empty:
            bajas_prueba = len(bajas_periodo_rot[(bajas_periodo_rot['FECHA_EGR_DT'] - bajas_periodo_rot['FECHA_ING_DT']).dt.days <= 180])
        else:
            bajas_prueba = 0
            
        sobrevivientes_prueba = len(df_periodo[(fecha_corte - df_periodo['FECHA_ING_DT']).dt.days <= 180])
        poblacion_en_prueba = sobrevivientes_prueba + bajas_prueba
        efectividad_sel = 100 - ((bajas_prueba / poblacion_en_prueba * 100) if poblacion_en_prueba > 0 else 0)

        # KPI EFECTIVIDAD SELECCIÓN COMERCIAL
        if not bajas_periodo_rot.empty:
            bajas_prueba_com = len(bajas_periodo_rot[(bajas_periodo_rot['AREA'] == 'COMERCIAL') & ((bajas_periodo_rot['FECHA_EGR_DT'] - bajas_periodo_rot['FECHA_ING_DT']).dt.days <= 180)])
        else:
            bajas_prueba_com = 0
            
        sobrevivientes_prueba_com = len(df_periodo[((fecha_corte - df_periodo['FECHA_ING_DT']).dt.days <= 180) & (df_periodo['AREA'] == 'COMERCIAL')])
        poblacion_en_prueba_com = sobrevivientes_prueba_com + bajas_prueba_com
        efectividad_sel_com = 100 - ((bajas_prueba_com / poblacion_en_prueba_com * 100) if poblacion_en_prueba_com > 0 else 0)

        # CÁLCULOS DE STAFF Y OPERACIÓN
        df_staff = df_filt[df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        dot_ini_staff = len(df_staff[(df_staff['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((df_staff['FECHA_EGR_DT'].isna()) | (df_staff['FECHA_EGR_DT'] >= fecha_inicio_periodo))])
        dot_fin_staff = len(df_staff[(df_staff['FECHA_ING_DT'] <= fecha_corte) & ((df_staff['FECHA_EGR_DT'].isna()) | (df_staff['FECHA_EGR_DT'] > fecha_corte))])
        prom_staff = (dot_ini_staff + dot_fin_staff) / 2
        prom_staff_calc = prom_staff if prom_staff > 0 else 1
        bajas_staff = len(bajas_periodo_rot[bajas_periodo_rot['EMPRESA'].str.contains('LA LUZ', na=False, case=False)])
        rot_staff_pct = (bajas_staff / prom_staff_calc) * 100
        
        df_op = df_filt[~df_filt['EMPRESA'].str.contains('LA LUZ', na=False, case=False)]
        dot_ini_op = len(df_op[(df_op['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((df_op['FECHA_EGR_DT'].isna()) | (df_op['FECHA_EGR_DT'] >= fecha_inicio_periodo))])
        dot_fin_op = len(df_op[(df_op['FECHA_ING_DT'] <= fecha_corte) & ((df_op['FECHA_EGR_DT'].isna()) | (df_op['FECHA_EGR_DT'] > fecha_corte))])
        prom_op = (dot_ini_op + dot_fin_op) / 2
        prom_op_calc = prom_op if prom_op > 0 else 1
        bajas_op = len(bajas_periodo_rot[~bajas_periodo_rot['EMPRESA'].str.contains('LA LUZ', na=False, case=False)])
        rot_op_pct = (bajas_op / prom_op_calc) * 100

        cr1, cr2, cr3, cr_new, cr_com = st.columns(5)
        
        cr1.metric("Rotación Total", f"{rot_total_pct:.1f}%", f"{tot_bajas_rot} egresos")
        cr2.metric("Rotación Voluntaria", f"{rot_vol_pct:.1f}%", f"{tot_bajas_vol_rot} renuncias", delta_color="inverse")
        cr3.metric("Rot. Voluntaria Temprana", f"{rot_vol_temp_pct:.1f}%", f"{tot_bajas_vol_temp_rot} renuncias < 1 año", delta_color="inverse")
        
        def get_efectividad_html(label, score, bajas, pob):
            color = "#15803d" if score >= 90 else "#dc2626"
            bg = "#f0fdf4" if score >= 90 else "#fef2f2"
            return f"""
            <div style='background-color: {bg}; border: 1px solid {color}; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 100%; min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                <div style='color: #64748b; font-weight: 600; font-size: 13px; padding-bottom: 4px;'>{label}</div>
                <div style='color: {color}; font-weight: 700; font-size: 28px; line-height: 1.1;'>{score:.1f}%</div>
                <div style='color: {color}; font-size: 12px; font-weight: 500; padding-top: 4px;'>Obj: ≥90% | Bajas: {bajas} de {pob}</div>
            </div>
            """

        with cr_new:
            st.markdown(get_efectividad_html("Efectividad Selección", efectividad_sel, bajas_prueba, poblacion_en_prueba), unsafe_allow_html=True)
            
        with cr_com:
            st.markdown(get_efectividad_html("Efec. Sel. Comercial", efectividad_sel_com, bajas_prueba_com, poblacion_en_prueba_com), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cr4, cr5, cr6 = st.columns(3)
        cr4.metric("Dotación Promedio Global", f"{dot_promedio_rot:.1f}", f"Inicial: {dot_inicial_rot} | Final: {dot_final_rot}", delta_color="off")
        cr5.metric("Rotación de STAFF (La Luz)", f"{rot_staff_pct:.1f}%", f"{bajas_staff} bajas (Promedio: {prom_staff:.1f})")
        cr6.metric("Rotación de OPERACIÓN", f"{rot_op_pct:.1f}%", f"{bajas_op} bajas (Promedio: {prom_op:.1f})")
        
        st.divider()
        
        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Evolución Mensual de Rotación</h4>", unsafe_allow_html=True)
        if not df_historia.empty:
            tasas_rotacion_hist = []
            tasas_vol_hist = []
            tasas_temprana_hist = []
            
            for f in df_historia['Fecha']:
                mes_f = f.month
                ano_f = f.year
                ini_mes_f = pd.to_datetime(f"{ano_f}-{mes_f:02d}-01")
                
                d_ini = len(df_filt[(df_filt['FECHA_ING_DT'] <= ini_mes_f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= ini_mes_f))])
                d_fin = len(df_filt[(df_filt['FECHA_ING_DT'] <= f) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] > f))])
                prom = (d_ini + d_fin) / 2
                prom_c = prom if prom > 0 else 1
                
                bajas_m = df_filt[(df_filt['FECHA_EGR_DT'] >= ini_mes_f) & (df_filt['FECHA_EGR_DT'] <= f)]
                b_tot = len(bajas_m)
                
                bajas_v = bajas_m[bajas_m['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False)]
                b_vol = len(bajas_v)
                
                bajas_v_temp = bajas_v[(bajas_v['FECHA_EGR_DT'] - bajas_v['FECHA_ING_DT']).dt.days <= 365]
                b_temp = len(bajas_v_temp)
                
                tasas_rotacion_hist.append((b_tot / prom_c) * 100)
                tasas_vol_hist.append((b_vol / prom_c) * 100)
                tasas_temprana_hist.append((b_temp / prom_c) * 100)
                
            df_hist_rot = df_historia.copy()
            df_hist_rot['TASA_TOTAL'] = tasas_rotacion_hist
            df_hist_rot['TASA_VOL'] = tasas_vol_hist
            df_hist_rot['TASA_TEMP'] = tasas_temprana_hist
            
            tab_rot_tot, tab_rot_vol, tab_rot_temp = st.tabs(["Rotación Total", "Rotación Voluntaria", "Rotación Temprana (< 1 año)"])
            
            with tab_rot_tot:
                fig_rt = px.line(df_hist_rot, x='Fecha', y='TASA_TOTAL', markers=True, text='TASA_TOTAL')
                fig_rt.update_traces(textposition="top center", textfont_size=11, texttemplate='%{text:.1f}%', marker=dict(size=7, color="#b91c1c"), line=dict(color="#ef4444", width=2), hovertemplate="<b>%{y:.1f}% Rotación Total</b><extra></extra>")
                fig_rt.update_xaxes(title="", tickmode='array', tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45, showgrid=False)
                fig_rt.update_yaxes(title="Tasa (%)", showgrid=True, gridcolor='#f1f5f9')
                fig_rt.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60, t=10), font=dict(color="#475569"), height=250) 
                st.plotly_chart(fig_rt, use_container_width=True)
                
            with tab_rot_vol:
                fig_rv = px.line(df_hist_rot, x='Fecha', y='TASA_VOL', markers=True, text='TASA_VOL')
                fig_rv.update_traces(textposition="top center", textfont_size=11, texttemplate='%{text:.1f}%', marker=dict(size=7, color="#c2410c"), line=dict(color="#f97316", width=2), hovertemplate="<b>%{y:.1f}% Rotación Voluntaria</b><extra></extra>")
                fig_rv.update_xaxes(title="", tickmode='array', tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45, showgrid=False)
                fig_rv.update_yaxes(title="Tasa (%)", showgrid=True, gridcolor='#f1f5f9')
                fig_rv.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60, t=10), font=dict(color="#475569"), height=250) 
                st.plotly_chart(fig_rv, use_container_width=True)
                
            with tab_rot_temp:
                fig_rtemp = px.line(df_hist_rot, x='Fecha', y='TASA_TEMP', markers=True, text='TASA_TEMP')
                fig_rtemp.update_traces(textposition="top center", textfont_size=11, texttemplate='%{text:.1f}%', marker=dict(size=7, color="#a16207"), line=dict(color="#eab308", width=2), hovertemplate="<b>%{y:.1f}% Rotación Temprana</b><extra></extra>")
                fig_rtemp.update_xaxes(title="", tickmode='array', tickvals=df_hist_rot['Fecha'], ticktext=df_hist_rot['Mes_Esp'], tickangle=-45, showgrid=False)
                fig_rtemp.update_yaxes(title="Tasa (%)", showgrid=True, gridcolor='#f1f5f9')
                fig_rtemp.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60, t=10), font=dict(color="#475569"), height=250) 
                st.plotly_chart(fig_rtemp, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        sel_rot_tipo = None
        if 'k_rot_tipo' in st.session_state and isinstance(st.session_state.k_rot_tipo, dict):
            points = st.session_state.k_rot_tipo.get('selection', {}).get('points', [])
            if points: sel_rot_tipo = points[0].get('label')
            
        sel_rot_area = None
        if 'k_rot_area' in st.session_state and isinstance(st.session_state.k_rot_area, dict):
            points = st.session_state.k_rot_area.get('selection', {}).get('points', [])
            if points: sel_rot_area = points[0].get('y')

        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Composición de la Rotación</h4>", unsafe_allow_html=True)
            if tot_bajas_rot > 0:
                bajas_periodo_rot['TIPO_BAJA'] = np.where(bajas_periodo_rot['MOTIVO DE EGRESO'].str.contains('RENUNCIA|VOLUNTARI', na=False, case=False), 'Renuncia Voluntaria', 'Involuntaria / Otros Motivos')
                res_tipo = bajas_periodo_rot.groupby('TIPO_BAJA').size().reset_index(name='CANTIDAD')
                fig_tipo = px.pie(res_tipo, names='TIPO_BAJA', values='CANTIDAD', hole=0.4, color_discrete_sequence=['#ef4444', paleta_neutra[2]])
                fig_tipo.update_traces(textinfo='value+percent', hovertemplate="<b>%{label}</b><br>Bajas: %{value} (%{percent})<extra></extra>")
                fig_tipo.update_layout(font=dict(color="#475569"), margin=dict(t=10))
                draw_safe_interactive_chart(fig_tipo, "k_rot_tipo")
            else:
                st.info("No se registraron bajas en el periodo para analizar su composición.")
                
        with col_r2:
            st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Top Áreas con Mayor Fuga Voluntaria</h4>", unsafe_allow_html=True)
            if tot_bajas_vol_rot > 0:
                res_area_vol = bajas_voluntarias_rot.groupby('AREA').size().reset_index(name='CANTIDAD').sort_values('CANTIDAD', ascending=False).head(7)
                fig_area_vol = px.bar(res_area_vol, x='CANTIDAD', y='AREA', orientation='h', text='CANTIDAD', color_discrete_sequence=[paleta_neutra[1]])
                fig_area_vol.update_traces(hovertemplate="<b>Área: %{y}</b><br>Renuncias: %{text}<extra></extra>")
                fig_area_vol.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Renuncias", yaxis_title="", plot_bgcolor='#ffffff', font=dict(color="#475569"), margin=dict(t=10))
                draw_safe_interactive_chart(fig_area_vol, "k_rot_area")
            else:
                st.info("No se registraron renuncias voluntarias en el periodo.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>↳ Detalle Interactivo de Bajas</h4>", unsafe_allow_html=True)

        if tot_bajas_rot > 0:
            df_show_rot = bajas_periodo_rot.copy()
            filtros_rot = []
            
            if sel_rot_tipo:
                df_show_rot = df_show_rot[df_show_rot['TIPO_BAJA'] == sel_rot_tipo]
                filtros_rot.append(f"Tipo: {sel_rot_tipo}")
            if sel_rot_area:
                df_show_rot = df_show_rot[df_show_rot['AREA'] == sel_rot_area]
                filtros_rot.append(f"Área: {sel_rot_area}")

            if filtros_rot:
                st.markdown(f"<div style='background:#fef2f2; padding:15px; border-radius:8px; border-left: 4px solid #ef4444; margin-bottom:15px;'><b>Filtro activo ({len(df_show_rot)} resultados):</b> {' | '.join(filtros_rot)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 13px; color: #64748b;'>💡 <b>Consejo:</b> Haz clic en los gráficos superiores para filtrar esta tabla y auditar detalles específicos.</p>", unsafe_allow_html=True)

            if not df_show_rot.empty:
                def formatear_antiguedad(dias):
                    if pd.isna(dias) or dias < 0: return "Desconocida"
                    anios = int(dias // 365.25)
                    meses = int((dias % 365.25) // 30.416)
                    res = []
                    if anios > 0: res.append(f"{anios} año{'s' if anios > 1 else ''}")
                    if meses > 0: res.append(f"{meses} mes{'es' if meses > 1 else ''}")
                    if not res: return "Menos de 1 mes"
                    return " y ".join(res)
                
                df_show_rot['ANTIGÜEDAD'] = (df_show_rot['FECHA_EGR_DT'] - df_show_rot['FECHA_ING_DT']).dt.days.apply(formatear_antiguedad)
                df_show_rot['FECHA_EGR_STR'] = df_show_rot['FECHA_EGR_DT'].dt.strftime('%d/%m/%Y')
                
                cols_rot_show = [c for c in [col_nombre, 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'ANTIGÜEDAD', 'FECHA_EGR_STR', 'MOTIVO DE EGRESO'] if c in df_show_rot.columns]
                st.dataframe(df_show_rot[cols_rot_show].rename(columns={'FECHA_EGR_STR': 'FECHA EGRESO'}), use_container_width=True)
            else:
                st.info("No hay registros que coincidan con la selección de los gráficos.")

    # ---------------------------------------------------------------------
    # TAB 3: AUSENTISMO
    # ---------------------------------------------------------------------
    with tab_ausentismo:
        st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Indicadores Clave de Ausentismo</h3>", unsafe_allow_html=True)
        try:
            df_aus = load_data_ausentismo()
            if not df_aus.empty and 'FECHA_AUS_DT' in df_aus.columns:
                
                df_aus_periodo = df_aus[
                    (df_aus['FECHA_AUS_DT'].dt.year == anio_analisis) & 
                    (df_aus['FECHA_AUS_DT'].dt.month.isin(meses_sel))
                ].copy()
                
                if sel_emp and 'EMPRESA' in df_aus_periodo.columns: df_aus_periodo = df_aus_periodo[df_aus_periodo['EMPRESA'].isin(sel_emp)]
                if sel_loc and 'LOCALIDAD' in df_aus_periodo.columns: df_aus_periodo = df_aus_periodo[df_aus_periodo['LOCALIDAD'].isin(sel_loc)]
                if sel_area and 'AREA' in df_aus_periodo.columns: df_aus_periodo = df_aus_periodo[df_aus_periodo['AREA'].isin(sel_area)]
                
                total_ausencias = len(df_aus_periodo)
                total_dias_ausentes = df_aus_periodo['DIAS_AUSENCIA'].sum() if 'DIAS_AUSENCIA' in df_aus_periodo.columns else total_ausencias
                
                meses_contados = len(meses_sel)
                dot_promedio_aus = ((len(df_filt[(df_filt['FECHA_ING_DT'] <= fecha_inicio_periodo) & ((df_filt['FECHA_EGR_DT'].isna()) | (df_filt['FECHA_EGR_DT'] >= fecha_inicio_periodo))]) + dot_actual) / 2) if dot_actual > 0 else 1
                dias_teoricos_trabajados = dot_promedio_aus * 22 * meses_contados
                
                indice_ausentismo = (total_dias_ausentes / dias_teoricos_trabajados * 100) if dias_teoricos_trabajados > 0 else 0
                
                ca1, ca2, ca3, ca4 = st.columns(4)
                ca1.metric("Índice Ausentismo Estimado", f"{indice_ausentismo:.1f}%", f"{total_dias_ausentes:.1f} días perdidos", delta_color="inverse")
                ca2.metric("Total Eventos Registrados", total_ausencias, f"En {meses_contados} mes(es) sel.", delta_color="off")
                
                if 'MOTIVO_AUSENCIA' in df_aus_periodo.columns and not df_aus_periodo.empty:
                    top_mot = df_aus_periodo['MOTIVO_AUSENCIA'].value_counts()
                    ca3.metric("Motivo Principal", str(top_mot.index[0]), f"{top_mot.iloc[0]} casos", delta_color="off")
                else:
                    ca3.metric("Motivo Principal", "N/A")
                    
                if 'NOMBRE' in df_aus_periodo.columns and not df_aus_periodo.empty:
                    top_colab = df_aus_periodo.groupby('NOMBRE')['DIAS_AUSENCIA'].sum().sort_values(ascending=False)
                    if not top_colab.empty:
                        ca4.metric("Mayor Ausentismo (Colab.)", str(top_colab.index[0]), f"{top_colab.iloc[0]:.1f} días", delta_color="inverse")
                    else:
                        ca4.metric("Mayor Ausentismo (Colab.)", "N/A")
                else:
                    ca4.metric("Mayor Ausentismo (Colab.)", "N/A")
                    
                st.divider()
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Distribución por Motivo</h4>", unsafe_allow_html=True)
                    if 'MOTIVO_AUSENCIA' in df_aus_periodo.columns and not df_aus_periodo.empty:
                        res_mot_aus = df_aus_periodo.groupby('MOTIVO_AUSENCIA')['DIAS_AUSENCIA'].sum().reset_index(name='DIAS')
                        fig_mot_aus = px.pie(res_mot_aus, names='MOTIVO_AUSENCIA', values='DIAS', hole=0.4, color_discrete_sequence=paleta_neutra)
                        fig_mot_aus.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Días: %{value} (%{percent})<extra></extra>")
                        fig_mot_aus.update_layout(font=dict(color="#475569"), margin=dict(t=10))
                        st.plotly_chart(fig_mot_aus, use_container_width=True)
                        
                with col_a2:
                    st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Top 10 Áreas (Días Perdidos)</h4>", unsafe_allow_html=True)
                    if 'AREA' in df_aus_periodo.columns and not df_aus_periodo.empty:
                        res_area_aus = df_aus_periodo.groupby('AREA')['DIAS_AUSENCIA'].sum().reset_index(name='DIAS').sort_values('DIAS', ascending=False).head(10)
                        fig_area_aus = px.bar(res_area_aus, x='DIAS', y='AREA', orientation='h', text='DIAS', color_discrete_sequence=[paleta_neutra[2]])
                        fig_area_aus.update_traces(hovertemplate="<b>Área: %{y}</b><br>Días perdidos: %{text}<extra></extra>")
                        fig_area_aus.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Días Perdidos", yaxis_title="", plot_bgcolor='#ffffff', font=dict(color="#475569"), margin=dict(t=10))
                        st.plotly_chart(fig_area_aus, use_container_width=True)
                
                st.markdown("<br><h4 style='font-size: 15px; font-weight: 600;'>Evolución Mensual del Ausentismo (Días Perdidos)</h4>", unsafe_allow_html=True)
                df_aus_hist = df_aus[df_aus['FECHA_AUS_DT'].dt.year >= anio_analisis - 1].copy()
                if not df_aus_hist.empty:
                    df_aus_hist['Mes_Esp'] = df_aus_hist['FECHA_AUS_DT'].dt.month.map(meses_nombres) + " " + df_aus_hist['FECHA_AUS_DT'].dt.year.astype(str)
                    df_aus_hist['Periodo'] = df_aus_hist['FECHA_AUS_DT'].dt.to_period('M')
                    res_evol_aus = df_aus_hist.groupby('Periodo')['DIAS_AUSENCIA'].sum().reset_index()
                    res_evol_aus['Fecha'] = res_evol_aus['Periodo'].dt.to_timestamp()
                    res_evol_aus['Mes_Esp'] = res_evol_aus['Fecha'].dt.month.map(meses_nombres) + " " + res_evol_aus['Fecha'].dt.year.astype(str)
                    
                    fig_evol_aus = px.line(res_evol_aus, x='Fecha', y='DIAS_AUSENCIA', markers=True, text='DIAS_AUSENCIA')
                    fig_evol_aus.update_traces(textposition="top center", textfont_size=11, marker=dict(size=7, color="#ca8a04"), line=dict(color="#eab308", width=2), hovertemplate="<b>%{x}</b><br>%{y} Días<extra></extra>")
                    fig_evol_aus.update_xaxes(title="", tickmode='array', tickvals=res_evol_aus['Fecha'], ticktext=res_evol_aus['Mes_Esp'], tickangle=-45, showgrid=False)
                    fig_evol_aus.update_yaxes(title="Días Ausentes", showgrid=True, gridcolor='#f1f5f9')
                    fig_evol_aus.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', margin=dict(b=60, t=10), font=dict(color="#475569"), height=300) 
                    st.plotly_chart(fig_evol_aus, use_container_width=True)

                with st.expander("↳ Ver Nómina Interactiva de Ausentismo"):
                    if not df_aus_periodo.empty:
                        df_aus_periodo['FECHA_AUS_STR'] = df_aus_periodo['FECHA_AUS_DT'].dt.strftime('%d/%m/%Y')
                        cols_aus = [c for c in ['FECHA_AUS_STR', 'NOMBRE', 'EMPRESA', 'LOCALIDAD', 'AREA', 'PUESTO', 'MOTIVO_AUSENCIA', 'DIAS_AUSENCIA'] if c in df_aus_periodo.columns]
                        st.dataframe(df_aus_periodo.sort_values(by='FECHA_AUS_DT', ascending=False)[cols_aus].rename(columns={'FECHA_AUS_STR': 'FECHA AUSENTISMO'}), use_container_width=True)
            else:
                st.info("No se detectó columna de fechas o datos en la base de ausentismo para analizar.")
        except Exception as e:
            st.error(f"Error al cargar módulo de ausentismo. Detalle técnico: {e}")

except Exception as e:
    st.error(f"Error técnico general: {e}")
