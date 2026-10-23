"""Publica la copia editorial preservando los demás miembros OOXML del DOCX.

Uso: python publicar_word_41.py copia_corregida.docx original.docx salida.docx
La salida sigue siendo borrador: no cierra campañas ni referencias bibliográficas.
"""
from copy import deepcopy
from pathlib import Path
import sys
from zipfile import ZipFile
from lxml import etree as E

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def tag(name):
    return "{" + W + "}" + name


def text(p):
    return "".join(p.xpath(".//w:t/text()", namespaces=NS))


def put(p, value):
    props = deepcopy(p.find(tag("pPr")))
    runprops = p.find(".//" + tag("rPr"))
    runprops = deepcopy(runprops) if runprops is not None else None
    p.clear()
    if props is not None:
        p.append(props)
    run = E.SubElement(p, tag("r"))
    if runprops is not None:
        run.append(runprops)
    E.SubElement(run, tag("t")).text = value


def main():
    source, original, output = map(Path, sys.argv[1:])
    assert output.parent.is_dir()
    with ZipFile(source) as z, ZipFile(original) as old:
        root = E.fromstring(z.read("word/document.xml"))
        previous = E.fromstring(old.read("word/document.xml"))
        body = root.find(tag("body"))
        ps = body.findall(tag("p"))
        ops = previous.find(tag("body")).findall(tag("p"))
        # Restaurar la explicación de Eq. 7 que la edición anterior duplicó.
        body.replace(ps[100], deepcopy(ops[100]))
        # La definición de latencias debe seguir a Eq. 8, no preceder la tabla 5.
        body.replace(ps[128], deepcopy(ops[116]))
        body.remove(ps[116])
        put(ps[74], "3.3.4 Escalado y entrenamiento")
        put(ps[8], (
            "Resumen: Se presenta CyberFlow, un sistema de código abierto para detectar anomalías de red y aplicar respuestas graduadas. "
            "El sensor observa tráfico IPv4 mediante un espejo SPAN y extrae 28 variables de red, transporte y aplicación. "
            "Combina un Isolation Forest congelado con cuatro heurísticos; las decisiones se distribuyen mediante un feed firmado "
            "y las restricciones temporales se aplican con nftables en el host protegido. En una evaluación reutilizada de 65 421 "
            "ventanas normales y 84 etiquetadas como ataque, el IF detectó 54/84, con precisión de 1,79 %, FPR de 4,53 %, "
            "ROC-AUC de 0,9247 y precisión media de 0,1858. Estos resultados describen el IF fuera de línea, no el desempeño "
            "del híbrido completo en operación. Se declaran el desbalance de clases, la incertidumbre de las etiquetas proxy y "
            "la necesidad de una prueba independiente."
        ))
        tables = body.findall(tag("tbl"))
        validation = tables[2].findall(tag("tr"))[4].findall(tag("tc"))[2]
        put(validation.find(tag("p")), "Calibrar el umbral; incluye 80 ventanas Kali, 17 con actividad observable y normalidad no verificada")
        row = tables[4].findall(tag("tr"))[2].findall(tag("tc"))
        put(row[1].find(tag("p")), "Ventanas de actividad etiquetadas por familia proxy observable")
        put(row[2].find(tag("p")), "65 505 ventanas; evaluación reutilizada, no test ciego independiente")
        put(row[3].find(tag("p")), "Precisión, recall, F1, FPR, ROC-AUC y AP")
        # Texto original de 3.6 restaurado; definición de episodio solo una vez.
        body.remove(ps[124])
        for p in body.findall(tag("p")):
            if text(p).startswith("La comparación por componentes utiliza"):
                put(p, "La comparación por componentes utiliza los mismos episodios para identificar el aporte del IF y de los heurísticos. "
                    "Un episodio se considera detectado cuando se registra al menos una señal durante su ejecución, asociada a actividad "
                    "etiquetada por familia proxy observable. Esta cobertura se presenta separada de la detección por ventana. "
                    "La comparación con Suricata requiere los mismos PCAP y declarar las reglas y el alcance de inspección.")
        # 4.1 ocupa una sección de una columna, necesaria para tabla y figura.
        first = next(p for p in body.findall(tag("p")) if text(p).startswith("4.1 Evaluación"))
        last = next(p for p in body.findall(tag("p")) if text(p).startswith("Como limitaciones,"))
        section = deepcopy(body.find(tag("sectPr")))
        section_type = section.find(tag("type"))
        if section_type is None:
            section_type = E.Element(tag("type"))
            section.insert(0, section_type)
        section_type.set(tag("val"), "continuous")
        boundary = E.Element(tag("p"))
        E.SubElement(boundary, tag("pPr")).append(deepcopy(section))
        body.insert(body.index(first), boundary)
        heading = E.Element(tag("p"))
        props = E.SubElement(heading, tag("pPr"))
        E.SubElement(props, tag("pStyle")).set(tag("val"), "Heading1")
        E.SubElement(E.SubElement(heading, tag("r")), tag("t")).text = "4. Resultados y discusión"
        body.insert(body.index(first), heading)
        section.find(tag("cols")).set(tag("num"), "1")
        last_props = last.find(tag("pPr"))
        if last_props is None:
            last_props = E.Element(tag("pPr"))
            last.insert(0, last_props)
        last_props.append(section)
        for table in tables[5:]:
            widths = [4800, 4800] if table is tables[5] else [2300, 1300] + [1000] * 6
            grid = table.find(tag("tblGrid"))
            for col, width in zip(grid, widths):
                col.set(tag("w"), str(width))
            table_rows = table.findall(tag("tr"))
            for row in table_rows:
                row_props = row.find(tag("trPr"))
                if row_props is None:
                    row_props = E.Element(tag("trPr"))
                    row.insert(0, row_props)
                E.SubElement(row_props, tag("cantSplit"))
                if row is table.findall(tag("tr"))[0]:
                    E.SubElement(row_props, tag("tblHeader"))
                for cell, width in zip(row.findall(tag("tc")), widths):
                    cell.find(tag("tcPr")).find(tag("tcW")).set(tag("w"), str(width))
                    if table is tables[6] and row is not table_rows[-1]:
                        for paragraph in cell.findall(tag("p")):
                            pp = paragraph.find(tag("pPr"))
                            if pp is None:
                                pp = E.Element(tag("pPr"))
                                paragraph.insert(0, pp)
                            E.SubElement(pp, tag("keepNext"))
            for p in table.xpath(".//w:p", namespaces=NS):
                for r in p.findall(tag("r")):
                    props = r.find(tag("rPr"))
                    if props is None:
                        props = E.Element(tag("rPr"))
                        r.insert(0, props)
                    size = props.find(tag("sz"))
                    if size is None:
                        size = E.SubElement(props, tag("sz"))
                    size.set(tag("val"), "18")
        for number, table in zip((6, 7), tables[5:]):
            caption = next(p for p in body.findall(tag("p")) if text(p).startswith(f"Tabla {number}."))
            props = caption.find(tag("pPr"))
            if props is None:
                props = E.Element(tag("pPr"))
                caption.insert(0, props)
            E.SubElement(props, tag("keepNext"))
            body.remove(caption)
            body.insert(body.index(table), caption)
        # Uniform/exact se conservan como filas con duplicación explícita.
        comparison = next(p for p in body.findall(tag("p")) if text(p).startswith("Los candidatos de laboratorio"))
        put(comparison, text(comparison) + " IF uniform e IF exact tienen idénticos scores: son nueve filas, pero ocho configuraciones distintas.")
        extra = E.Element(tag("p"))
        put(extra, "La sensibilidad de α se calculó con las 65 633 ventanas de validación originales; α = 0,05 reproduce el "
            "umbral operativo, sin demostrar que sea óptimo. En el test normal, las ventanas con paquetes recientes tuvieron "
            "2 837 falsos positivos entre 19 863 ventanas (14,28 %); las ventanas sin paquetes recientes pero con actividad "
            "retrospectiva tuvieron 124 entre 12 208 (1,02 %); las 33 350 restantes no tuvieron falsos positivos. El FPR global "
            "depende de esta composición. Offline se puntúan todas las ventanas; en vivo, las ventanas sin paquetes omiten el IF "
            "pero aún pueden activar heurísticos. Por ello, estos resultados no equivalen al FPR operativo del sistema completo.")
        body.insert(body.index(last), extra)
        xml = E.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        with ZipFile(output, "w") as dest:
            for item in z.infolist():
                dest.writestr(item, xml if item.filename == "word/document.xml" else z.read(item.filename))
    print(output)


if __name__ == "__main__":
    main()
