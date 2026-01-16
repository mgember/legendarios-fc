import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from PIL import Image

# =========================
# Configuración Streamlit
# =========================
st.set_page_config(page_title="Estadísticas Legendarios FC 2026", layout="wide")

# =========================
# Encabezado
# =========================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        logo = Image.open("2026/logo.png")  # <-- importante: ruta con carpeta
        st.image(logo, width=120)
    except Exception:
        pass

st.title("⚽ Estadísticas Legendarios FC - Temporada 2026")

ultima_actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(
    f"<div style='text-align: right; font-size: 12px; color: gray;'>Última actualización: {ultima_actualizacion}</div>",
    unsafe_allow_html=True
)

# =========================
# Acceso
# =========================
CLAVE = "LEGENDARIOS2026"  # cámbiala si quieres
clave_usuario = st.text_input("🔐 Ingresa tu código de acceso", type="password")
if clave_usuario != CLAVE:
    st.warning("⚠️ Ingresa el código correcto para ver las estadísticas.")
    st.stop()

# Botón para evitar "reboot" por cache
if st.button("🔄 Recargar datos (limpiar cache)"):
    st.cache_data.clear()
    st.rerun()

# =========================
# Parámetros / constantes
# =========================
DATA_FILE = "2026/estadisticas_2026.xlsx"
HOJA_J = "Jugadores"
HOJA_P = "Partidos"
HOJA_E = "Eventos"

EQUIPOS_VALIDOS = {"amarillo", "azul"}
POS_VALIDAS = {"arquero", "defensa", "mediocampista", "delantero"}

# =========================
# Carga de datos
# =========================
@st.cache_data(show_spinner=False)
def load_data(path: str):
    jugadores = pd.read_excel(path, sheet_name=HOJA_J)
    partidos = pd.read_excel(path, sheet_name=HOJA_P)
    eventos = pd.read_excel(path, sheet_name=HOJA_E)
    return jugadores, partidos, eventos

try:
    jugadores_df, partidos_df, eventos_df = load_data(DATA_FILE)
except Exception as e:
    st.error(f"No pude leer el archivo '{DATA_FILE}'. Revisa que exista en el repo y tenga las 3 hojas. Detalle: {e}")
    st.stop()

# =========================
# Normalización básica
# =========================
partidos_df["fecha"] = pd.to_datetime(partidos_df["fecha"], errors="coerce")
jugadores_df["posicion"] = jugadores_df["posicion"].astype(str).str.strip().str.lower()
eventos_df.columns = [c.strip() for c in eventos_df.columns]  # por si acaso

# =========================
# Validaciones robustas (sin romper por NaN)
# =========================
def validate(jugadores, partidos, eventos):
    errors = []

    req_j = {"id_jugador", "nombre", "posicion", "activo", "sancion_grave"}
    req_p = {"id_partido", "fecha", "resultado_amarillo", "resultado_azul", "marcador_amarillo", "marcador_azul"}
    req_e = {"id_partido","id_jugador","equipo","gol_recibido","fue_delantero","gol_primer","gol_segundo","gol_total",
             "autogoles","asistencia_gol","amarillas","rojas","penal_atajado"}

    if not req_j.issubset(set(jugadores.columns)):
        errors.append(f"Hoja Jugadores: faltan columnas: {sorted(list(req_j - set(jugadores.columns)))}")
    if not req_p.issubset(set(partidos.columns)):
        errors.append(f"Hoja Partidos: faltan columnas: {sorted(list(req_p - set(partidos.columns)))}")
    if not req_e.issubset(set(eventos.columns)):
        errors.append(f"Hoja Eventos: faltan columnas: {sorted(list(req_e - set(eventos.columns)))}")

    # Eventos puede estar vacío al inicio
    if len(eventos) == 0:
        return errors

    # Normalizar ids para validación
    ev = eventos.copy()
    ev["id_partido"] = pd.to_numeric(ev["id_partido"], errors="coerce")
    ev["id_jugador"] = pd.to_numeric(ev["id_jugador"], errors="coerce")
    ev = ev.dropna(subset=["id_partido", "id_jugador"])
    ev["id_partido"] = ev["id_partido"].astype(int)
    ev["id_jugador"] = ev["id_jugador"].astype(int)

    ids_j = set(pd.to_numeric(jugadores["id_jugador"], errors="coerce").dropna().astype(int).tolist())
    ids_p = set(pd.to_numeric(partidos["id_partido"], errors="coerce").dropna().astype(int).tolist())

    bad_j = ev[~ev["id_jugador"].isin(ids_j)]
    if len(bad_j) > 0:
        errors.append("Eventos: hay id_jugador que no existen en Jugadores (revisa filas).")

    bad_p = ev[~ev["id_partido"].isin(ids_p)]
    if len(bad_p) > 0:
        errors.append("Eventos: hay id_partido que no existen en Partidos (revisa filas).")

    # equipo válido
    if "equipo" in eventos.columns:
        bad_team = eventos[~eventos["equipo"].astype(str).str.strip().str.lower().isin(EQUIPOS_VALIDOS)]
        if len(bad_team) > 0:
            errors.append("Eventos: hay valores en 'equipo' distintos a 'amarillo'/'azul' (en minúscula).")

    # posición válida
    bad_pos = jugadores[~jugadores["posicion"].astype(str).str.strip().str.lower().isin(POS_VALIDAS)]
    if len(bad_pos) > 0:
        errors.append("Jugadores: hay valores en 'posicion' fuera de: arquero/defensa/mediocampista/delantero (minúscula).")

    # unicidad jugador-partido
    dup = eventos.duplicated(subset=["id_partido", "id_jugador"]).sum()
    if dup > 0:
        errors.append(f"Eventos: hay {dup} registros duplicados (id_partido + id_jugador). Debe ser 1 fila por jugador por partido.")

    return errors

errs = validate(jugadores_df, partidos_df, eventos_df)
if errs:
    st.error("Encontré problemas en el Excel. Corrige esto y vuelve a subir el archivo:")
    for e in errs:
        st.write(f"- {e}")

# =========================
# Si no hay eventos aún
# =========================
if len(eventos_df) == 0:
    st.info("La hoja 'Eventos' está vacía. Cuando cargues el primer partido, aquí verás todos los rankings y gráficas.")
    st.stop()

# =========================
# Preparación de Eventos (tipos)
# =========================
# equipo en minúscula
eventos_df["equipo"] = eventos_df["equipo"].astype(str).str.strip().str.lower()

# Recalcular gol_total
eventos_df["gol_primer"] = pd.to_numeric(eventos_df["gol_primer"], errors="coerce").fillna(0).astype(int)
eventos_df["gol_segundo"] = pd.to_numeric(eventos_df["gol_segundo"], errors="coerce").fillna(0).astype(int)
eventos_df["gol_total"] = (eventos_df["gol_primer"] + eventos_df["gol_segundo"]).astype(int)

# columnas numéricas (enteras)
int_cols = ["gol_recibido","fue_delantero","autogoles","asistencia_gol","amarillas","rojas","penal_atajado"]
for c in int_cols:
    eventos_df[c] = pd.to_numeric(eventos_df[c], errors="coerce").fillna(0).astype(int)

# fraccion_partido para TODOS (float)
if "fraccion_partido" not in eventos_df.columns:
    eventos_df["fraccion_partido"] = 1.0
else:
    eventos_df["fraccion_partido"] = pd.to_numeric(eventos_df["fraccion_partido"], errors="coerce").fillna(1.0).astype(float)

# ids
eventos_df["id_partido"] = pd.to_numeric(eventos_df["id_partido"], errors="coerce")
eventos_df["id_jugador"] = pd.to_numeric(eventos_df["id_jugador"], errors="coerce")
eventos_df = eventos_df.dropna(subset=["id_partido","id_jugador"])
eventos_df["id_partido"] = eventos_df["id_partido"].astype(int)
eventos_df["id_jugador"] = eventos_df["id_jugador"].astype(int)

# =========================
# Merge base
# =========================
jugadores_df["id_jugador"] = pd.to_numeric(jugadores_df["id_jugador"], errors="coerce").astype(int)
partidos_df["id_partido"] = pd.to_numeric(partidos_df["id_partido"], errors="coerce").astype(int)

base = (
    eventos_df
    .merge(jugadores_df, on="id_jugador", how="left")
    .merge(partidos_df, on="id_partido", how="left", suffixes=("", "_partido"))
)

base["activo"] = pd.to_numeric(base["activo"], errors="coerce").fillna(0).astype(int)
base["sancion_grave"] = pd.to_numeric(base["sancion_grave"], errors="coerce").fillna(0).astype(int)

# =========================
# Utilidades de cálculo
# =========================
def resultado_puntos(row):
    eq = row["equipo"]
    if eq == "amarillo":
        r = str(row["resultado_amarillo"]).strip().lower()
    else:
        r = str(row["resultado_azul"]).strip().lower()
    if r == "g":
        return 3
    if r == "e":
        return 1
    return 0

def goles_recibidos_equipo(row):
    # marcador del rival
    if row["equipo"] == "amarillo":
        return int(row["marcador_azul"]) if pd.notna(row["marcador_azul"]) else 0
    else:
        return int(row["marcador_amarillo"]) if pd.notna(row["marcador_amarillo"]) else 0

base["puntos_resultado"] = base.apply(resultado_puntos, axis=1)
base["goles_recibidos_equipo"] = base.apply(goles_recibidos_equipo, axis=1)
base["valla_invicta_equipo"] = (base["goles_recibidos_equipo"] == 0).astype(int)

# Penalizaciones por partido (NO se prorratean)
base["penal_partido"] = (-1 * base["amarillas"]) + (-3 * base["rojas"])

def puntos_posicion(row):
    pos = str(row["posicion"]).strip().lower()
    goles = int(row["gol_total"])
    asis = int(row["asistencia_gol"])
    pen_at = int(row["penal_atajado"])
    valla = int(row["valla_invicta_equipo"])
    fue_del = int(row["fue_delantero"])

    puntos = 0

    if pos == "arquero":
        puntos += 3 * valla
        puntos += 3 * pen_at
        puntos += 3 * goles
        puntos += 1 * asis

    elif pos == "defensa":
        puntos += 3 * valla
        if fue_del == 0:
            puntos += 3 * goles
        puntos += 1 * asis
        if goles >= 3:
            puntos += 1

    elif pos == "mediocampista":
        puntos += 1 * asis
        if goles >= 3:
            puntos += 1

    elif pos == "delantero":
        puntos += 1 * asis
        if goles >= 3:
            puntos += 1

    return puntos

base["puntos_posicion"] = base.apply(puntos_posicion, axis=1)

# =========================
# Puntos por partido (con fracción para TODOS)
# - Se prorratea: puntos_resultado + puntos_posicion
# - NO se prorratea: penal_partido
# =========================
base["puntos_participacion"] = (base["puntos_resultado"] + base["puntos_posicion"]) * base["fraccion_partido"]
base["puntos_partido"] = base["puntos_participacion"] + base["penal_partido"]

# =========================
# Acumulados por jugador (temporada)
# =========================
agg = base.groupby(["id_jugador","nombre","posicion","activo","sancion_grave"], as_index=False).agg(
    puntos_partido_total=("puntos_partido","sum"),
    partidos_jugados=("id_partido","nunique"),
    partidos_equivalentes=("fraccion_partido","sum"),
    goles=("gol_total","sum"),
    asistencia_gol=("asistencia_gol","sum"),
    autogoles=("autogoles","sum"),
    amarillas=("amarillas","sum"),
    rojas=("rojas","sum"),
    penales_atajados=("penal_atajado","sum"),
    goles_recibidos_total=("goles_recibidos_equipo","sum"),   # equipo (se deja por si lo quieres)
    goles_recibidos_arquero=("gol_recibido","sum"),          # arquero (Opción 2)
)

# Penalización por umbrales reiniciables
agg["penal_umbral_amarillas"] = (-3) * (agg["amarillas"] // 5)
agg["penal_umbral_rojas"] = (-5) * (agg["rojas"] // 3)

# Total final año (umbral extra se suma aquí; lo por partido ya estaba)
agg["puntos_total"] = agg["puntos_partido_total"] + agg["penal_umbral_amarillas"] + agg["penal_umbral_rojas"]

# Sanción grave: borra TODOS los puntos (temporada)
agg.loc[agg["sancion_grave"] == 1, "puntos_total"] = 0

# =========================
# Valla menos vencida (Opción 2) y puntos arquero ajustados
# valla_promedio = goles_recibidos_arquero / partidos_equivalentes
# =========================
mask_arq = (agg["posicion"] == "arquero") & (agg["partidos_equivalentes"] > 0)

agg["valla_promedio"] = pd.Series([float("nan")] * len(agg), dtype="float64")
agg.loc[mask_arq, "valla_promedio"] = (
    agg.loc[mask_arq, "goles_recibidos_arquero"] / agg.loc[mask_arq, "partidos_equivalentes"]
)
agg["valla_promedio"] = pd.to_numeric(agg["valla_promedio"], errors="coerce").round(3)

agg["puntos_arquero_ajustados"] = agg["puntos_total"].astype(float)
agg.loc[mask_arq, "puntos_arquero_ajustados"] = (
    (agg.loc[mask_arq, "puntos_total"].astype(float) - agg.loc[mask_arq, "valla_promedio"]).round(3)
)

# =========================
# Ranking con desempate
# 1) puntos
# 2) partidos_jugados
# 3) goles
# 4) asistencia_gol
# =========================
def rank_puntos(df_in, use_arquero_ajustado=False):
    df = df_in.copy()
    df["_p"] = df["puntos_arquero_ajustados"] if use_arquero_ajustado else df["puntos_total"]
    df = df.sort_values(
        by=["_p","partidos_jugados","goles","asistencia_gol"],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)
    df.insert(0, "posicion_ranking", range(1, len(df) + 1))
    return df.drop(columns=["_p"])

# Solo activos para premiaciones/rankings
agg_activos = agg[agg["activo"] == 1].copy()

# =========================
# 1) RANKING POR POSICIÓN - ÚLTIMA FECHA (NO acumulado)
# =========================
ultima_fecha = partidos_df["fecha"].dropna().max()
if pd.isna(ultima_fecha):
    st.warning("No hay fechas válidas en Partidos.")
    st.stop()

base_ultima_fecha = base[(base["fecha"].dt.date == ultima_fecha.date()) & (base["activo"] == 1)].copy()

st.markdown(f"## 🧾 Ranking por posición de la última fecha – {ultima_fecha.date()}")

def ranking_ultima_fecha_por_pos(pos):
    dfp = base_ultima_fecha[base_ultima_fecha["posicion"] == pos].copy()
    if dfp.empty:
        return dfp

    r = dfp.groupby(["id_jugador","nombre"], as_index=False).agg(
        puntos=("puntos_partido","sum"),
        fraccion_total=("fraccion_partido","sum"),
        goles=("gol_total","sum"),
        asistencia_gol=("asistencia_gol","sum"),
        amarillas=("amarillas","sum"),
        rojas=("rojas","sum"),
    )

    r = r.sort_values(
        by=["puntos","fraccion_total","goles","asistencia_gol"],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)

    r.insert(0, "posicion_ranking", range(1, len(r) + 1))
    return r

pos_list = ["arquero","defensa","mediocampista","delantero"]
cols = st.columns(2)
for i, pos in enumerate(pos_list):
    with cols[i % 2]:
        st.subheader(pos.capitalize())
        r = ranking_ultima_fecha_por_pos(pos)
        if r.empty:
            st.info("Sin datos para esta posición en la última fecha.")
        else:
            st.dataframe(r, use_container_width=True)
            fig, ax = plt.subplots()
            ax.bar(r["nombre"], r["puntos"])
            ax.set_title(f"Puntos (última fecha) - {pos.capitalize()}")
            ax.set_ylabel("Puntos")
            ax.tick_params(axis='x', rotation=90)
            st.pyplot(fig)

# =========================
# 2) RANKING ACUMULADO AÑO - POR POSICIÓN
# =========================
st.markdown("## 🏆 Ranking acumulado por puntos (año) - por posición")

def show_rank_acum(pos):
    dfp = agg_activos[agg_activos["posicion"] == pos].copy()
    if dfp.empty:
        st.info("Sin datos.")
        return

    if pos == "arquero":
        ranked = rank_puntos(dfp, use_arquero_ajustado=True)
        st.caption("Nota: Arqueros usan Puntos Ajustados = Puntos Totales - Valla (goles_recibidos_arquero/partidos_equivalentes).")
        show_cols = ["posicion_ranking","nombre","puntos_total","valla_promedio","puntos_arquero_ajustados","partidos_jugados","partidos_equivalentes","goles","asistencia_gol","amarillas","rojas"]
        ycol = "puntos_arquero_ajustados"
    else:
        ranked = rank_puntos(dfp, use_arquero_ajustado=False)
        show_cols = ["posicion_ranking","nombre","puntos_total","partidos_jugados","partidos_equivalentes","goles","asistencia_gol","amarillas","rojas"]
        ycol = "puntos_total"

    st.dataframe(ranked[show_cols], use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(ranked["nombre"], ranked[ycol])
    ax.set_title(f"Puntos acumulados - {pos.capitalize()}")
    ax.set_ylabel("Puntos")
    ax.tick_params(axis='x', rotation=90)
    st.pyplot(fig)

cols = st.columns(2)
for i, pos in enumerate(pos_list):
    with cols[i % 2]:
        st.subheader(pos.capitalize())
        show_rank_acum(pos)

# =========================
# 3) Rankings generales año: goles, asistencias, tarjetas, autogoles
# =========================
st.markdown("## 📊 Rankings generales (año)")

c1, c2 = st.columns(2)
with c1:
    st.subheader("⚽ Goleador (goles acumulados)")
    goleador = agg_activos.sort_values(by=["goles","partidos_jugados"], ascending=[False, False]).reset_index(drop=True)
    goleador = goleador[goleador["goles"] > 0].copy()
    goleador.insert(0, "posicion_ranking", range(1, len(goleador) + 1))
    st.dataframe(goleador[["posicion_ranking","nombre","goles","partidos_jugados","partidos_equivalentes"]], use_container_width=True)
    if not goleador.empty:
        fig, ax = plt.subplots()
        ax.bar(goleador["nombre"], goleador["goles"])
        ax.set_title("Goles por jugador")
        ax.tick_params(axis='x', rotation=90)
        st.pyplot(fig)

with c2:
    st.subheader("🎯 Mayor asistencia_gol (asistencias acumuladas)")
    asis = agg_activos.sort_values(by=["asistencia_gol","partidos_jugados"], ascending=[False, False]).reset_index(drop=True)
    asis = asis[asis["asistencia_gol"] > 0].copy()
    asis.insert(0, "posicion_ranking", range(1, len(asis) + 1))
    st.dataframe(asis[["posicion_ranking","nombre","asistencia_gol","partidos_jugados","partidos_equivalentes"]], use_container_width=True)
    if not asis.empty:
        fig, ax = plt.subplots()
        ax.bar(asis["nombre"], asis["asistencia_gol"])
        ax.set_title("Asistencia_gol por jugador")
        ax.tick_params(axis='x', rotation=90)
        st.pyplot(fig)

c3, c4 = st.columns(2)
with c3:
    st.subheader("🟨 Ranking amarillas")
    am = agg_activos.sort_values(by=["amarillas","partidos_jugados"], ascending=[False, False]).reset_index(drop=True)
    am = am[am["amarillas"] > 0].copy()
    am.insert(0, "posicion_ranking", range(1, len(am) + 1))
    st.dataframe(am[["posicion_ranking","nombre","amarillas","partidos_jugados","partidos_equivalentes"]], use_container_width=True)

with c4:
    st.subheader("🟥 Ranking rojas")
    rj = agg_activos.sort_values(by=["rojas","partidos_jugados"], ascending=[False, False]).reset_index(drop=True)
    rj = rj[rj["rojas"] > 0].copy()
    rj.insert(0, "posicion_ranking", range(1, len(rj) + 1))
    st.dataframe(rj[["posicion_ranking","nombre","rojas","partidos_jugados","partidos_equivalentes"]], use_container_width=True)

st.subheader("🤦 Ranking autogoles")
ag = agg_activos.sort_values(by=["autogoles","partidos_jugados"], ascending=[False, False]).reset_index(drop=True)
ag = ag[ag["autogoles"] > 0].copy()
ag.insert(0, "posicion_ranking", range(1, len(ag) + 1))
st.dataframe(ag[["posicion_ranking","nombre","autogoles","partidos_jugados","partidos_equivalentes"]], use_container_width=True)

# =========================
# 4) Valla menos vencida
# =========================
st.markdown("## 🧤 Ranking valla menos vencida (goles_recibidos_arquero / partidos_equivalentes)")

valla = agg_activos[agg_activos["posicion"] == "arquero"].copy()
valla = valla[valla["partidos_equivalentes"] > 0].copy()
valla = valla.sort_values(by=["valla_promedio","partidos_equivalentes"], ascending=[True, False]).reset_index(drop=True)
valla.insert(0, "posicion_ranking", range(1, len(valla) + 1))

st.dataframe(
    valla[["posicion_ranking","nombre","valla_promedio","goles_recibidos_arquero","partidos_equivalentes","partidos_jugados","puntos_total","puntos_arquero_ajustados"]],
    use_container_width=True
)

if not valla.empty:
    fig, ax = plt.subplots()
    ax.bar(valla["nombre"], valla["valla_promedio"])
    ax.set_title("Promedio de goles recibidos (menor es mejor)")
    ax.tick_params(axis='x', rotation=90)
    st.pyplot(fig)

# =========================
# 5) Resumen de goles por fecha, acumulado por equipo, promedio
# =========================
st.markdown("## 📅 Resumen de goles por fecha (amarillo vs azul)")

resumen = partidos_df.copy().dropna(subset=["fecha"]).sort_values("fecha", ascending=False)
resumen["goles_total_partido"] = resumen["marcador_amarillo"].fillna(0).astype(int) + resumen["marcador_azul"].fillna(0).astype(int)
st.dataframe(resumen[["fecha","marcador_amarillo","marcador_azul","goles_total_partido"]], use_container_width=True)

fig, ax = plt.subplots()
ax.plot(resumen["fecha"], resumen["marcador_amarillo"], marker="o", label="amarillo")
ax.plot(resumen["fecha"], resumen["marcador_azul"], marker="o", label="azul")
ax.set_title("Goles por fecha")
ax.set_ylabel("Goles")
ax.tick_params(axis='x', rotation=45)
ax.legend()
st.pyplot(fig)

st.markdown("## 📈 Resumen acumulado de goles por equipo")
total_goles_amarillo = int(partidos_df["marcador_amarillo"].fillna(0).sum())
total_goles_azul = int(partidos_df["marcador_azul"].fillna(0).sum())

c1, c2, c3 = st.columns(3)
c1.metric("Goles amarillo (acum)", total_goles_amarillo)
c2.metric("Goles azul (acum)", total_goles_azul)

total_partidos = int(partidos_df["id_partido"].nunique())
prom_total = round((total_goles_amarillo + total_goles_azul) / total_partidos, 2) if total_partidos > 0 else 0
c3.metric("⚽ Promedio total goles/partido", prom_total)

# =========================
# 6) Jugador más regular (Índice)
# =========================
st.markdown("## 🧠 Ranking jugador más regular (Índice de Regularidad)")

reg = agg_activos.copy()

# Asistencia: usamos partidos_equivalentes (más justo si hay medias asistencias)
max_part_eq = reg["partidos_equivalentes"].max() if len(reg) else 1
reg["score_asistencia"] = (reg["partidos_equivalentes"] / max_part_eq) if max_part_eq else 0

# Rendimiento por rol: percentil dentro de posición (arquero usa ajustado)
reg["score_rol"] = 0.0
for pos in POS_VALIDAS:
    sub = reg[reg["posicion"] == pos].copy()
    if sub.empty:
        continue
    if pos == "arquero":
        s = sub["puntos_arquero_ajustados"].rank(pct=True)
    else:
        s = sub["puntos_total"].rank(pct=True)
    reg.loc[reg["posicion"] == pos, "score_rol"] = s.values

# Aporte ofensivo global
reg["ofensivo"] = reg["goles"] + reg["asistencia_gol"]
reg["score_ofensivo"] = reg["ofensivo"].rank(pct=True) if len(reg) else 0

# Disciplina (castigo): más castigo => peor
reg["castigo_disciplina"] = (reg["amarillas"] * 1) + (reg["rojas"] * 3) + ((reg["amarillas"] // 5) * 3) + ((reg["rojas"] // 3) * 5)
disc_pct = reg["castigo_disciplina"].rank(pct=True) if len(reg) else 0
reg["score_disciplina"] = 1 - disc_pct

reg["indice_regularidad"] = (
    0.40 * reg["score_asistencia"] +
    0.35 * reg["score_rol"] +
    0.15 * reg["score_ofensivo"] +
    0.10 * reg["score_disciplina"]
).round(4)

reg = reg.sort_values(by=["indice_regularidad","partidos_equivalentes","goles","asistencia_gol"], ascending=[False, False, False, False]).reset_index(drop=True)
reg.insert(0, "posicion_ranking", range(1, len(reg) + 1))

st.dataframe(
    reg[["posicion_ranking","nombre","posicion","indice_regularidad","partidos_jugados","partidos_equivalentes","puntos_total","goles","asistencia_gol","amarillas","rojas"]],
    use_container_width=True
)

fig, ax = plt.subplots()
ax.bar(reg["nombre"], reg["indice_regularidad"])
ax.set_title("Índice de regularidad (mayor es mejor)")
ax.tick_params(axis='x', rotation=90)
st.pyplot(fig)
