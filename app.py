import streamlit as st
import pandas as pd
from predictor import calcular_tabla, match_probabilities, top_scorelines, FILE

# 🔐 Usuarios con roles
USUARIOS = {
    "agustin": {"clave": "premier2025", "rol": "admin"},
    "invitado": {"clave": "futbol2025", "rol": "public"}
}

# 🔒 Estado inicial
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# 🔐 Login
if not st.session_state["autenticado"]:
    st.set_page_config(page_title="Premier Predictor", layout="centered")
    st.title("🔐 Acceso privado")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario in USUARIOS and USUARIOS[usuario]["clave"] == clave:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.session_state["rol"] = USUARIOS[usuario]["rol"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ✅ App principal
st.set_page_config(page_title="Premier Predictor", layout="wide")
df = pd.read_csv(FILE, parse_dates=["fecha"])

st.title("🏆 Premier Predictor 2025")
st.markdown(f"👋 Bienvenido, **{st.session_state['usuario']}**. Rol: `{st.session_state['rol']}`")
st.sidebar.divider()

# 🔒 Cierre de sesión
if st.sidebar.button("🔒 Cerrar sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

# 🎯 Menú dinámico
opciones_publicas = [
    "Ver tabla de posiciones",
    "Predicción de la próxima jornada"
]

opciones_admin = [
    "Ver partidos pendientes",
    "Ver marcadores más probables de un partido",
    "Seleccionar jornada para ver y editar",
    "Editar partido por índice",
    "Editar todos los partidos de una jornada"
]

menu = opciones_publicas + opciones_admin if st.session_state["rol"] == "admin" else opciones_publicas
opcion = st.sidebar.selectbox("Selecciona una opción", menu)


# 📊 Tabla de posiciones
if opcion == "Ver tabla de posiciones":
    st.subheader("📊 Tabla de posiciones")
    tabla = calcular_tabla(df)
    st.dataframe(tabla[["PJ","PG","PE","PP","GF","GC","DG","Pts"]])
    st.divider()

# 📅 Partidos pendientes
elif opcion == "Ver partidos pendientes":
    st.subheader("📅 Partidos pendientes")
    pendientes = df[df["goles_local"].isna() | df["goles_visitante"].isna()]
    if pendientes.empty:
        st.success("No hay partidos pendientes.")
    else:
        st.dataframe(pendientes[["jornada","fecha","local","visitante"]])
    st.divider()

# ✏️ Editar partido por índice (solo admin)
elif opcion == "Editar partido por índice":
    if st.session_state["rol"] != "admin":
        st.warning("⚠️ Esta función solo está disponible para administradores.")
        st.stop()
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
    st.divider()

# 🗓️ Editar jornada completa (solo admin)
elif opcion == "Editar todos los partidos de una jornada":
    if st.session_state["rol"] != "admin":
        st.warning("⚠️ Esta función solo está disponible para administradores.")
        st.stop()
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
    st.divider()

# 🔮 Predicción de marcador
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
    st.divider()

# 🧮 Ver y editar jornada
elif opcion == "Seleccionar jornada para ver y editar":
    st.subheader("🧮 Ver y editar jornada")
    jsel = st.number_input("Selecciona jornada", min_value=1, step=1)
    jornada = df[df["jornada"] == jsel]
    if jornada.empty:
        st.warning("No existe esa jornada.")
    else:
        st.dataframe(jornada[["local","visitante","goles_local","goles_visitante"]])
    st.divider()

elif opcion == "Predicción de la próxima jornada":
    st.subheader("📅 Predicción de la próxima jornada pendiente")

    # Detectar la próxima jornada con partidos sin resultado
    jornadas_pendientes = df[df["goles_local"].isna()]["jornada"].sort_values().unique()
    if len(jornadas_pendientes) == 0:
        st.success("✅ Todas las jornadas están completas.")
    else:
        jsel = jornadas_pendientes[0]
        st.info(f"🔮 Mostrando predicciones para la jornada {jsel}")
        jornada = df[df["jornada"] == jsel]
        pendientes = jornada[jornada["goles_local"].isna()]

        tabla = calcular_tabla(df)
        tabla["posicion"] = tabla["Pts"].rank(method="min", ascending=False).astype(int)

        for _, row in pendientes.iterrows():
            with st.container():
                local_original = row["local"]
                visitante_original = row["visitante"]

                try:
                    pos_local = tabla.loc[local_original]["posicion"]
                    pos_visitante = tabla.loc[visitante_original]["posicion"]
                except KeyError:
                    st.warning(f"No se encontró posición para {local_original} o {visitante_original}.")
                    continue

                local = local_original if pos_local < pos_visitante else visitante_original
                visitante = visitante_original if local == local_original else local_original

                st.markdown(f"### 🗓️ Jornada {row['jornada']} — ⚔️ {local} vs {visitante}")

                df_hist = df[(df["jornada"] < row["jornada"]) & df["goles_local"].notna() & df["goles_visitante"].notna()]

                gf_local = df_hist[df_hist["visitante"] == local]["goles_visitante"].mean() or 1.0
                gc_visitante = df_hist[df_hist["local"] == visitante]["goles_visitante"].mean() or 1.0
                gf_visitante = df_hist[df_hist["visitante"] == visitante]["goles_visitante"].mean() or 1.0
                gc_local = df_hist[df_hist["local"] == local]["goles_visitante"].mean() or 1.0

                lambda_home = (gf_local + gc_visitante) / 2
                lambda_away = (gf_visitante + gc_local) / 2
                p_home, p_draw, p_away = match_probabilities(lambda_home, lambda_away)

                favorito = local if p_home > max(p_draw, p_away) else visitante if p_away > max(p_home, p_draw) else "Empate"

                st.write(f"⚽ Goles esperados: {local} {lambda_home:.2f} - {lambda_away:.2f} {visitante}")
                st.write(f"📊 Probabilidades: {local} {p_home:.1%}, Empate {p_draw:.1%}, {visitante} {p_away:.1%}")
                st.write(f"👉 Favorito: **{favorito}**")

                st.write("🎯 Marcadores más probables:")
                top5 = top_scorelines(lambda_home, lambda_away)
                for (gh, ga), p in top5:
                    st.write(f"- {local} {gh}-{ga} {visitante} → {p:.1%}")
                st.divider()

