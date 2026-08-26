#!/usr/bin/env python3
"""ArchiveFS - monolithic archive format supporting binaries."""
import struct, os, json, hashlib
from pathlib import Path
from typing import Dict

MAGIC = b"ARFS\x01\x02"
VERSION = 1

class ArchiveFSEntry:
    def __init__(self, path: str, data: bytes, mode: int = 0o644, flags: int = 0):
        self.path = path
        self.data = data
        self.size = len(data)
        self.mode = mode
        self.flags = flags
        self.checksum = hashlib.sha256(data).digest()[:8]

    def to_dict(self):
        return {
            "path": self.path,
            "size": self.size,
            "mode": oct(self.mode),
            "flags": self.flags,
            "checksum": self.checksum.hex(),
        }

class ArchiveFS:
    def __init__(self):
        self.entries: Dict[str, ArchiveFSEntry] = {}

    def add_file(self, path: str, data: bytes, mode: int = 0o644, flags: int = 0):
        self.entries[path] = ArchiveFSEntry(path, data, mode, flags)

    def add_from_disk(self, filepath: Path, arcpath: str = None):
        arcpath = arcpath or str(filepath)
        data = filepath.read_bytes()
        mode = filepath.stat().st_mode
        flags = 0x01 if os.access(filepath, os.X_OK) else 0x00
        self.add_file(arcpath, data, mode, flags)

    def write(self, output: Path):
        index_bytes = b""
        data_bytes = b""
        current_offset = 0

        for entry in self.entries.values():
            path_b = entry.path.encode("utf-8")
            index_bytes += struct.pack("<H", len(path_b))
            index_bytes += path_b
            index_bytes += struct.pack("<Q", entry.size)
            index_bytes += struct.pack("<Q", current_offset)
            index_bytes += struct.pack("<I", entry.mode)
            index_bytes += entry.checksum
            index_bytes += struct.pack("<B", entry.flags)
            data_bytes += entry.data
            current_offset += entry.size

        header = MAGIC
        header += struct.pack("<H", VERSION)
        header += struct.pack("<I", len(self.entries))
        header += struct.pack("<Q", 256)
        header += struct.pack("<Q", 256 + len(index_bytes))
        header += struct.pack("<B", 0)
        header += b"\x00" * (256 - len(header))

        with open(output, "wb") as f:
            f.write(header)
            f.write(index_bytes)
            f.write(data_bytes)

        return output.stat().st_size

    @classmethod
    def read(cls, input_path: Path):
        ar = cls()
        with open(input_path, "rb") as f:
            header = f.read(256)
            if header[:6] != MAGIC:
                raise ValueError("Invalid ArchiveFS magic")

            entry_count = struct.unpack("<I", header[8:12])[0]
            index_offset = struct.unpack("<Q", header[12:20])[0]
            data_offset = struct.unpack("<Q", header[20:28])[0]

            f.seek(index_offset)
            for _ in range(entry_count):
                path_len = struct.unpack("<H", f.read(2))[0]
                path = f.read(path_len).decode("utf-8")
                size = struct.unpack("<Q", f.read(8))[0]
                offset = struct.unpack("<Q", f.read(8))[0]
                mode = struct.unpack("<I", f.read(4))[0]
                checksum = f.read(8)
                flags = struct.unpack("<B", f.read(1))[0]

                idx_pos = f.tell()
                f.seek(data_offset + offset)
                data = f.read(size)
                f.seek(idx_pos)

                ar.entries[path] = ArchiveFSEntry(path, data, mode, flags)

        return ar

    def extract(self, output_dir: Path):
        for entry in self.entries.values():
            out = output_dir / entry.path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(entry.data)
            os.chmod(out, entry.mode)
        return len(self.entries)

    def manifest(self) -> dict:
        return {
            "version": VERSION,
            "entries": [e.to_dict() for e in self.entries.values()],
            "total_size": sum(e.size for e in self.entries.values()),
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ArchiveFS tool")
    parser.add_argument("command", choices=["create", "extract", "manifest", "test"])
    parser.add_argument("--input", "-i", help="Input path")
    parser.add_argument("--output", "-o", help="Output path")
    parser.add_argument("--files", "-f", nargs="+", help="Files to add")
    args = parser.parse_args()

    if args.command == "create":
        ar = ArchiveFS()
        for f in args.files or []:
            fp = Path(f)
            if fp.exists():
                ar.add_from_disk(fp)
                print(f"Added: {f}")
        size = ar.write(Path(args.output))
        print(f"Archive created: {args.output} ({size} bytes)")

    elif args.command == "extract":
        ar = ArchiveFS.read(Path(args.input))
        count = ar.extract(Path(args.output))
        print(f"Extracted {count} files to {args.output}")

    elif args.command == "manifest":
        ar = ArchiveFS.read(Path(args.input))
        print(json.dumps(ar.manifest(), indent=2))

    elif args.command == "test":
        ar = ArchiveFS()
        ar.add_file("test.txt", b"Hello ArchiveFS")
        ar.add_file("bin/hello", b"#!/bin/bash\necho hello", 0o755, 0x01)
        ar.write(Path("/tmp/test.arfs"))
        ar2 = ArchiveFS.read(Path("/tmp/test.arfs"))
        assert ar2.entries["test.txt"].data == b"Hello ArchiveFS"
        print("Self-test passed")

if __name__ == "__main__":
    main()
