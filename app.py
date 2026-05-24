import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium


# ==========================================
# BLOQUE 1: Configuración Inicial
# ==========================================
st.set_page_config(page_title="Dashboard Agrícola 2024", layout="wide")
st.title("🌾 Tablero Interactivo: Cierre Agrícola 2024")

# ==========================================
# BLOQUE 2: Carga de Datos
# ==========================================
@st.cache_data
def cargar_datos():
    df = pd.read_csv('Cierre_agricola_dashboard.csv', dtype={'CVEGEO': str, 'Idcultivo': str, 'Idciclo': str})
    try:
        dicc = pd.read_csv('Diccionario_agricola_2003_a_2023.xlsx - Dicc 03 a 23.csv', skiprows=13, encoding='utf-8', on_bad_lines='skip')
    except:
        dicc = pd.DataFrame()
    return df, dicc

@st.cache_data
def cargar_mapa():
    return gpd.read_file('mexico_municipios_ligero.geojson')

df, dicc = cargar_datos()
mapa = cargar_mapa()

# Extracción segura de descripciones para las nubes de ayuda
try:
    desc_volumen = dicc[dicc['Nombre\nde campo'] == 'Volumenproduccion']['Descripción'].values[0]
    desc_valor = dicc[dicc['Nombre\nde campo'] == 'Valorproduccion']['Descripción'].values[0]
except:
    desc_volumen = "Volumen de producción de la superficie cosechada cuya unidad de medida son las toneladas, con excepción del maguey pulquero y trigo ornamental, con una métrica de miles de litros y gruesas, respectivamente."
    desc_valor = "Valor expresado en pesos corrientes nacionales."

# ==========================================
# BLOQUE 3: Interruptor Global
# ==========================================
st.markdown("### Selecciona la métrica a analizar:")
tipo_analisis = st.radio(
    "Variable Principal",
    options=["Valor de Producción ($)", "Volumen de Producción (Ton)"],
    horizontal=True,
    label_visibility="collapsed"
)

col_variable = 'Valorproduccion' if tipo_analisis == "Valor de Producción ($)" else 'Volumenproduccion'
desc_variable = desc_valor if tipo_analisis == "Valor de Producción ($)" else desc_volumen

# ==========================================
# BLOQUE 4: Funciones Modulares Avanzadas
# ==========================================
def crear_filtros_cruzados(prefijo, df_fuente):
    """Genera 4 filtros interconectados bidireccionalmente y ordenados alfabéticamente."""
    # Recuperamos de forma segura las elecciones previas guardadas en memoria
    est_curr = st.session_state.get(f"est_{prefijo}", "Todos")
    mun_curr = st.session_state.get(f"mun_{prefijo}", "Todos")
    cult_curr = st.session_state.get(f"cult_{prefijo}", "Todos")
    ciclo_curr = st.session_state.get(f"ciclo_{prefijo}", "Todos")
    
    # 1. Opciones de ESTADO (Filtrado por Cultivo y Ciclo activos)
    df_est = df_fuente.copy()
    if cult_curr != "Todos": df_est = df_est[df_est['Nomcultivo'] == cult_curr]
    if ciclo_curr != "Todos": df_est = df_est[df_est['Nomcicloproductivo'] == ciclo_curr]
    estados_opciones = ["Todos"] + sorted(list(df_est['Nomestado'].dropna().unique()))
    if est_curr not in estados_opciones: est_curr = "Todos"
    
    col1, col2 = st.columns(2)
    with col1:
        estado_sel = st.selectbox("Estado", estados_opciones, index=estados_opciones.index(est_curr), key=f"est_{prefijo}")
        
    # 2. Opciones de MUNICIPIO (Filtrado por Estado, Cultivo y Ciclo activos)
    df_mun = df_fuente.copy()
    if estado_sel != "Todos": df_mun = df_mun[df_mun['Nomestado'] == estado_sel]
    if cult_curr != "Todos": df_mun = df_mun[df_mun['Nomcultivo'] == cult_curr]
    if ciclo_curr != "Todos": df_mun = df_mun[df_mun['Nomcicloproductivo'] == ciclo_curr]
    muns_opciones = ["Todos"] + sorted(list(df_mun['Nommunicipio'].dropna().unique()))
    if mun_curr not in muns_opciones: mun_curr = "Todos"
    
    with col2:
        mun_sel = st.selectbox("Municipio", muns_opciones, index=muns_opciones.index(mun_curr), key=f"mun_{prefijo}")
        
    col3, col4 = st.columns(2)
    # 3. Opciones de CULTIVO (Filtrado por Estado, Municipio y Ciclo activos)
    df_cult = df_fuente.copy()
    if estado_sel != "Todos": df_cult = df_cult[df_cult['Nomestado'] == estado_sel]
    if mun_sel != "Todos": df_cult = df_cult[df_cult['Nommunicipio'] == mun_sel]
    if ciclo_curr != "Todos": df_cult = df_cult[df_cult['Nomcicloproductivo'] == ciclo_curr]
    cultivos_opciones = ["Todos"] + sorted(list(df_cult['Nomcultivo'].dropna().unique()))
    if cult_curr not in cultivos_opciones: cult_curr = "Todos"
    
    with col3:
        cultivo_sel = st.selectbox("Cultivo", cultivos_opciones, index=cultivos_opciones.index(cult_curr), key=f"cult_{prefijo}")
        
    # 4. Opciones de CICLO PRODUCTIVO (Filtrado por Estado, Municipio y Cultivo activos)
    df_ciclo = df_fuente.copy()
    if estado_sel != "Todos": df_ciclo = df_ciclo[df_ciclo['Nomestado'] == estado_sel]
    if mun_sel != "Todos": df_ciclo = df_ciclo[df_ciclo['Nommunicipio'] == mun_sel]
    if cultivo_sel != "Todos": df_ciclo = df_ciclo[df_ciclo['Nomcultivo'] == cultivo_sel]
    ciclos_opciones = ["Todos"] + sorted(list(df_ciclo['Nomcicloproductivo'].dropna().unique()))
    if ciclo_curr not in ciclos_opciones: ciclo_curr = "Todos"
    
    with col4:
        ciclo_sel = st.selectbox("Ciclo Productivo", ciclos_opciones, index=ciclos_opciones.index(ciclo_curr), key=f"ciclo_{prefijo}")
        
    # Construcción de la base final filtrada por el conjunto completo de variables
    df_filt = df_fuente.copy()
    if estado_sel != "Todos": df_filt = df_filt[df_filt['Nomestado'] == estado_sel]
    if mun_sel != "Todos":    df_filt = df_filt[df_filt['Nommunicipio'] == mun_sel]
    if cultivo_sel != "Todos":df_filt = df_filt[df_filt['Nomcultivo'] == cultivo_sel]
    if ciclo_sel != "Todos":  df_filt = df_filt[df_filt['Nomcicloproductivo'] == ciclo_sel]
    
    return df_filt, estado_sel

def renderizar_grafica_avanzada(df_datos, estado_seleccionado):
    """Dibuja la gráfica y tabla con cálculo de %, formato e interruptor de orden usando Streamlit nativo."""
    if df_datos.empty:
        st.info("No hay datos disponibles para graficar en esta combinación.")
        return

    # Controles para ordenar la gráfica por monto o letra
    orden_sel = st.selectbox(
        "Ordenar gráfica por:",
        ["Por Monto o Volumen (Mayor a Menor)", "Por Monto o Volumen (Menor a Mayor)", "Orden Alfabético (A-Z)", "Orden Alfabético (Z-A)"],
        key="ordenamiento_grafica"
    )

    # Definición automática del nivel jerárquico (Drill-down)
    if estado_seleccionado == "Todos":
        st.markdown("#### Aportación por Estado (Top 15)")
        df_agrup = df_datos.groupby('Nomestado')[col_variable].sum().reset_index()
        col_x = 'Nomestado'
    else:
        st.markdown(f"#### Aportación por Municipio en {estado_seleccionado} (Top 15)")
        df_agrup = df_datos.groupby('Nommunicipio')[col_variable].sum().reset_index()
        col_x = 'Nommunicipio'
        
    # Cálculo exacto del porcentaje de participación
    total_contexto = df_datos[col_variable].sum()
    df_agrup['Porcentaje'] = (df_agrup[col_variable] / total_contexto * 100) if total_contexto > 0 else 0
    
    # Ejecución del ordenamiento solicitado
    if orden_sel == "Por Monto o Volumen (Mayor a Menor)":
        df_agrup = df_agrup.sort_values(by=col_variable, ascending=False)
    elif orden_sel == "Por Monto o Volumen (Menor a Mayor)":
        df_agrup = df_agrup.sort_values(by=col_variable, ascending=True)
    elif orden_sel == "Orden Alfabético (A-Z)":
        df_agrup = df_agrup.sort_values(by=col_x, ascending=True)
    else:
        df_agrup = df_agrup.sort_values(by=col_x, ascending=False)
        
    df_agrup = df_agrup.head(15)
    
    # 1. Gráfica nativa de Streamlit
    st.bar_chart(data=df_agrup, x=col_x, y=col_variable, use_container_width=True)
    
    # 2. Tabla de detalle con formato de Pandas/Streamlit para mostrar $ y %
    df_mostrar = df_agrup.copy()
    if col_variable == 'Valorproduccion':
        df_mostrar[col_variable] = df_mostrar[col_variable].apply(lambda x: f"${x:,.2f}")
    else:
        df_mostrar[col_variable] = df_mostrar[col_variable].apply(lambda x: f"{x:,.2f} Ton")
        
    df_mostrar['Porcentaje'] = df_mostrar['Porcentaje'].apply(lambda x: f"{x:.1f}%")
    
    # Renombramos columnas para que la tabla sea fácil de leer
    df_mostrar = df_mostrar.rename(columns={col_variable: "Monto / Volumen", col_x: "Ubicación"})
    
    st.markdown("##### Detalle de Participación")
    st.dataframe(df_mostrar, hide_index=True, use_container_width=True)

def generar_mapa(df_datos, mapa_base, variable_analisis, clave_mapa):
    """Genera el mapa coroplético oficial con zoom automatizado por límites geográficos."""
    if df_datos.empty:
        st.warning("No hay registros geográficos.")
        return
        
    datos_mapa = df_datos.groupby('CVEGEO').agg({
        'Valorproduccion': 'sum',
        'Volumenproduccion': 'sum',
        'Nommunicipio': 'first'
    }).reset_index()

    mapa_filtrado = mapa_base[mapa_base['CVEGEO'].isin(datos_mapa['CVEGEO'])]
    mapa_filtrado = mapa_filtrado.merge(datos_mapa, on='CVEGEO')

    if not mapa_filtrado.empty:
        bounds = mapa_filtrado.total_bounds
        centro_lat = (bounds[1] + bounds[3]) / 2
        centro_lon = (bounds[0] + bounds[2]) / 2
        
        m = folium.Map(location=[centro_lat, centro_lon], tiles="CartoDB positron")
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        folium.GeoJson(
            mapa_filtrado,
            style_function=lambda feature: {
                'fillColor': '#2ca25f' if feature['properties'][variable_analisis] > 0 else '#cccccc',
                'color': 'black',
                'weight': 0.8,
                'fillOpacity': 0.65,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['Nommunicipio', 'Volumenproduccion', 'Valorproduccion'],
                aliases=['Municipio:', 'Volumen (Ton):', 'Valor ($):'],
                localize=True
            )
        ).add_to(m)
        
        st_folium(m, width=700, height=420, returned_objects=[], key=clave_mapa)
    else:
        st.warning("Sin polígonos correspondientes.")

def mostrar_bloque_kpis(df_fuente, total_val):
    """Despliega las tres tarjetas de indicadores unificados."""
    sub1, sub2, sub3 = st.columns(3)
    muns = df_fuente['CVEGEO'].nunique()
    prods = df_fuente['Idcultivo'].nunique()
    
    if col_variable == 'Valorproduccion':
        sub1.metric("💰 Total Seleccionado", f"${total_val:,.2f}", help=desc_variable)
    else:
        sub1.metric("📦 Total Seleccionado", f"{total_val:,.2f}", help=desc_variable)
        
    sub2.metric("🗺️ Municipios Activos", f"{muns}")
    sub3.metric("🌱 Variedad Productos", f"{prods}")

# ==========================================
# BLOQUE 5: Construcción de Pestañas
# ==========================================
tab1, tab2 = st.tabs(["📊 Análisis Individual", "⚖️ Comparador Regional"])

# --- PESTAÑA 1: ANÁLISIS INDIVIDUAL ---
with tab1:
    st.markdown("### Filtros de Búsqueda")
    df_t1, est_sel_t1 = crear_filtros_cruzados("General", df)
    
    st.markdown("---")
    total_var_t1 = df_t1[col_variable].sum()
    mostrar_bloque_kpis(df_t1, total_var_t1)
    
    st.markdown("---")
    col_graf, col_map = st.columns([1, 2])
    with col_graf:
        renderizar_grafica_avanzada(df_t1, est_sel_t1)
            
    with col_map:
        st.markdown("#### Distribución Geográfica")
        generar_mapa(df_t1, mapa, col_variable, clave_mapa="mapa_principal")

# --- PESTAÑA 2: COMPARADOR REGIONAL ---
with tab2:
    st.markdown("Selecciona los filtros para cada región y evalúa su comportamiento simultáneo.")
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("### 🟦 Región A")
        df_A, est_sel_A = crear_filtros_cruzados("A", df)
        total_A = df_A[col_variable].sum()
        muns_A = df_A['CVEGEO'].nunique()
        prods_A = df_A['Idcultivo'].nunique()
        
    with colB:
        st.markdown("### 🟧 Región B")
        df_B, est_sel_B = crear_filtros_cruzados("B", df)
        total_B = df_B[col_variable].sum()
        muns_B = df_B['CVEGEO'].nunique()
        prods_B = df_B['Idcultivo'].nunique()
        
    st.markdown("---")
    
    colMapA, colMapB = st.columns(2)
    with colMapA:
        st.markdown("#### 📊 Resumen Región A")
        mostrar_bloque_kpis(df_A, total_A)
        st.markdown(" ")
        generar_mapa(df_A, mapa, col_variable, clave_mapa="mapa_comparativo_a")
        
    with colMapB:
        st.markdown("#### 📊 Resumen Región B")
        mostrar_bloque_kpis(df_B, total_B)
        st.markdown(" ")
        generar_mapa(df_B, mapa, col_variable, clave_mapa="mapa_comparativo_b")
        
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>📉 Reporte de Desviación y Brechas (Región A vs Región B)</h3>", unsafe_allow_html=True)
    
    # Modelado de variaciones porcentuales y absolutas
    diff_prod = total_A - total_B
    pct_prod = (diff_prod / total_B * 100) if total_B > 0 else (100.0 if total_A > 0 else 0.0)
    
    diff_mun = muns_A - muns_B
    pct_mun = (diff_mun / muns_B * 100) if muns_B > 0 else (100.0 if muns_A > 0 else 0.0)
    
    diff_prd = prods_A - prods_B
    pct_prd = (diff_prd / prods_B * 100) if prods_B > 0 else (100.0 if prods_A > 0 else 0.0)
    
    comp1, comp2, comp3 = st.columns(3)
    
    label_prod = "Brecha en Valor ($)" if col_variable == 'Valorproduccion' else "Brecha en Volumen (Ton)"
    signo_prod = "$" if col_variable == 'Valorproduccion' else ""
    
    comp1.metric(
        label=label_prod, 
        value=f"{pct_prod:+.1f}%", 
        delta=f"Absoluto: {signo_prod}{diff_prod:,.2f}",
        help="Diferencia porcentual de la Región A respecto a la B."
    )
    
    comp2.metric(
        label="Brecha en Cobertura Municipal", 
        value=f"{pct_mun:+.1f}%", 
        delta=f"Absoluto: {diff_mun:+,} muns"
    )
    
    comp3.metric(
        label="Brecha en Variedad de Cultivos", 
        value=f"{pct_prd:+.1f}%", 
        delta=f"Absoluto: {diff_prd:+,} prods"
    )

# ==========================================
# BLOQUE 6: Pie de Página
# ==========================================
st.markdown("---")
st.caption("Fuente de información espacial: Marco Geoestadístico Municipal, INEGI. | Datos agrícolas: Cierre Agrícola, SADER (https://nube.agricultura.gob.mx/cierre_agricola/).")