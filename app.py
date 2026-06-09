import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Resultados EvAU La Salle Griñón", layout="wide")

st.title("📊 Resultados EvAU - La Salle Griñón")

# --- 2. MENÚ LATERAL ---
st.sidebar.title("Navegación")
opcion = st.sidebar.radio(
    "Selecciona una vista:",
    [
        "Nº Presentados por Año", 
        "Comparación por Centros", 
        "Por Materias", 
        "Por Años"
    ]
)

# --- 3. LÓGICA DE LAS SECCIONES ---

if opcion == "Nº Presentados por Año":
    st.header("📈 Evolución de presentados en PAU/EvAU por año")
    
    try:
        # Cargamos la pestaña donde están los datos generales de presentación.
        # Ajusta "Fase General" o "Titulan" según cómo se llame la pestaña en tu Excel.
        df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Fase General")
        
        # Renombramos la primera columna para que se llame "Curso"
        df.rename(columns={df.columns[0]: 'Curso'}, inplace=True)
        
        # Limpiamos posibles espacios en blanco en la columna Materia
        if 'Materia' in df.columns:
            df['Materia'] = df['Materia'].astype(str).str.strip()
            df_totales = df[df['Materia'] == 'Fase General'].copy()
        else:
            df_totales = df.copy() # Si no hay columna materia, asumimos que todos los datos son válidos
            
        # Eliminamos filas sin año y ordenamos cronológicamente
        df_totales = df_totales.dropna(subset=['Curso'])
        df_totales = df_totales.sort_values(by='Curso')
        
        # Creación de la gráfica de columnas interactiva
        fig = px.bar(
            df_totales, 
            x="Curso", 
            y="Presentados", 
            text="Presentados",
            title="Número de Alumnos Presentados (Fase General) por Curso Escolar",
            labels={"Curso": "Curso Escolar", "Presentados": "Nº de Alumnos"},
            color_discrete_sequence=["#1f77b4"]
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis={'categoryorder':'category ascending'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Ver tabla de datos detallada"):
            st.dataframe(df_totales, use_container_width=True)
            
    except FileNotFoundError:
        st.error("⚠️ No se ha encontrado el archivo 'Historico_EvAU.xlsx'.")
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el código: {e}")

elif opcion == "Comparación por Centros":
    st.header("🏫 Comparación con otros centros")
    
    try:
        # Leemos el archivo en bruto apuntando a la pestaña "Otros Coles"
        raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Otros Coles", header=None)
        
        # Limpiamos filas que estén 100% en blanco
        raw_df = raw_df.dropna(how='all').reset_index(drop=True)
        
        # 1. Buscamos automáticamente dónde empiezan los colegios
        start_idx = -1
        for i in range(len(raw_df)):
            val = str(raw_df.iloc[i, 0]).strip().upper()
            if val in ["CAM", "LSG", "CASTILLA", "IES GRIÑÓN", "VILLA GRIÑÓN", "CATÓN", "IES CUBAS"]:
                start_idx = i
                break
                
        if start_idx == -1:
            st.error("⚠️ No se pudo detectar el inicio de los datos en la primera columna.")
        else:
            # 2. Rescatamos los años (fila 0) y rellenamos hacia la derecha
            años = pd.Series(raw_df.iloc[0, :].values).ffill().values
            
            # 3. Forzamos LAS VARIABLES EXACTAS
            lista_metricas_oficial = [
                "% Titulados Bach", 
                "%Aprobados EvAU", 
                "Presentados EvAU", 
                "Media EvAU Aprobados", 
                "Media FG"
            ]
            
            datos_limpios = []
            
            # 4. Procesamos fila por fila y columna por columna
            for i in range(start_idx, len(raw_df)):
                centro = str(raw_df.iloc[i, 0]).strip()
                if pd.isna(raw_df.iloc[i, 0]) or centro == "nan" or centro == "":
                    continue
                    
                for col_idx in range(1, len(raw_df.columns)):
                    año = str(años[col_idx]).strip()
                    
                    if año == "nan" or año == "" or len(año) < 4:
                        continue
                        
                    # Calculamos qué métrica es según su posición
                    metrica_actual = lista_metricas_oficial[(col_idx - 1) % 5]
                    valor = raw_df.iloc[i, col_idx]
                    
                    # 5. Limpiamos las comas por puntos
                    if pd.notna(valor) and str(valor).strip() != "":
                        if isinstance(valor, str):
                            valor = valor.replace('"', '').replace("'", "").replace(",", ".").strip()
                        try:
                            datos_limpios.append({
                                "Centro": centro,
                                "Curso": año,
                                "Métrica": metrica_actual,
                                "Valor": float(valor)
                            })
                        except ValueError:
                            pass 
                            
            # Convertimos a DataFrame
            df_clean = pd.DataFrame(datos_limpios)
            
            if df_clean.empty:
                st.warning("No se pudieron procesar los números. Comprueba los datos de la pestaña.")
            else:
                # --- INTERFAZ ---
                metrica_sel = st.selectbox(
                    "Selecciona la métrica que deseas comparar visualmente:", 
                    lista_metricas_oficial
                )
                
                df_filtrado = df_clean[df_clean["Métrica"] == metrica_sel]
                df_filtrado = df_filtrado.sort_values(by="Curso")
                
                # Gráfica de columnas agrupadas
                fig2 = px.bar(
                    df_filtrado, 
                    x="Curso", 
                    y="Valor", 
                    color="Centro", 
                    barmode="group",
                    title=f"Evolución Histórica Comparada: {metrica_sel}",
                    labels={"Curso": "Curso Académico", "Valor": "Resultado / Nota", "Centro": "Centro Educativo"}
                )
                
                fig2.update_layout(
                    hovermode="x unified",
                    xaxis={'categoryorder':'category ascending'}
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el archivo: {e}")

elif opcion == "Por Materias":
    st.header("📚 Resultados por Materia")
    st.info("¡Sección en construcción! El siguiente paso será programar esta pestaña.")

elif opcion == "Por Años":
    st.header("📅 Resultados detallados por Año")
    st.info("¡Sección en construcción! Más adelante programaremos esta vista detallada.")