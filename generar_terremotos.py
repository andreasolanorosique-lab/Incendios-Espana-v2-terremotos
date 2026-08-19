import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, atan2, degrees, asin
import xml.etree.ElementTree as ET

URL = "https://www.ign.es/web/ign/portal/ultimos-terremotos/-/ultimos-terremotos/get10dias"

# Descargar datos del IGN
response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

ahora = datetime.now(timezone.utc)
limite = ahora - timedelta(hours=24)

terremotos = []
def crear_circulo(lat, lon, radio_m, pasos=48):
    radio_tierra = 6371000
    puntos = []

    lat1 = radians(lat)
    lon1 = radians(lon)

    for i in range(pasos + 1):
        angulo = radians(i * 360 / pasos)

        lat2 = asin(
            sin(lat1) * cos(radio_m / radio_tierra)
            + cos(lat1) * sin(radio_m / radio_tierra) * cos(angulo)
        )

        lon2 = lon1 + atan2(
            sin(angulo) * sin(radio_m / radio_tierra) * cos(lat1),
            cos(radio_m / radio_tierra) - sin(lat1) * sin(lat2)
        )

        puntos.append((degrees(lat2), degrees(lon2)))

    return puntos

# Buscar las filas de la tabla
for fila in soup.select("tr"):
    columnas = [
        td.get_text(" ", strip=True)
        for td in fila.find_all("td")
    ]

    # Una fila válida debe tener al menos los datos básicos
    if len(columnas) < 9:
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

        # La localización puede variar según la estructura
        localizacion = columnas[10] if len(columnas) > 10 else "Sin localización"

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
        print(
            "Error procesando fila:",
            columnas,
            e
        )
# Crear KML
kml = ET.Element(
    "kml",
    xmlns="http://www.opengis.net/kml/2.2"
)

document = ET.SubElement(kml, "Document")

nombre = ET.SubElement(document, "name")
nombre.text = "🌍 Terremotos España - Últimas 24 horas"


for t in terremotos:

    magnitud = t["magnitud"]

    radio_exterior = max(1200, magnitud * 1800)
    radio_interior = max(400, magnitud * 600)

    # ================================
    # HALO ROJO
    # ================================

    placemark_halo = ET.SubElement(
        document,
        "Placemark"
    )

    style_halo = ET.SubElement(
        placemark_halo,
        "Style"
    )

    line_halo = ET.SubElement(
        style_halo,
        "LineStyle"
    )

    ET.SubElement(
        line_halo,
        "color"
    ).text = "ff0000ff"

    ET.SubElement(
        line_halo,
        "width"
    ).text = "2"

    poly_halo = ET.SubElement(
        style_halo,
        "PolyStyle"
    )

    ET.SubElement(
        poly_halo,
        "color"
    ).text = "550000ff"

    polygon_halo = ET.SubElement(
        placemark_halo,
        "Polygon"
    )

    outer_halo = ET.SubElement(
        polygon_halo,
        "outerBoundaryIs"
    )

    ring_halo = ET.SubElement(
        outer_halo,
        "LinearRing"
    )

    coords_halo = ET.SubElement(
        ring_halo,
        "coordinates"
    )

    puntos_halo = crear_circulo(
        t["latitud"],
        t["longitud"],
        radio_exterior
    )

    coords_halo.text = " ".join(
        f"{lon},{lat},0"
        for lat, lon in puntos_halo
    )

    # ================================
    # CÍRCULO CENTRAL
    # ================================

    placemark = ET.SubElement(
        document,
        "Placemark"
    )

    name = ET.SubElement(
        placemark,
        "name"
    )

    name.text = f"M {magnitud} - {t['localizacion']}"

    fecha_es = t["fecha_hora"].strftime("%d/%m/%Y")
    hora_es = t["fecha_hora"].strftime("%H:%M:%S UTC")

    description = ET.SubElement(
        placemark,
        "description"
    )

    description.text = f"""
    <![CDATA[
    <h3>🌍 Terremoto</h3>
    <b>Magnitud:</b> {magnitud} {t['tipo_magnitud']}<br>
    <b>Profundidad:</b> {t['profundidad']} km<br>
    <b>Fecha:</b> {fecha_es}<br>
    <b>Hora:</b> {hora_es}<br>
    <b>Localización:</b> {t['localizacion']}<br>
    <b>Coordenadas:</b> {t['latitud']}, {t['longitud']}
    ]]>
    """

    style = ET.SubElement(
        placemark,
        "Style"
    )

    line = ET.SubElement(
        style,
        "LineStyle"
    )

    ET.SubElement(
        line,
        "color"
    ).text = "ff0000ff"

    ET.SubElement(
        line,
        "width"
    ).text = "3"

    poly = ET.SubElement(
        style,
        "PolyStyle"
    )

    ET.SubElement(
        poly,
        "color"
    ).text = "ffff0000"

    polygon = ET.SubElement(
        placemark,
        "Polygon"
    )

    outer = ET.SubElement(
        polygon,
        "outerBoundaryIs"
    )

    ring = ET.SubElement(
        outer,
        "LinearRing"
    )

    coords = ET.SubElement(
        ring,
        "coordinates"
    )

    puntos = crear_circulo(
        t["latitud"],
        t["longitud"],
        radio_interior
    )

    coords.text = " ".join(
        f"{lon},{lat},0"
        for lat, lon in puntos
    )
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
