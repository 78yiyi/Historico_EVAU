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
    st.write("Análisis comparativo utilizando el archivo 'Histórico EvAU - Otros Coles.csv'.")
    # Lógica futura para leer y graficar "Otros Coles.csv"

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