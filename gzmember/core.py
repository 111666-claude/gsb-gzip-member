"""gzip 成员解析与索引。"""

import zlib

MAGIC = b"\x1f\x8b"


class Counter:
    """记录解析过的成员数。"""

    def __init__(self):
        self.scanned = 0


def _header_len(raw, off, counter):
    if raw[off:off + 2] != MAGIC:
        raise ValueError("bad-magic")
    counter.scanned += 1
    return 10, ""


class Index:
    def __init__(self, raw):
        self.raw = raw
        self.members = []

    def read(self, i, counter):
        members = open_members(self.raw, counter).members
        if 0 <= i < len(members):
            return members[i]["data"]
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
        index.members.append({
            "offset": off,
            "size": len(plain),
            "name": name,
            "data": plain,
        })
        off = trailer + 8
    return index
