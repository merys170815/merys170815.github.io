import time
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
import os

# Configuración de la conexión a la API de IQ Option
email = "sirem66@gmail.com"
password = "22520873Me"
API = IQ_Option(email, password)

try:
    API.connect()
    if not API.check_connect():
        raise Exception("Conexión no establecida")
except Exception as e:
    print("Error al conectar a la API:", e)
    exit()

# Configuración del activo y el tamaño de la vela
activo = "EURUSD"
tamaño_vela = 1  # En minutos

# Función para obtener el precio actual del activo
def get_current_price():
    try:
        candles = API.get_candles(activo, tamaño_vela, count=1, endtime=time.time())
        if candles:
            return candles[0]["close"]
        else:
            print("No se encontraron velas")
            return None
    except Exception as e:
        print("Error al obtener velas:", e)
        return None


def calculate_ichimoku_cloud(price_data):
    high_prices = [data['max'] for data in price_data]
    low_prices = [data['min'] for data in price_data]

    tenkan_sen = (max(high_prices[-9:]) + min(low_prices[-9:])) / 2
    kijun_sen = (max(high_prices[-26:]) + min(low_prices[-26:])) / 2
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    senkou_span_b = (max(high_prices[-52:]) + min(low_prices[-52:])) / 2

    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b


def calculate_momentum(price_data, period=14):
    if len(price_data) < period:
        return None
    momentum = price_data[-1]['close'] - price_data[-period]['close']
    return momentum


def calculate_stochastic(price_data, period=14):
    if len(price_data) < period:
        return None
    high_prices = [data['max'] for data in price_data]
    low_prices = [data['min'] for data in price_data]
    close_prices = [data['close'] for data in price_data]

    highest_high = max(high_prices[-period:])
    lowest_low = min(low_prices[-period:])
    current_close = close_prices[-1]

    if highest_high != lowest_low:
        stochastic = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
    else:
        stochastic = 50

    return stochastic


def calculate_rsi(price_data, period=14):
    if len(price_data) < period:
        return None
    close_prices = [data['close'] for data in price_data]
    gains = [close_prices[i] - close_prices[i - 1] for i in range(1, len(close_prices)) if
             close_prices[i] > close_prices[i - 1]]
    losses = [close_prices[i - 1] - close_prices[i] for i in range(1, len(close_prices)) if
              close_prices[i] < close_prices[i - 1]]

    average_gain = sum(gains) / period if gains else 0
    average_loss = sum(losses) / period if losses else 0

    if average_loss == 0:
        return 100
    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_adx(price_data, period=14):
    if len(price_data) < period + 1:  # Asegurarse de tener suficientes datos para el cálculo
        return None
    df = pd.DataFrame(price_data)

    # Calcular el True Range (TR)
    df['TR'] = df['max'] - df['min']
    df['TR'] = df['TR'].combine(df['max'].shift(1) - df['min'], max)
    df['TR'] = df['TR'].combine(df['min'] - df['close'].shift(1), max)

    # Calcular +DM y -DM
    df['+DM'] = df['max'] - df['max'].shift(1)
    df['-DM'] = df['min'].shift(1) - df['min']

    df['+DM'] = df.apply(lambda row: row['+DM'] if row['+DM'] > row['-DM'] and row['+DM'] > 0 else 0, axis=1)
    df['-DM'] = df.apply(lambda row: row['-DM'] if row['-DM'] > row['+DM'] and row['-DM'] > 0 else 0, axis=1)

    # Calcular el ATR, +DI y -DI
    df['ATR'] = df['TR'].rolling(window=period).mean()
    df['+DI'] = 100 * (df['+DM'].rolling(window=period).mean() / df['ATR'])
    df['-DI'] = 100 * (df['-DM'].rolling(window=period).mean() / df['ATR'])

    # Calcular el DX
    df['DX'] = 100 * abs((df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI']))

    # Calcular el ADX
    adx = df['DX'].rolling(window=period).mean().iloc[-1]

    return adx


def calculate_parabolic_sar(price_data):
    # Implementación simplificada del SAR parabólico
    af = 0.02
    max_af = 0.2
    psar = [0] * len(price_data)
    trend = 1 if price_data[1]['close'] > price_data[0]['close'] else -1

    psar[0] = price_data[0]['close']
    for i in range(1, len(price_data)):
        psar[i] = psar[i - 1] + af * (
                    max([data['max'] for data in price_data[:i + 1]]) - psar[i - 1]) if trend == 1 else psar[
                                                                                                            i - 1] + af * (
                                                                                                                    min([
                                                                                                                            data[
                                                                                                                                'min']
                                                                                                                            for
                                                                                                                            data
                                                                                                                            in
                                                                                                                            price_data[
                                                                                                                            :i + 1]]) -
                                                                                                                    psar[
                                                                                                                        i - 1])
        if trend == 1:
            if price_data[i]['close'] < psar[i]:
                trend = -1
                psar[i] = max([data['max'] for data in price_data[:i + 1]])
                af = 0.02
        else:
            if price_data[i]['close'] > psar[i]:
                trend = 1
                psar[i] = min([data['min'] for data in price_data[:i + 1]])
                af = 0.02
        af = min(af + 0.02, max_af)

    return psar[-1]

def predict_next_candle_direction(price_data):
    if len(price_data) < 52:
        return "no claro"  # No hay suficientes datos para Ichimoku y otros indicadores

    tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = calculate_ichimoku_cloud(price_data)
    momentum = calculate_momentum(price_data)
    stochastic = calculate_stochastic(price_data)
    rsi = calculate_rsi(price_data)
    adx = calculate_adx(price_data)

    if any(x is None for x in [momentum, stochastic, rsi, adx]):
        return "no claro"  # Si alguno de los indicadores no se pudo calcular, devolver "no claro"

    last_close_price = price_data[-1]['close']

    # Condiciones para la dirección de las próximas velas
    if (last_close_price > senkou_span_a and last_close_price > senkou_span_b and
            momentum > 0 and stochastic > 80 and rsi > 50 and adx > 25):
        return "alcista"
    elif (last_close_price < senkou_span_a and last_close_price < senkou_span_b and
          momentum < 0 and stochastic < 20 and rsi < 50 and adx > 25):
        return "bajista"
    else:
        return "no claro"


def wait_for_next_candle():
    # Calcular el tiempo hasta el próximo minuto
    current_time = time.time()
    next_minute = ((current_time // 60) + 1) * 60
    sleep_time = next_minute - current_time
    time.sleep(sleep_time)


def run_strategy():
    while True:
        while not API.check_connect():
            try:
                API.connect()
                if not API.check_connect():
                    raise Exception("No se pudo reconectar")
            except Exception as e:
                print("Error al reconectar a la API:", e)
                time.sleep(60)  # Esperar 1 minuto antes de intentar reconectar

        wait_for_next_candle()  # Esperar hasta el inicio de la próxima vela

        precio_actual = get_current_price()

        if precio_actual:
            print("Precio actual:", precio_actual)

            endtime = int(time.time())  # Obtener la marca de tiempo actual
            try:
                price_data = API.get_candles(activo, tamaño_vela, count=100, endtime=endtime)
            except Exception as e:
                print("Error al obtener datos históricos:", e)
                continue

            direction = predict_next_candle_direction(price_data)
            print("Dirección de las próximas velas:", direction)

            if direction != "no claro":
                subject = f"Información de trading - {activo}"
                message = f"Precio actual: {precio_actual}\nDirección: {direction}"


        else:
            print("Error al obtener el precio actual")


# Ejecutar la estrategia
run_strategy()
