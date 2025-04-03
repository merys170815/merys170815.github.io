import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import pandas as pd
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
    try:
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
    except Exception as e:
        print("Error al enviar correo:", e)

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

def calculate_ichimoku_cloud(price_data):
    high_prices = [data['max'] for data in price_data]
    low_prices = [data['min'] for data in price_data]

    tenkan_sen = (max(high_prices[-9:]) + min(low_prices[-9:])) / 2
    kijun_sen = (max(high_prices[-26:]) + min(low_prices[-26:])) / 2
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    senkou_span_b = (max(high_prices[-52:]) + min(low_prices[-52:])) / 2

    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

def calculate_momentum(price_data, period=10):
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

def predict_next_candle_direction(price_data):
    if len(price_data) < 52:  # Asegurarse de que hay suficientes datos para el cálculo de Ichimoku
        return "no claro"

    tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = calculate_ichimoku_cloud(price_data)
    momentum = calculate_momentum(price_data)
    stochastic = calculate_stochastic(price_data)

    if momentum is None or stochastic is None:
        return "no claro"

    last_close_price = price_data[-1]['close']

    if (last_close_price > senkou_span_a and last_close_price > senkou_span_b and
            momentum > 0 and stochastic > 80):
        return "alcista"
    elif (last_close_price < senkou_span_a and last_close_price < senkou_span_b and
          momentum < 0 and stochastic < 20):
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
        if not API.check_connect():
            try:
                API.connect()
            except Exception as e:
                print("Error al reconectar a la API:", e)
                continue

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
                send_email(subject, message)

        else:
            print("Error al obtener el precio actual")

# Ejecutar la estrategia
run_strategy()
