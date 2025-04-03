import csv
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta

# Configuración de la conexión a la API de IQ Option
email = "sirem66@gmail.com"
password = "22520873Me"
API = IQ_Option(email, password)
API.connect()

# Configuración del activo y el tamaño de la vela
activo = "EURUSD-OTC"  # Cambia a opciones digitales
tamaño_vela = 1  # En minutos

# Función para obtener los datos históricos de precios y guardarlos en un archivo CSV
def download_historical_data(asset, timeframe, start_date, end_date, filename):
    # Convertir las fechas a marcas de tiempo
    start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())

    # Obtener las velas históricas
    candles = API.get_candles(asset, timeframe, start_timestamp, end_timestamp)

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'open', 'close', 'high', 'low', 'volume']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for candle in candles:
            writer.writerow({
                'timestamp': candle['from'],
                'open': candle['open'],
                'close': candle['close'],
                'high': candle['max'],
                'low': candle['min'],
                'volume': candle['volume']
            })

# Definir la fecha de inicio (hace un año) y la fecha actual
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

# Descargar datos históricos de precios y guardarlos en un archivo CSV
download_historical_data(activo, tamaño_vela, start_date, end_date, 'historical_data.csv')
