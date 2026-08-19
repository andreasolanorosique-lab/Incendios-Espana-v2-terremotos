
"""
extraer_gasoductos.py
---------------------
Fase 1 del proyecto Incendios-Espana-v2

Este script:
  - Recorre todos los archivos .kmz de infraestructuras/gasoductos
  - Extrae todos los LineString (trazados)
  - Genera gasoductos.json

No modifica ningún otro archivo del proyecto.
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path("infraestructuras") / "gasoductos"
SALIDA = BASE / "gasoductos.json"

NS = {"kml": "http://www.opengis.net/kml/2.2"}

def leer_kmz(ruta):
    with zipfile.ZipFile(ruta, "r") as z:
        nombre_kml = next(
            (n for n in z.namelist() if n.lower().endswith(".kml")),
            None
        )
        if nombre_kml is None:
            return []

        xml = z.read(nombre_kml)
        raiz = ET.fromstring(xml)

        elementos = []

        for placemark in raiz.findall(".//kml:Placemark", NS):

            nombre = placemark.findtext("kml:name", default="Sin nombre", namespaces=NS)

            for linea in placemark.findall(".//kml:LineString", NS):

                coords = linea.findtext("kml:coordinates", default="", namespaces=NS)

                puntos = []

                for c in coords.strip().split():

                    partes = c.split(",")

                    if len(partes) >= 2:
                        lon = float(partes[0])
                        lat = float(partes[1])

                        puntos.append([lon, lat])

                if puntos:
                    elementos.append({
                        "nombre": nombre,
                        "origen": ruta.name,
                        "tipo": "gasoducto",
                        "coordenadas": puntos
                    })

        return elementos


def main():

    if not BASE.exists():
        print(f"No existe la carpeta: {BASE}")
        return

    resultado = []

    archivos = sorted(BASE.glob("*.kmz"))

    if not archivos:
        print("No se encontraron archivos KMZ.")
        return

    for archivo in archivos:
        print(f"Leyendo {archivo.name}...")
        datos = leer_kmz(archivo)
        print(f"   {len(datos)} trazados encontrados")
        resultado.extend(datos)

    for i, g in enumerate(resultado, start=1):
        g["id"] = i

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print()
    print("===================================")
    print(f"Gasoductos extraídos: {len(resultado)}")
    print(f"Archivo generado: {SALIDA}")
    print("===================================")


if __name__ == "__main__":
    main()
