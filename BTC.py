import praw
import smtplib
import json
import websocket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from textblob import TextBlob
from binance.client import Client
from sklearn.preprocessing import MinMaxScaler
import time
import pandas as pd
import numpy as np

from scipy.signal import find_peaks

# Definir las variables globales necesarias
closing_prices = None
volume_data = None
last_real_time_price = None
# Definir la variable comentarios
comentarios = []

# Convertir el array numpy en DataFrame de Pandas
closing_prices_df = pd.DataFrame(closing_prices)

# Configuración de la API de Reddit
REDDIT_CLIENT_ID = 'syTgPQWR92sh3umGqTVpOg'
REDDIT_CLIENT_SECRET = 'oflk5tr4jOJmS1rXv65A5VdpqWkq2g'
REDDIT_USER_AGENT = 'script by /u/username'  # Puedes cambiar 'username' por tu nombre de usuario de Reddit

# Configuración de la API de Binance
API_KEY = '5vWrP5bgXUpFa89KQBrJoTfAUUH8eZwccU7Q6CZcD4hrU7Rs9aqKf46bqBJTMRwU'
API_SECRET = 'ica2XnjMGd5HOgwWH4spFiSXZvn8ogukQHWbGUTpvt4I9z6wpQbtnM4YZISqhMNU'
client = Client(API_KEY, API_SECRET)


# En algún lugar de tu código, antes de usarlo
scaler = MinMaxScaler()

def obtener_datos_binance(symbol, intervalo, limit):
    klines = client.get_klines(symbol=symbol, interval=intervalo, limit=limit)
    closing_prices = [float(kline[4]) for kline in klines]
    volume_data = [float(kline[5]) for kline in klines]

    # Usar el scaler y guardar el scaler para usarlo más tarde
    dataset = scaler.fit_transform(np.array(closing_prices).reshape(-1, 1))

    df = pd.DataFrame({'closing_prices': closing_prices, 'volume_data': volume_data})
    df['closing_prices_scaled'] = dataset

    return df, closing_prices, volume_data, scaler

def calcular_rsi(precios_serie):
    """
    Calcular el RSI (Relative Strength Index) de una serie de precios.
    """
    try:
        # Calcula los cambios en los precios
        delta = precios_serie.diff()

        # Calcula las ganancias y las pérdidas
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calcula las medias móviles de ganancias y pérdidas
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        # Evita la división por cero
        avg_loss[avg_loss == 0] = np.nan

        # Calcula el RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    except Exception as e:
        print("Error al calcular el RSI:", e)
        return pd.Series([50] * len(precios_serie))  # Valor de RSI ficticio
def detectar_divergencias_y_estado_en_tiempo_real():
    try:
        # Obtener datos en tiempo real
        data_source = DataSource(client)
        precios_serie = data_source.obtener_datos_en_tiempo_real()['closing_prices']

        # Calcular el RSI en tiempo real
        rsi = calcular_rsi(precios_serie)

        # Detectar divergencias en tiempo real
        divergencias, tipo_divergencia = detectar_divergencias(rsi, precios_serie)

        # Detectar el estado del mercado en tiempo real
        estado_mercado = detectar_estado_mercado(rsi)

        return divergencias, tipo_divergencia, rsi, estado_mercado  # Devolver las divergencias, el tipo de divergencia, el RSI y el estado del mercado en tiempo real

    except Exception as e:
        print("Error al detectar divergencias y estado del mercado en tiempo real:", e)
        return False, None, None, None  # Devolver valores predeterminados si hay un error
def detectar_divergencias(rsi, precios_serie):
    """
    Detectar divergencias en el RSI.
    """
    try:
        # Filtrar los valores NaN e inf en el RSI
        rsi = rsi.replace([np.inf, -np.inf], np.nan).dropna()
        # Alinea los índices de rsi y precios_serie
        rsi, precios_serie = rsi.align(precios_serie, join='inner')

        if len(rsi) < 2 or len(precios_serie) < 2:
            return False, None

        # Calcula la diferencia entre los precios
        delta_precios = np.diff(precios_serie)

        # Encuentra los cambios de dirección en el RSI
        delta_rsi = np.diff(rsi)

        # Índices donde ocurren los cambios de dirección en el RSI
        indices_cambios_rsi = np.where(delta_rsi != 0)[0]

        # Verifica si hay divergencia en cada cambio de dirección en el RSI
        for idx in indices_cambios_rsi:
            print(f"Índice de cambio RSI: {idx}")
            print(f"Delta RSI: {delta_rsi[idx]}")
            print(f"Delta precios: {delta_precios[idx]}")
            if delta_rsi[idx] > 0 and delta_precios[idx] < 0:  # Divergencia bajista
                return True, 'Bajista'
            elif delta_rsi[idx] < 0 and delta_precios[idx] > 0:  # Divergencia alcista
                return True, 'Alcista'

        return False, None

    except Exception as e:
        print("Error al detectar divergencias:", e)
        return False, None

def detectar_estado_mercado(rsi):
    """
    Detecta el estado del mercado (sobrecompra o sobreventa) en tiempo real utilizando el RSI.
    """
    try:
        if rsi.iloc[-1] >= 70:
            return "Sobrecompra"
        elif rsi.iloc[-1] <= 30:
            return "Sobreventa"
        else:
            return "Neutral"
    except Exception as e:
        print("Error al detectar el estado del mercado:", e)
        return "Neutral"
def detectar_ley_dow_avanzado(closing_prices_df):
    try:
        ultimo_cierre = closing_prices_df['closing_prices'].iloc[-1]
        cierre_anterior = closing_prices_df['closing_prices'].iloc[-2]
        cambio_porcentual = (ultimo_cierre - cierre_anterior) / cierre_anterior * 100
        sma_50 = closing_prices_df['closing_prices'].rolling(window=50, min_periods=1).mean().iloc[-1]
        sma_200 = closing_prices_df['closing_prices'].rolling(window=200, min_periods=1).mean().iloc[-1]
        ema_50 = closing_prices_df['closing_prices'].ewm(span=50, adjust=False, min_periods=1).mean().iloc[-1]
        ema_200 = closing_prices_df['closing_prices'].ewm(span=200, adjust=False, min_periods=1).mean().iloc[-1]
        if sma_50 > sma_200 and ema_50 > ema_200:
            tendencia = "Tendencia alcista fuerte" if cambio_porcentual > 0.5 else "Tendencia alcista"
        elif sma_50 < sma_200 and ema_50 < ema_200:
            tendencia = "Tendencia bajista fuerte" if cambio_porcentual < -0.5 else "Tendencia bajista"
        else:
            tendencia = "Tendencia lateral" if cambio_porcentual > 0 else "Tendencia bajista"
        return f"{tendencia} según la Ley de Dow"
    except Exception as e:
        print("Error al detectar la Ley de Dow:", e)
        return "Neutral"

def detectar_tendencia_macd_con_cambio_porcentual(closing_prices_df):
    try:
        if closing_prices_df.empty:
            print("El DataFrame 'closing_prices_df' está vacío.")
            return "No hay señal clara en este momento"

        # Calculamos el MACD y las señales
        ema_12 = closing_prices_df['closing_prices'].ewm(span=12, adjust=False).mean()
        ema_26 = closing_prices_df['closing_prices'].ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9, adjust=False).mean()

        # Calcular el cambio porcentual
        if len(closing_prices_df) < 2:
            print("No hay suficientes datos para calcular el cambio porcentual.")
            return "No hay señal clara en este momento"

        cambio_porcentual = (closing_prices_df['closing_prices'].iloc[-1] - closing_prices_df['closing_prices'].iloc[-2]) / closing_prices_df['closing_prices'].iloc[-2] * 100

        # Definir umbrales para identificar señales claras
        umbral_cambio_porcentual = 0.1  # Puedes ajustar este umbral según tus necesidades

        # Si el MACD cruza por encima de la señal y el cambio porcentual es positivo, es una señal alcista
        if macd.iloc[-1] > signal_line.iloc[-1] and cambio_porcentual > umbral_cambio_porcentual:
            return "Tendencia alcista según el MACD y cambio porcentual"
        # Si el MACD cruza por debajo de la señal y el cambio porcentual es negativo, es una señal bajista
        elif macd.iloc[-1] < signal_line.iloc[-1] and cambio_porcentual < -umbral_cambio_porcentual:
            return "Tendencia bajista según el MACD y cambio porcentual"
        # Si el MACD y la señal están cerca y el cambio porcentual es bajo, considera esto como tendencia lateral
        else:
            return "Tendencia lateral según el MACD y cambio porcentual"

    except Exception as e:
        print("Error:", e)
        return "Neutral"  # Resultado por defecto en caso de error

def detectar_patrones_graficos(data_source, intervalo_tiempo=1, tamaño_muestra=10):
    try:
        # Obtener los nuevos datos en tiempo real
        df = data_source.obtener_datos_en_tiempo_real()

        # Verificar si los datos son válidos
        if isinstance(df, pd.DataFrame) and not df.empty:
            precios = df['closing_prices'].to_numpy()
            volumenes = df['volume_data'].to_numpy()

            patrones_detectados = {}

            # Priorizar la detección de patrones más significativos y específicos primero
            if detectar_doble_piso(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Doble Piso"] = "Alcista"
            if detectar_doble_techo(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Doble Techo"] = "Bajista"
            if tipo := detectar_cabeza_hombros(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Cabeza y Hombros"] = tipo
            if detectar_triangulo_ascendente(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Triángulo Ascendente"] = "Alcista"
            if detectar_triangulo_descendente(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Triángulo Descendente"] = "Bajista"
            if detectar_cuña_ascendente(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Cuña Ascendente"] = "Alcista"
            if detectar_cuña_descendente(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Cuña Descendente"] = "Bajista"
            if tipo := detectar_bandera(precios, volumenes, intervalo_tiempo, tamaño_muestra):
                patrones_detectados["Bandera"] = tipo

            # Encontrar el patrón predominante
            patron_predominante = None
            tipo_predominante = None
            for patron, tipo in patrones_detectados.items():
                if tipo_predominante is None or tipo_predominante == tipo:
                    patron_predominante = patron
                    tipo_predominante = tipo
                else:
                    # Si hay discrepancia en los tipos, determinar cuál tiene más influencia
                    if tipo_predominante == "Alcista" and tipo == "Bajista":
                        patron_predominante = "Doble Piso"  # Priorizar patrones alcistas
                    elif tipo_predominante == "Bajista" and tipo == "Alcista":
                        patron_predominante = "Doble Techo"  # Priorizar patrones bajistas

            # Imprimir el patrón predominante
            if patron_predominante:
                print(f"Resultado del análisis práctico: Patrón detectado: {patron_predominante} ({tipo_predominante})")
                return {patron_predominante: tipo_predominante}
            else:
                print("No se encontraron patrones predominantes.")
                return {}

        else:
            print("Los datos en tiempo real son inválidos o están vacíos.")
            return {}

    except Exception as e:
        print("Error al detectar patrones gráficos:", e)
        return {}  # Dummy pattern detection
def detectar_triangulo_ascendente(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= intervalo_tiempo * 2 and len(volumes) >= intervalo_tiempo * 2:
        indices = np.arange(intervalo_tiempo, len(closing_prices) + 1)
        for i in indices:
            precios_segmento = closing_prices[i - intervalo_tiempo:i]
            vol_segmento = volumes[i - intervalo_tiempo:i]
            print(f"Verificando triángulo ascendente en precios: {precios_segmento}, volúmenes: {vol_segmento}")
            if np.all(precios_segmento > precios_segmento[0]) and \
               np.all(vol_segmento < vol_segmento[0]):
                return True
    return False

def detectar_triangulo_descendente(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= intervalo_tiempo * 2 and len(volumes) >= intervalo_tiempo * 2:
        indices = np.arange(intervalo_tiempo, len(closing_prices) + 1)
        for i in indices:
            precios_segmento = closing_prices[i - intervalo_tiempo:i]
            vol_segmento = volumes[i - intervalo_tiempo:i]
            print(f"Verificando triángulo descendente en precios: {precios_segmento}, volúmenes: {vol_segmento}")
            if np.all(precios_segmento < precios_segmento[0]) and \
               np.all(vol_segmento > vol_segmento[0]):
                return True
    return False

def detectar_cuña_ascendente(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= tamaño_muestra * 2 and len(volumes) >= tamaño_muestra * 2:
        indices = np.arange(intervalo_tiempo * 2, len(closing_prices) + 1)
        for i in indices:
            precios_segmento = closing_prices[i - tamaño_muestra:i]
            vol_segmento = volumes[i - tamaño_muestra:i]
            # Verificar si hay suficientes datos en el segmento
            if len(precios_segmento) == tamaño_muestra and len(vol_segmento) == tamaño_muestra:
                print(f"Verificando cuña ascendente en precios: {precios_segmento}, volúmenes: {vol_segmento}")
                if np.all(precios_segmento > precios_segmento[0]) and \
                   np.all(vol_segmento < vol_segmento[0]):
                    return True
    return False

def detectar_cuña_descendente(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= tamaño_muestra * 2 and len(volumes) >= tamaño_muestra * 2:
        indices = np.arange(intervalo_tiempo * 2, len(closing_prices) + 1)
        for i in indices:
            precios_segmento = closing_prices[i - tamaño_muestra:i]
            vol_segmento = volumes[i - tamaño_muestra:i]
            # Verificar si hay suficientes datos en el segmento
            if len(precios_segmento) == tamaño_muestra and len(vol_segmento) == tamaño_muestra:
                print(f"Verificando cuña descendente en precios: {precios_segmento}, volúmenes: {vol_segmento}")
                if np.all(precios_segmento < precios_segmento[0]) and \
                   np.all(vol_segmento > vol_segmento[0]):
                    return True
    return False
def detectar_cabeza_hombros(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= intervalo_tiempo + tamaño_muestra and len(volumes) >= intervalo_tiempo + tamaño_muestra:
        indices = np.arange(intervalo_tiempo - 1, len(closing_prices))
        for i in indices:
            precios_segmento = closing_prices[i - tamaño_muestra:i]
            vol_segmento = volumes[i - tamaño_muestra:i]
            print(f"Verificando cabeza y hombros en precios: {precios_segmento}, volúmenes: {vol_segmento}")
            if np.all(precios_segmento < closing_prices[i]) and np.all(vol_segmento < volumes[i]):
                return "Bajista"
            elif np.all(precios_segmento > closing_prices[i]) and np.all(vol_segmento < volumes[i]):
                return "Alcista"
    return None

def detectar_bandera(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) >= intervalo_tiempo and len(volumes) >= intervalo_tiempo:
        indices = np.arange(intervalo_tiempo - 1, len(closing_prices))
        for i in indices:
            precios_segmento = closing_prices[i - tamaño_muestra:i]
            vol_segmento = volumes[i - tamaño_muestra:i]
            # Verificar si hay suficientes datos en el segmento
            if len(precios_segmento) == tamaño_muestra and len(vol_segmento) == tamaño_muestra:
                print(f"Verificando bandera en precios: {precios_segmento}, volúmenes: {vol_segmento}")
                if np.all(closing_prices[i] > precios_segmento) and \
                   np.all(vol_segmento < volumes[i]):
                    return "Alcista"
                elif np.all(closing_prices[i] < precios_segmento) and \
                     np.all(vol_segmento < volumes[i]):
                    return "Bajista"
    return None

def detectar_doble_piso(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) < tamaño_muestra * 2:
        return False

    indices = np.arange(tamaño_muestra, len(closing_prices) - tamaño_muestra)
    patron_detectado = False  # Variable para evitar impresión repetida
    for i in indices:
        piso_actual = closing_prices[i]
        piso_anterior = closing_prices[i - tamaño_muestra:i]
        piso_posterior = closing_prices[i + 1:i + tamaño_muestra]
        vol_segmento = volumes[i - tamaño_muestra:i]
        print(f"Verificando doble piso en precios: {piso_anterior}, {piso_actual}, {piso_posterior} y volúmenes: {vol_segmento}")
        if piso_actual < np.min(piso_anterior) and piso_actual < np.min(piso_posterior):
            if volumes[i] > np.max(vol_segmento) * 0.8:
                patron_detectado = True
                break  # Salir del bucle una vez que se detecta el patrón

    if patron_detectado:
        return True
    else:
        return False

def detectar_doble_techo(closing_prices, volumes, intervalo_tiempo, tamaño_muestra):
    if len(closing_prices) < tamaño_muestra * 2:
        return False

    indices = np.arange(tamaño_muestra, len(closing_prices) - tamaño_muestra)
    for i in indices:
        techo_actual = closing_prices[i]
        techo_anterior = closing_prices[i - tamaño_muestra:i]
        techo_posterior = closing_prices[i + 1:i + tamaño_muestra]
        vol_segmento = volumes[i - tamaño_muestra:i]
        print(f"Verificando doble techo en precios: {techo_anterior}, {techo_actual}, {techo_posterior} y volúmenes: {vol_segmento}")
        if techo_actual > np.max(techo_anterior) and techo_actual > np.max(techo_posterior):
            if volumes[i] > np.max(vol_segmento) * 0.8:
                return True

    return False

def calcular_probabilidad_elliott(wave_patterns):
    try:
        impulsiva_count = sum(1 for patron in wave_patterns if patron['tipo'] == 'impulsiva')
        correctiva_count = sum(1 for patron in wave_patterns if patron['tipo'] == 'correctiva')

        total_patterns = len(wave_patterns)

        if total_patterns == 0:
            return 0

        # Calcular la probabilidad como la diferencia entre las ondas impulsivas y correctivas,
        # normalizada por el número total de patrones
        probabilidad_elliott = (impulsiva_count - correctiva_count) / total_patterns

        # Asegurarse de que la probabilidad esté dentro del rango [-1, 1]
        probabilidad_elliott = max(min(probabilidad_elliott, 1), -1)

        return probabilidad_elliott

    except Exception as e:
        print("Error al calcular la probabilidad de la Ley de Elliott:", e)
        return 0

def determinar_etapa_mercado(wave_patterns):
    try:
        if not wave_patterns:
            return "No hay señal clara en este momento"

        # Contar el número de ondas impulsivas y correctivas
        impulsiva_count = sum(1 for patron in wave_patterns if patron['tipo'] == 'impulsiva')
        correctiva_count = sum(1 for patron in wave_patterns if patron['tipo'] == 'correctiva')

        # Verificar si hay al menos una onda correctiva para determinar la tendencia
        if correctiva_count > 0:
            tendencia = "bajista"
        else:
            tendencia = "alcista"

        # Calcular la fuerza de la tendencia (puedes adaptar esto según tus criterios)
        if tendencia == "alcista":
            fuerza = "fuerte" if wave_patterns[-1]['longitud'] > wave_patterns[0]['longitud'] else "débil"
        elif tendencia == "bajista":
            fuerza = "fuerte" if wave_patterns[0]['longitud'] > wave_patterns[-1]['longitud'] else "débil"
        else:
            fuerza = "indeterminada"

        return f"La tendencia es {tendencia} y la fuerza es {fuerza}"

    except Exception as e:
        print("Error al determinar la etapa del mercado:", e)
        return "No hay señal clara en este momento"

def detectar_ley_elliott_avanzado(data_source):
    try:
        # Obtener los datos en tiempo real
        closing_prices_df = data_source.obtener_datos_en_tiempo_real()

        # Verificar si el DataFrame está vacío
        if closing_prices_df.empty:
            print("El DataFrame 'closing_prices_df' está vacío.")
            return "No hay señal clara en este momento", 0

        # Cálculo de la primera derivada de los precios de cierre
        price_diff = np.gradient(closing_prices_df['closing_prices'])

        # Identificación de picos y valles en la primera derivada
        peaks, _ = find_peaks(price_diff, prominence=0.1)
        valleys, _ = find_peaks(-price_diff, prominence=0.1)

        print("Picos detectados:", peaks)
        print("Valles detectados:", valleys)

        # Verificar si las listas de picos y valles están vacías
        if len(peaks) == 0 or len(valleys) == 0:
            print("No se encontraron picos o valles en los datos.")
            return "No hay señal clara en este momento", 0

        # Definición de longitud mínima para considerar un patrón de onda
        min_wave_length = 3

        # Inicializar la lista de patrones de onda
        wave_patterns = []

        # Identificar patrones de ondas de impulso y corrección
        impulsive_count = 0
        corrective_count = 0
        for i in range(len(peaks) - 1):
            wave_length = peaks[i+1] - peaks[i]
            if wave_length >= min_wave_length:
                if impulsive_count < 5:  # Detectar las cinco ondas impulsivas
                    wave_patterns.append({
                        'tipo': 'impulsiva',
                        'inicio': peaks[i],
                        'fin': peaks[i+1],
                        'longitud': wave_length
                    })
                    impulsive_count += 1
                elif corrective_count < 3:  # Detectar la corrección ABC
                    wave_patterns.append({
                        'tipo': 'correctiva',
                        'inicio': peaks[i],
                        'fin': peaks[i+1],
                        'longitud': wave_length
                    })
                    corrective_count += 1

        print("Patrones de onda detectados:", wave_patterns)

        # Determinar la etapa del mercado
        etapa_mercado = determinar_etapa_mercado(wave_patterns)

        # Calcular la probabilidad de formación de onda de Elliott
        probabilidad_elliott = calcular_probabilidad_elliott(wave_patterns)

        resultado = f"El mercado está en la etapa {etapa_mercado}."
        print(resultado)
        return resultado, probabilidad_elliott

    except Exception as e:
        print("Error al detectar la Ley de Elliott:", e)
        return "Neutral", 0.5

def analisis_practico(closing_prices_df, volume_data, ema_50, rsi_data,
                      tolerancia=0.5, resultado_elliott=None,
                      resultado_dow=None, tipo_divergencia=None,
                      resultado_divergencias=False, resultado_patrones=None,
                      estado_mercado=None, probabilidad_elliott=None,
                      resultado_macd=None, niveles_soporte=None,
                      niveles_resistencia=None):
    try:
        # Verificar si los datos en tiempo real son válidos
        if closing_prices_df.empty or ema_50 is None:
            print("Al menos uno de los DataFrames está vacío o ema_50 es None.")
            return "No hay señal clara en este momento", ""

        # Realizar el análisis práctico con los datos proporcionados
        resultado_practico = ""

        # Concatenar los patrones detectados al resultado práctico
        if resultado_patrones:
            for patron, tipo in resultado_patrones.items():
                resultado_practico += f"Patrón detectado: {patron} ({tipo})\n"
        else:
            resultado_practico += "No se encontraron patrones.\n"

        # Agregar resultados adicionales
        if resultado_elliott:
            resultado_practico += f"Ley de Elliott: {resultado_elliott}"
            if probabilidad_elliott is not None:
                resultado_practico += f", Probabilidad de formación de onda de Elliott: {probabilidad_elliott}"
        if resultado_dow:
            resultado_practico += f", Ley de Dow: {resultado_dow}"
        if resultado_divergencias:
            resultado_practico += f", Divergencias RSI: Sí, {tipo_divergencia}"
        else:
            resultado_practico += f", Divergencias RSI: No"
        if rsi_data is not None and not rsi_data.empty:
            resultado_practico += f", RSI: {rsi_data.iloc[-1]}"
        if estado_mercado is not None:
            resultado_practico += f", Estado del mercado: {estado_mercado}"
        if resultado_macd:
            resultado_practico += f", Tendencia MACD: {resultado_macd}"

        # Llamar a la función enviar_correo con los resultados específicos de este análisis
        resultado_envio_correo = enviar_correo(resultado_practico)
        print(resultado_envio_correo)

        print("Resultado del análisis práctico:", resultado_practico)
        return resultado_practico

    except Exception as e:
        print("Error al realizar el análisis práctico:", e)
        return "No hay señal clara en este momento"

def obtener_datos_en_tiempo_real():
    """
    Simula la obtención de datos en tiempo real generando precios de cierre y datos de volumen aleatorios.
    """
    # Simulamos la obtención de precios de cierre y datos de volumen aleatorios
    closing_prices = np.random.randint(100, 500, size=10)  # Genera 10 precios de cierre aleatorios
    volume_data = np.random.randint(1000, 5000, size=10)   # Genera 10 datos de volumen aleatorios
    return closing_prices, volume_data

def analisis_fundamental_en_tiempo_real():
    """
    Realiza un análisis fundamental en tiempo real de los datos financieros simulados.
    """
    try:
        while True:
            # Obtener los nuevos datos en tiempo real
            closing_prices, volume_data = obtener_datos_en_tiempo_real()

            # Realizar análisis fundamental con los nuevos datos
            resultados_fundamentales = analisis_fundamental(closing_prices, volume_data)

            # Interpretar los resultados del análisis fundamental
            señal = interpretar_analisis_fundamental(resultados_fundamentales)
            print(señal)

            # Esperar un tiempo antes de obtener nuevos datos (simula el tiempo en tiempo real)
            time.sleep(5)  # Espera 5 segundos antes de obtener nuevos datos

    except KeyboardInterrupt:
        print("Proceso interrumpido.")

def analisis_fundamental(closing_prices, volume_data):
    """
    Realiza un análisis fundamental de los datos financieros.

    Args:
    - closing_prices (numpy.ndarray): Array numpy de precios de cierre.
    - volume_data (numpy.ndarray): Array numpy de datos de volumen.

    Returns:
    - dict: Un diccionario que contiene los resultados del análisis fundamental.
    """
    try:
        if closing_prices is not None and volume_data is not None:
            # Calculamos el promedio de los precios de cierre para evaluar la tendencia general
            average_price = np.mean(closing_prices)

            # Calculamos la volatilidad de los precios como medida del riesgo
            price_volatility = np.std(closing_prices)

            # Calculamos la tendencia a largo plazo utilizando una media móvil de 200 días
            long_term_trend = np.mean(closing_prices[-200:]) if len(closing_prices) >= 200 else average_price

            # Calculamos la liquidez del activo basándonos en el volumen promedio de operaciones
            average_volume = np.mean(volume_data)

            # Retornamos los resultados del análisis fundamental en un diccionario
            return {
                "average_price": average_price,
                "price_volatility": price_volatility,
                "long_term_trend": long_term_trend,
                "average_volume": average_volume,
                # Puedes agregar más métricas fundamentales aquí
            }
        else:
            # Aquí decides qué hacer cuando closing_prices o volume_data es None
            default_value = 0
            print("Los datos de precios de cierre o volumen están ausentes.")
            return {
                "average_price": default_value,
                "price_volatility": default_value,
                "long_term_trend": default_value,
                "average_volume": default_value,
                # Puedes agregar más métricas fundamentales aquí
            }

    except Exception as e:
        print("Error al realizar el análisis fundamental:", e)
        return "No hay señal clara en este momento"

def interpretar_analisis_fundamental(resultados_fundamentales):
    """
    Interpreta los resultados del análisis fundamental y genera una señal de compra, venta o mantenerse en espera.

    Args:
    - resultados_fundamentales (dict): Un diccionario que contiene los resultados del análisis fundamental.

    Returns:
    - str: Una cadena que representa la interpretación del análisis fundamental.
    """
    if resultados_fundamentales:
        average_price = resultados_fundamentales.get("average_price")
        long_term_trend = resultados_fundamentales.get("long_term_trend")
        average_volume = resultados_fundamentales.get("average_volume")
        price_volatility = resultados_fundamentales.get("price_volatility")

        if average_price is not None and long_term_trend is not None and average_volume is not None and price_volatility is not None:
            if average_price > long_term_trend and average_volume > 1000000:
                return "Señal: Comprar"
            elif price_volatility > 0.5:
                return "Señal: Vender"
            else:
                return "Señal: Mantenerse en espera"
        else:
            return "Los datos fundamentales son incompletos."
    else:
        return "No se pudo realizar el análisis fundamental."

def enviar_correo(resultado_practico):
    try:
        # Configurar los parámetros del servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("sirem66@gmail.com", 'kdxf kcbt guaj itgc')  # Correo y contraseña válidos para enviar el correo

        # Crear el mensaje de correo electrónico
        msg = MIMEMultipart()
        msg['From'] = "sirem66@gmail.com"
        msg['To'] = "sirem66@gmail.com"  # Destinatario del correo
        msg['Subject'] = "Análisis de criptomonedas BTC"

        # Cuerpo del mensaje de correo
        body = f"""\
            Resultado práctico: {resultado_practico}
        """

        msg.attach(MIMEText(body, 'plain'))

        # Enviar el correo electrónico
        server.sendmail("sirem66@gmail.com", "sirem66@gmail.com", msg.as_string())

        # Cerrar la conexión con el servidor SMTP
        server.quit()

        return "Correo enviado exitosamente."

    except Exception as e:
        print("Error al enviar el correo electrónico:", e)
        return "Error al enviar el correo electrónico: " + str(e)

def planificar_tareas(resultado_practico):
    try:
        # Implementa la lógica de planificación de tareas aquí
        print("Planificación de tareas con los resultados de los análisis y la recomendación obtenida.")
        # Simplemente imprimir los resultados por ahora

        print("Resultado práctico:", resultado_practico)


        # Llamar a la función enviar_correo con los resultados
        resultado_envio_correo = enviar_correo(resultado_practico)

        print(resultado_envio_correo)

    except Exception as e:
        print("Error al planificar las tareas:", e)

class DataSource:
    def __init__(self, client, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = client
        self.buffer_size = 20

    def obtener_datos_en_tiempo_real(self):
        try:
            print("Recopilando datos en tiempo real con intervalo de 15 minutos...")
            klines = self.client.get_klines(symbol='ETHUSDT', interval='15m', limit=self.buffer_size)

            price_buffer = []
            volume_buffer = []
            for kline in klines:
                price = float(kline[4])  # Close price of the 15 minute candle
                volume = float(kline[5])  # Volume of the 15 minute candle
                price_buffer.append(price)
                volume_buffer.append(volume)

            df = pd.DataFrame({'closing_prices': price_buffer, 'volume_data': volume_buffer})
            df.index = pd.date_range(start=pd.Timestamp.now().floor('1D'), periods=len(df), freq='15min')
            print("Datos recopilados en intervalos de 15 minutos:")
            print(df)
            print("Recopilación de datos en tiempo real completa.")
            return df

        except Exception as e:
            print("Error al obtener datos en tiempo real de la API de Binance:", e)
            return pd.DataFrame()

def obtener_precio_real_time_futuros(symbol):
        global last_real_time_price

        try:
            def on_message(ws, message):
                global last_real_time_price
                data = json.loads(message)

                if 'p' in data and 's' in data:
                    symbol = data['s']
                    if symbol == 'ETHUSDT':
                        last_real_time_price = float(data['p'])
                        print(f"Precio en tiempo real de futuros de ETH: {last_real_time_price}")

            def on_error(ws, error):
                print("Error en la transmisión WebSocket:", error)

            def on_close(ws):
                print("Conexión WebSocket cerrada")

            def on_open(ws):
                print("Conexión WebSocket abierta")

            websocket.enableTrace(True)

            socket_ws = "wss://fstream.binance.com/ws/ETHusdt@trade"
            ws = websocket.WebSocketApp(socket_ws, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()

        except Exception as e:
            print("Error al obtener el precio en tiempo real de futuros:", e)

def ejecutar_analisis_continuo():
    global resultado_practico, resultado_patrones
    divergencias_detectadas = False  # Variable para indicar si se han detectado divergencias
    resultado_patrones = {}  # Inicializar resultado_patrones

    while True:
        try:
            # Definir umbral_teórico
            umbral_teórico = 0.5

            data_source = DataSource(client)
            df_exchange = data_source.obtener_datos_en_tiempo_real()

            if df_exchange is not None and not df_exchange.empty:
                print("Datos en tiempo real de intercambios:")
                print(df_exchange.head())
            else:
                print("No se pudieron obtener datos en tiempo real de intercambios.")
                time.sleep(900)  # Esperar 15 minutos antes de reintentar
                continue

            if hasattr(data_source, 'obtener_datos_en_tiempo_real'):
                df = data_source.obtener_datos_en_tiempo_real()

                if isinstance(df, pd.DataFrame) and not df.empty:
                    print("¡'precios' es un DataFrame de Pandas!")
                    print("Primeros registros de 'precios':")
                    print(df.head())

                    precios_serie = df['closing_prices']
                    volumenes = df['volume_data'].tolist()

                    # Calcular el RSI
                    rsi_data = calcular_rsi(precios_serie)

                    # Obtener divergencias y estado del mercado en tiempo real
                    divergencias, tipo_divergencia, _, estado_mercado = detectar_divergencias_y_estado_en_tiempo_real()

                    # Verificar si se han detectado divergencias
                    if divergencias:
                        print("Se han detectado divergencias en tiempo real:")
                        print(f"Divergencia {tipo_divergencia}")
                        divergencias_detectadas = True
                    else:
                        print("No se han detectado divergencias en tiempo real.")
                        divergencias_detectadas = False

                    print(f"RSI en tiempo real: {rsi_data.iloc[-1]}")
                    print(f"Estado del mercado en tiempo real: {estado_mercado}")

                    resultado_dow = detectar_ley_dow_avanzado(df)
                    print(resultado_dow)

                    resultado_elliott, probabilidad_elliott = detectar_ley_elliott_avanzado(data_source)

                    resultado_macd = detectar_tendencia_macd_con_cambio_porcentual(df)
                    print(resultado_macd)

                    ema_50 = precios_serie.ewm(span=50, adjust=False).mean()

                    # Detectar patrones gráficos
                    resultado_patrones = detectar_patrones_graficos(data_source)

                    resultado_practico = analisis_practico(df, volumenes, ema_50, rsi_data,
                                                           resultado_patrones=resultado_patrones,
                                                           resultado_elliott=resultado_elliott,
                                                           resultado_dow=resultado_dow,
                                                           resultado_divergencias=divergencias_detectadas,
                                                           tipo_divergencia=tipo_divergencia,
                                                           estado_mercado=estado_mercado,
                                                           resultado_macd=resultado_macd,
                                                           probabilidad_elliott=probabilidad_elliott)

                    # Ejecutar el análisis fundamental en tiempo real
                    analisis_fundamental_en_tiempo_real()

                    # Enviar correo con los resultados prácticos
                    resultado_envio_correo = enviar_correo(resultado_practico)
                    print(resultado_envio_correo)

                else:
                    print("El objeto data_source NO tiene el método obtener_datos_en_tiempo_real.")

            # Esperar 15 minutos antes de realizar el siguiente análisis
            time.sleep(900)  # 15 minutos = 900 segundos

        except Exception as e:
            print("Error:", e)
            time.sleep(900)  # Esperar 15 minutos en caso de error para evitar una sobrecarga de errores


if __name__ == '__main__':
    client = Client(API_KEY, API_SECRET)
    ejecutar_analisis_continuo()
