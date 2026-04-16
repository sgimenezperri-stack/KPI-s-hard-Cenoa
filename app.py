# Función para cargar datos en caché
@st.cache_data(ttl=3600) # Actualiza cada 1 hora
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQhx1mzO6cExRA4rtOkPx3t7CU1Ubvy0GVegOZpKv2KYe8E3vf6Z-Vb6y4xYjlLdg/pub?output=xlsx"
    
    try:
        # Cargar el archivo Excel completo para leer los nombres reales de las solapas
        xls = pd.ExcelFile(url)
        nombres_solapas = xls.sheet_names
        
        # Buscar los nombres reales ignorando mayúsculas, minúsculas o espacios
        nombre_dot = next((s for s in nombres_solapas if 'DOTACION' in s.upper()), None)
        nombre_rot = next((s for s in nombres_solapas if 'ROTACION' in s.upper()), None)
        nombre_baj = next((s for s in nombres_solapas if 'BAJAS' in s.upper()), None)

        # Si no encuentra la solapa, frena y te muestra qué solapas está leyendo realmente
        if not nombre_dot:
            st.error(f"No se encontró la solapa de Dotación. Solapas reales que lee el sistema: {nombres_solapas}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        df_dotacion = pd.read_excel(url, sheet_name=nombre_dot)
        df_rotacion = pd.read_excel(url, sheet_name=nombre_rot)
        df_bajas = pd.read_excel(url, sheet_name=nombre_baj)
        
        return df_dotacion, df_rotacion, df_bajas
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
