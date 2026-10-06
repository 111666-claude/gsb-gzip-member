"""固定场景，用来复现题面里的锚点。"""

import json
import zlib

from . import core


def _line(obj):
    print(json.dumps(obj, ensure_ascii=False))


def make_member(payload, name=None, crc=None, isize=None):
    flg = 0x08 if name else 0
    head = bytearray(b"\x1f\x8b\x08" + bytes([flg]))
    head += (0).to_bytes(4, "little")
    head += b"\x00\xff"
    if name:
        head += name.encode("latin-1") + b"\x00"
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    body = comp.compress(payload) + comp.flush()
    out = bytes(head) + body
    checksum = (zlib.crc32(payload) & 0xFFFFFFFF) if crc is None else crc
    length = (len(payload) & 0xFFFFFFFF) if isize is None else isize
    return out + checksum.to_bytes(4, "little") + length.to_bytes(4, "little")


def run(name):
    if name == "fname":
        raw = make_member(b"hello", name="a.txt")
        index = core.open_members(raw, core.Counter())
        _line({"name": index.members[0]["name"] if index.members else ""})
        return 0
    if name == "crc":
        raw = make_member(b"hello", crc=0)
        _line({"members": len(core.open_members(raw, core.Counter()).members)})
        return 0
    if name == "isize":
        raw = make_member(b"hello", isize=999)
        _line({"members": len(core.open_members(raw, core.Counter()).members)})
        return 0
    if name == "multi":
        raw = make_member(b"one") + make_member(b"two")
        _line({"members": len(core.open_members(raw, core.Counter()).members)})
        return 0
    if name == "work":
        raw = b"".join(make_member(b"x" * 10) for _ in range(300))
        index = core.open_members(raw, core.Counter())
        counter = core.Counter()
        for i in range(300):
            index.read(i, counter)
        _line({"members": 300, "scanned": counter.scanned})
        return 0
    raise SystemExit("未知场景：" + name)
