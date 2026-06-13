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
        # Cargamos la pestaña
        df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Fase General")
        
        # Renombramos y limpiamos
        df.rename(columns={df.columns[0]: 'Curso'}, inplace=True)
        if 'Materia' in df.columns:
            df['Materia'] = df['Materia'].astype(str).str.strip()
            df_totales = df[df['Materia'] == 'Fase General'].copy()
        else:
            df_totales = df.copy()
            
        df_totales = df_totales.dropna(subset=['Curso'])
        df_totales['Curso'] = df_totales['Curso'].astype(str)
        df_totales = df_totales.sort_values(by='Curso')
        
        # OBLIGAMOS a que 'Presentados' sea numérico para que nunca falle la barra
        df_totales['Presentados'] = pd.to_numeric(df_totales['Presentados'], errors='coerce')
        
        # Gráfica
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
            
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el código: {e}")

elif opcion == "Comparación por Centros":
    st.header("🏫 Comparación con otros centros")
    
    try:
        raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Otros Coles", header=None)
        raw_df = raw_df.dropna(how='all').reset_index(drop=True)
        
        start_idx = -1
        for i in range(len(raw_df)):
            val = str(raw_df.iloc[i, 0]).strip().upper()
            if val in ["CAM", "LSG", "CASTILLA", "IES GRIÑÓN", "VILLA GRIÑÓN", "CATÓN", "IES CUBAS"]:
                start_idx = i
                break
                
        if start_idx == -1:
            st.error("⚠️ No se pudo detectar el inicio de los datos en la primera columna.")
        else:
            años = pd.Series(raw_df.iloc[0, :].values).ffill().values
            
            lista_metricas_oficial = [
                "% Titulados Bach", 
                "%Aprobados EvAU", 
                "Presentados EvAU", 
                "Media EvAU Aprobados", 
                "Media FG"
            ]
            
            datos_limpios = []
            
            for i in range(start_idx, len(raw_df)):
                centro = str(raw_df.iloc[i, 0]).strip()
                if pd.isna(raw_df.iloc[i, 0]) or centro == "nan" or centro == "":
                    continue
                    
                for col_idx in range(1, len(raw_df.columns)):
                    año = str(años[col_idx]).strip()
                    if año == "nan" or año == "" or len(año) < 4:
                        continue
                        
                    metrica_actual = lista_metricas_oficial[(col_idx - 1) % 5]
                    valor = raw_df.iloc[i, col_idx]
                    
                    if pd.notna(valor) and str(valor).strip() != "":
                        val_str = str(valor).replace("%", "").replace('"', '').replace("'", "").replace(",", ".").strip()
                        try:
                            valor_num = float(val_str)
                            # Limpieza de porcentajes
                            if "%" in metrica_actual and 0 < valor_num <= 1.0:
                                valor_num = valor_num * 100
                                
                            datos_limpios.append({
                                "Centro": centro,
                                "Curso": año,
                                "Métrica": metrica_actual,
                                "Valor": round(valor_num, 2)
                            })
                        except ValueError:
                            pass 
                            
            df_clean = pd.DataFrame(datos_limpios)
            
            if df_clean.empty:
                st.warning("No se pudieron procesar los números. Comprueba los datos de la pestaña.")
            else:
                metrica_sel = st.selectbox("Selecciona la métrica:", lista_metricas_oficial)
                
                df_filtrado = df_clean[df_clean["Métrica"] == metrica_sel]
                df_filtrado = df_filtrado.sort_values(by="Curso")
                
                fig2 = px.bar(
                    df_filtrado, 
                    x="Curso", 
                    y="Valor", 
                    color="Centro", 
                    barmode="group",
                    title=f"Evolución Histórica Comparada: {metrica_sel}",
                    labels={"Curso": "Curso Académico", "Valor": "Resultado / Nota", "Centro": "Centro Educativo"}
                )
                fig2.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                st.plotly_chart(fig2, use_container_width=True)
                
                with st.expander(f"Ver tabla de datos detallada: {metrica_sel}"):
                    try:
                        df_tabla = df_filtrado.pivot(index="Centro", columns="Curso", values="Valor")
                        st.dataframe(df_tabla, use_container_width=True)
                    except:
                        st.dataframe(df_filtrado[["Centro", "Curso", "Valor"]], use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar el archivo: {e}")

elif opcion == "Por Materias":
    st.header("📚 Resultados por Materia")
    
    try:
        xls = pd.ExcelFile("Historico_EvAU.xlsx")
        hojas_excluir = ["Fase General", "Titulan", "Otros Coles", "Por año", "Por Año"]
        materias_disponibles = [hoja for hoja in xls.sheet_names if hoja not in hojas_excluir]
        
        if not materias_disponibles:
            st.warning("No se han encontrado pestañas de materias en el archivo Excel.")
        else:
            materia_sel = st.selectbox("Selecciona la materia:", materias_disponibles)
            df_mat = pd.read_excel(xls, sheet_name=materia_sel)
            
            df_mat.columns = [str(c).strip() for c in df_mat.columns]
            df_mat.rename(columns={df_mat.columns[0]: 'Curso'}, inplace=True)
            df_mat = df_mat.dropna(subset=['Curso'])
            
            # SOLUCIÓN al error de sort: Forzar que todos los años sean texto
            df_mat['Curso'] = df_mat['Curso'].astype(str)
            df_mat = df_mat.sort_values(by='Curso')
            
            def limpiar_numeros(val, es_porc):
                if pd.isna(val) or str(val).strip() == "": return None
                tiene_simbolo = isinstance(val, str) and "%" in val
                val_str = str(val).replace("%", "").replace('"', '').replace("'", "").replace(",", ".").strip()
                try: 
                    num = float(val_str)
                    if es_porc and not tiene_simbolo and 0 < num <= 1.0:
                        num = num * 100
                    return round(num, 2)
                except ValueError: 
                    return None
                
            cols_graficas = ["% LSG", "NM LSG EvAU", "NM LSG Cole", "% UC3M", "NM UC3M"]
            for col in cols_graficas:
                if col in df_mat.columns:
                    es_porcentaje = "%" in col 
                    df_mat[col] = df_mat[col].apply(lambda x: limpiar_numeros(x, es_porcentaje))
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "NM LSG EvAU" in df_mat.columns:
                    fig1 = px.bar(df_mat, x="Curso", y="NM LSG EvAU", title="1. Nota Media de la Materia (EvAU)", text="NM LSG EvAU", color_discrete_sequence=["#2ca02c"])
                    fig1.update_traces(textposition='outside')
                    fig1.update_layout(xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig1, use_container_width=True)
                
                if "NM LSG EvAU" in df_mat.columns and "NM UC3M" in df_mat.columns:
                    fig3 = px.line(df_mat, x="Curso", y=["NM LSG EvAU", "NM UC3M"], title="3. Nota Media EvAU: LSG vs Media UC3M", markers=True)
                    fig3.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig3, use_container_width=True)

            with col2:
                if "% LSG" in df_mat.columns and "% UC3M" in df_mat.columns:
                    fig2 = px.line(df_mat, x="Curso", y=["% LSG", "% UC3M"], title="2. % de Aprobados: LSG vs Media UC3M", markers=True)
                    fig2.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'}, yaxis=dict(ticksuffix="%"))
                    st.plotly_chart(fig2, use_container_width=True)
                
                if "NM LSG EvAU" in df_mat.columns and "NM LSG Cole" in df_mat.columns:
                    fig4 = px.line(df_mat, x="Curso", y=["NM LSG EvAU", "NM LSG Cole"], title="4. Desviación de Nota: EvAU vs Colegio (LSG)", markers=True)
                    fig4.update_layout(hovermode="x unified", xaxis={'categoryorder':'category ascending'})
                    st.plotly_chart(fig4, use_container_width=True)
                    
            with st.expander(f"Ver tabla detallada"):
                cols_mostrar = ["Curso"] + [c for c in cols_graficas if c in df_mat.columns]
                st.dataframe(df_mat[cols_mostrar], use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar las materias: {e}")

elif opcion == "Por Años":
    st.header("📅 Resultados detallados por Año Académico")
    
    try:
        try:
            raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Por año", header=None)
        except:
            raw_df = pd.read_excel("Historico_EvAU.xlsx", sheet_name="Por Año", header=None)
            
        datos = []
        for i in range(len(raw_df)):
            curso = str(raw_df.iloc[i, 0]).strip()
            materia = str(raw_df.iloc[i, 1]).strip()
            if "-" in curso and len(curso) == 5 and materia.lower() not in ["nan", "materia", ""]:
                datos.append({
                    "Curso": curso,
                    "Materia": materia,
                    "% LSG": raw_df.iloc[i, 4],
                    "NM LSG EvAU": raw_df.iloc[i, 5],
                    "NM LSG Cole": raw_df.iloc[i, 6],
                    "% UC3M": raw_df.iloc[i, 7],
                    "NM UC3M": raw_df.iloc[i, 8]
                })
                
        df_anyos = pd.DataFrame(datos)
        
        if df_anyos.empty:
            st.warning("⚠️ No se pudieron extraer los datos. Revisa el formato de la pestaña 'Por año'.")
        else:
            def limpiar_numeros(val, es_porc):
                if pd.isna(val) or str(val).strip() == "" or str(val).strip() == "nan": return None
                tiene_simbolo = isinstance(val, str) and "%" in val
                val_str = str(val).replace("%", "").replace('"', '').replace("'", "").replace(",", ".").strip()
                try: 
                    num = float(val_str)
                    if es_porc and not tiene_simbolo and 0 < num <= 1.0:
                        num = num * 100
                    return round(num, 2)
                except ValueError: 
                    return None

            for col in ["% LSG", "NM LSG EvAU", "NM LSG Cole", "% UC3M", "NM UC3M"]:
                es_porcentaje = "%" in col
                df_anyos[col] = df_anyos[col].apply(lambda x: limpiar_numeros(x, es_porcentaje))
                
            cursos_disponibles = sorted(df_anyos["Curso"].unique(), reverse=True)
            curso_sel = st.selectbox("Selecciona el curso académico:", cursos_disponibles)
            
            df_filtrado = df_anyos[df_anyos["Curso"] == curso_sel]
            df_filtrado = df_filtrado[~df_filtrado["Materia"].isin(["Fase General", "Titulan"])]
            
            st.divider()
            
            # Gráfica 1
            st.subheader(f"1. Porcentaje de Aprobados: LSG vs Media UC3M ({curso_sel})")
            df_melt_1 = df_filtrado.melt(id_vars="Materia", value_vars=["% LSG", "% UC3M"], var_name="Institución", value_name="% Aprobados")
            fig1 = px.bar(df_melt_1, x="Materia", y="% Aprobados", color="Institución", barmode="group", text="% Aprobados")
            fig1.update_traces(textposition='outside')
            fig1.update_layout(yaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig1, use_container_width=True)
            
            st.divider() 
            
            # Gráfica 2
            st.subheader("2. Nota Media: EvAU vs Colegio")
            df_melt_2 = df_filtrado.melt(id_vars="Materia", value_vars=["NM LSG EvAU", "NM LSG Cole"], var_name="Evaluación", value_name="Nota Media")
            fig2 = px.bar(df_melt_2, x="Materia", y="Nota Media", color="Evaluación", barmode="group", text="Nota Media", color_discrete_sequence=["#1f77b4", "#ff7f0e"])
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
            
            st.divider()
            
            # Gráfica 3
            st.subheader("3. Nota Media EvAU: LSG vs Media UC3M")
            df_melt_3 = df_filtrado.melt(id_vars="Materia", value_vars=["NM LSG EvAU", "NM UC3M"], var_name="Institución", value_name="Nota Media")
            fig3 = px.bar(df_melt_3, x="Materia", y="Nota Media", color="Institución", barmode="group", text="Nota Media", color_discrete_sequence=["#2ca02c", "#d62728"])
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
                
            with st.expander(f"Ver tabla de datos detallada del curso {curso_sel}"):
                st.dataframe(df_filtrado, use_container_width=True)
                
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al procesar los años: {e}")