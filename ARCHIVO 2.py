import pandas as pd
import xml.etree.ElementTree as ET

# Ruta del archivo Excel
excel_file_path = 'C:/Users/Usuario/Desktop/9009122875822024FT001.xlsx'
# Ruta del archivo XML de salida
xml_file_path = 'C:/Users/Usuario/Desktop/9009122875822024FT001.XML'

# Leer el archivo Excel
df = pd.read_excel(excel_file_path)

# Crear la raíz del XML
root = ET.Element('FT001')

# Iterar sobre las filas del DataFrame y construir el XML
for index, row in df.iterrows():
    registro = ET.SubElement(root, 'RegistroFT001')

    # Añadir los elementos al registro
    codigo_concepto = ET.SubElement(registro, 'codigoConcepto')
    codigo_concepto.text = str(row['codigoConcepto'])

    clase_concepto = ET.SubElement(registro, 'claseConcepto')
    clase_concepto.text = str(row['claseConcepto'])

    valor = ET.SubElement(registro, 'valor')
    valor.text = str(row['valor'])

# Crear el árbol del XML
tree = ET.ElementTree(root)

# Guardar el archivo XML
tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

print(f"Archivo XML creado: {xml_file_path}")
