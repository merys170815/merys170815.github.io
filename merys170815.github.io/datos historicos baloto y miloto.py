import sqlite3
import csv

# Conectar a la base de datos (creará una nueva si no existe)
conn = sqlite3.connect('lottery_results.db')
cursor = conn.cursor()

# Crear una tabla para Baloto
cursor.execute('''
    CREATE TABLE IF NOT EXISTS baloto (
        id INTEGER PRIMARY KEY,
        fecha TEXT,
        numero1 INTEGER,
        numero2 INTEGER,
        numero3 INTEGER,
        numero4 INTEGER,
        numero5 INTEGER,
        superbalota INTEGER
    )
''')

# Ruta completa al archivo CSV de resultados de Baloto
csv_file_path = r'C:\ruta\a\tu\archivo\baloto_resultados.csv'

# Cargar datos desde el archivo CSV a la tabla
try:
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Saltar encabezados si existen
        for row in csvreader:
            cursor.execute('''
                INSERT INTO baloto (fecha, numero1, numero2, numero3, numero4, numero5, superbalota)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', row)

    # Guardar cambios y cerrar la conexión
    conn.commit()
    print("Datos de Baloto importados correctamente a la base de datos.")

except FileNotFoundError:
    print(f"No se encontró el archivo CSV en la ruta especificada: {csv_file_path}")

except Exception as e:
    print(f"Ocurrió un error durante la importación de datos: {str(e)}")

finally:
    conn.close()
