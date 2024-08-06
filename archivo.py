import pandas as pd
import xml.etree.ElementTree as ET
import os
import subprocess

# Obtener la ruta del escritorio
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Ruta completa al archivo Excel
excel_file_path = os.path.join(desktop_path, '9009122875802024GT010.xlsx')

# Imprimir la ruta del archivo para depuración
print(f"Ruta del archivo Excel: {excel_file_path}")

# Leer el archivo de Excel especificando el motor openpyxl
try:
    df = pd.read_excel(excel_file_path, engine='openpyxl')
    print("Archivo leído correctamente.")
except FileNotFoundError:
    print("El archivo no se encuentra en la ubicación especificada.")
    df = None
except Exception as e:
    print(f"Ocurrió un error al leer el archivo: {e}")
    df = None

# Verificar si el DataFrame se ha cargado correctamente
if df is not None:
    # Crear el árbol XML
    root = ET.Element('GT010')

    for index, row in df.iterrows():
        registro = ET.SubElement(root, 'RegistroGT010')
        tipoReporte = ET.SubElement(registro, 'tipoReporte')
        tipoReporte.text = str(row['tipoReporte'])

        tipoIdAportante = ET.SubElement(registro, 'tipoIdAportante')
        tipoIdAportante.text = str(row['tipoIdAportante'])

        idAportante = ET.SubElement(registro, 'idAportante')
        idAportante.text = str(row['idAportante'])

        dvAportante = ET.SubElement(registro, 'dvAportante')
        dvAportante.text = str(row['dvAportante'])

        nombreAportante = ET.SubElement(registro, 'nombreAportante')
        nombreAportante.text = str(row['nombreAportante'])

        codigoMunicipio = ET.SubElement(registro, 'codigoMunicipio')
        codigoMunicipio.text = str(row['codigoMunicipio'])

        valor = ET.SubElement(registro, 'valor')
        valor.text = str(row['valor'])

    # Guardar el archivo XML en el escritorio con el nombre específico
    xml_file_path = os.path.join(desktop_path, '9009122875802024GT010.XML')
    tree = ET.ElementTree(root)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

    print(f"El archivo XML se ha guardado en: {xml_file_path}")

    # Firmar el archivo XML con OpenSSL
    signature_file_path = os.path.join(desktop_path, 'signature.bin')
    private_key_path = os.path.join(desktop_path, 'openssl-3.3.1', 'private_key.pem')

    try:
        # Ejecutar el comando OpenSSL para firmar el archivo XML
        result = subprocess.run([
            'openssl', 'dgst', '-sha256', '-sign', private_key_path,
            '-out', signature_file_path, xml_file_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f"El archivo XML ha sido firmado correctamente. La firma se guarda en: {signature_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ocurrió un error al firmar el archivo XML: {e}")
        print(f"Salida del error: {e.stderr.decode()}")
else:
    print("No se pudo procesar el archivo XML porque el DataFrame está vacío.")
