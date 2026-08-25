#!/usr/bin/env python3.12
"""
future_manifest_decoder.py — Decodes the 2026-08-25 test manifest
Extracts and analyzes the pre-scheduled broken test harness.
"""
import struct, json, base64, re
from pathlib import Path

def extract_manifest(archive_path: str) -> dict:
    with open(archive_path, 'rb') as f:
        hdr = f.read(256)
        count = struct.unpack('<I', hdr[8:12])[0]
        data_off = struct.unpack('<Q', hdr[20:28])[0]
        f.seek(256)
        for i in range(count):
            pl = struct.unpack('<H', f.read(2))[0]
            path = f.read(pl).decode('utf-8', errors='replace')
            nchunks = struct.unpack('<I', f.read(4))[0]
            data = b''
            for _ in range(nchunks):
                coff = struct.unpack('<Q', f.read(8))[0]
                csz = struct.unpack('<Q', f.read(8))[0]
                pos = f.tell()
                f.seek(data_off + coff)
                data += f.read(csz)
                f.seek(pos)
            mode = struct.unpack('<I', f.read(4))[0]
            f.read(8); f.read(1)
            if path == 'day/20260825/skill_tests.json':
                return json.loads(data.decode('utf-8', errors='replace'))
    return {}

def analyze_websocket(val: str) -> dict:
    key_match = re.search(r'"key_sent": "([^"]+)"', val)
    expected_match = re.search(r'"ws_accept_expected": "([^"]+)"', val)
    return {
        "key_sent": key_match.group(1) if key_match else None,
        "key_bytes": base64.b64decode(key_match.group(1)).hex() if key_match else None,
        "expected": expected_match.group(1) if expected_match else None,
        "response_code": "404" if "404 Not Found" in val else "unknown",
    }

def main():
    manifest = extract_manifest("/mnt/agents/archivefs/dot-master.archivefs")
    report = {"file": "day/20260825/skill_tests.json", "components": {}}
    for key, val in manifest.items():
        if "websocket" in key:
            report["components"][key] = analyze_websocket(val)
        elif "Traceback" in val:
            report["components"][key] = {"status": "CRASHED", "traceback": val[:200]}
        elif "404" in val:
            report["components"][key] = {"status": "404_NOT_FOUND", "detail": val[:200]}
        elif "400" in val:
            report["components"][key] = {"status": "400_BAD_REQUEST", "detail": val[:200]}
        else:
            report["components"][key] = {"status": "OK", "detail": val[:200]}
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
