import asyncio
import pandas as pd
from pyquotex.quotexapi.stable_api import Quotex
import time

# Define tus credenciales
username = "capsaludsas@gmail.com"
password = "22520873Me"

async def get_candles(client, symbol, period=1, end_from_time=None, offset=0):
    try:
        # Obtener datos históricos de velas
        data = await client.get_candles(symbol, period, end_from_time=end_from_time, offset=offset)
        print("Respuesta cruda de get_candles:", data)  # Imprime la respuesta cruda
        if data and 'data' in data:
            df = pd.DataFrame(data['data'])
            print("Datos de velas obtenidos:", df)  # Imprime los datos para depuración
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

def calculate_indicators(df):
    df['SMA50'] = df['close'].rolling(window=50).mean()
    df['SMA200'] = df['close'].rolling(window=200).mean()
    df['RSI'] = 100 - (100 / (1 + (df['close'].diff(1).clip(lower=0).rolling(window=14).mean() /
                                   df['close'].diff(1).clip(upper=0).rolling(window=14).mean())))
    return df

async def automated_trade():
    client = Quotex(username, password)

    if await client.connect():
        print("Conexión exitosa a Quotex")

        symbol = 'EUR/USD'

        # Obtener datos históricos
        end_from_time = int(time.time())  # Tiempo actual en segundos desde epoch
        df = await get_candles(client, symbol, period=1, end_from_time=end_from_time, offset=0)
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
                    await client.sell_option(symbol, amount=10)  # Vender $10 de EUR/USD (Ajusta según el método correcto)
                elif latest['SMA50'] < latest['SMA200'] and latest['RSI'] < 70:
                    print("Señal de venta detectada.")
                    await client.sell_option(symbol, amount=10)  # Vender $10 de EUR/USD (Ajusta según el método correcto)
                else:
                    print("No hay señales de trading.")
            else:
                print("No se pudo obtener el precio en tiempo real.")
        else:
            print("No se pudieron obtener datos históricos.")
    else:
        print("Error al conectar a Quotex")

# Ejecutar la estrategia
asyncio.run(automated_trade())
