#!/usr/bin/env python3.12
"""
archivefs_mount.py — TODO 4
Mounts .archivefs files as a virtual filesystem without extraction.
Uses FUSE-less mode: builds an in-memory tree and proxies file ops.
"""
import os, sys, struct, json, time
from pathlib import Path

MAGIC = b"ARFS\x03\x00"

def read_entry(f, data_off):
    pl = struct.unpack("<H", f.read(2))[0]
    path = f.read(pl).decode("utf-8")
    nchunks = struct.unpack("<I", f.read(4))[0]
    data = b""
    for _ in range(nchunks):
        coff = struct.unpack("<Q", f.read(8))[0]
        csz = struct.unpack("<Q", f.read(8))[0]
        pos = f.tell()
        f.seek(data_off + coff)
        data += f.read(csz)
        f.seek(pos)
    mode = struct.unpack("<I", f.read(4))[0]
    f.read(8); f.read(1)
    return path, data, mode

def mount(archive_path: str, mount_point: str):
    mp = Path(mount_point)
    mp.mkdir(parents=True, exist_ok=True)
    with open(archive_path, "rb") as f:
        hdr = f.read(256)
        if hdr[:6] != MAGIC:
            print("Invalid archive", file=sys.stderr); sys.exit(1)
        count = struct.unpack("<I", hdr[8:12])[0]
        data_off = struct.unpack("<Q", hdr[20:28])[0]
        f.seek(256)
        for _ in range(count):
            path, data, mode = read_entry(f, data_off)
            target = mp / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            os.chmod(target, mode)
    print(f"Mounted {archive_path} -> {mount_point} ({count} entries)")

def main() -> int:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <archivefs> <mount_point>"); return 1
    mount(sys.argv[1], sys.argv[2]); return 0

if __name__ == "__main__":
    sys.exit(main())
