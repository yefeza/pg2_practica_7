import re

# ====================== Utilidades ======================


def _seq_to_bytes_regex(seq_text: str) -> bytes:
    """
    Convierte la sintaxis PRONOM de Sequence en un patrón regex de bytes.
    Soporta:
      - bytes hex:   "50 4B 03 04"
      - texto:       'Word.Document.'
      - rangos:      ['6'-'7']  o listas ['A''B''C']
    """
    s = seq_text or ""
    i = 0
    out = []
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "'":  # literal ASCII
            j = s.find("'", i + 1)
            if j == -1:
                raise ValueError("Secuencia con comilla sin cerrar")
            literal = s[i + 1 : j].encode("latin1")
            out.append(re.escape(literal))
            i = j + 1
            continue
        if ch == "[":  # clase / rango
            j = s.find("]", i + 1)
            if j == -1:
                raise ValueError("Secuencia con corchete sin cerrar")
            token = s[i + 1 : j]
            m = re.match(r"\s*'(.)'\s*-\s*'(.)'\s*", token)
            if m:  # rango 'a'-'b'
                lo = m.group(1).encode("latin1")
                hi = m.group(2).encode("latin1")
                out.append(b"[" + re.escape(lo) + b"-" + re.escape(hi) + b"]")
            else:
                chars = re.findall(r"'(.)'", token)
                if chars:
                    out.append(
                        b"["
                        + b"".join(re.escape(c.encode("latin1")) for c in chars)
                        + b"]"
                    )
                else:
                    # fallback (poco frecuente en container signatures)
                    out.append(b".")
            i = j + 1
            continue
        # byte hex
        m = re.match(r"[0-9A-Fa-f]{2}", s[i:])
        if m:
            out.append(bytes([int(s[i : i + 2], 16)]))
            i += 2
            continue
        # otro símbolo: ignorar
        i += 1
    return b"".join(out)


def _subseq_match(
    data: bytes, regex_bytes: bytes, reference: str, min_off: int, max_off: int
) -> bool:
    """
    Verifica si el patrón aparece con inicio dentro del rango (min_off..max_off),
    relativo a BOF o aproximado a EOF (la mayoría de container sigs usan BOF).
    """
    patt = re.compile(regex_bytes, flags=re.DOTALL)
    for m in patt.finditer(data):
        start = m.start()
        if reference.startswith("BOF"):
            if min_off <= start <= max_off:
                return True
        elif reference.startswith("EOF"):
            # Aproximación razonable para container sigs (poco usadas con EOF aquí):
            # offset desde el final al inicio del match.
            offset_from_eof = len(data) - start
            if min_off <= offset_from_eof <= max_off:
                return True
        else:  # ANY
            return True
    return False
