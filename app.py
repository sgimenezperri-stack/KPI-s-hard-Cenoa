import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CSS
# =====================================================================
st.set_page_config(page_title="Dotación | Talent Hub", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #1e293b !important; }
    .main-title { color: #0f172a; font-weight: 700; font-size: 28px; margin-bottom: -5px; }
    .sub-title { color: #64748b; font-weight: 600; font-size: 12px; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 20px; }
    [data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    [data-testid="metric-container"] label { color: #64748b !important; font-weight: 500; }
    [data-testid="metric-container"] div { color: #1e293b !important; }
    hr { border-color: #e2e8f0; }
    .stExpander { background-color: #ffffff; border: 1px solid #e2e8f0 !important; border-radius: 6px !important; }
    </style>
""", unsafe_allow_html=True)

paleta_neutra = ['#2563eb', '#64748b', '#94a3b8', '#334155', '#cbd5e1', '#0f172a', '#e2e8f0']

# =====================================================================
# 2. CONEXIÓN A BASES DE DATOS
# =====================================================================
CSV_URL_DOTACION = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?output=csv"
CSV_URL_MOVIMIENTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTId4k_HPY240A63Nn2desUFZHUvEC4VB0Xnl4x0_JVFJUmduPilSBYMnjuIeTN3A/pub?gid=176641150&single=true&output=csv" 

@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
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
    # 3. ENCABEZADO Y FILTROS GLOBALES
    # =====================================================================
    col_icon, col_text = st.columns([0.5, 11.5])
    with col_icon:
        st.markdown("<div style='background-color: #0f172a; width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px; letter-spacing: 1px;'>TH</div>", unsafe_allow_html=True)
    with col_text:
        st.markdown("<div class='main-title'>Dotación</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Estructura Organizacional</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    df_filt = df_raw.copy()
    
    with f4: anio_analisis = st.selectbox("AÑO", [2026, 2025, 2024], index=0)
    with f5: 
        meses_nombres = {1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'}
        mes_sel = st.selectbox("MES", ["Todos"] + list(range(1, 13)), index=hoy.month, format_func=lambda x: "TODOS" if x == "Todos" else meses_nombres[x])
        
    # Lógica de cálculo si selecciona "Todos"
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
    
    # Inyección de las nuevas columnas solicitadas
    cols_base = ['CUIL', 'EMPRESA', 'LOCALIDAD', 'AREA', 'SUB AREA', 'PUESTO', 'CATEGORIA', 'CATEGORIA DE VARIABLE', 'FRECUENCIA DEL VARIABLE', 'FECHA DE INGRESO']
    if col_nombre: cols_base.insert(1, col_nombre)
    cols_nomina = [c for c in cols_base if c in df_periodo.columns]

    # =====================================================================
    # 4. CÁLCULO DE KPIS SUPERIORES
    # =====================================================================
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

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dotación en Periodo", dot_actual)
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

    with st.expander(f"Nómina completa y Búsqueda: {dot_actual} colaboradores", expanded=False):
        if not df_periodo.empty:
            col_b1, col_b2 = st.columns([1, 3])
            with col_b1:
                search_name = st.text_input("🔍 Buscar por Nombre:", placeholder="Ej: Perez...")
            
            df_show_nomina = df_periodo.copy()
            if search_name and col_nombre:
                df_show_nomina = df_show_nomina[df_show_nomina[col_nombre].str.contains(search_name, case=False, na=False)]
                
            sort_cols = [c for c in ['EMPRESA', 'AREA', col_nombre] if c in df_show_nomina.columns]
            st.dataframe(df_show_nomina[cols_nomina].sort_values(by=sort_cols), use_container_width=True)

    st.divider()

    # =====================================================================
    # 5. CROSS-FILTERING DASHBOARD (AHORA CON CATEGORÍA)
    # =====================================================================
    st.markdown("<h3 style='font-size: 18px; font-weight: 600;'>Paneles Interactivos (Cross-Filtering)</h3>", unsafe_allow_html=True)
    
    def draw_safe_interactive_chart(fig, unique_key):
        try: return st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=unique_key)
        except TypeError: return st.plotly_chart(fig, use_container_width=True)

    sel_click_empresa, sel_click_localidad, sel_click_antiguedad, sel_click_lider, sel_click_categoria = None, None, None, None, None
    if 'k_emp' in st.session_state and isinstance(st.session_state.k_emp, dict) and st.session_state.k_emp.get('selection', {}).get('points'): sel_click_empresa = st.session_state.k_emp['selection']['points'][0].get('x')
    if 'k_loc' in st.session_state and isinstance(st.session_state.k_loc, dict) and st.session_state.k_loc.get('selection', {}).get('points'): pt = st.session_state.k_loc['selection']['points'][0]; sel_click_localidad = pt.get('label', pt.get('x'))
    if 'k_ant' in st.session_state and isinstance(st.session_state.k_ant, dict) and st.session_state.k_ant.get('selection', {}).get('points'): sel_click_antiguedad = st.session_state.k_ant['selection']['points'][0].get('x')
    if 'k_lid' in st.session_state and isinstance(st.session_state.k_lid, dict) and st.session_state.k_lid.get('selection', {}).get('points'): sel_click_lider = st.session_state.k_lid['selection']['points'][0].get('y')
    if 'k_cat' in st.session_state and isinstance(st.session_state.k_cat, dict) and st.session_state.k_cat.get('selection', {}).get('points'): sel_click_categoria = st.session_state.k_cat['selection']['points'][0].get('x')

    def cross_filter(exclude_chart):
        df_x = df_periodo.copy()
        if exclude_chart != 'emp' and sel_click_empresa: df_x = df_x[df_x['EMPRESA'] == sel_click_empresa]
        if exclude_chart != 'loc' and sel_click_localidad: df_x = df_x[df_x['LOCALIDAD'] == sel_click_localidad]
        if exclude_chart != 'ant' and sel_click_antiguedad: df_x = df_x[df_x['RANGO_ANTIGUEDAD'] == sel_click_antiguedad]
        if exclude_chart != 'lid' and sel_click_lider and col_lider: df_x = df_x[df_x[col_lider] == sel_click_lider]
        if exclude_chart != 'cat' and sel_click_categoria and 'CATEGORIA' in df_x.columns: df_x = df_x[df_x['CATEGORIA'] == sel_click_categoria]
        return df_x

    col_x1, col_x2 = st.columns(2)
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

    col_x3, col_x4 = st.columns(2)
    with col_x3:
        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Distribución por Antigüedad</h4>", unsafe_allow_html=True)
        df_chart_ant = cross_filter('ant')
        if not df_chart_ant.empty:
            res_ant = df_chart_ant['RANGO_ANTIGUEDAD'].value_counts().reindex(labels_ant).reset_index(name='CANTIDAD')
            res_ant['ETIQUETA'] = res_ant['CANTIDAD'].astype(str) + " (" + (res_ant['CANTIDAD']/res_ant['CANTIDAD'].sum()*100).round(1).astype(str) + "%)"
            fig_ant = px.bar(res_ant, x='RANGO_ANTIGUEDAD', y='CANTIDAD', text='ETIQUETA', color_discrete_sequence=[paleta_neutra[1]])
            fig_ant.update_traces(hovertemplate="<b>Rango: %{x}</b><br>Colaboradores: %{text}<extra></extra>")
            fig_ant.update_layout(xaxis_title="", yaxis_title="Cantidad", plot_bgcolor='#ffffff', font=dict(color="#475569"))
            draw_safe_interactive_chart(fig_ant, "k_ant")

    with col_x4:
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
        else: st.info("No se detectó columna 'LIDER' o 'JEFE'.")

    col_x5, col_x6 = st.columns(2)
    with col_x5:
        st.markdown("<h4 style='font-size: 15px; font-weight: 600;'>Estructura por Categoría</h4>", unsafe_allow_html=True)
        df_chart_cat = cross_filter('cat')
        if not df_chart_cat.empty and 'CATEGORIA' in df_chart_cat.columns:
            df_cat = df_chart_cat.groupby('CATEGORIA').size().reset_index(name='CANTIDAD')
            df_cat['ETIQUETA'] = df_cat['CANTIDAD'].astype(str) + " (" + (df_cat['CANTIDAD']/df_cat['CANTIDAD'].sum()*100).round(1).astype(str) + "%)"
            fig_cat = px.bar(df_cat.sort_values('CANTIDAD', ascending=False), x='CATEGORIA', y='CANTIDAD', text='ETIQUETA', color_discrete_sequence=[paleta_neutra[3]])
            fig_cat.update_traces(hovertemplate="<b>Categoría: %{x}</b><br>Colaboradores: %{text}<extra></extra>")
            fig_cat.update_layout(xaxis_title="", yaxis_title="Cantidad", plot_bgcolor='#ffffff', font=dict(color="#475569"))
            draw_safe_interactive_chart(fig_cat, "k_cat")

    df_tabla_final = cross_filter('none')
    filtros_activos = [f for f in [f"Empresa: {sel_click_empresa}" if sel_click_empresa else "", f"Localidad: {sel_click_localidad}" if sel_click_localidad else "", f"Antigüedad: {sel_click_antiguedad}" if sel_click_antiguedad else "", f"Líder: {sel_click_lider}" if sel_click_lider else "", f"Categoría: {sel_click_categoria}" if sel_click_categoria else ""] if f]
    if filtros_activos:
        st.markdown(f"<div style='background:#f1f5f9; padding:15px; border-radius:8px; border-left: 4px solid #2563eb;'><b>↳ Nómina Interactiva ({len(df_tabla_final)} filtrados):</b> {' | '.join(filtros_activos)}</div><br>", unsafe_allow_html=True)
        st.dataframe(df_tabla_final[cols_nomina].sort_values(by=[c for c in ['EMPRESA', 'AREA', col_nombre] if c in df_tabla_final.columns]), use_container_width=True)

    st.divider()

    # =====================================================================
    # 7. MÓDULO: MOVILIDAD INTERNA Y DESARROLLO DE TALENTO
    # =====================================================================
    try:
        df_mov = load_data_mov()
        
        if 'FECHA_MOV_DT' in df_mov.columns:
            # Si eligió "Todos", toma todo el año. Si no, toma el mes exacto.
            if es_acumulado:
                df_mov_periodo = df_mov[df_mov['FECHA_MOV_DT'].dt.year == anio_analisis].copy()
            else:
                df_mov_periodo = df_mov[(df_mov['FECHA_MOV_DT'].dt.year == anio_analisis) & (df_mov['FECHA_MOV_DT'].dt.month == mes_calc)].copy()
            
            if not df_mov_periodo.empty:
                st.markdown(f"<h3 style='font-size: 18px; font-weight: 600;'>Movilidad Interna y Desarrollo de Talento</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 13px; color: #64748b;'>💡 <b>Consejo:</b> Haz clic en el gráfico de torta para auditar los resultados de las evaluaciones de potencial.</p>", unsafe_allow_html=True)

                # --- NUEVO KPI DE RIESGO DE RETENCIÓN ---
                total_movs = len(df_mov_periodo)
                df_mov_kpi = df_mov_periodo.merge(df_raw[[col_nombre, 'FECHA_EGR_DT']], left_on='NOMBRE', right_on=col_nombre, how='left')
                df_mov_kpi['DIAS_POST_MOV'] = (df_mov_kpi['FECHA_EGR_DT'] - df_mov_kpi['FECHA_MOV_DT']).dt.days
                bajas_temp_mov = len(df_mov_kpi[(df_mov_kpi['DIAS_POST_MOV'] >= 0) & (df_mov_kpi['DIAS_POST_MOV'] <= 365)])
                
                if bajas_temp_mov > 0:
                    pct_fracaso = (bajas_temp_mov / total_movs) * 100
                    st.markdown(f"<div style='background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><p style='color: #b45309; font-weight: 600; font-size: 14px; margin: 0;'>⚠️ <b>Riesgo de Retención de Talento:</b> {bajas_temp_mov} de los {total_movs} movimientos/promociones del periodo (<b>{pct_fracaso:.1f}%</b>) resultaron en una baja antes de cumplir 12 meses en el nuevo rol.</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><p style='color: #15803d; font-weight: 600; font-size: 14px; margin: 0;'>✅ Excelente retención: Ningún talento promovido o reubicado en este periodo se ha dado de baja.</p></div>", unsafe_allow_html=True)

                sel_click_tipo = None
                if 'k_tipo' in st.session_state and isinstance(st.session_state.k_tipo, dict) and st.session_state.k_tipo.get('selection', {}).get('points'):
                    sel_click_tipo = st.session_state.k_tipo['selection']['points'][0].get('label')

                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    st.markdown("<h4 style='font-size: 14px; font-weight: 600; color: #475569;'>Distribución de Movimientos</h4>", unsafe_allow_html=True)
                    if 'TIPO_MOV' in df_mov_periodo.columns:
                        res_tipo = df_mov_periodo.groupby('TIPO_MOV').size().reset_index(name='CANTIDAD')
                        fig_tipo = px.pie(res_tipo, names='TIPO_MOV', values='CANTIDAD', hole=0.4, color_discrete_sequence=paleta_neutra)
                        fig_tipo.update_traces(textinfo='value+percent', hovertemplate="<b>%{label}</b><br>Cantidad: %{value} (%{percent})<extra></extra>")
                        fig_tipo.update_layout(font=dict(color="#475569"), margin=dict(t=10))
                        draw_safe_interactive_chart(fig_tipo, "k_tipo")
                
                with col_m2:
                    if sel_click_tipo:
                        df_eval = df_mov_periodo[df_mov_periodo['TIPO_MOV'] == sel_click_tipo].copy()
                        titulo_eval = f"Evaluación de Potencial en: {sel_click_tipo}"
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
                    
                    if sel_click_tipo:
                        df_show_mov = df_show_mov[df_show_mov['TIPO_MOV'] == sel_click_tipo]
                        st.markdown(f"<div style='font-size:13px; color:#2563eb; margin-bottom:10px;'><b>Filtro activo:</b> Mostrando solo {sel_click_tipo}</div>", unsafe_allow_html=True)
                        
                    st.dataframe(df_show_mov.sort_values(by='FECHA_MOV_DT', ascending=False)[cols_mov], use_container_width=True)
            else:
                st.info("No hay registros de movimientos internos en el periodo seleccionado.")
        else:
            st.warning("No se detectó la columna de Fechas en la pestaña de Movimientos.")
    except Exception as e:
        st.error(f"Error al cargar módulo de movimientos. Detalle técnico: {e}")

except Exception as e:
    st.error(f"Error técnico general: {e}")
