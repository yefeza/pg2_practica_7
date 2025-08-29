import zipfile, xml.etree.ElementTree as ET
from .utils import _seq_to_bytes_regex, _subseq_match

# ---- Opcional OLE2 ----
try:
    import olefile  # pip install olefile

    HAVE_OLE = True
except Exception:
    HAVE_OLE = False

# ====================== Firmas de contenedores (ContainerSignatureMapping) ======================


class _ContainerDB:
    def __init__(self, mapping_xml_path: str):
        t = ET.parse(mapping_xml_path)
        root = t.getroot()  # ContainerSignatureMapping
        self._csigs = (
            []
        )  # lista de dict: {id, type, files:[{path, bin_sigs:[{byte_sequences:[{reference, subseqs:[{min,max,regex,reference}]}]}]}]}
        self._id_to_puid = {}  # signatureId -> PUID
        self._puid_to_type = {}  # TriggerPuids: PUID -> ContainerType

        # ---- ContainerSignatures
        for cs in root.find("ContainerSignatures"):
            if cs.tag != "ContainerSignature":
                continue
            cid = cs.attrib["Id"]
            ctype = cs.attrib["ContainerType"]
            files_node = cs.find("Files")
            files = []
            if files_node is not None:
                for f in files_node:
                    if f.tag != "File":
                        continue
                    path = (f.findtext("Path") or "").strip()
                    bin_sigs = []
                    bs_node = f.find("BinarySignatures")
                    if bs_node is not None:
                        isc = bs_node.find("InternalSignatureCollection")
                        if isc is not None:
                            for ins in isc.findall("InternalSignature"):
                                bseqs = []
                                for bs in ins.findall("ByteSequence"):
                                    ref = bs.attrib.get("Reference", "BOFoffset")
                                    subseqs = []
                                    for sub in bs.findall("SubSequence"):
                                        min_off = int(
                                            sub.attrib.get("SubSeqMinOffset", 0)
                                        )
                                        max_off = int(
                                            sub.attrib.get("SubSeqMaxOffset", min_off)
                                        )
                                        seq_txt = sub.findtext("Sequence") or ""
                                        regex_bytes = _seq_to_bytes_regex(seq_txt)
                                        subseqs.append(
                                            {
                                                "min": min_off,
                                                "max": max_off,
                                                "regex": regex_bytes,
                                                "reference": ref,
                                            }
                                        )
                                    bseqs.append({"reference": ref, "subseqs": subseqs})
                                bin_sigs.append({"byte_sequences": bseqs})
                    files.append({"path": path, "bin_sigs": bin_sigs})
            self._csigs.append({"id": cid, "type": ctype, "files": files})

        # ---- FileFormatMappings
        ffm = root.find("FileFormatMappings")
        if ffm is not None:
            for m in ffm:
                sid = m.attrib["signatureId"]
                puid = m.attrib["Puid"]
                self._id_to_puid[sid] = puid

        # ---- TriggerPuids
        tr = root.find("TriggerPuids")
        if tr is not None:
            for tp in tr:
                self._puid_to_type[tp.attrib["Puid"]] = tp.attrib["ContainerType"]

    def is_trigger(self, base_puid: str) -> str | None:
        """Devuelve 'ZIP'/'OLE2' si el PUID base debe disparar análisis de contenedor."""
        return self._puid_to_type.get(base_puid)

    def _zip_match(self, file_path: str) -> list[str]:
        out = []
        with zipfile.ZipFile(file_path, "r") as zf:
            names = set(zf.namelist())
            for cs in self._csigs:
                if cs["type"] != "ZIP":
                    continue
                # 1) Todos los paths deben existir
                if any(f["path"] not in names for f in cs["files"]):
                    continue
                # 2) Para cada File con BinarySignatures, al menos una InternalSignature válida
                ok = True
                for f in cs["files"]:
                    if not f["bin_sigs"]:
                        continue
                    data = zf.read(f["path"])
                    file_ok = False
                    for ins in f["bin_sigs"]:
                        # AND de todos los ByteSequences; cada ByteSequence es AND de sus SubSequences
                        bs_all = True
                        for bs in ins["byte_sequences"]:
                            ref = bs["reference"]
                            sub_ok = True
                            for sub in bs["subseqs"]:
                                if not _subseq_match(
                                    data, sub["regex"], ref, sub["min"], sub["max"]
                                ):
                                    sub_ok = False
                                    break
                            if not sub_ok:
                                bs_all = False
                                break
                        if bs_all:
                            file_ok = True
                            break
                    if not file_ok:
                        ok = False
                        break
                if ok:
                    out.append(cs["id"])
        return out

    def _ole2_match(self, file_path: str) -> list[str]:
        if not HAVE_OLE:
            return []
        out = []
        if not olefile.isOleFile(file_path):
            return out
        with olefile.OleFileIO(file_path) as ole:
            # lista de streams/storages como "A/B/C"
            entries = {"/".join(e) for e in ole.listdir(streams=True, storages=True)}
            for cs in self._csigs:
                if cs["type"] != "OLE2":
                    continue
                # 1) Paths existen (en OLE2 son nombres de stream/storage)
                if any(
                    not any(f["path"] == e or f["path"] in e for e in entries)
                    for f in cs["files"]
                ):
                    continue
                # 2) Validar BinarySignatures si existen
                ok = True
                for f in cs["files"]:
                    if not f["bin_sigs"]:
                        continue
                    # buscar el stream que corresponda (exact o prefijo)
                    stream_name = None
                    for e in entries:
                        if e == f["path"] or f["path"] in e:
                            stream_name = e
                            break
                    if stream_name is None or not ole.exists(stream_name.split("/")):
                        ok = False
                        break
                    with ole.openstream(stream_name.split("/")) as st:
                        data = st.read()
                    file_ok = False
                    for ins in f["bin_sigs"]:
                        bs_all = True
                        for bs in ins["byte_sequences"]:
                            ref = bs["reference"]
                            sub_ok = True
                            for sub in bs["subseqs"]:
                                if not _subseq_match(
                                    data, sub["regex"], ref, sub["min"], sub["max"]
                                ):
                                    sub_ok = False
                                    break
                            if not sub_ok:
                                bs_all = False
                                break
                        if bs_all:
                            file_ok = True
                            break
                    if not file_ok:
                        ok = False
                        break
                if ok:
                    out.append(cs["id"])
        return out

    def refine(self, file_path: str, base_puid: str) -> list[str]:
        """Devuelve lista de PUIDs refinados (vía container signatures)."""
        ctype = self.is_trigger(base_puid)
        if not ctype:
            return []
        if ctype == "ZIP":
            sig_ids = self._zip_match(file_path)
        elif ctype == "OLE2":
            sig_ids = self._ole2_match(file_path)
        else:
            sig_ids = []
        # Mapear signatureId -> PUID
        return [self._id_to_puid[sid] for sid in sig_ids if sid in self._id_to_puid]
