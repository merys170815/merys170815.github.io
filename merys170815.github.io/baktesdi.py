from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.stable_api import IQ_Option
import time

# Configuración de la conexión a la API de IQ Option
email = "sirem66@gmail.com"
password = "22520873Me"
API = IQ_Option(email, password)

try:
    API.connect()
    time.sleep(2)  # Esperar a que la conexión sea estable

    # Obtener la lista de todos los activos disponibles y sus estados
    activos = API.get_all_open_time()

    # Filtrar y mostrar solo los activos digitales que están abiertos
    for tipo, activos_tipo in activos.items():
        if tipo == "digital":
            print(f"Categoría: {tipo}")
            for activo, detalles in activos_tipo.items():
                if detalles['open']:
                    print(f"Activo: {activo} - Abierto: {detalles['open']}")
except Exception as e:
    print("Error al conectar a la API:", e)
finally:
    # Desconectar de la API
    API.api.close()
