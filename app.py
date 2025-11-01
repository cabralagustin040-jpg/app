import streamlit as st
import pandas as pd
from predictor import calcular_tabla, match_probabilities, top_scorelines, FILE
from utils import escudo_path


# 🔐 Usuarios con roles
USUARIOS = {
    "agustin": {"clave": "premier2025", "rol": "admin"},
    "invitado": {"clave": "futbol2025", "rol": "public"},
     "premier": {"clave": "futbol2025", "rol": "public"},
     "Premier": {"clave": "futbol2025", "rol": "public"}  
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
 "🛠️ Rellenar encuentros (admin)"
]

menu = opciones_publicas + opciones_admin if st.session_state["rol"] == "admin" else opciones_publicas
opcion = st.sidebar.selectbox("Selecciona una opción", menu)

if opcion == "Ver tabla de posiciones":
    st.subheader("📊 Tabla de posiciones")
    tabla = calcular_tabla(df).copy()

    for club, fila in tabla.iterrows():
        col1, col2 = st.columns([1, 5])
        ruta = escudo_path(club)
        col1.image(ruta, width=60)
        col2.markdown(
            f"""
            <div style='line-height: 1.6'>
            <b>{club}</b><br>
            Pts: {fila['Pts']} | PJ: {fila['PJ']} | PG: {fila['PG']} | PE: {fila['PE']} | PP: {fila['PP']}<br>
            GF: {fila['GF']} | GC: {fila['GC']} | DG: {fila['DG']}
            </div>
            """,
            unsafe_allow_html=True
        )
    st.divider()

elif opcion == "🛠️ Rellenar encuentros (admin)":
    st.subheader("🛠️ Rellenar encuentros")

    jornadas = sorted(df["jornada"].unique())
    jornada_seleccionada = st.selectbox("Seleccioná la jornada", jornadas)

    partidos_jornada = df[df["jornada"] == jornada_seleccionada]

    for idx, partido in partidos_jornada.iterrows():
        st.markdown(f"**{partido['local']} vs {partido['visitante']}**")

        col1, col2 = st.columns(2)

        # Manejo seguro de NaN
        valor_local = int(partido["goles_local"]) if pd.notna(partido["goles_local"]) else 0
        valor_visitante = int(partido["goles_visitante"]) if pd.notna(partido["goles_visitante"]) else 0

        valor_local = int(partido["goles_local"]) if pd.notna(partido["goles_local"]) else 0
        gol_local = col1.number_input(f"Goles {partido['local']}", min_value=0, value=valor_local, key=f"local_{idx}")

        gol_visitante = col2.number_input(f"Goles {partido['visitante']}", min_value=0, value=valor_visitante, key=f"visitante_{idx}")

        if st.button("Guardar", key=f"guardar_{idx}"):
            df.at[idx, "goles_local"] = gol_local
            df.at[idx, "goles_visitante"] = gol_visitante
            st.success("✅ Partido actualizado")

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


