# Importamos las librerías necesarias
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
# Aquí definimos el título de la pestaña del navegador y que ocupe todo el ancho de la pantalla
st.set_page_config(page_title="Resultados EvAU La Salle Griñón", layout="wide")

# 2. TÍTULO PRINCIPAL
st.title("📊 Resultados EvAU - La Salle Griñón")

# 3. MENÚ DE NAVEGACIÓN (BARRA LATERAL)
st.sidebar.title("Navegación")
# Creamos botones de selección (radio buttons) para las distintas vistas
opcion = st.sidebar.radio(
    "Selecciona una vista:",
    [
        "Nº Presentados por Año", 
        "Comparación por Centros", 
        "Por Materias", 
        "Por Años"
    ]
)

# 4. LÓGICA DE LAS SECCIONES
# Dependiendo de lo que elija el usuario en el menú, mostramos una cosa u otra

if opcion == "Nº Presentados por Año":
    st.header("📈 Evolución de presentados en PAU/EvAU por año")
    
    try:
        # 1. Cargamos el archivo de datos. 
        # Si tu archivo está en formato Excel, usaríamos pd.read_excel("Histórico EvAU.xlsx")
        df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Fase General")
        
        # 2. Limpieza de datos:
        # La primera columna contiene el año (ej. 23-24) pero en tu archivo no tiene nombre de cabecera.
        # Vamos a renombrarla a "Curso" para poder usarla fácilmente.
        df.rename(columns={df.columns[0]: 'Curso'}, inplace=True)
        
        # Limpiamos posibles espacios en blanco sobrantes en los textos para evitar errores de búsqueda
        df['Materia'] = df['Materia'].astype(str).str.strip()
        
        # 3. Filtrado:
        # Buscamos la fila "Fase General" que nos da el total de presentados por curso escolar.
        df_totales = df[df['Materia'] == 'Fase General'].copy()
        
        # Eliminamos las filas donde no haya un año definido (por si hay filas en blanco en tu archivo)
        df_totales = df_totales.dropna(subset=['Curso'])
        
        # Ordenamos los datos para que los años aparezcan cronológicamente
        df_totales = df_totales.sort_values(by='Curso')
        
        # 4. Creación de la gráfica interactiva:
        fig = px.bar(
            df_totales, 
            x="Curso", 
            y="Presentados", 
            text="Presentados", # Esto dibuja el número total encima de cada barra
            title="Número de Alumnos Presentados (Fase General) por Curso Escolar",
            labels={"Curso": "Curso Escolar", "Presentados": "Nº de Alumnos"},
            color_discrete_sequence=["#1f77b4"]
        )
        
        # Mejoramos el aspecto visual para que el texto resalte fuera de la barra
        fig.update_traces(textposition='outside')
        
        # 5. Mostramos la gráfica final en nuestra página web
        st.plotly_chart(fig, use_container_width=True)
        
        # Añadimos un menú desplegable oculto con la tabla de datos por si alguien quiere ver los números en crudo
        with st.expander("Ver tabla de datos detallada"):
            st.dataframe(df_totales[["Curso", "Presentados"]], use_container_width=True)
            
    except FileNotFoundError:
        st.error("⚠️ No se ha encontrado el archivo. Por favor, asegúrate de tener un archivo llamado 'Historico_EvAU.xlsx' en tu carpeta del proyecto.")
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el código: {e}")
elif opcion == "Comparación por Centros":
    st.header("🏫 Comparación con otros centros")
    
    try:
        # 1. Cargamos el archivo de Excel apuntando a la pestaña específica
        # NOTA: Asegúrate de que el nombre "Otros Coles" coincide exactamente con tu pestaña de Excel
        raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Otros Coles", header=None)
        
        # 2. Procesamiento de cabeceras dobles (Años y Métricas)
        # Extraemos los nombres de los colegios (están a partir de la fila index 3, columna 0)
        centros = raw_df.iloc[3:, 0].dropna().values
        
        # Rellenamos los años hacia la derecha (ffill) porque en Excel suelen estar en celdas combinadas
        años = pd.Series(raw_df.iloc[0, :].values).ffill().values
        metricas = raw_df.iloc[1, :].values
        
        # Creamos una lista limpia para reestructurar los datos
        datos_limpios = []
        
        # Recorremos cada fila de colegios
        for i, centro in enumerate(centros):
            fila_idx = i + 3  # Los datos de los colegios empiezan en la fila 3 (index)
            
            # Recorremos cada columna de datos (empezando en la columna 1)
            for col_idx in range(1, raw_df.shape[1]):
                año = años[col_idx]
                metrica = metricas[col_idx]
                valor = raw_df.iloc[fila_idx, col_idx]
                
                # Si la celda no está vacía, procesamos el número
                if pd.notna(valor) and str(valor).strip() != "" and str(valor).strip() != "nan":
                    # Limpieza de formato de texto/comas de Excel
                    if isinstance(valor, str):
                        valor = valor.replace('"', '').replace("'", "").replace(",", ".").strip()
                    
                    try:
                        valor_numerico = float(valor)
                        datos_limpios.append({
                            "Centro": str(centro).strip(),
                            "Curso": str(año).strip(),
                            "Métrica": str(metrica).strip(),
                            "Valor": valor_numerico
                        })
                    except ValueError:
                        # Si hay un texto que no se puede convertir a número, lo saltamos de forma segura
                        pass
        
        # Convertimos la lista en un DataFrame de Pandas estructurado
        df_clean = pd.DataFrame(datos_limpios)
        
        # Mapeamos los nombres exactos de tus columnas de Excel para que el menú sea amigable
        # Esto asegura que encuentre exactamente el texto de tu segunda fila
        lista_metricas_disponibles = df_clean["Métrica"].unique()
        
        # 3. Interfaz de usuario: Desplegable para seleccionar qué comparar
        metrica_sel = st.selectbox(
            "Selecciona la métrica que deseas comparar visualmente:", 
            lista_metricas_disponibles
        )
        
        # 4. Filtramos los datos por la métrica elegida
        df_filtrado = df_clean[df_clean["Métrica"] == metrica_sel]
        
        # Ordenamos por curso para que la línea de la gráfica evolucione cronológicamente de izquierda a derecha
        df_filtrado = df_filtrado.sort_values(by="Curso")
        
        # 5. Creamos la gráfica de líneas interactiva con Plotly
        fig2 = px.line(
            df_filtrado, 
            x="Curso", 
            y="Valor", 
            color="Centro",        # Una línea de diferente color para cada colegio
            markers=True,          # Añade puntitos en cada año para pinchar con el ratón
            title=f"Evolución Histórica Comparada: {metrica_sel}",
            labels={"Curso": "Curso Académico", "Valor": "Resultado / Nota", "Centro": "Centro Educativo"}
        )
        
        # Mejoramos el diseño de la gráfica para que se vea más limpia y moderna
        fig2.update_layout(hovermode="x unified")
        
        # Mostramos la gráfica en la aplicación web
        st.plotly_chart(fig2, use_container_width=True)
        
        # Extra: Desplegable opcional para ver los datos limpios en formato tabla
        with st.expander("Ver tabla de datos procesados"):
            st.dataframe(df_filtrado, use_container_width=True)
            
    except FileNotFoundError:
        st.error("⚠️ No se ha encontrado el archivo 'Historico_EvAU.xlsx' en la carpeta del proyecto.")
    except KeyError:
        st.error("⚠️ No se encontró la pestaña 'Otros Coles'. Revisa que el nombre en tu Excel sea exacto.")
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error inesperado al procesar los datos: {e}")

elif opcion == "Por Materias":
    st.header("📚 Resultados por Materia")
    # Submenú para elegir la asignatura
    materia = st.selectbox(
        "Selecciona la materia que deseas consultar:", 
        ["Lengua", "Inglés", "Historia", "Mate II", "Mate CCSS II", "Física", "Química", "Biología", "Dibujo Técnico", "Economía", "Filosofía", "Historia del Arte", "Geografía", "Francés"]
    )
    st.write(f"Mostrando estadísticas para: **{materia}**")
    # Lógica futura: pd.read_csv(f"Histórico EvAU - {materia}.csv")

elif opcion == "Por Años":
    st.header("📅 Resultados detallados por Año")
    st.write("Desglose completo de todas las asignaturas para un curso escolar en concreto.")
    # Lógica futura para filtrar "Histórico EvAU - Por año.csv"