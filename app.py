import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Estadísticas de Fútbol", layout="wide")
st.markdown("""
    <div style='text-align: center;'>
        <img src='logo.png' width='120' style='border-radius: 20px;'>
    </div>
""", unsafe_allow_html=True)
st.title("⚽ Generador de Estadísticas Legendarios FC")

ultima_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"<div style='text-align: right; font-size: 12px; color: gray;'>Última actualización: {ultima_actualizacion}</div>", unsafe_allow_html=True)

# Ingreso de clave
clave_usuario = st.sidebar.text_input("🔐 Ingresa tu código de acceso", type="password")
if clave_usuario != "LEGENDARIOS2025":
    st.warning("⚠️ Ingresa el código correcto para ver las estadísticas.")
    st.stop()

# Cargar archivo fijo desde el repositorio
datos_path = "datos.xlsx"
jugadores_df = pd.read_excel(datos_path, sheet_name="Jugadores")
df = pd.read_excel(datos_path, sheet_name="Partidos")
df = df[df["equipo"].notna()]
df["fecha"] = pd.to_datetime(df["fecha"])
df = df.merge(jugadores_df.rename(columns={"posición": "posicion_regular"}), on="jugador", how="left")

# Rankings y estadísticas

for col in ["Penales_Atajados", "asistencias"]:
    if col not in df.columns:
        df[col] = 0

st.markdown("<h3 style='text-align: center;'>Ranking de Goleadores</h3>", unsafe_allow_html=True)
goleadores = df.groupby("jugador")["goles"].sum().reset_index()
goleadores = goleadores[goleadores["goles"] > 0].sort_values(by="goles", ascending=False).reset_index(drop=True)
goleadores.insert(0, "Posición", range(1, len(goleadores) + 1))
st.dataframe(goleadores)
fig, ax = plt.subplots()
ax.bar(goleadores["jugador"], goleadores["goles"], color="skyblue")
ax.set_title("Goles por Jugador")
ax.set_ylabel("Goles")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Asistencias</h3>", unsafe_allow_html=True)
asistencias = df.groupby("jugador")["asistencias"].sum().reset_index()
asistencias = asistencias[asistencias["asistencias"] > 0].sort_values(by="asistencias", ascending=False).reset_index(drop=True)
asistencias.insert(0, "Posición", range(1, len(asistencias) + 1))
st.dataframe(asistencias)
fig, ax = plt.subplots()
ax.bar(asistencias["jugador"], asistencias["asistencias"], color="orange")
ax.set_title("Asistencias por Jugador")
ax.set_ylabel("Asistencias")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Tarjetas Amarillas</h3>", unsafe_allow_html=True)
amarillas = df.groupby("jugador")["tarjetas_amarillas"].sum().reset_index()
amarillas = amarillas[amarillas["tarjetas_amarillas"] > 0].sort_values(by="tarjetas_amarillas", ascending=False).reset_index(drop=True)
amarillas.insert(0, "Posición", range(1, len(amarillas) + 1))
st.dataframe(amarillas)
fig, ax = plt.subplots()
ax.bar(amarillas["jugador"], amarillas["tarjetas_amarillas"], color="gold")
ax.set_title("Tarjetas Amarillas")
ax.set_ylabel("Cantidad")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Tarjetas Rojas</h3>", unsafe_allow_html=True)
rojas = df.groupby("jugador")["tarjetas_rojas"].sum().reset_index()
rojas = rojas[rojas["tarjetas_rojas"] > 0].sort_values(by="tarjetas_rojas", ascending=False).reset_index(drop=True)
rojas.insert(0, "Posición", range(1, len(rojas) + 1))
st.dataframe(rojas)
fig, ax = plt.subplots()
ax.bar(rojas["jugador"], rojas["tarjetas_rojas"], color="red")
ax.set_title("Tarjetas Rojas")
ax.set_ylabel("Cantidad")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Autogoles</h3>", unsafe_allow_html=True)
autogoles = df.groupby("jugador")["autogoles"].sum().reset_index()
autogoles = autogoles[autogoles["autogoles"] > 0].sort_values(by="autogoles", ascending=False).reset_index(drop=True)
autogoles.insert(0, "Posición", range(1, len(autogoles) + 1))
st.dataframe(autogoles)
fig, ax = plt.subplots()
ax.bar(autogoles["jugador"], autogoles["autogoles"], color="gray")
ax.set_title("Autogoles")
ax.set_ylabel("Cantidad")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Penales Atajados</h3>", unsafe_allow_html=True)
penales = df[df["Penales_Atajados"] > 0].groupby("jugador")["Penales_Atajados"].sum().reset_index()
penales = penales.sort_values(by="Penales_Atajados", ascending=False).reset_index(drop=True)
penales.insert(0, "Posición", range(1, len(penales) + 1))
st.dataframe(penales)
fig, ax = plt.subplots()
ax.bar(penales["jugador"], penales["Penales_Atajados"], color="green")
ax.set_title("Penales Atajados")
ax.set_ylabel("Cantidad")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

st.markdown("<h3 style='text-align: center;'>Ranking de Valla Menos Vencida</h3>", unsafe_allow_html=True)
arqueros = df[df["arquero"] == True]
rendimiento = arqueros.groupby("jugador").agg(partidos=("fecha", "count"), goles_recibidos=("goles_recibidos", "sum")).reset_index()
rendimiento["promedio"] = rendimiento["goles_recibidos"] / rendimiento["partidos"]
rendimiento = rendimiento.sort_values(by="promedio")
rendimiento.insert(0, "Posición", range(1, len(rendimiento) + 1))
st.dataframe(rendimiento)
fig, ax = plt.subplots()
ax.bar(rendimiento["jugador"], rendimiento["promedio"], color="teal")
ax.set_title("Promedio de Goles Recibidos")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)

# Puntajes y jugador de la fecha
df["valla_invicta"] = (df["arquero"] == True) & (df["goles_recibidos"] == 0)
df["puntos"] = (
    df["goles"] * 3 +
    df["asistencias"] * 1 +
    df["valla_invicta"] * 2 -
    df["tarjetas_amarillas"] -
    df["tarjetas_rojas"] * 2 +
    df["Penales_Atajados"] * 3
)

fechas_ordenadas = sorted(df["fecha"].unique(), reverse=True)
resumen_fecha = []
puntos_por_jugador_fecha = []

for fecha in fechas_ordenadas:
    df_fecha = df[df["fecha"] == fecha].copy()
    puntajes = df_fecha.groupby("jugador")["puntos"].sum().reset_index().sort_values(by="puntos", ascending=False)
    resumen_fecha.append({"Fecha": fecha.date(), "Jugador de la Fecha": puntajes.iloc[0]["jugador"], "Puntos": puntajes.iloc[0]["puntos"]})
    for _, row in puntajes.iterrows():
        puntos_por_jugador_fecha.append({"Fecha": fecha.date(), "Jugador": row["jugador"], "Puntos": row["puntos"]})

df_resumen = pd.DataFrame(resumen_fecha)
df_evolutivo = pd.DataFrame(puntos_por_jugador_fecha)
df_acumulado = df_evolutivo.groupby("Jugador")["Puntos"].sum().reset_index().sort_values(by="Puntos", ascending=False).reset_index(drop=True)
df_acumulado.insert(0, "Posición", range(1, len(df_acumulado) + 1))

st.markdown("<h3 style='text-align: center;'>Jugador de la Fecha</h3>", unsafe_allow_html=True)
st.dataframe(df_resumen)

st.markdown("<h3 style='text-align: center;'>Ranking acumulado de puntos año</h3>", unsafe_allow_html=True)
st.dataframe(df_acumulado)

# Top 3 del último partido
if fechas_ordenadas:
    ultima_fecha = fechas_ordenadas[0]
    df_ultima_fecha = df[df["fecha"] == ultima_fecha]
    puntajes_ultima = df_ultima_fecha.groupby("jugador")["puntos"].sum().reset_index().sort_values(by="puntos", ascending=False)
    df_top3 = puntajes_ultima.head(3).copy()
    df_top3.insert(0, "Posición", range(1, len(df_top3) + 1))
    df_top3.insert(0, "Fecha", ultima_fecha.date())
    st.markdown("<h3 style='text-align: center;'>Top 3 Jugador de la Fecha del Último Partido</h3>", unsafe_allow_html=True)
    st.dataframe(df_top3)

# Jugador con mayor regularidad
st.markdown("<h3 style='text-align: center;'>Jugador con mayor regularidad</h3>", unsafe_allow_html=True)
menciones = pd.concat([
    goleadores[["jugador"]], asistencias[["jugador"]], amarillas[["jugador"]],
    rojas[["jugador"]], autogoles[["jugador"]], rendimiento[["jugador"]], penales[["jugador"]]
])
conteo_menciones = menciones["jugador"].value_counts().reset_index()
conteo_menciones.columns = ["Jugador", "Menciones"]
conteo_menciones.insert(0, "Posición", range(1, len(conteo_menciones) + 1))
st.dataframe(conteo_menciones)

# Evolución de puntos por jugador
st.markdown("<h3 style='text-align: center;'>Evolución de puntos por jugador</h3>", unsafe_allow_html=True)
jugador_seleccionado = st.selectbox("Selecciona un jugador", df_evolutivo["Jugador"].unique())
df_jugador = df_evolutivo[df_evolutivo["Jugador"] == jugador_seleccionado].sort_values("Fecha")
fig, ax = plt.subplots()
ax.plot(df_jugador["Fecha"], df_jugador["Puntos"], marker="o")
ax.set_title(f"Evolución de {jugador_seleccionado}")
ax.set_xlabel("Fecha")
ax.set_ylabel("Puntos")
ax.grid(True)
st.pyplot(fig)

# Resumen de goles por fecha y análisis
resumen_base = df.groupby(["fecha", "equipo"])["goles"].sum().reset_index()
resumen_goles = resumen_base.pivot(index="fecha", columns="equipo", values="goles")

for equipo in ["Azul", "Amarillo"]:
    if equipo not in resumen_goles.columns:
        resumen_goles[equipo] = 0

resumen_goles = resumen_goles[["Amarillo", "Azul"]].fillna(0)

for _, row in df[df["autogoles"] > 0].iterrows():
    fecha = row["fecha"]
    equipo_contrario = "Amarillo" if row["equipo"] == "Azul" else "Azul"
    if fecha in resumen_goles.index:
        resumen_goles.at[fecha, equipo_contrario] += row["autogoles"]
    else:
        resumen_goles.loc[fecha] = {"Azul": 0, "Amarillo": 0}
        resumen_goles.at[fecha, equipo_contrario] = row["autogoles"]

resumen_goles = resumen_goles.astype(int).reset_index()
resumen_goles["Resultado"] = resumen_goles.apply(
    lambda row: "Empate" if row["Azul"] == row["Amarillo"] else ("Azul" if row["Azul"] > row["Amarillo"] else "Amarillo"), axis=1
)
resumen_goles = resumen_goles.sort_values(by="fecha", ascending=False)
st.markdown("<h3 style='text-align: center;'>Resumen goles por fecha</h3>", unsafe_allow_html=True)
st.dataframe(resumen_goles)

# Resumen anual
st.subheader("Resumen Anual de Goles por Equipo")
total_partidos = df["fecha"].nunique()
goles_equipo = df.groupby("equipo")["goles"].sum()
autogoles_equipo = df[df["autogoles"] > 0].copy()
autogoles_equipo["equipo_beneficiado"] = autogoles_equipo["equipo"].apply(lambda x: "Amarillo" if x == "Azul" else "Azul")
autogoles_por_equipo = autogoles_equipo.groupby("equipo_beneficiado")["autogoles"].sum()
total_goles = goles_equipo.add(autogoles_por_equipo, fill_value=0).reset_index()
total_goles.columns = ["equipo", "goles"]
total_goles["Promedio Goles por Fecha"] = total_goles["goles"] / total_partidos
st.dataframe(total_goles)

st.subheader("Promedio Total de Goles por Partido")
total_goles_general = total_goles["goles"].sum()
promedio_general = total_goles_general / total_partidos
st.metric(label="⚽ Promedio General de Goles por Partido", value=round(promedio_general, 2))

# Análisis comparativo de goles por equipo
st.subheader("Comparativo de Goles por Equipo")
fig, ax = plt.subplots()
ax.bar(total_goles["equipo"], total_goles["goles"], color=["blue" if e == "Azul" else "yellow" for e in total_goles["equipo"]])
ax.set_ylabel("Goles Totales")
ax.set_title("Goles Totales por Equipo")
ax.set_ylim(0, max(total_goles["goles"]) + 2)
st.pyplot(fig)

st.subheader("Promedio de Goles por Fecha por Equipo")
fig, ax = plt.subplots()
ax.bar(total_goles["equipo"], total_goles["Promedio Goles por Fecha"], color=["blue" if e == "Azul" else "yellow" for e in total_goles["equipo"]])
ax.set_ylabel("Promedio")
ax.set_title("Promedio Goles por Fecha por Equipo")
ax.set_ylim(0, max(total_goles["Promedio Goles por Fecha"]) + 0.5)
st.pyplot(fig))

# Ranking MVP del Año
st.markdown("<h3 style='text-align: center;'>Ranking MVP del año</h3>", unsafe_allow_html=True)
mvp = df_acumulado.merge(conteo_menciones, on="Jugador", how="left")
mvp["Menciones"] = mvp["Menciones"].fillna(0)
mvp["MVP_Score"] = mvp["Puntos"] + mvp["Menciones"] * 2
mvp = mvp.sort_values(by="MVP_Score", ascending=False).reset_index(drop=True)
if "Posición" in mvp.columns:
    mvp.drop(columns=["Posición"], inplace=True)
mvp.insert(0, "Posición", range(1, len(mvp) + 1))
st.dataframe(mvp)
