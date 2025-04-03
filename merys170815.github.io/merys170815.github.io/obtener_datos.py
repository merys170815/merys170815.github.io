from binance.client import Client
import pandas as pd

# Configuración de la API de Binance
API_KEY = '5vWrP5bgXUpFa89KQBrJoTfAUUH8eZwccU7Q6CZcD4hrU7Rs9aqKf46bqBJTMRwU'
API_SECRET = 'ica2XnjMGd5HOgwWH4spFiSXZvn8ogukQHWbGUTpvt4I9z6wpQbtnM4YZISqhMNU'
client = Client(API_KEY, API_SECRET)

# Símbolo del par de trading (por ejemplo, BTCUSDT)
symbol = 'BTCUSDT'

# Intervalo de tiempo de las velas
interval = Client.KLINE_INTERVAL_15MINUTE

# Rango de fechas
start_date = '2023-04-01'
end_date = '2023-04-30'

# Obtener datos históricos
klines = client.get_historical_klines(symbol, interval, start_date, end_date)

# Crear un DataFrame de pandas con los datos
columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
df = pd.DataFrame(klines, columns=columns)

# Convertir la columna de timestamp a formato datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Guardar los datos en un archivo CSV
df.to_csv('datos_historicos_binance.csv', index=False)

print('Datos históricos guardados en datos_historicos_binance.csv')
