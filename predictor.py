import pandas as pd
import numpy as np
from math import exp, factorial

# Archivo base de datos
FILE = "premier 2025.csv"

# -----------------------------
# Funciones auxiliares
# -----------------------------
def poisson_pmf(lmbda, k):
    return (lmbda ** k) * exp(-lmbda) / factorial(k)

def match_probabilities(lambda_home, lambda_away, max_goals=10):
    p_home = p_draw = p_away = 0
    for gh in range(max_goals+1):
        for ga in range(max_goals+1):
            p = poisson_pmf(lambda_home, gh) * poisson_pmf(lambda_away, ga)
            if gh > ga: p_home += p
            elif gh == ga: p_draw += p
            else: p_away += p
    return p_home, p_draw, p_away

def top_scorelines(lambda_home, lambda_away, max_goals=5, top_n=5):
    resultados = []
    for gh in range(max_goals+1):
        for ga in range(max_goals+1):
            p = poisson_pmf(lambda_home, gh) * poisson_pmf(lambda_away, ga)
            resultados.append(((gh, ga), p))
    return sorted(resultados, key=lambda x: x[1], reverse=True)[:top_n]

def calcular_tabla(df):
    equipos = set(df["local"]).union(set(df["visitante"]))
    tabla = {team: {"PJ":0,"PG":0,"PE":0,"PP":0,"GF":0,"GC":0,"DG":0,"Pts":0} for team in equipos}
    for _, row in df.iterrows():
        if pd.isna(row["goles_local"]) or pd.isna(row["goles_visitante"]): continue
        h,a = row["local"], row["visitante"]
        gh,ga = int(row["goles_local"]), int(row["goles_visitante"])
        tabla[h]["PJ"]+=1; tabla[a]["PJ"]+=1
        tabla[h]["GF"]+=gh; tabla[h]["GC"]+=ga
        tabla[a]["GF"]+=ga; tabla[a]["GC"]+=gh
        if gh>ga: tabla[h]["PG"]+=1; tabla[a]["PP"]+=1; tabla[h]["Pts"]+=3
        elif gh<ga: tabla[a]["PG"]+=1; tabla[h]["PP"]+=1; tabla[a]["Pts"]+=3
        else: tabla[h]["PE"]+=1; tabla[a]["PE"]+=1; tabla[h]["Pts"]+=1; tabla[a]["Pts"]+=1
        tabla[h]["DG"]=tabla[h]["GF"]-tabla[h]["GC"]
        tabla[a]["DG"]=tabla[a]["GF"]-tabla[a]["GC"]
    df_tabla = pd.DataFrame.from_dict(tabla, orient="index")
    df_tabla.index.name="Equipo"
    return df_tabla.sort_values(by=["Pts","DG","GF"], ascending=[False,False,False])

