import re, binascii

# ====================== Firmas binarias (DROID_SignatureFile) ======================


class _PRONOMSignature:
    def __init__(self, sig_id, sequences):
        self.sig_id = sig_id
        self.sequences = sequences  # lista de dicts: {location, pattern(bytes hex COMO TEXTO), min_offset, max_offset}

    def match(self, data_start: bytes, data_end: bytes) -> bool:
        # Motor minimalista: hex puro y BOF/EOF/ANY; suficiente para muchos casos.
        for seq in self.sequences:
            # En firmas binarias, el <Sequence> suele ser hex puro.
            try:
                hex_bytes = binascii.unhexlify(re.sub(r"\s+", "", seq["pattern"]))
            except binascii.Error:
                # Si aparece algo raro (muy raro en binario), fallamos esta firma
                return False

            min_off = seq.get("min_offset", 0)
            max_off = seq.get("max_offset", 0)
            loc = seq["location"]

            if loc == "BOF":
                found = False
                limit = min(len(data_start), max_off + 1)
                for off in range(min_off, max(0, limit - len(hex_bytes) + 1)):
                    if data_start[off : off + len(hex_bytes)] == hex_bytes:
                        found = True
                        break
                if not found:
                    return False

            elif loc == "EOF":
                found = False
                # Buscar desde cola; offsets cuentan desde el final
                for off in range(min_off, max_off + 1):
                    start = len(data_end) - off - len(hex_bytes)
                    if (
                        start >= 0
                        and data_end[start : start + len(hex_bytes)] == hex_bytes
                    ):
                        found = True
                        break
                if not found:
                    return False

            else:  # ANY
                if hex_bytes not in data_start and hex_bytes not in data_end:
                    return False
        return True
