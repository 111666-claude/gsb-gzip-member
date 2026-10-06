"""gzip 成员解析与索引。"""

import zlib

MAGIC = b"\x1f\x8b"

FHCRC = 0x02
FEXTRA = 0x04
FNAME = 0x08
FCOMMENT = 0x10


class Counter:
    """记录解析过的成员数。"""

    def __init__(self):
        self.scanned = 0


def _read_cstring(raw, off):
    end = raw.index(b"\x00", off)
    return raw[off:end], end + 1


def _header_len(raw, off, counter):
    if raw[off:off + 2] != MAGIC:
        raise ValueError("bad-magic")
    if off + 10 > len(raw):
        raise ValueError("short-header")
    if raw[off + 2] != 8:
        raise ValueError("bad-method")
    flg = raw[off + 3]
    pos = off + 10
    if flg & FEXTRA:
        if pos + 2 > len(raw):
            raise ValueError("short-extra")
        xlen = int.from_bytes(raw[pos:pos + 2], "little")
        pos += 2 + xlen
    name = ""
    if flg & FNAME:
        try:
            raw_name, pos = _read_cstring(raw, pos)
        except ValueError:
            raise ValueError("short-name")
        name = raw_name.decode("latin-1")
    if flg & FCOMMENT:
        try:
            _, pos = _read_cstring(raw, pos)
        except ValueError:
            raise ValueError("short-comment")
    if flg & FHCRC:
        pos += 2
    if pos > len(raw):
        raise ValueError("short-header")
    counter.scanned += 1
    return pos - off, name


class Index:
    def __init__(self, raw):
        self.raw = raw
        self.members = []

    def read(self, i, counter):
        counter.scanned += 1
        if 0 <= i < len(self.members):
            return self.members[i]["data"]
        return None


def open_members(raw, counter):
    index = Index(raw)
    off = 0
    while off + 18 <= len(raw):
        counter.scanned += 1
        try:
            hlen, name = _header_len(raw, off, counter)
        except ValueError:
            break
        start = off + hlen
        dec = zlib.decompressobj(-15)
        try:
            plain = dec.decompress(raw[start:])
        except zlib.error:
            break
        if not dec.eof:
            break
        consumed = len(raw) - start - len(dec.unused_data)
        trailer = start + consumed
        if trailer + 8 > len(raw):
            break
        crc = int.from_bytes(raw[trailer:trailer + 4], "little")
        isize = int.from_bytes(raw[trailer + 4:trailer + 8], "little")
        if crc != (zlib.crc32(plain) & 0xFFFFFFFF):
            break
        if isize != (len(plain) & 0xFFFFFFFF):
            break
        index.members.append({
            "offset": off,
            "size": len(plain),
            "name": name,
            "data": plain,
        })
        off = trailer + 8
    return index
