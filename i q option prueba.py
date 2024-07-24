import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from iqoptionapi.stable_api import IQ_Option

# Configuración de la conexión a la API de IQ Option
email = "sirem66@gmail.com"
password = "22520873Me"
API = IQ_Option(email, password)

try:
    API.connect()
except Exception as e:
    print("Error al conectar a la API:", e)

# Configuración del activo y el tamaño de la vela
activo = "EURUSD"  # Cambia a opciones digitales
tamaño_vela = 1  # En minutos

# Configuración del correo electrónico
email_sender = "sirem66@gmail.com"
email_receiver = "sirem66@gmail.com"
email_password = "kdxf kcbt guaj itgc"

def send_email(subject, message):
    # Configurar el servidor SMTP de Gmail
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_sender, email_password)

    # Crear el mensaje de correo electrónico
    msg = MIMEMultipart()
    msg["From"] = email_sender
    msg["To"] = email_receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    # Enviar el correo electrónico
    server.sendmail(email_sender, email_receiver, msg.as_string())
    server.quit()

# Función para obtener el precio actual del activo
def get_current_price():
    try:
        candles = API.get_candles(activo, tamaño_vela, count=1, endtime=time.time())
        if candles:
            return candles[0]["close"]
        else:
            return None
    except Exception as e:
        print("Error al obtener velas:", e)
        return None

def calculate_rsi(price_data, rsi_period=14):
    # Calcular las diferencias de precios
    deltas = [price_data[i]['close'] - price_data[i - 1]['close'] for i in range(1, len(price_data))]

    # Calcular las ganancias y pérdidas
    gains = [delta for delta in deltas if delta >= 0]
    losses = [-delta for delta in deltas if delta < 0]

    # Calcular el promedio de las ganancias y pérdidas
    avg_gain = sum(gains[:rsi_period]) / rsi_period
    avg_loss = sum(losses[:rsi_period]) / rsi_period

    # Calcular el RSI
    for i in range(rsi_period, len(price_data)):
        delta = deltas[i - 1]
        gain = delta if delta >= 0 else 0
        loss = -delta if delta < 0 else 0

        avg_gain = (avg_gain * (rsi_period - 1) + gain) / rsi_period
        avg_loss = (avg_loss * (rsi_period - 1) + loss) / rsi_period

    if avg_loss != 0:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    else:
        rsi = 100

    return rsi

def calculate_bollinger_bands(price_data, window_size=20):
    # Lista para almacenar los precios de cierre
    closes = [data['close'] for data in price_data]

    # Calcular la media móvil simple (SMA)
    sma = sum(closes) / len(closes)

    # Calcular la desviación estándar
    std_dev = (sum((close - sma) ** 2 for close in closes) / len(closes)) ** 0.5

    # Calcular las Bandas de Bollinger
    upper_band = sma + 2 * std_dev
    lower_band = sma - 2 * std_dev

    return upper_band, lower_band

def predict_next_candle_direction(price_data, rsi_period=14, window_size=20):
    # Calcular el RSI
    rsi = calculate_rsi(price_data, rsi_period)

    # Calcular las Bandas de Bollinger
    upper_band, lower_band = calculate_bollinger_bands(price_data, window_size)

    # Obtener el precio de cierre de la última vela
    last_close_price = price_data[-1]['close']

    # Verificar la dirección basada en los indicadores
    if last_close_price > upper_band and rsi > 70:
        return "alcista"
    elif last_close_price < lower_band and rsi < 30:
        return "bajista"
    else:
        return "no claro"

# Función para ejecutar la estrategia de trading
def run_strategy():
    while True:
        # Obtener el precio actual del activo
        precio_actual = get_current_price()

        if precio_actual:
            print("Precio actual:", precio_actual)

            # Obtener datos históricos de precios
            endtime = int(time.time())  # Obtener la marca de tiempo actual
            start_time = endtime - (60 * 100)  # Obtener el tiempo de inicio (100 velas hacia atrás)
            try:
                price_data = API.get_candles(activo, tamaño_vela, count=100, endtime=endtime)
            except Exception as e:
                print("Error al obtener datos históricos:", e)
                continue

            # Calcular el RSI (Índice de Fuerza Relativa)
            rsi = calculate_rsi(price_data)

            # Calcular las Bandas de Bollinger
            upper_band, lower_band = calculate_bollinger_bands(price_data)

            # Predecir la dirección de las próximas velas
            direction = predict_next_candle_direction(price_data)
            print("Dirección de las próximas velas:", direction)

            # Enviar correo electrónico con la información
            subject = f"Información de trading - {activo}"
            message = f"Precio actual: {precio_actual}\nRSI: {rsi}\nDirección: {direction}"
            send_email(subject, message)

        else:
            print("Error al obtener el precio actual")

        # Esperar 1 minuto antes de la próxima iteración
        time.sleep(60)

# Ejecutar la estrategia
run_strategy()
