import requests

# Reemplaza 'your_api_key' con tu clave API de Quotex
API_KEY = '22520873Me'
BASE_URL = 'https://qxbroker.com/es'

headers = {
    'Authorization': f'Bearer {API_KEY}'
}

# Obtener información de la cuenta
response = requests.get(f'{BASE_URL}account', headers=headers)
if response.status_code == 200:
    account_info = response.json()
    print('Información de la Cuenta:', account_info)
else:
    print('Error al obtener la información de la cuenta:', response.text)

# Realizar una operación
trade_data = {
    'asset': 'EURUSD',    # El activo con el que deseas operar
    'amount': 100,        # Cantidad a invertir
    'direction': 'buy',   # Dirección de la operación ('buy' o 'sell')
    'duration': 60        # Duración de la operación en segundos
}

response = requests.post(f'{BASE_URL}trade', headers=headers, json=trade_data)
if response.status_code == 200:
    trade_result = response.json()
    print('Resultado de la Operación:', trade_result)
else:
    print('Error al realizar la operación:', response.text)

