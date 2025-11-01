import os

def escudo_path(nombre):
    archivo = f"{nombre}.png"
    return os.path.join("assets", "escudos", archivo)
