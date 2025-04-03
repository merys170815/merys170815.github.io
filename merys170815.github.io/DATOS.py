import ccxt
import pandas as pd

# Configurar el intercambio (exchange)
exchange = ccxt.binance()

# Símbolos de las criptomonedas que deseas obtener datos
symbols = ['BTC/USDT', 'ETH/USDT']  # Por ejemplo, BTC/USDT para Bitcoin y ETH/USDT para Ethereum

# Obtener datos financieros reales para cada símbolo
for symbol in symbols:
    # Obtener datos OHLCV (Open, High, Low, Close, Volume) para el símbolo
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', since=None, limit=1000)

    # Convertir los datos a un DataFrame de pandas
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Convertir el timestamp a formato de fecha
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

    # Renombrar la columna 'closing_prices' como 'Close'
    df.rename(columns={'closing_prices': 'Close'}, inplace=True)

    # Guardar los datos en un archivo CSV
    filename = 'datos_financieros.csv'
    df.to_csv(filename, index=False)

    print(f"Datos financieros reales para {symbol} guardados exitosamente en '{filename}'")
