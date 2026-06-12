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
                with st.expander(f"Ver tabla de datos detallada: {metrica_sel}"):
                    try:
                        # Transformamos los datos para que los centros sean las filas y los años las columnas
                        df_tabla = df_filtrado.pivot(index="Centro", columns="Curso", values="Valor")
                        
                        # Mostramos la tabla en la web
                        st.dataframe(df_tabla, use_container_width=True)
                    except Exception as e:
                        # Por si hay algún dato duplicado raro en el Excel que impida hacer la tabla
                        st.dataframe(df_filtrado[["Centro", "Curso", "Valor"]], use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el archivo: {e}")

elif opcion == "Por Materias":
    st.header("📚 Resultados por Materia")
    
    try:
        # 1. Leer las hojas disponibles en el Excel dinámicamente
        xls = pd.ExcelFile("Historico_EvAU.xlsx")
        
        # Excluimos las pestañas que no son asignaturas individuales
        hojas_excluir = ["Fase General", "Titulan", "Otros Coles", "Por año", "Por Año"]
        materias_disponibles = [hoja for hoja in xls.sheet_names if hoja not in hojas_excluir]
        
        if not materias_disponibles:
            st.warning("No se han encontrado pestañas de materias en el archivo Excel.")
        else:
            # 2. Menú desplegable para elegir la asignatura
            materia_sel = st.selectbox("Selecciona la materia para ver su análisis detallado:", materias_disponibles)
            
            # 3. Leer los datos de la pestaña seleccionada
            df_mat = pd.read_excel(xls, sheet_name=materia_sel)
            
            # Limpiamos los nombres de las columnas por si hay espacios invisibles
            df_mat.columns = [str(c).strip() for c in df_mat.columns]
            
            # Renombramos la primera columna a "Curso"
            df_mat.rename(columns={df_mat.columns[0]: 'Curso'}, inplace=True)
            df_mat = df_mat.dropna(subset=['Curso'])
            df_mat = df_mat.sort_values(by='Curso')
            
            # Función para limpiar los números (quitar %, cambiar comas por puntos)
            def limpiar_numeros(val):
                if pd.isna(val) or str(val).strip() == "": 
                    return None
                val_str = str(val).replace("%", "").replace(",", ".").strip()
                try: 
                    return float(val_str)
                except ValueError: 
                    return None
                
            # Aplicamos la limpieza a las columnas clave que vamos a graficar
            cols_graficas = ["% LSG", "NM LSG EvAU", "NM LSG Cole", "% UC3M", "NM UC3M"]
            for col in cols_graficas:
                if col in df_mat.columns:
                    df_mat[col] = df_mat[col].apply(limpiar_numeros)
            
            st.divider() # Añade una línea separadora elegante
            st.subheader(f"Estadísticas Históricas: {materia_sel}")
            
            # 4. DISEÑO EN CUADRÍCULA (2 columnas)
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfica 1: Nota media histórica de la materia (Columnas)
                if "NM LSG EvAU" in df_mat.columns:
                    fig1 = px.bar(df_mat, x="Curso", y="NM LSG EvAU", 
                                  title="1. Nota Media de la Materia (EvAU)",
                                  text="NM LSG EvAU",
                                  color_discrete_sequence=["#2ca02c"]) # Color verde
                    fig1.update_traces(textposition='outside')
                    fig1.update_layout(xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig1, use_container_width=True)
                
                # Gráfica 3: Nota Media EvAU: LSG vs UC3M (Líneas comparativas)
                if "NM LSG EvAU" in df_mat.columns and "NM UC3M" in df_mat.columns:
                    fig3 = px.line(df_mat, x="Curso", y=["NM LSG EvAU", "NM UC3M"], 
                                   title="3. Nota Media EvAU: LSG vs Media UC3M",
                                   markers=True,
                                   labels={"value": "Nota Media", "variable": "Institución"})
                    fig3.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig3, use_container_width=True)

            with col2:
                # Gráfica 2: % Aprobados: LSG vs UC3M (Líneas comparativas)
                if "% LSG" in df_mat.columns and "% UC3M" in df_mat.columns:
                    fig2 = px.line(df_mat, x="Curso", y=["% LSG", "% UC3M"], 
                                   title="2. % de Aprobados: LSG vs Media UC3M",
                                   markers=True,
                                   labels={"value": "% Aprobados", "variable": "Institución"})
                    fig2.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Gráfica 4: Nota Media: EvAU vs Colegio (Líneas comparativas)
                if "NM LSG EvAU" in df_mat.columns and "NM LSG Cole" in df_mat.columns:
                    fig4 = px.line(df_mat, x="Curso", y=["NM LSG EvAU", "NM LSG Cole"], 
                                   title="4. Desviación de Nota: EvAU vs Colegio (LSG)",
                                   markers=True,
                                   labels={"value": "Nota Media", "variable": "Evaluación"})
                    fig4.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig4, use_container_width=True)
                    
            # 5. Añadimos la tabla de datos procesados al final
            with st.expander(f"Ver tabla de datos detallada de {materia_sel}"):
                # Filtramos para mostrar solo las columnas que existen en esta asignatura
                cols_mostrar = ["Curso"] + [c for c in cols_graficas if c in df_mat.columns]
                st.dataframe(df_mat[cols_mostrar], use_container_width=True)
                
    except FileNotFoundError:
        st.error("⚠️ No se ha encontrado el archivo 'Historico_EvAU.xlsx'.")
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar las materias: {e}")
elif opcion == "Por Años":
    st.header("📅 Resultados detallados por Año")
    st.info("¡Sección en construcción! Más adelante programaremos esta vista detallada.")