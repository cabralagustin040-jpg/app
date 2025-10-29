import streamlit as st
import pandas as pd
from predictor import calcular_tabla, match_probabilities, top_scorelines, FILE

# 🔐 Login básico
USUARIOS = {
    "agustin": "premier2025",
    "admin": "1234"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.set_page_config(page_title="Premier Predictor", layout="centered")
    st.title("🔐 Acceso privado")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario in USUARIOS and USUARIOS[usuario] == clave:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ✅ App principal (solo si está autenticado)
st.set_page_config(page_title="Premier Predictor", layout="wide")
df = pd.read_csv(FILE, parse_dates=["fecha"])

st.title("🏆 Premier Predictor 2025")

opcion = st.sidebar.selectbox("Selecciona una opción", [
    "Ver tabla de posiciones",
    "Ver partidos pendientes",
    "Editar partido por índice",
    "Editar todos los partidos de una jornada",
    "Ver marcadores más probables de un partido",
    "Seleccionar jornada para ver y editar",
    "Posibles apuestas por jornada"
])

if opcion == "Ver tabla de posiciones":
    st.subheader("📊 Tabla de posiciones")
    tabla = calcular_tabla(df)
    st.dataframe(tabla[["PJ","PG","PE","PP","GF","GC","DG","Pts"]])

elif opcion == "Ver partidos pendientes":
    st.subheader("📅 Partidos pendientes")
    pendientes = df[df["goles_local"].isna() | df["goles_visitante"].isna()]
    if pendientes.empty:
        st.success("No hay partidos pendientes.")
    else:
        st.dataframe(pendientes[["jornada","fecha","local","visitante"]])

elif opcion == "Editar partido por índice":
    st.subheader("✏️ Editar partido por índice")
    idx = st.number_input("Índice del partido", min_value=0, max_value=len(df)-1, step=1)
    row = df.loc[idx]
    st.write(f"Editando: Jornada {row['jornada']} {row['local']} vs {row['visitante']}")
    gl = st.number_input("Goles local", min_value=0, step=1)
    gv = st.number_input("Goles visitante", min_value=0, step=1)
    if st.button("Guardar cambios"):
        df.at[idx,"goles_local"] = gl
        df.at[idx,"goles_visitante"] = gv
        df.to_csv(FILE, index=False)
        st.success("✅ Partido actualizado.")

elif opcion == "Editar todos los partidos de una jornada":
    st.subheader("🗓️ Editar jornada completa")
    jsel = st.number_input("Número de jornada", min_value=1, step=1)
    jornada = df[df["jornada"] == jsel]
    if jornada.empty:
        st.warning("No existe esa jornada.")
    else:
        for idx, row in jornada.iterrows():
            if pd.isna(row["goles_local"]) or pd.isna(row["goles_visitante"]):
                st.write(f"{row['local']} vs {row['visitante']}")
                gl = st.number_input(f"Goles {row['local']} (idx {idx})", min_value=0, step=1, key=f"gl{idx}")
                gv = st.number_input(f"Goles {row['visitante']} (idx {idx})", min_value=0, step=1, key=f"gv{idx}")
                if st.button(f"Guardar partido {idx}"):
                    df.at[idx,"goles_local"] = gl
                    df.at[idx,"goles_visitante"] = gv
                    df.to_csv(FILE, index=False)
                    st.success(f"✅ Partido {idx} actualizado.")

elif opcion == "Ver marcadores más probables de un partido":
    st.subheader("🔮 Predicción de marcador")
    idx = st.number_input("Índice del partido", min_value=0, max_value=len(df)-1, step=1)
    row = df.loc[idx]
    st.write(f"Partido: {row['local']} vs {row['visitante']}")

    df_hist = df[(df["fecha"] < row["fecha"]) & df["goles_local"].notna() & df["goles_visitante"].notna()]
    gf_home = df_hist[df_hist["local"] == row["local"]]["goles_local"].mean() or 1.0
    gc_home = df_hist[df_hist["local"] == row["local"]]["goles_visitante"].mean() or 1.0
    gf_away = df_hist[df_hist["visitante"] == row["visitante"]]["goles_visitante"].mean() or 1.0
    gc_away = df_hist[df_hist["visitante"] == row["visitante"]]["goles_local"].mean() or 1.0

    lambda_home = (gf_home + gc_away) / 2
    lambda_away = (gf_away + gc_home) / 2
    p_home, p_draw, p_away = match_probabilities(lambda_home, lambda_away)

    favorito = row['local'] if p_home > max(p_draw, p_away) else row['visitante'] if p_away > max(p_home, p_draw) else "Empate"
    st.write(f"⚽ Goles esperados: {row['local']} {lambda_home:.2f} - {lambda_away:.2f} {row['visitante']}")
    st.write(f"📊 Probabilidades: {row['local']} {p_home:.1%}, Empate {p_draw:.1%}, {row['visitante']} {p_away:.1%}")
    st.write(f"👉 Favorito: **{favorito}**")

    st.write("🎯 Marcadores más probables:")
    top5 = top_scorelines(lambda_home, lambda_away)
    for (gh, ga), p in top5:
        st.write(f"- {row['local']} {gh}-{ga} {row['visitante']} → {p:.1%}")

elif opcion == "Seleccionar jornada para ver y editar":
    st.subheader("🧮 Ver y editar jornada")
    jsel = st.number_input("Selecciona jornada", min_value=1, step=1)
    jornada = df[df["jornada"] == jsel]
    if jornada.empty:
        st.warning("No existe esa jornada.")
    else:
        st.dataframe(jornada[["local","visitante","goles_local","goles_visitante"]])

elif opcion == "Posibles apuestas por jornada":
    st.subheader("💰 Predicción por jornada")
    jsel = st.number_input("Selecciona jornada", min_value=1, step=1)
    jornada = df[df["jornada"] == jsel]
    pendientes = jornada[jornada["goles_local"].isna()]
    if pendientes.empty:
        st.success("Todos los partidos tienen resultado.")
    else:
        for idx, row in pendientes.iterrows():
            st.write(f"Partido: {row['local']} vs {row['visitante']}")
            df_hist = df[(df["fecha"] < row["fecha"]) & df["goles_local"].notna() & df["goles_visitante"].notna()]
            gf_home = df_hist[df_hist["local"] == row["local"]]["goles_local"].mean() or 1.0
            gc_home = df_hist[df_hist["local"] == row["local"]]["goles_visitante"].mean() or 1.0
            gf_away = df_hist[df_hist["visitante"] == row["visitante"]]["goles_visitante"].mean() or 1.0
            gc_away = df_hist[df_hist["visitante"] == row["visitante"]]["goles_local"].mean() or 1.0

            lambda_home = (gf_home + gc_away) / 2
            lambda_away = (gf_away + gc_home) / 2
            p_home, p_draw, p_away = match_probabilities(lambda_home, lambda_away)

            favorito = row['local'] if p_home > max(p_draw, p_away) else row['visitante'] if p_away > max(p_home, p_draw) else "Empate"
            st.write(f"⚽ Goles esperados: {row['local']} {lambda_home:.2f} - {lambda_away:.2f} {row['visitante']}")
            st.write(f"📊 Probabilidades: {row['local']} {p_home:.1%}, Empate {p_draw:.1%}, {row['visitante']} {p_away:.1%}")
            st.write(f"👉 Favorito: **{favorito}**")
            st.write

