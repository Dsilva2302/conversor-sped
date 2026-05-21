"""Desktop entrypoint for the local SPED converter."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from app.api.main import app


HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _porta_em_uso() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((HOST, PORT)) == 0


def _abrir_navegador_quando_pronto() -> None:
    for _ in range(40):
        if _porta_em_uso():
            webbrowser.open(URL)
            return
        time.sleep(0.5)


def main() -> None:
    os.chdir(_base_dir())
    if _porta_em_uso():
        webbrowser.open(URL)
        return

    threading.Thread(target=_abrir_navegador_quando_pronto, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
