import praw
import pandas as pd
import smtplib
import json
import websocket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from textblob import TextBlob
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from binance.client import Client
import spacy
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np
from sklearn.model_selection import train_test_split
from scipy.signal import find_peaks
import pandas_ta as ta
import time
import datetime
import pandas_ta
import random
from DATOS import symbol

# Definir las variables globales necesarias
closing_prices = None
volume_data = None
last_real_time_price = None
# Definir la variable comentarios
comentarios = []

# Convertir el array numpy en DataFrame de Pandas
closing_prices_df = pd.DataFrame(closing_prices)

# Cargar el modelo pre-entrenado en inglés
nlp = spacy.load('en_core_web_sm')

# Configuración de la API de Reddit
REDDIT_CLIENT_ID = 'syTgPQWR92sh3umGqTVpOg'
REDDIT_CLIENT_SECRET = 'oflk5tr4jOJmS1rXv65A5VdpqWkq2g'
REDDIT_USER_AGENT = 'script by /u/username'  # Puedes cambiar 'username' por tu nombre de usuario de Reddit

# Configuración de la API de Binance
API_KEY = '5vWrP5bgXUpFa89KQBrJoTfAUUH8eZwccU7Q6CZcD4hrU7Rs9aqKf46bqBJTMRwU'
API_SECRET = 'ica2XnjMGd5HOgwWH4spFiSXZvn8ogukQHWbGUTpvt4I9z6wpQbtnM4YZISqhMNU'
client = Client(API_KEY, API_SECRET)

# Variable para almacenar el último precio real en tiempo real
last_real_time_price = None

# Lista para almacenar los resultados históricos de las recomendaciones
historical_recommendations = []


def obtener_datos_cripto():
    # Incluir el código que obtiene datos de criptomonedas desde CoinGecko
    pass


def obtener_reddit_comments():
    try:
        reddit = praw.Reddit(client_id='syTgPQWR92sh3umGqTVpOg',
                             client_secret='oflk5tr4jOJmS1rXv65A5VdpqWkq2g',
                             user_agent='script by /u/username')

        subreddit_name = 'Bitcoin'  # Cambia esto al nombre del subreddit que desees
        subreddit = reddit.subreddit(subreddit_name)

        comments = []
        for submission in subreddit.new(limit=10):
            if isinstance(submission.title, str):
                comments.append(submission.title)
            if isinstance(submission.selftext, str):
                comments.append(submission.selftext)

        print("Comentarios obtenidos:", comments)

        if comments:
            sentiment_scores = []
            for comment in comments:
                analysis = TextBlob(comment)
                sentiment_scores.append(analysis.sentiment.polarity)

            average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            print("Puntajes de sentimiento:", sentiment_scores)
            print("Promedio de puntajes de sentimiento:", average_sentiment)

            if average_sentiment > 0:
                return "Recomendación: Comprar"
            elif average_sentiment < 0:
                return "Recomendación: Vender"
            else:
                return "Recomendación: Mantenerse en espera"
        else:
            return "No hay suficientes comentarios para analizar"

    except Exception as e:
        print("Error al obtener comentarios de Reddit:", e)
        return "No hay señal clara en este momento"


def build_model(seq_length):
    model = Sequential()
    model.add(LSTM(100, return_sequences=True, input_shape=(seq_length, 1)))
    model.add(Dropout(0.4))
    model.add(LSTM(80, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(1))

    optimizer = Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='mean_squared_error')

    return model


def train_model(model, X_train, y_train, X_val, y_val, epochs, batch_size):
    # Usar EarlyStopping de Keras
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, verbose=1, restore_best_weights=True)

    # Entrenar el modelo
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val),
                        callbacks=[early_stopping], verbose=1)

    return model, history


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print("Error Cuadrático Medio (MSE):", mse)


def load_data(historical_data, seq_length):
    data = []

    for i in range(len(historical_data) - seq_length + 1):
        seq = historical_data[i:i + seq_length]
        data.append(seq)

    data = np.array(data)
    X = datos.drop('variable_objetivo', axis=1)
    y = datos['variable_objetivo']

    # Dividir los datos en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, X_test, y_train, y_test


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print("Error Cuadrático Medio (MSE):", mse)

    for real, pred in zip(y_test, y_pred):
        print(f"Real: {real}, Predicción: {pred[0]}")


def create_dataset(data, time_step):
    X, y = [], []
    for i in range(len(data) - time_step - 1):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)


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


def calcular_niveles_soporte(closing_prices_df, encontrar_minimos_locales):
    try:
        # Convertir closing_prices_df a DataFrame si es una lista
        if isinstance(closing_prices_df, list):
            closing_prices_df = pd.DataFrame(closing_prices_df)

        # Calcular mínimos locales llamando a la función encontrar_minimos_locales
        indices_minimos_locales = encontrar_minimos_locales(closing_prices_df)

        # Verificar si se encontraron mínimos locales
        if not indices_minimos_locales:
            print("No se encontraron mínimos locales en el DataFrame.")
            return None

        # Obtener el índice del último mínimo local
        ultimo_indice_minimo_local = indices_minimos_locales[-1]

        # Obtener el precio del último mínimo local
        minimo_local = closing_prices_df.iloc[ultimo_indice_minimo_local][0]  # Acceso genérico al primer valor del DataFrame

        return minimo_local

    except Exception as e:
        print("Error al calcular niveles de soporte:", e)
        return None

def encontrar_minimos_locales(closing_prices_df):
    indices_minimos_locales = []

    # Convertir closing_prices_df a DataFrame si es una lista
    if isinstance(closing_prices_df, list):
        closing_prices_df = pd.DataFrame(closing_prices_df)

    for index, row in closing_prices_df.iterrows():
        i = index
        if i > 0 and i < len(closing_prices_df) - 1:
            if row[0] < closing_prices_df.iloc[i - 1, 0] and row[0] < closing_prices_df.iloc[i + 1, 0]:
                indices_minimos_locales.append(i)

    return indices_minimos_locales



def calcular_niveles_resistencia(closing_prices_df):
    # Si closing_prices_df es una lista
    if isinstance(closing_prices_df, list):
        closing_prices_df = pd.DataFrame(closing_prices_df)

    niveles_resistencia = []

    # Ahora puedes usar closing_prices_df como un DataFrame de pandas
    for index, row in closing_prices_df.iterrows():
        i = index
        maximo_local = row[0]
        if i > 0 and i < len(closing_prices_df) - 1:
            if maximo_local == closing_prices_df.iloc[i - 1, 0]:
                if maximo_local > closing_prices_df.iloc[i + 1, 0]:
                    niveles_resistencia.append(maximo_local)

    return niveles_resistencia


def identificar_etapa_onda(onda_actual):
    if onda_actual in ['1', '3', '5', 'a', 'c']:
        return 'Impulsiva'
    elif onda_actual in ['2', '4', 'b']:
        return 'Correctiva'
    else:
        return 'No se pudo identificar'


def determinar_etapa_mercado(tipo_onda, onda_especifica):
    if tipo_onda == 'Impulsiva':
        if onda_especifica == 'Onda 1':
            return 'Inicio de una tendencia alcista'
        elif onda_especifica == 'Onda 3':
            return 'Tendencia alcista fuerte'
        elif onda_especifica == 'Onda 5':
            return 'Finalización de una tendencia alcista'
    elif tipo_onda == 'Correctiva':
        if onda_especifica == 'Onda A':
            return 'Corrección en una tendencia alcista'
        elif onda_especifica == 'Onda B':
            return 'Retroceso temporal en una tendencia alcista'
        elif onda_especifica == 'Onda C':
            return 'Desarrollo de una tendencia bajista'
    return 'No se pudo determinar'
def detectar_ley_elliott_avanzado(closing_prices_df):
    try:
        if closing_prices_df.empty:
            print("El DataFrame 'closing_prices_df' está vacío.")
            return "No hay señal clara en este momento"

        # Cálculo de la primera derivada de los precios de cierre
        price_diff = np.gradient(closing_prices_df['closing_prices'])

        # Identificación de picos y valles en la primera derivada
        peaks, _ = find_peaks(price_diff, prominence=0.1)
        valleys, _ = find_peaks(-price_diff, prominence=0.1)

        # Definición de longitud mínima para considerar un patrón de onda
        min_wave_length = 3

        # Inicializar la lista de patrones de onda
        wave_patterns = []

        # Identificar patrones de ondas de impulso
        for peak in peaks:
            next_valley_idx = np.argmax(valleys > peak)
            if next_valley_idx < len(valleys) and valleys[next_valley_idx] > peak:
                valley = valleys[next_valley_idx]
                wave_length = valley - peak
                if wave_length >= min_wave_length:
                    wave_patterns.append({
                        'tipo': 'impulsiva',
                        'inicio': peak,
                        'fin': valley,
                        'longitud': wave_length
                    })

        # Identificar patrones de ondas correctivas
        for valley in valleys:
            next_peak_idx = np.argmax(peaks > valley)
            if next_peak_idx < len(peaks) and peaks[next_peak_idx] > valley:
                peak = peaks[next_peak_idx]
                wave_length = peak - valley
                if wave_length >= min_wave_length:
                    wave_patterns.append({
                        'tipo': 'correctiva',
                        'inicio': valley,
                        'fin': peak,
                        'longitud': wave_length
                    })

        # Detectar la onda dominante y determinar la etapa y descripción del mercado
        onda_dominante = None
        onda_especifica = None
        for patron in wave_patterns:
            if patron['tipo'] == 'impulsiva':
                onda_dominante = 'Impulsiva'
                break
            elif patron['tipo'] == 'correctiva':
                onda_dominante = 'Correctiva'
                break

        # Determinar la onda específica
        onda_especifica = None
        if onda_dominante == 'Impulsiva':
            if len(peaks) > 0:
                onda_especifica = 'Onda 3'  # Si es una onda impulsiva y hay picos detectados, probablemente sea la Onda 3
            else:
                onda_especifica = 'Onda 1'  # Si no hay picos detectados, probablemente sea la Onda 1
        elif onda_dominante == 'Correctiva':
            onda_especifica = 'Onda C'  # Si es una onda correctiva, probablemente sea la Onda C

        # Determinar la etapa del mercado
        etapa_mercado = determinar_etapa_mercado(onda_dominante, onda_especifica)

        # Realizar el análisis de los patrones de ondas detectados fuera del bucle
        probabilidad_elliott = calcular_probabilidad_elliott(wave_patterns)
        print(f"Probabilidad de formación de onda de Elliott: {probabilidad_elliott}")

        resultado = f"El mercado está en la {onda_especifica}. {etapa_mercado}."
        print(resultado)
        return resultado

    except Exception as e:
        print("Error al detectar la Ley de Elliott:", e)
        return "No hay señal clara en este momento"


# La función calcular_probabilidad_elliott debe estar definida fuera de la función detectar_ley_elliott_avanzado
def calcular_probabilidad_elliott(wave_patterns):
    try:
        # Inicializar la probabilidad
        probabilidad_elliott = 0

        # Calcular la probabilidad basada en el tipo y longitud de las ondas
        for patron in wave_patterns:
            if patron['tipo'] == 'impulsiva':
                probabilidad_elliott += 0.2
            elif patron['tipo'] == 'correctiva':
                probabilidad_elliott += 0.1

        return probabilidad_elliott

    except Exception as e:
        print("Error al calcular la probabilidad de la Ley de Elliott:", e)
        return 0.0

def detectar_ley_dow_avanzado(closing_prices_df):
    try:
        # Calcular el cambio porcentual entre el precio de cierre actual y el precio de cierre anterior
        cambio_porcentual = (closing_prices_df['closing_prices'].iloc[-1] - closing_prices_df['closing_prices'].iloc[-2]) / closing_prices_df['closing_prices'].iloc[-2] * 100

        # Calcular la media móvil simple de 50 días y 200 días
        sma_50 = closing_prices_df['closing_prices'].rolling(window=50).mean()
        sma_200 = closing_prices_df['closing_prices'].rolling(window=200).mean()

        # Calcular la media móvil exponencial de 50 días y 200 días
        ema_50 = closing_prices_df['closing_prices'].ewm(span=50, adjust=False).mean()
        ema_200 = closing_prices_df['closing_prices'].ewm(span=200, adjust=False).mean()

        # Verificar si el precio está por encima o por debajo de las medias móviles
        if cambio_porcentual > 0 and sma_50.iloc[-1] > sma_200.iloc[-1] and ema_50.iloc[-1] > ema_200.iloc[-1]:
            return "Tendencia alcista según la Ley de Dow"
        elif cambio_porcentual < 0 and sma_50.iloc[-1] < sma_200.iloc[-1] and ema_50.iloc[-1] < ema_200.iloc[-1]:
            return "Tendencia bajista según la Ley de Dow"
        else:
            return "Tendencia lateral según la Ley de Dow"

    except Exception as e:
        print("Error al detectar la Ley de Dow:", e)
        return "No se pudo determinar la tendencia según la Ley de Dow"


def detectar_patrones_graficos(closing_prices, volume_data):
    patrones_detectados = {}

    def detectar_triangulo_ascendente(closing_prices, volumes):
        # Detectar Triángulo Ascendente
        if volumes is not None and len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                # Identificar patrón: precios formando mínimos significativamente crecientes y volúmenes decrecientes pronunciados
                if closing_prices[i] > closing_prices[i - 1] * 1.02 > closing_prices[i - 2] * 1.04 and volumes[i] < volumes[i - 1] * 0.95 < volumes[i - 2] * 0.9:
                    return True
        return False

    def detectar_triangulo_descendente(closing_prices, volumes):
        # Detectar Triángulo Descendente
        if volumes is not None and len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                # Identificar patrón: precios formando máximos significativamente decrecientes y volúmenes decrecientes pronunciados
                if closing_prices[i] < closing_prices[i - 1] * 0.98 < closing_prices[i - 2] * 0.96 and volumes[i] < volumes[i - 1] * 0.95 < volumes[i - 2] * 0.9:
                    return True
        return False

    def detectar_cabeza_hombros(closing_prices, volumes):
        if volumes is not None and len(closing_prices) >= 5:
            for i in range(2, len(closing_prices) - 2):
                # Identificar patrón: pico central más alto que los dos picos a su lado y volúmenes decrecientes
                if closing_prices[i - 2] < closing_prices[i - 1] * 1.02 > closing_prices[i] < closing_prices[i + 1] and \
                        volumes[i] < volumes[i - 1] < volumes[i - 2] * 0.9:
                    return True
        return False

    def detectar_cuña_descendente(closing_prices, volumes):
        if volumes is not None and len(closing_prices) >= 5:
            for i in range(4, len(closing_prices)):
                if all(volumes[j] is not None for j in range(i - 4, i + 1)):
                    if all(closing_prices[j] > closing_prices[j + 1] for j in range(i - 4, i)) and all(
                            volumes[j] > volumes[j + 1] for j in range(i - 4, i)):
                        if i - 4 >= 0 and (i + 1) < len(closing_prices):
                            duration = i + 1 - (i - 4)
                            if duration >= 7:
                                return True
        return False

        # Función para detectar el patrón de cuña ascendente

    def detectar_cuña_ascendente(closing_prices, volumes):
        if len(closing_prices) >= 5:
            for i in range(2, len(closing_prices) - 2):
                # Identificar patrón: formación de mínimos más altos y volúmenes decrecientes
                if closing_prices[i] > closing_prices[i - 1] > closing_prices[i - 2] and volumes[i] < volumes[i - 1] < \
                        volumes[i - 2]:
                    return True
        return False

    def detectar_bandera(closing_prices, volumes):
        if volumes is not None and len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                if volumes[i - 1] is not None and volumes[i - 2] is not None and volumes[i] is not None:
                    if closing_prices[i - 2] < closing_prices[i - 1] * 1.02 < closing_prices[i] and volumes[i] < \
                            volumes[i - 1] * 0.95 < volumes[i - 2] * 0.9:
                        if i - 2 >= 0 and (i + 1) < len(closing_prices):
                            duration = i + 1 - (i - 2)
                            if duration >= 3:
                                return True
        return False

    def detectar_doble_piso(closing_prices, volumes):
        if volumes is not None and len(volumes) >= len(closing_prices) >= 4:
            for i in range(3, len(closing_prices)):
                if closing_prices[i] < closing_prices[i - 1] and closing_prices[i - 2] > closing_prices[i - 1] > \
                        closing_prices[i]:
                    if volumes[i] > volumes[i - 1] and volumes[i - 2] < volumes[i - 1] < volumes[i]:
                        if i - 2 >= 0 and (i + 1) < len(closing_prices):
                            duration = i + 1 - (i - 2)
                            if duration >= 6:
                                return True
        return False

    def detectar_doble_techo(closing_prices, volumes):
        if volumes is not None and len(volumes) >= len(closing_prices) >= 4:
            for i in range(3, len(closing_prices)):
                if closing_prices[i] > closing_prices[i - 1] and closing_prices[i - 2] < closing_prices[i - 1] < \
                        closing_prices[i]:
                    if volumes[i] > volumes[i - 1] and volumes[i - 2] < volumes[i - 1] < volumes[i]:
                        if i - 2 >= 0 and (i + 1) < len(closing_prices):
                            duration = i + 1 - (i - 2)
                            if duration >= 6:
                                return True
        return False

    patrones_detectados["Triángulo Ascendente"] = detectar_triangulo_ascendente(closing_prices, volume_data)
    patrones_detectados["Triángulo Descendente"] = detectar_triangulo_descendente(closing_prices, volume_data)
    patrones_detectados["Cabeza y Hombros"] = detectar_cabeza_hombros(closing_prices, volume_data)
    patrones_detectados["Cuña Descendente"] = detectar_cuña_descendente(closing_prices, volume_data)
    patrones_detectados["Cuña Ascendente"] = detectar_cuña_ascendente(closing_prices, volume_data)
    patrones_detectados["Bandera"] = detectar_bandera(closing_prices, volume_data)
    patrones_detectados["Doble Piso"] = detectar_doble_piso(closing_prices, volume_data)
    patrones_detectados["Doble Techo"] = detectar_doble_techo(closing_prices, volume_data)

    patrones_detectados = {patron: detectado for patron, detectado in patrones_detectados.items() if detectado}
    return patrones_detectados.keys() if patrones_detectados else None


# Función para calcular el MACD
def calcular_macd(closing_prices, fast_period=12, slow_period=26, signal_period=9):
    # Calcular el MACD utilizando pandas_ta
    macd_data = ta.macd(closing_prices, fast=fast_period, slow=slow_period, signal=signal_period)
    return macd_data

# Función para detectar divergencias y convergencias en el MACD
def detectar_divergencias(macd_data, umbral=0.0):
    try:
        divergencia_detectada = False
        tipo_divergencia = None
        fila_divergencia = None

        for i, row in macd_data.iterrows():
            macdh = row['MACDh_12_26_9']
            macds = row['MACDs_12_26_9']

            # Detección de divergencia alcista
            if macdh > umbral and macdh > macds:
                divergencia_detectada = True
                tipo_divergencia = 'Alcista'
                fila_divergencia = i
                break

            # Detección de divergencia bajista
            if macdh < -umbral and macdh < macds:
                divergencia_detectada = True
                tipo_divergencia = 'Bajista'
                fila_divergencia = i
                break

        if divergencia_detectada:
            resultado = f"Divergencia {tipo_divergencia} detectada en la fila {fila_divergencia}"
        else:
            resultado = "No se detectaron divergencias en el MACD."

        return resultado

    except Exception as e:
        resultado = "Error al detectar divergencias en el MACD: " + str(e)
        return resultado


# Ruta al archivo CSV
file_path = "datos_financieros.csv"

# Cargar los datos en un DataFrame de pandas
df = pd.read_csv(file_path)

# Calcular el MACD
closing_prices = df['Close']
macd_data = calcular_macd(closing_prices)

# Imprimir el DataFrame macd_data para verificar el contenido
print("DataFrame macd_data:")
print(macd_data)

# Llamar a la función detectar_divergencias con los datos del MACD
divergencia_detectada = detectar_divergencias(macd_data, umbral=0.5)
print(divergencia_detectada)


# Definir la función de análisis técnico
def analisis_tecnico(closing_prices_df, volume_data, macd_data):
    try:
        # Paso 1: Calcular Soportes y Resistencias
        niveles_soporte = calcular_niveles_soporte(closing_prices_df, encontrar_minimos_locales)
        niveles_resistencia = calcular_niveles_resistencia(closing_prices_df)

        # Paso 2: Detectar Patrones Gráficos
        patrones_graficos = detectar_patrones_graficos(closing_prices_df['closing_prices'], volume_data)

        # Paso 3: Analizar Ley de Elliott y Ley de Dow
        resultado_elliott = detectar_ley_elliott_avanzado(closing_prices_df)
        resultado_dow = detectar_ley_dow_avanzado(closing_prices_df)

        # Paso 4: Detectar divergencias en el MACD
        divergencia_macd = detectar_divergencias(macd_data, umbral=0.5)

        # Paso 5: Integrar los Resultados
        resultados = {
            'Soportes': niveles_soporte,
            'Resistencias': niveles_resistencia,
            'Patrones Gráficos': patrones_graficos,
            'Ley de Elliott': resultado_elliott,
            'Ley de Dow': resultado_dow,
            'Divergencia MACD': divergencia_macd  # Agregar el resultado de la divergencia MACD
        }

        # Paso 6: Generar la Señal de Compra, Venta o No Hacer Nada
        senal = generar_senal(patrones_graficos, resultado_elliott, resultado_dow, divergencia_macd)

        # Paso 7: Imprimir los Resultados
        imprimir_resultados(resultados, senal)

        # Retornar la señal generada
        return senal

    except Exception as e:
        print("Error en el análisis técnico:", e)
        return 'Error'


# Definir la función para generar señales
def generar_senal(patrones_graficos, resultado_elliott, resultado_dow, divergencia_macd):
    if patrones_graficos:
        if 'Tendencia alcista fuerte' in resultado_elliott and 'Tendencia alcista según la Ley de Dow' in resultado_dow:
            if divergencia_macd:
                return 'Comprar con divergencia alcista MACD'
            else:
                return 'Comprar sin divergencia alcista MACD'
        elif 'Tendencia bajista según la Ley de Dow' in resultado_dow:
            return 'Vender'
        else:
            return 'No hacer nada'
    else:
        return 'No hacer nada'

def imprimir_resultados(resultados, senal):
    print("Resultados del Análisis Técnico:")
    for aspecto, resultado in resultados.items():
        print(f"{aspecto}: {resultado}")
    print("Señal: ", senal)


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
            long_term_trend = np.mean(closing_prices[-200:])

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
            # Por ejemplo, puedes establecer un valor predeterminado para cada métrica
            default_value = 0
            print("Los datos de precios de cierre o volumen están ausentes.")
            return {
                "average_price": default_value,
                "price_volatility": default_value,
                "long_term_trend": default_value,
                "average_volume": default_value,
                # Puedes agregar más métricas fundamentales aquí
            }

            # O simplemente omitir silenciosamente
            # pass

    except Exception as e:
        # Manejar cualquier excepción que ocurra durante el análisis
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
    if resultados_fundamentales is not None:
        average_price = resultados_fundamentales.get("average_price")
        long_term_trend = resultados_fundamentales.get("long_term_trend")
        average_volume = resultados_fundamentales.get("average_volume")
        price_volatility = resultados_fundamentales.get("price_volatility")

        if average_price is not None and long_term_trend is not None and average_volume is not None and price_volatility is not None:
            # Lógica para generar una señal de compra, venta o mantenerse en espera
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

def analisis_de_sentimiento(comentarios, puntajes_sentimiento):
    try:
        # Verificar si los comentarios y los puntajes de sentimiento son listas no vacías
        if comentarios and puntajes_sentimiento:
            # Concatenar todos los comentarios en un solo texto
            texto_completo = ' '.join(comentarios)

            # Realizar el análisis de sentimiento utilizando TextBlob
            sentimiento = TextBlob(texto_completo).sentiment.polarity

            # Devolver una recomendación basada en el análisis de sentimiento
            if sentimiento > 0:
                return "Recomendación: Comprar"
            elif sentimiento < 0:
                return "Recomendación: Vender"
            else:
                return "Mantenerse en espera"
        else:
            # Manejar el caso de listas vacías
            return "No hay suficientes comentarios para analizar el sentimiento."
    except Exception as e:
        # Manejar cualquier excepción y devolver un mensaje de error
        return f"Error en el análisis de sentimiento: {e}"


def obtener_analisis_integral(df, umbral_teórico, comentarios, puntajes_sentimiento, interpretacion_fundamental):
    try:
        ## Llamar a la función para obtener los datos de Binance
        df, closing_prices, volume_data, scaler = obtener_datos_binance(symbol='ETHUSDT', intervalo='15m', limit=900)
        print(df.head())
        print(df.columns)
        print(df.info())
        print(closing_prices[:10])  # Imprime los primeros 10 valores de la lista de precios de cierre
        print("Tamaño del DataFrame:", df.shape)
        print("Longitud de la lista de precios de cierre:", len(closing_prices))
        print("Longitud de la lista de volumen de datos:", len(volume_data))

        # Imprimir los datos de precios de cierre
        print("Datos de precios de cierre:")
        print(closing_prices)

        # Convertir los datos en un DataFrame de pandas
        closing_prices_df = pd.DataFrame({'closing_prices': closing_prices})

        # Calcular la EMA de 50 períodos utilizando los datos resampleados
        ema_50 = closing_prices_df['closing_prices'].ewm(span=50, adjust=False).mean()

        # Calcular los niveles de soporte y resistencia
        niveles_soporte = calcular_niveles_soporte(closing_prices_df, encontrar_minimos_locales)
        niveles_resistencia = calcular_niveles_resistencia(closing_prices_df)

        # Realizar análisis de sentimiento
        sentimiento = analisis_de_sentimiento(comentarios, puntajes_sentimiento)

        # Realizar análisis fundamental
        closing_prices_series = pd.Series(closing_prices)
        volume_data_series = pd.Series(volume_data)

        # Llamada a la función de análisis fundamental
        fundamental_result = analisis_fundamental(closing_prices_series, volume_data_series)

        # Imprimir el resultado del análisis fundamental
        print("Resultado del análisis fundamental:")
        print(fundamental_result)

        # Llamada a la función de interpretación del análisis fundamental
        interpretacion_fundamental = interpretar_analisis_fundamental(fundamental_result)

        # Imprimir la interpretación del análisis fundamental
        print("Interpretación del análisis fundamental:")
        print(interpretacion_fundamental)

        # Integrar análisis técnico
        analisis_tecnico_resultado = analisis_tecnico(closing_prices_df, volume_data, macd_data)

        recommendation = integrar_analisis(analisis_tecnico_resultado, interpretacion_fundamental)

        planificar_tareas(analisis_tecnico_resultado, interpretacion_fundamental, recommendation)

        # Devolver los resultados integrados
        return resultado_teórico, ema_50, fundamental_result, recommendation, analisis_tecnico_resultado

    except Exception as e:
        print("Error en obtener_analisis_integral:", e)
        return None, None, None, None, None

def integrar_analisis(resultado_TECNICO, interpretacion_fundamental):
    # Analizar la respuesta técnica
    if "Señal de compra" in resultado_TECNICO:
        tecnico_compra = True
    else:
        tecnico_compra = False

    if "Señal de venta" in resultado_TECNICO:
        tecnico_venta = True
    else:
        tecnico_venta = False

    if "Tendencia alcista" in resultado_TECNICO:
        tecnico_alcista = True
    else:
        tecnico_alcista = False

    if "Tendencia bajista" in resultado_TECNICO:
        tecnico_bajista = True
    else:
        tecnico_bajista = False

    # Analizar la interpretación fundamental
    if interpretacion_fundamental == "Recomendación: Comprar":
        fundamental_compra = True
    else:
        fundamental_compra = False

    # Generar recomendación final
    if tecnico_compra and fundamental_compra:
        recomendacion_final = "Comprar"
    elif tecnico_venta:
        recomendacion_final = "Vender"
    elif tecnico_alcista:
        recomendacion_final = "Mantenerse"
    else:
        recomendacion_final = "No hacer nada"

    return recomendacion_final



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

        socket_ws = "wss://fstream.binance.com/ws/ethusdt@trade"
        ws = websocket.WebSocketApp(socket_ws, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()

    except Exception as e:
        print("Error al obtener el precio en tiempo real de futuros:", e)
def planificar_tareas(resultado_tecnico, interpretacion_fundamental, recommendation):
    # Implementa la lógica de planificación de tareas aquí
    print("Planificación de tareas con los resultados de los análisis y la recomendación obtenida.")
    # Simplemente imprimir los resultados por ahora
    print("Resultado técnico:", resultado_tecnico)
    print("Resultado fundamental:", interpretacion_fundamental)
    print("Recomendación:", recommendation)

    # Enviar un correo electrónico con los resultados
    resultado_envio_correo = enviar_correo(resultado_tecnico, interpretacion_fundamental, recommendation)
    print(resultado_envio_correo)



def enviar_correo(resultado_practico, interpretacion_fundamental, recommendation):
    try:
        # Configurar los parámetros del servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("sirem66@gmail.com", 'icld fxnt ucze ywmx')  # Correo y contraseña válidos para enviar el correo

        # Crear el mensaje de correo electrónico
        msg = MIMEMultipart()
        msg['From'] = "sirem66@gmail.com"
        msg['To'] = "sirem66@gmail.com"  # Destinatario del correo
        msg['Subject'] = "Análisis de criptomonedas ETH"

        # Cuerpo del mensaje de correo
        body = f"""\
                    Recomendación final: {recommendation}
                    Resultado práctico: {resultado_practico}
                    Resultado fundamental: {interpretacion_fundamental}

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


# Llamada principal al programa
if __name__ == '__main__':
    # Inicializar resultado_teórico como None
    resultado_teórico = None

    # Ruta al archivo CSV histórico
    archivo_csv = 'datos_financieros.csv'

    # Cargar el archivo CSV en un DataFrame histórico
    df_historico = pd.read_csv(archivo_csv)

    # Convertir la columna 'Timestamp' a tipo datetime en el DataFrame histórico
    df_historico['Timestamp'] = pd.to_datetime(df_historico['Timestamp'])

    # Eliminar la columna 'Timestamp' del DataFrame histórico ya que no se necesita para el análisis
    df_historico = df_historico.drop(columns=['Timestamp'])

    # Normalizar los datos utilizando Min-Max Scaling
    scaler = MinMaxScaler()
    df_scaled = scaler.fit_transform(df_historico)

    # Convertir el DataFrame escalado a un nuevo DataFrame de Pandas
    df_scaled = pd.DataFrame(df_scaled, columns=df_historico.columns)

    # Mostrar las primeras filas del DataFrame escalado
    print("\nDatos escalados:")
    print(df_scaled.head())

    # Definir umbral_teórico
    umbral_teórico = 0.5

    # Suponiendo que tienes comentarios y puntajes_sentimiento obtenidos previamente
    comentarios = [...]  # Lista de comentarios
    puntajes_sentimiento = [...]  # Lista de puntajes de sentimiento

    # Suponiendo que tienes la interpretación del análisis fundamental
    interpretacion_fundamental = "Recomendación: Comprar"

    resultado_teórico, ema_50, fundamental_result, recommendation, analisis_tecnico_resultado = obtener_analisis_integral(df, umbral_teórico, comentarios, puntajes_sentimiento, interpretacion_fundamental)