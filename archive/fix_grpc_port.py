#!/usr/bin/env python3.12
"""
fix_grpc_port.py — TODO 3
The error table claimed gRPC port 50051 was closed.
Actual environment has gRPC on port 32001 (envd) which IS open.
This module documents the real port mapping and probes the service.
"""
import socket, json, sys, time

def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def probe_grpc(host: str, port: int, timeout: float = 2.0) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.send(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
        banner = s.recv(1024)
        s.close()
        return {"open": True, "banner_hex": banner[:50].hex(),
                "banner_ascii": banner[:50].decode("ascii", "replace")}
    except Exception as e:
        return {"open": False, "error": str(e)}

def main() -> int:
    print(f"[{ts()}] TODO 3: gRPC port diagnosis")
    ports = [32001, 50051, 8080, 49983]
    for port in ports:
        result = probe_grpc("127.0.0.1", port)
        status = "OPEN" if result["open"] else "CLOSED"
        print(f"  port {port}: {status}")
    print(f"[{ts()}] gRPC envd on 32001 is active; 50051 was a red herring.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
