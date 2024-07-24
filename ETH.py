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

# Configuración de la API de Reddit
REDDIT_CLIENT_ID = 'syTgPQWR92sh3umGqTVpOg'
REDDIT_CLIENT_SECRET = 'oflk5tr4jOJmS1rXv65A5VdpqWkq2g'
REDDIT_USER_AGENT = 'script by /u/username'  # Puedes cambiar 'username' por tu nombre de usuario de Reddit

# Configuración de la API de Binance
API_KEY = '5vWrP5bgXUpFa89KQBrJoTfAUUH8eZwccU7Q6CZcD4hrU7Rs9aqKf46bqBJTMRwU'
API_SECRET = 'ica2XnjMGd5HOgwWH4spFiSXZvn8ogukQHWbGUTpvt4I9z6wpQbtnM4YZISqhMNU'
client = Client(API_KEY, API_SECRET)


# Lista para almacenar los resultados históricos de las recomendaciones
historical_recommendations = []
def obtener_reddit_comments(puntajes_sentimiento):
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

        # Filtrar los comentarios para asegurarse de que sean cadenas de texto válidas
        comments = [comment for comment in comments if isinstance(comment, str)]

        # Luego, pasar la lista filtrada a la función de análisis de sentimiento
        sentimiento = analisis_de_sentimiento(comentarios, puntajes_sentimiento)
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

def analisis_de_sentimiento(comentarios, puntajes_sentimiento):
    try:
        # Filtrar los comentarios para asegurarse de que sean cadenas de texto válidas
        comentarios_validos = [comment for comment in comentarios if isinstance(comment, str)]

        if comentarios_validos:
            # Realizar el análisis de sentimiento utilizando TextBlob para cada comentario
            puntajes_sentimiento = [TextBlob(comment).sentiment.polarity for comment in comentarios_validos]

            # Calcular el puntaje promedio de sentimiento
            puntaje_promedio = np.mean(puntajes_sentimiento)

            print("Puntajes de sentimiento:", puntajes_sentimiento)
            print("Promedio de puntajes de sentimiento:", puntaje_promedio)

            # Clasificar el sentimiento en positivo, negativo o neutral basado en el puntaje promedio
            if puntaje_promedio > 0.5:
                resultado_sentimiento = "Sentimiento positivo"
            elif puntaje_promedio < 0.5:
                resultado_sentimiento = "Sentimiento negativo"
            else:
                resultado_sentimiento = "Sentimiento neutral"
        else:
            resultado_sentimiento = "No hay comentarios para analizar"

        return puntajes_sentimiento, resultado_sentimiento

    except Exception as e:
        print("Error al realizar el análisis de sentimiento:", e)
        return [], "No se pudo realizar el análisis de sentimiento debido a un error."


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



def obtener_datos_binance(symbol, intervalo, limit, intentos=3):
    for _ in range(intentos):
        try:
            klines = client.get_klines(symbol=symbol, interval=intervalo, limit=limit)
            closing_prices = [float(kline[4]) for kline in klines]
            volume_data = [float(kline[5]) for kline in klines]

            # Escalar los precios de cierre en tiempo real
            closing_prices_scaled = scaler.fit_transform(np.array(closing_prices).reshape(-1, 1))

            df = pd.DataFrame({'closing_prices': closing_prices, 'volume_data': volume_data})
            df['closing_prices_scaled'] = closing_prices_scaled

            return df, closing_prices, volume_data
        except Exception as e:
            print(f"Error al obtener datos de Binance en el intento {_ + 1}: {e}")
            if _ < intentos - 1:
                print("Reintentando en 5 segundos...")
                time.sleep(5)
            else:
                print("Se agotaron los intentos. No se pudo obtener los datos de Binance.")

def analisis_teórico(df, closing_prices):
    print("Columnas del DataFrame:", df.columns)
    try:
        # Verificar si 'closing_prices' está en las columnas del DataFrame
        if 'closing_prices' in df.columns:
            print("Columna 'closing_prices' encontrada en el DataFrame.")
            # Si está presente, puedes acceder a la columna
            closing_prices = df['closing_prices']
            print("Precios de cierre obtenidos correctamente.")
        else:
            print("La columna 'closing_prices' no está presente en el DataFrame.")

        if isinstance(closing_prices, pd.Series) and not closing_prices.empty:
            # Preparar los datos para el modelo LSTM
            scaler = MinMaxScaler(feature_range=(0, 1))
            # Convertir la serie en un array de NumPy
            closing_prices_array = np.array(closing_prices)
            dataset = scaler.fit_transform(closing_prices_array.reshape(-1, 1))
            print("Datos escalados correctamente.")

            # Dividir los datos en conjuntos de entrenamiento y prueba
            train_size = int(len(dataset) * 0.9)
            test_size = len(dataset) - train_size
            train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]

            # Verificar si los conjuntos de entrenamiento y prueba están vacíos
            if len(train) == 0 or len(test) == 0:
                raise ValueError("Al menos uno de los conjuntos de datos de entrenamiento o prueba está vacío.")

            print("Dimensiones del conjunto de entrenamiento:", train.shape)
            print("Dimensiones del conjunto de prueba:", test.shape)

            # Reestructurar los datos en X=t y Y=t+1
            time_step = 50
            X_train, y_train = create_dataset(train, time_step)
            X_test, y_test = create_dataset(test, time_step)

            # Reestructurar los datos para que sean compatibles con LSTM
            X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
            X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
            print("Dimensiones de X_train:", X_train.shape)
            print("Dimensiones de y_train:", y_train.shape)

            # Construir y entrenar el modelo LSTM
            lstm_model = build_model(time_step)
            print("Modelo LSTM construido correctamente.")

            lstm_model, history = train_model(lstm_model, X_train, y_train, X_test, y_test, epochs=30, batch_size=32)
            print("Modelo LSTM entrenado correctamente.")

            # Realizar predicciones con el modelo LSTM
            train_predict = lstm_model.predict(X_train)
            test_predict = lstm_model.predict(X_test)

            # Invertir la transformación de escala
            train_predict = scaler.inverse_transform(train_predict)
            y_train = scaler.inverse_transform([y_train])
            test_predict = scaler.inverse_transform(test_predict)
            y_test = scaler.inverse_transform([y_test])

            # Calcular el error cuadrático medio
            train_score = np.sqrt(mean_squared_error(y_train[0], train_predict[:, 0]))
            print('Puntuación del entrenamiento: %.2f RMSE' % (train_score))
            test_score = np.sqrt(mean_squared_error(y_test[0], test_predict[:, 0]))
            print('Puntuación de la prueba: %.2f RMSE' % (test_score))

            # Predecir el próximo precio de cierre
            last_data = dataset[-time_step:]
            last_data = last_data.reshape((1, time_step, 1))
            next_price = lstm_model.predict(last_data)
            next_price = scaler.inverse_transform(next_price)
            print('Próximo precio de cierre predicho:', next_price[0][0])

            # Realizar una recomendación en función de la predicción
            if next_price[0][0] > closing_prices.iloc[-1]:
                return "Recomendación: Comprar"
            else:
                return "Recomendación: Vender"
        else:
            return "No se pudieron obtener datos de precios de cierre válidos."

    except Exception as e:
        print("Error durante el análisis teórico:", repr(e))
        return "Error: " + str(e)  # Devolver un mensaje de error en caso de excepción

def calcular_niveles_soporte_en_tiempo_real(closing_prices):
    try:
        # Verificar si closing_prices es una lista o array
        if isinstance(closing_prices, (list, np.ndarray)):
            # Calcular mínimos locales en los precios de cierre en tiempo real
            indices_minimos_locales = encontrar_minimos_locales_en_tiempo_real(closing_prices)

            # Verificar si se encontraron mínimos locales
            if indices_minimos_locales.any():  # Usando .any() para verificar si hay algún mínimo local
                # Obtener el precio del último mínimo local
                minimo_local = min(closing_prices)
                return minimo_local
            else:
                print("No se encontraron mínimos locales en los precios de cierre.")
                return None
        else:
            raise ValueError("Los precios de cierre deben ser proporcionados como una lista o un array.")

    except Exception as e:
        print("Error al calcular niveles de soporte:", e)
        return None

def encontrar_minimos_locales_en_tiempo_real(closing_prices):
    try:
        # Imprimir los precios de cierre para depurar
        print("Precios de cierre:", closing_prices)

        # Encontrar los índices de los mínimos locales utilizando el algoritmo de find_peaks
        peaks, _ = find_peaks(-1 * closing_prices,
                              distance=10)  # Cambiamos el signo y especificamos una distancia mínima entre picos

        # Imprimir los índices de los mínimos locales para depurar
        print("Índices de mínimos locales:", peaks)

        return peaks

    except Exception as e:
        print("Error al encontrar mínimos locales:", e)
        return []

def calcular_niveles_resistencia_en_tiempo_real(closing_prices):
    try:
        # Verificar si closing_prices es una lista o array
        if isinstance(closing_prices, (list, np.ndarray)):
            # Calcular máximos locales en los precios de cierre en tiempo real
            indices_maximos_locales = encontrar_maximos_locales_en_tiempo_real(closing_prices)

            # Verificar si se encontraron máximos locales
            if indices_maximos_locales.any():  # Usando .any() para verificar si hay algún máximo local
                # Obtener el precio del último máximo local
                maximo_local = max(closing_prices)
                return maximo_local
            else:
                print("No se encontraron máximos locales en los precios de cierre.")
                return None
        else:
            raise ValueError("Los precios de cierre deben ser proporcionados como una lista o un array.")

    except Exception as e:
        print("Error al calcular niveles de resistencia:", e)
        return None

def encontrar_maximos_locales_en_tiempo_real(prices):
    try:
        # Encontrar los índices de los máximos locales utilizando el algoritmo de find_peaks
        peaks, _ = find_peaks(prices, prominence=0.01) # Ajusta el valor de prominence según tus datos
        return peaks

    except Exception as e:
        print("Error al encontrar máximos locales:", e)
        return []


# Función para calcular la probabilidad de la Ley de Elliott
def calcular_probabilidad_elliott(wave_patterns):
    try:
        probabilidad_elliott = 0

        for patron in wave_patterns:
            if patron['tipo'] == 'impulsiva':
                probabilidad_elliott += 1
            elif patron['tipo'] == 'correctiva':
                probabilidad_elliott -= 1

        return probabilidad_elliott

    except Exception as e:
        print("Error al calcular la probabilidad de la Ley de Elliott:", e)


def determinar_etapa_mercado(onda_dominante, onda_especifica):
    try:
        etapa_mercado = ""

        if onda_dominante == "Impulsiva":
            if onda_especifica == "Onda 1":
                etapa_mercado = "Inicio de tendencia alcista"
            elif onda_especifica == "Onda 3":
                etapa_mercado = "Fuerte impulso alcista"
        elif onda_dominante == "Correctiva":
            if onda_especifica == "Onda C":
                etapa_mercado = "Corrección en una tendencia bajista"

        return etapa_mercado

    except Exception as e:
        print("Error al determinar la etapa del mercado:", e)


def detectar_ley_elliott_avanzado(data_source):
    try:
        # Obtener los datos en tiempo real
        closing_prices_df = data_source.obtener_datos_en_tiempo_real()

        # Verificar si el DataFrame está vacío
        if closing_prices_df.empty:
            print("El DataFrame 'closing_prices_df' está vacío.")
            return "No hay señal clara en este momento"


        # Cálculo de la primera derivada de los precios de cierre
        price_diff = np.gradient(closing_prices_df['closing_prices'])

        # Identificación de picos y valles en la primera derivada
        peaks, _ = find_peaks(price_diff, prominence=0.1)
        valleys, _ = find_peaks(-price_diff, prominence=0.1)

        # Verificar si las listas de picos y valles están vacías
        if len(peaks) == 0 or len(valleys) == 0:
            print("No se encontraron picos o valles en los datos.")
            return "No hay señal clara en este momento"

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

        probabilidad_elliott = calcular_probabilidad_elliott(wave_patterns)
        print(f"Probabilidad de formación de onda de Elliott: {probabilidad_elliott}")

        resultado = f"El mercado está en la {onda_especifica}. {etapa_mercado}."
        print(resultado)
        return resultado

    except Exception as e:
        print("Error al detectar la Ley de Elliott:", e)
        return "No hay señal clara en este momento"


def detectar_patrones_graficos(data_source, closing_prices, volume_data):
    patrones_detectados = {}

    # Verificar los datos de entrada
    if not isinstance(closing_prices, (list, np.ndarray)) or not isinstance(volume_data, (list, np.ndarray)):
        print("Los datos de entrada no son del tipo correcto.")
        return

    print("Closing prices:", closing_prices)
    print("Volume data:", volume_data)

    # Manejo de datos faltantes
    if closing_prices is None or volume_data is None:
        print("Los datos en tiempo real son None.")
        return

    def detectar_triangulo_ascendente(closing_prices, volumes):
        if volumes is not None and len(volumes) >= len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                if closing_prices[i] > closing_prices[i - 1] > closing_prices[i - 2] and volumes[i] > volumes[i - 1] > \
                        volumes[i - 2]:
                    if i - 2 >= 0 and (i + 1) < len(closing_prices):
                        duration = i + 1 - (i - 2)
                        if duration >= 5:
                            return True
        return False

    def detectar_triangulo_descendente(closing_prices, volumes):
        if volumes is not None and len(volumes) >= len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                if closing_prices[i] < closing_prices[i - 1] < closing_prices[i - 2] and volumes[i] > volumes[i - 1] > \
                        volumes[i - 2]:
                    if i - 2 >= 0 and (i + 1) < len(closing_prices):
                        duration = i + 1 - (i - 2)
                        if duration >= 5:
                            return True
        return False

    def detectar_cabeza_hombros(closing_prices, volumes):
        if volumes is not None and len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                if closing_prices[i - 2] > closing_prices[i - 1] < closing_prices[i] and volumes[i] < volumes[i - 1] < \
                        volumes[i - 2]:
                    if i - 2 >= 0 and (i + 1) < len(closing_prices):
                        duration = i + 1 - (i - 2)
                        if duration >= 5:
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

    def detectar_cuña_ascendente(closing_prices, volumes):
        if len(closing_prices) < 5 or volumes is None or len(volumes) < 5:
            return False

        for i in range(4, len(closing_prices)):
            if all(closing_prices[j] > closing_prices[j + 1] for j in range(i - 4, i)) and all(
                    volumes[j] > volumes[j + 1] for j in range(i - 4, i)):
                return True

        return False

    def detectar_bandera(closing_prices, volumes):
        if volumes is not None and len(closing_prices) >= 3:
            for i in range(2, len(closing_prices)):
                if volumes[i - 1] is not None and volumes[i - 2] is not None and volumes[i] is not None:
                    if closing_prices[i - 2] < closing_prices[i - 1] < closing_prices[i] and volumes[i] < volumes[
                        i - 1] < volumes[i - 2]:
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

    while True:
        # Obtener los nuevos datos en tiempo real
        closing_prices, volume_data = data_source.obtener_datos_en_tiempo_real()

        # Lógica de detección de patrones
        patrones_detectados["Triángulo Ascendente"] = detectar_triangulo_ascendente(closing_prices, volume_data)
        patrones_detectados["Triángulo Descendente"] = detectar_triangulo_descendente(closing_prices, volume_data)
        patrones_detectados["Cabeza y Hombros"] = detectar_cabeza_hombros(closing_prices, volume_data)
        patrones_detectados["Cuña Descendente"] = detectar_cuña_descendente(closing_prices, volume_data)
        patrones_detectados["Cuña Ascendente"] = detectar_cuña_ascendente(closing_prices, volume_data)
        patrones_detectados["Bandera"] = detectar_bandera(closing_prices, volume_data)
        patrones_detectados["Doble Piso"] = detectar_doble_piso(closing_prices, volume_data)
        patrones_detectados["Doble Techo"] = detectar_doble_techo(closing_prices, volume_data)

        # Filtrar los patrones detectados y retornarlos
        patrones_detectados = {patron: detectado for patron, detectado in patrones_detectados.items() if detectado}
        if patrones_detectados:
            yield patrones_detectados.keys()

def detectar_ley_dow_avanzado(closing_prices_df):
    try:
        if closing_prices_df.empty:
            print("El DataFrame 'closing_prices_df' está vacío.")
            return "No hay señal clara en este momento"

        cambio_porcentual = (closing_prices_df['closing_prices'].iloc[-1] - closing_prices_df['closing_prices'].iloc[
            -2]) / closing_prices_df['closing_prices'].iloc[-2] * 100

        sma_50 = closing_prices_df['closing_prices'].rolling(window=50).mean()
        sma_200 = closing_prices_df['closing_prices'].rolling(window=200).mean()
        ema_50 = closing_prices_df['closing_prices'].ewm(span=50, adjust=False).mean()
        ema_200 = closing_prices_df['closing_prices'].ewm(span=200, adjust=False).mean()

        if cambio_porcentual > 0 and sma_50.iloc[-1] > sma_200.iloc[-1] and ema_50.iloc[-1] > ema_200.iloc[-1]:
            return "Tendencia alcista según la Ley de Dow"
        elif cambio_porcentual < 0 and sma_50.iloc[-1] < sma_200.iloc[-1] and ema_50.iloc[-1] < ema_200.iloc[-1]:
            return "Tendencia bajista según la Ley de Dow"
        else:
            return "Tendencia lateral según la Ley de Dow"

    except Exception as e:
        print("Error al detectar la Ley de Dow:", e)
        return "No se pudo determinar la tendencia según la Ley de Dow"
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
            print(f"Divergencia {tipo_divergencia} detectada en la fila {fila_divergencia}")
        else:
            print("No se detectaron divergencias en el MACD.")

        return tipo_divergencia

    except Exception as e:
        print("Error al detectar divergencias en el MACD:", e)


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

def analisis_practico(closing_prices_df, volume_data, ema_50, niveles_soporte, niveles_resistencia, macd_data, tolerancia=0.5):
    try:
        if not closing_prices_df or len(closing_prices_df) == 0 or ema_50 is None:
            print("Al menos uno de los DataFrames está vacío o ema_50 es None.")
            return "No hay señal clara en este momento", ""  # Asegúrate de devolver un valor para resultado_ellio

        # Realizar el análisis práctico con los datos proporcionados
        patrones = detectar_patrones_graficos(data_source, closing_prices_df['closing_prices'], volume_data)
        resultado_practico = None

        if not patrones:
            print("No se detectaron patrones gráficos")
            return "No hay señal clara en este momento", ""  # Asegúrate de devolver un valor para resultado_elliott

        # Aquí se realiza la detección de los patrones gráficos directamente
        patrones_ascendentes = ['Triángulo Ascendente', 'Cabeza y Hombros', 'Cuña Ascendente', 'Bandera', 'Doble Techo']
        patrones_descendentes = ['Triángulo Descendente', 'Cabeza y Hombros', 'Cuña Descendente', 'Bandera', 'Doble Piso']

        nombre_patron = None
        for pat in patrones:
            if pat in patrones_ascendentes or pat in patrones_descendentes:
                nombre_patron = pat
                break

        # Establecer el resultado práctico con el nombre del patrón
        if nombre_patron:
            resultado_practico = f"Señal de compra por {nombre_patron}"
        else:
            resultado_practico = "Sin señal por patrones"

            # Verificar si el precio está cerca de un nivel de soporte o resistencia
            if (abs(closing_prices_df.iloc[-1]['closing_prices'] - niveles_soporte) < tolerancia).any():
                resultado_practico += ", Señal de compra por nivel de soporte"
            elif (abs(closing_prices_df.iloc[-1]['closing_prices'] - niveles_resistencia) < tolerancia).any():
                resultado_practico += ", Señal de venta por nivel de resistencia"

        # Agregar detección de la Ley de Elliott
        resultado_elliott = detectar_ley_elliott_avanzado(data_source)
        if resultado_elliott:
            resultado_practico += f", {resultado_elliott}"  # Añadir el resultado de la Ley de Elliott a la salida
        return resultado_practico, resultado_elliott  # Asegúrate de devolver un valor para resultado_elliott

    except Exception as e:
        print("Error al realizar el análisis práctico:", e)
        return "No hay señal clara en este momento", ""  # Asegúrate de devolver un valor para resultado_elliott

def calcular_puntaje(probabilidad_elliott):
    try:
        if probabilidad_elliott >= 70:
            return "Alto"
        elif probabilidad_elliott >= 40:
            return "Medio"
        else:
            return "Bajo"
    except Exception as e:
        print("Error al calcular el puntaje:", e)
        return "Desconocido"

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

def obtener_analisis_integral(resultado_teórico, umbral_teórico, comentarios, data_source):
    try:
        # Llamar a la función para obtener los datos en tiempo real
        precios, volumen = data_source.obtener_datos_en_tiempo_real()

        # Calcular la media móvil exponencial (EMA) de 50 períodos
        ema_50 = precios.ewm(span=50, adjust=False).mean()

        # Suponiendo que tienes los precios de cierre en una variable llamada 'closing_prices'

        closing_prices = [...]  # Aquí debes proporcionar los precios de cierre como una lista o un array
        soporte = calcular_niveles_soporte_en_tiempo_real(closing_prices)
        resistencia = calcular_niveles_resistencia_en_tiempo_real(closing_prices)



        # Calcular el indicador MACD
        macd_data = calcular_macd(precios)

        # Detectar patrones gráficos
        patrones_detectados = detectar_patrones_graficos(data_source, precios, volumen)

        # Detectar la Ley de Elliott
        resultado_elliott = detectar_ley_elliott_avanzado(data_source)

        # Realizar análisis práctico
        resultado_practico, resultado_elliott_practico = analisis_practico(precios, volumen, ema_50, nivel_soporte,
                                                                           nivel_resistencia, macd_data)

        # Realizar análisis fundamental
        fundamental_result = analisis_fundamental(precios, volumen)

        # Interpretar análisis fundamental
        interpretacion_fundamental = interpretar_analisis_fundamental(fundamental_result)

        # Obtener el resultado del sentimiento (esto es un placeholder, reemplaza con la lógica real)
        resultado_sentimiento = obtener_resultado_sentimiento()

        # Integrar análisis y generar recomendación
        recommendation = integrar_analisis(resultado_practico, interpretacion_fundamental, resultado_sentimiento)

        # Planificar tareas con los resultados de los análisis y la recomendación obtenida
        planificar_tareas(resultado_teórico, resultado_practico, interpretacion_fundamental,
                          recommendation)

        # Devolver los resultados integrados
        return resultado_teórico, fundamental_result, recommendation  # Asegúrate de devolver los resultados necesarios

    except Exception as e:
        print("Error en obtener_analisis_integral:", e)
        return None, None, None  # Devuelve valores nulos en caso de error
def integrar_analisis(resultado_practico, interpretacion_fundamental, resultado_sentimiento):
    # Inicializar variables de sentimiento
    sentimiento_positivo = False
    sentimiento_negativo = False
    sentimiento_neutral = False

    # Analizar la respuesta práctica
    if "Señal de compra" in resultado_practico:
        practico_compra = True
    else:
        practico_compra = False

    if "Señal de venta" in resultado_practico:
        practico_venta = True
    else:
        practico_venta = False

    if "Tendencia alcista" in resultado_practico:
        practico_alcista = True
    else:
        practico_alcista = False

    if "Tendencia bajista" in resultado_practico:
        practico_bajista = True
    else:
        practico_bajista = False

    # Analizar la interpretación fundamental
    if interpretacion_fundamental == "Recomendación: Comprar":
        fundamental_compra = True
    else:
        fundamental_compra = False

    # Analizar el resultado de sentimiento
    if resultado_sentimiento == "Sentimiento positivo":
        sentimiento_positivo = True
    elif resultado_sentimiento == "Sentimiento negativo":
        sentimiento_negativo = True
    else:
        sentimiento_neutral = True

    # Generar recomendación final
    if practico_compra and fundamental_compra and sentimiento_positivo:
        recomendacion_final = "Comprar"
    elif practico_venta or sentimiento_negativo:
        recomendacion_final = "Vender"
    elif practico_alcista:
        recomendacion_final = "Mantenerse"
    else:
        recomendacion_final = "No hacer nada"

    return recomendacion_final

def planificar_tareas(resultado_teórico, resultado_practico, interpretar_analisis_fundamental, recommendation):
    # Implementa la lógica de planificación de tareas aquí
    print("Planificación de tareas con los resultados de los análisis y la recomendación obtenida.")
    # Simplemente imprimir los resultados por ahora
    print("Resultado teórico:", resultado_teórico)
    print("Resultado práctico:", resultado_practico)
    print("Interpretación del análisis fundamental:", interpretar_analisis_fundamental)
    print("Recomendación:", recommendation)

    # Enviar un correo electrónico con los resultados
    resultado_envio_correo = enviar_correo(resultado_practico, interpretar_analisis_fundamental, recommendation)
    print(resultado_envio_correo)


def enviar_correo(resultado_practico, interpretar_analisis_fundamental, recommendation):
    try:
        # Configurar los parámetros del servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("sirem66@gmail.com", 'icld fxnt ucze ywmx')  # Correo y contraseña válidos para enviar el correo

        # Crear el mensaje de correo electrónico
        msg = MIMEMultipart()
        msg['From'] = "sirem66@gmail.com"
        msg['To'] = "sirem66@gmail.com"  # Destinatario del correo
        msg['Subject'] = "Análisis de criptomonedas BTC"

        # Cuerpo del mensaje de correo
        body = f"""\
                    Recomendación final: {recommendation}
                    Resultado práctico: {resultado_practico}
                    Resultado fundamental: {interpretar_analisis_fundamental}

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

class DataSource:
    def __init__(self, client, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = client
        self.price_buffer = []
        self.volume_buffer = []
        self.buffer_size = 20

    def obtener_datos_en_tiempo_real(self):
        try:
            while True:
                depth = self.client.get_order_book(symbol='BTCUSDT')
                last_trade = self.client.get_recent_trades(symbol='BTCUSDT', limit=1)[0]
                price = float(last_trade['price'])
                volume = float(last_trade['qty'])

                self.price_buffer.append(price)
                self.volume_buffer.append(volume)

                if len(self.price_buffer) >= self.buffer_size:
                    # Construir un DataFrame a partir de los buffers de precios y volumen
                    df = pd.DataFrame({'closing_prices': self.price_buffer, 'volume_data': self.volume_buffer})
                    # Extraer los precios de cierre como una lista
                    closing_prices = df['closing_prices'].tolist()
                    return closing_prices, df['volume_data'].tolist()

                time.sleep(5)

        except Exception as e:
            print("Error al obtener datos en tiempo real de la API de Binance:", e)
            return [], []  # Devolver listas vacías en caso de error

def obtener_precio_real_time_futuros(symbol):
    global last_real_time_price

    try:
        def on_message(ws, message):
            global last_real_time_price
            data = json.loads(message)

            if 'p' in data and 's' in data:
                symbol = data['s']
                if symbol == 'BTCUSDT':
                    last_real_time_price = float(data['p'])
                    print(f"Precio en tiempo real de futuros de BTC: {last_real_time_price}")

        def on_error(ws, error):
            print("Error en la transmisión WebSocket:", error)

        def on_close(ws):
            print("Conexión WebSocket cerrada")

        def on_open(ws):
            print("Conexión WebSocket abierta")

        websocket.enableTrace(True)

        socket_ws = "wss://fstream.binance.com/ws/btcusdt@trade"
        ws = websocket.WebSocketApp(socket_ws, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()

    except Exception as e:
        print("Error al obtener el precio en tiempo real de futuros:", e)

if __name__ == '__main__':
    umbral_teórico = 0.5

    client = Client(api_key='5vWrP5bgXUpFa89KQBrJoTfAUUH8eZwccU7Q6CZcD4hrU7Rs9aqKf46bqBJTMRwU', api_secret='ica2XnjMGd5HOgwWH4spFiSXZvn8ogukQHWbGUTpvt4I9z6wpQbtnM4YZISqhMNU')
    data_source = DataSource(client)

    if hasattr(data_source, 'obtener_datos_en_tiempo_real'):
        print("El objeto data_source tiene el método obtener_datos_en_tiempo_real.")
    else:
        print("El objeto data_source NO tiene el método obtener_datos_en_tiempo_real.")

    # Obtener los datos de precios y volumen en tiempo real
    precios, volumenes = data_source.obtener_datos_en_tiempo_real()

    # Calcular los niveles de soporte y resistencia
    soporte = calcular_niveles_soporte_en_tiempo_real(precios)
    resistencia = calcular_niveles_resistencia_en_tiempo_real(precios)

    # Detectar patrones gráficos y ley de Elliott
    patrones_detectados = detectar_patrones_graficos(data_source, precios, volumenes)
    resultado_elliott = detectar_ley_elliott_avanzado(data_source)

    comentarios = [...]  # Lista de comentarios

    resultado_teórico = "valor_inicial"  # Asigna un valor inicial a resultado_teórico

    # Luego puedes llamar a la función obtener_analisis_integral
    resultado_teórico, fundamental_result, recommendation = obtener_analisis_integral(resultado_teórico, umbral_teórico,
                                                                                      comentarios, data_source)