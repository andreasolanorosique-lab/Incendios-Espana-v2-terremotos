import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

URL = "https://www.ign.es/web/ign/portal/ultimos-terremotos/-/ultimos-terremotos/get10dias"

# Descargar datos del IGN
response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

ahora = datetime.now(timezone.utc)
limite = ahora - timedelta(hours=24)

terremotos = []

# Buscar las filas de la tabla
for fila in soup.select("table tbody tr"):
    columnas = [td.get_text(" ", strip=True) for td in fila.find_all("td")]

    if len(columnas) < 11:
        continue

    try:
        evento = columnas[0]
        fecha = columnas[1]
        hora = columnas[2]

        latitud = float(columnas[4].replace(",", "."))
        longitud = float(columnas[5].replace(",", "."))
        profundidad = float(columnas[6].replace(",", "."))
        magnitud = float(columnas[7].replace(",", "."))
        tipo_magnitud = columnas[8]
        localizacion = columnas[10]

        fecha_hora = datetime.strptime(
            f"{fecha} {hora}",
            "%d/%m/%Y %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        # Solo últimas 24 horas
        if fecha_hora >= limite:
            terremotos.append({
                "evento": evento,
                "fecha_hora": fecha_hora,
                "latitud": latitud,
                "longitud": longitud,
                "profundidad": profundidad,
                "magnitud": magnitud,
                "tipo_magnitud": tipo_magnitud,
                "localizacion": localizacion
            })

    except Exception as e:
        print("Error procesando fila:", e)


# Crear KML
kml = ET.Element(
    "kml",
    xmlns="http://www.opengis.net/kml/2.2"
)

document = ET.SubElement(kml, "Document")

nombre = ET.SubElement(document, "name")
nombre.text = "🌍 Terremotos España - Últimas 24 horas"

# Estilo del marcador
style = ET.SubElement(document, "Style", id="terremoto")

icon_style = ET.SubElement(style, "IconStyle")

scale = ET.SubElement(icon_style, "scale")
scale.text = "1.2"

icon = ET.SubElement(icon_style, "Icon")

href = ET.SubElement(icon, "href")
href.text = "http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png"


for t in terremotos:

    placemark = ET.SubElement(document, "Placemark")

    name = ET.SubElement(placemark, "name")
    name.text = f"M {t['magnitud']} - {t['localizacion']}"

    style_url = ET.SubElement(placemark, "styleUrl")
    style_url.text = "#terremoto"

    description = ET.SubElement(placemark, "description")

    fecha_es = t["fecha_hora"].strftime("%d/%m/%Y")
    hora_es = t["fecha_hora"].strftime("%H:%M:%S UTC")

    description.text = f"""
    <![CDATA[
    <h3>🌍 Terremoto</h3>
    <b>Magnitud:</b> {t['magnitud']} {t['tipo_magnitud']}<br>
    <b>Profundidad:</b> {t['profundidad']} km<br>
    <b>Fecha:</b> {fecha_es}<br>
    <b>Hora:</b> {hora_es}<br>
    <b>Localización:</b> {t['localizacion']}<br>
    <b>Coordenadas:</b> {t['latitud']}, {t['longitud']}
    ]]>
    """

    point = ET.SubElement(placemark, "Point")

    coordinates = ET.SubElement(point, "coordinates")
    coordinates.text = f"{t['longitud']},{t['latitud']},0"


# Guardar archivo
tree = ET.ElementTree(kml)

ET.indent(tree, space="  ")

tree.write(
    "terremotos_actual.kml",
    encoding="utf-8",
    xml_declaration=True
)

print(f"Terremotos encontrados en las últimas 24 horas: {len(terremotos)}")
print("Archivo generado: terremotos_actual.kml")
