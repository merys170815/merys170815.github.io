import asyncio
import pandas as pd
from pyquotex.quotexapi.stable_api import Quotex

# Define tus credenciales
username = "capsaludsas@gmail.com"
password = "22520873Me"


async def get_candles(client, symbol):
    try:
        # Obtener datos históricos de velas
        data = await client.get_candle_v2(symbol, interval=1, limit=200)  # Ajusta según la API
        if data:
            df = pd.DataFrame(data)
            return df
        else:
            print("No se obtuvieron datos de velas.")
            return pd.DataFrame()  # Retorna un DataFrame vacío
    except Exception as e:
        print(f"Error al obtener datos de velas: {e}")
        return pd.DataFrame()  # Retorna un DataFrame vacío en caso de error


async def get_realtime_price(client, symbol):
    try:
        # Obtener el precio en tiempo real
        price = await client.get_realtime_price(symbol)
        return price
    except Exception as e:
        print(f"Error al obtener el precio en tiempo real: {e}")
        return None

# Funciones para cálculos de indicadores
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
    df['TR'] = df[['max', 'min', 'close']].apply(lambda x: max(x['max'] - x['min'], x['max'] - x['close'].shift(), x['close'] - x['min']), axis=1)

    # Calcular +DM y -DM
    df['+DM'] = df['max'] - df['max'].shift()
    df['-DM'] = df['min'].shift() - df['min']

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

async def automated_trade():
    client = Quotex(username, password)

    if await client.connect():
        print("Conexión exitosa a Quotex")

        symbol = 'EUR/USD'

        # Obtener datos históricos
        df = await get_candles(client, symbol)
        if not df.empty:
            df = calculate_indicators(df)

            latest = df.iloc[-1]

            # Obtener precio en tiempo real
            real_time_price = await get_realtime_price(client, symbol)

            if real_time_price is not None:
                print(f"Precio en tiempo real del par {symbol}: {real_time_price}")

                # Ejemplo de decisión de trading basado en indicadores
                if latest['SMA50'] > latest['SMA200'] and latest['RSI'] > 30:
                    print("Señal de compra detectada.")
                    await client.sell_option(symbol,
                                             amount=10)  # Vender $10 de EUR/USD (Ajusta según el método correcto)
                elif latest['SMA50'] < latest['SMA200'] and latest['RSI'] < 70:
                    print("Señal de venta detectada.")
                    await client.sell_option(symbol,
                                             amount=10)  # Vender $10 de EUR/USD (Ajusta según el método correcto)
                else:
                    print("No hay señales de trading.")
            else:
                print("No se pudo obtener el precio en tiempo real.")
        else:
            print("No se pudieron obtener datos históricos.")
    else:
        print("Error al conectar a Quotex")


asyncio.run(automated_trade())

