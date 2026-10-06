"""gzip 成员解析与索引。"""

import zlib

MAGIC = b"\x1f\x8b"
CM_DEFLATE = 8

FTEXT = 0x01
FHCRC = 0x02
FEXTRA = 0x04
FNAME = 0x08
FCOMMENT = 0x10


class Counter:
    """记录解析过的成员数。"""

    def __init__(self):
        self.scanned = 0


def _zero_terminated(raw, pos):
    end = raw.index(0, pos)
    return raw[pos:end], end + 1


def _parse_header(raw, off, counter):
    """按 FLG 跳过额外字段、原始文件名、注释与头校验，返回 (头长, 文件名)。"""
    if raw[off:off + 2] != MAGIC:
        raise ValueError("bad-magic")
    counter.scanned += 1
    if raw[off + 2] != CM_DEFLATE:
        raise ValueError("bad-method")
    flg = raw[off + 3]
    pos = off + 10
    if flg & FEXTRA:
        if pos + 2 > len(raw):
            raise ValueError("truncated-extra")
        xlen = int.from_bytes(raw[pos:pos + 2], "little")
        pos += 2 + xlen
    name = ""
    if flg & FNAME:
        field, pos = _zero_terminated(raw, pos)
        name = field.decode("latin-1")
    if flg & FCOMMENT:
        _, pos = _zero_terminated(raw, pos)
    if flg & FHCRC:
        pos += 2
    if pos > len(raw):
        raise ValueError("truncated-header")
    return pos - off, name


class Index:
    def __init__(self, raw):
        self.raw = raw
        self.members = []

    def read(self, i, counter):
        if 0 <= i < len(self.members):
            counter.scanned += 1
            return self.members[i]["data"]
        return None


def open_members(raw, counter):
    index = Index(raw)
    off = 0
    while off + 18 <= len(raw):
        counter.scanned += 1
        try:
            hlen, name = _parse_header(raw, off, counter)
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
