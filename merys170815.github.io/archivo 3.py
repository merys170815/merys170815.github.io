import xml.etree.ElementTree as ET
import pandas as pd

# Leer el archivo Excel
archivo_excel = "C:/Users/Usuario/Desktop/9009122875402024.xlsx"
df = pd.read_excel(archivo_excel)

# Crear la estructura XML
root = ET.Element("GT004")

# Iterar sobre las filas del DataFrame y crear elementos XML
for _, row in df.iterrows():
    registro = ET.SubElement(root, "RegistroGT004")

    ET.SubElement(registro, "nombreAsociacion").text = str(row.get("Nombre de la Asociación", ""))
    ET.SubElement(registro, "nivelTerritorial").text = str(row.get("Nivel Territorial", ""))
    ET.SubElement(registro, "municipio").text = str(row.get("Municipio", ""))
    ET.SubElement(registro, "fechaConvocatoria").text = str(row.get("Fecha de Convocatoria", ""))
    ET.SubElement(registro, "fechaConformacion").text = str(row.get("Fecha de Conformación", ""))
    ET.SubElement(registro, "nombreContactoEntidad").text = str(row.get("Nombre del Contacto de la Entidad", ""))
    ET.SubElement(registro, "telefonoContactoEntidad").text = str(row.get("Teléfono del Contacto de la Entidad", ""))
    ET.SubElement(registro, "correoContactoEntidad").text = str(row.get("Correo del Contacto de la Entidad", ""))
    ET.SubElement(registro, "nombreContactoAlianza").text = str(
        row.get("Nombre del Contacto de la Alianza", "[No aplica]"))
    ET.SubElement(registro, "telefonoContactoAlianza").text = str(
        row.get("Teléfono del Contacto de la Alianza", "[No aplica]"))
    ET.SubElement(registro, "correoContactoAlianza").text = str(
        row.get("Correo del Contacto de la Alianza", "[No aplica]"))
    ET.SubElement(registro, "linkPagina").text = str(row.get("Link de la Página", "[No aplica]"))

# Crear el archivo XML
nombre_archivo_xml = "C:/Users/Usuario/Desktop/9009122875402024GT004.xml"
tree = ET.ElementTree(root)
tree.write(nombre_archivo_xml, encoding="UTF-8", xml_declaration=True)
