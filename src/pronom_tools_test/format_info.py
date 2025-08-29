import os, xml.etree.ElementTree as ET
from .containers import _ContainerDB
from .single_signature import _PRONOMSignature

# ====================== Colector principal ======================


class FormatInfoCollector:
    def __init__(self, signature_xml: str, container_xml: str | None = None):
        self.signatures = self._load_signatures(signature_xml)
        self.formats = self._load_formats(signature_xml)
        self.sig_to_formats = self._build_mapping()
        self.container_db = _ContainerDB(container_xml) if container_xml else None

    # ---- Firmas binarias
    def _load_signatures(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {"p": "http://www.nationalarchives.gov.uk/pronom/SignatureFile"}
        signatures = []
        for sig in root.findall(".//p:InternalSignature", ns):
            sig_id = sig.attrib["ID"]
            seqs = []
            for bs in sig.findall(".//p:ByteSequence", ns):
                location = bs.attrib.get("Reference", "BOFoffset")
                for subseq in bs.findall("p:SubSequence", ns):
                    pattern = (subseq.find("p:Sequence", ns).text or "").strip()
                    min_off = int(subseq.attrib.get("SubSeqMinOffset", 0))
                    max_off = int(subseq.attrib.get("SubSeqMaxOffset", min_off))
                    if location.startswith("BOF"):
                        loc = "BOF"
                    elif location.startswith("EOF"):
                        loc = "EOF"
                    else:
                        loc = "ANY"
                    seqs.append(
                        {
                            "location": loc,
                            "pattern": pattern,
                            "min_offset": min_off,
                            "max_offset": max_off,
                        }
                    )
            signatures.append(_PRONOMSignature(sig_id, seqs))
        return signatures

    def _load_formats(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {"p": "http://www.nationalarchives.gov.uk/pronom/SignatureFile"}
        formats = []
        for ff in root.findall(".//p:FileFormat", ns):
            fmt_id = ff.attrib.get("ID")
            name = ff.attrib.get("Name")
            puid = ff.attrib.get("PUID")
            mime = ff.attrib.get("MIMEType")
            internal_ids = [n.text for n in ff.findall("p:InternalSignatureID", ns)]
            extensions = [n.text for n in ff.findall("p:Extension", ns)]
            formats.append(
                {
                    "id": fmt_id,
                    "name": name,
                    "puid": puid,
                    "mime": mime,
                    "extensions": extensions,
                    "internal_ids": internal_ids,
                }
            )
        return formats

    def _build_mapping(self):
        mapping = {}
        for fmt in self.formats:
            for sig_id in fmt["internal_ids"]:
                mapping.setdefault(sig_id, []).append(fmt)
        return mapping

    # ---- Identificación principal
    def identify_file(self, file_path: str):
        # leer head/tail con seguridad en archivos pequeños
        fsize = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            head = f.read(min(65536, fsize))
            if fsize > 65536:
                f.seek(-65536, os.SEEK_END)
                tail = f.read()
            else:
                f.seek(0)
                tail = f.read()

        for sig in self.signatures:
            if sig.match(head, tail):
                base_formats = self.sig_to_formats.get(sig.sig_id, [])
                results = []
                refined_results = []
                for fmt in base_formats:
                    results.append(fmt)
                    # Refinar con contenedores si procede
                    if self.container_db and fmt["puid"]:
                        refined_puids = self.container_db.refine(file_path, fmt["puid"])
                        for puid in refined_puids:
                            rf = next(
                                (x for x in self.formats if x["puid"] == puid), None
                            )
                            if rf and rf not in refined_results:
                                refined_results.append(rf)
                main_format = None
                if len(refined_results) > 0:
                    main_format = refined_results[0]
                elif len(results) > 0:
                    main_format = results[0]
                return {
                    "signature_id": sig.sig_id,
                    "main_format": main_format,
                    "base_formats": results,
                    "container_formats": refined_results,
                }
        return None

    # ---- Agrupar formatos por la primera parte del mime type
    def _get_mime_type_info(self, mime_type: str) -> str:
        """Convierte un mime type a una categoría legible."""
        MIME_INFO = {
            "application": {
                "human": "Aplicación",
                "description": (
                    "Incluye formatos de uso general que no encajan en otras categorías. "
                    "Aquí están documentos de oficina (Word, Excel, PDF), paquetes comprimidos (ZIP, RAR), "
                    "archivos ejecutables, bibliotecas, scripts y otros tipos que requieren un programa específico para abrirse."
                ),
            },
            "text": {
                "human": "Texto",
                "description": (
                    "Formatos basados en caracteres legibles o estructurados como texto. "
                    "Incluye TXT, HTML, XML, JSON, CSV, scripts de programación y otros lenguajes basados en texto plano."
                ),
            },
            "image": {
                "human": "Imagen",
                "description": (
                    "Archivos gráficos estáticos, como fotografías y diagramas. "
                    "Incluye formatos comunes (JPEG, PNG, GIF, BMP, TIFF) y especializados para impresión o edición (SVG, PSD)."
                ),
            },
            "audio": {
                "human": "Audio",
                "description": (
                    "Archivos de sonido digital. "
                    "Incluye formatos comprimidos (MP3, AAC, OGG, WMA) y sin compresión (WAV, FLAC, AIFF)."
                ),
            },
            "video": {
                "human": "Video",
                "description": (
                    "Formatos de imagen en movimiento, con o sin audio. "
                    "Incluye contenedores multimedia (MP4, AVI, MKV, MOV) y flujos de vídeo para transmisión."
                ),
            },
            "model": {
                "human": "Modelo 3D",
                "description": (
                    "Archivos que representan modelos tridimensionales o estructuras matemáticas. "
                    "Incluye formatos como STL, OBJ, 3MF y X3D, usados en gráficos, animación y manufactura aditiva (impresión 3D)."
                ),
            },
            "multipart": {
                "human": "Multiparte",
                "description": (
                    "Agrupa varios archivos o partes en un mismo mensaje o contenedor. "
                    "Usado principalmente en correos electrónicos (MIME multipart/alternative, multipart/mixed) "
                    "y protocolos web para enviar datos combinados."
                ),
            },
            "font": {
                "human": "Fuente tipográfica",
                "description": (
                    "Archivos que contienen tipografías digitales. "
                    "Incluye TrueType (TTF), OpenType (OTF), WOFF/WOFF2 para la web y Type 1 PostScript."
                ),
            },
            "message": {
                "human": "Mensaje",
                "description": (
                    "Formatos que representan mensajes electrónicos. "
                    "Incluye correos electrónicos completos (message/rfc822), "
                    "respuestas automáticas y encapsulados de protocolos de mensajería."
                ),
            },
            "chemical": {
                "human": "Químico",
                "description": (
                    "Archivos especializados para representar datos químicos o biomoleculares. "
                    "Incluye formatos como CML (Chemical Markup Language) o PDB (Protein Data Bank). "
                    "Se usan en investigación científica y bioinformática."
                ),
            },
        }
        return MIME_INFO.get(
            mime_type,
            {"human": "Otros", "description": "Otros formatos no categorizados."},
        )

    # ---- Agrupar formatos por mime type
    def group_formats_by_mime(self):
        mime_groups = {}
        for fmt in self.formats:
            if fmt["mime"]:
                mime_type = fmt["mime"].split("/")[0]
                mime_type = mime_type.strip().lower()
                if mime_type not in mime_groups:
                    mime_groups[mime_type] = []
                mime_groups[mime_type].append(fmt)
            else:
                if "others" not in mime_groups:
                    mime_groups["others"] = []
                mime_groups["others"].append(fmt)
        parsed_mime_groups = []
        for mime_type, formats in mime_groups.items():
            mime_info = self._get_mime_type_info(mime_type)
            parsed_mime_groups.append(
                {
                    "mime_type": mime_type,
                    "human_mime_type": mime_info["human"],
                    "description": mime_info["description"],
                    "human_mime_type": mime_type.replace("_", " ").title(),
                    "formatos": [
                        {
                            "puid": fmt["puid"],
                            "name": fmt["name"],
                            "mime": fmt["mime"],
                            "extensions": fmt["extensions"],
                        }
                        for fmt in formats
                    ],
                }
            )
        sorted_mime_groups = sorted(
            parsed_mime_groups, key=lambda x: x["human_mime_type"]
        )
        return sorted_mime_groups

    # ---- Obtener formato por PUID
    def get_format_by_puid(self, puid: str):
        return next((f for f in self.formats if f["puid"] == puid), None)
