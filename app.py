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
        # Leemos el archivo en bruto
        raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Otros Coles", header=None)
        
        # Limpiamos filas que estén 100% en blanco para evitar descuadres
        raw_df = raw_df.dropna(how='all').reset_index(drop=True)
        
        # 1. Buscamos automáticamente dónde empiezan los colegios para no depender de una fila fija
        start_idx = -1
        for i in range(len(raw_df)):
            val = str(raw_df.iloc[i, 0]).strip().upper()
            # Si encuentra uno de estos nombres, sabemos que aquí empiezan los datos reales
            if val in ["CAM", "LSG", "CASTILLA", "IES GRIÑÓN", "VILLA GRIÑÓN", "CATÓN", "IES CUBAS"]:
                start_idx = i
                break
                
        if start_idx == -1:
            st.error("⚠️ No se pudo detectar el inicio de los datos en la primera columna.")
        else:
            # 2. Rescatamos los años. En tu archivo están arriba del todo (fila 0).
            # ffill() rellena los años hacia la derecha para cubrir las celdas combinadas de Excel
            años = pd.Series(raw_df.iloc[0, :].values).ffill().values
            
            # 3. Forzamos LAS VARIABLES EXACTAS que me has indicado
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
                # Saltamos si no hay centro
                if pd.isna(raw_df.iloc[i, 0]) or centro == "nan" or centro == "":
                    continue
                    
                # Recorremos cada columna de datos (empezando por la 1, donde están las notas)
                for col_idx in range(1, len(raw_df.columns)):
                    año = str(años[col_idx]).strip()
                    
                    # Ignoramos columnas fuera de los años (por si Excel lee columnas extra a la derecha)
                    if año == "nan" or año == "" or len(año) < 4:
                        continue
                        
                    # MAGIA AQUÍ: Calculamos qué métrica es según su posición.
                    # Al ser grupos de 5 columnas, el resto de la división nos da la métrica exacta.
                    metrica_actual = lista_metricas_oficial[(col_idx - 1) % 5]
                    
                    valor = raw_df.iloc[i, col_idx]
                    
                    # 5. Limpiamos las comas por puntos para que sean números
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
                            pass # Si hay texto extraño en la tabla, lo ignora
                            
            # Convertimos la lista en una tabla limpia
            df_clean = pd.DataFrame(datos_limpios)
            
            if df_clean.empty:
                st.warning("No se pudieron procesar los números. Comprueba los datos de la pestaña.")
            else:
                # --- INTERFAZ ---
                # Ahora el menú mostrará sí o sí tus 5 variables limpias
                metrica_sel = st.selectbox(
                    "Selecciona la métrica que deseas comparar visualmente:", 
                    lista_metricas_oficial
                )
                
                # Filtramos los datos para la gráfica
                df_filtrado = df_clean[df_clean["Métrica"] == metrica_sel]
                
                # Ordenamos las fechas de izquierda a derecha
                df_filtrado = df_filtrado.sort_values(by="Curso")
                
                # Dibujamos la gráfica
                fig2 = px.line(
                    df_filtrado, 
                    x="Curso", 
                    y="Valor", 
                    color="Centro", 
                    markers=True, 
                    title=f"Evolución Histórica Comparada: {metrica_sel}"
                )
                
                # Efecto visual al pasar el ratón
                fig2.update_layout(hovermode="x unified")
                st.plotly_chart(fig2, use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el archivo: {e}")
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