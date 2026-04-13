#!/usr/bin/env python3
"""Salvar uma imagem de URL ou base64 para images/avatar.png

Uso:
  python save_avatar.py --url https://example.com/img.jpg
  python save_avatar.py --base64 "<base64string>"
  python save_avatar.py --base64-file arquivo.txt
"""

import os
import sys
import argparse
import base64
import urllib.request


def save_bytes(data: bytes, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    print("Salvo:", out_path)


def from_url(url: str, out: str):
    try:
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        save_bytes(data, out)
    except Exception as e:
        print("Erro ao baixar URL:", e)
        sys.exit(2)


def from_base64_string(s: str, out: str):
    try:
        # Accept data URLs like data:image/png;base64,AAAA
        if s.startswith("data:") and "," in s:
            s = s.split(",", 1)[1]
        data = base64.b64decode(s)
        save_bytes(data, out)
    except Exception as e:
        print("Erro ao decodificar base64:", e)
        sys.exit(3)


def from_base64_file(path: str, out: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            s = f.read().strip()
        from_base64_string(s, out)
    except Exception as e:
        print("Erro ao ler arquivo base64:", e)
        sys.exit(4)


def main():
    parser = argparse.ArgumentParser(description="Salvar avatar em images/avatar.png")
    parser.add_argument("--url", help="URL da imagem")
    parser.add_argument("--base64", help="String base64 da imagem")
    parser.add_argument("--base64-file", help="Arquivo contendo base64")
    parser.add_argument(
        "--out",
        help="Caminho de saída (relativo ao repo ou absoluto)",
        default="images/avatar.png",
    )
    args = parser.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))
    out = args.out if os.path.isabs(args.out) else os.path.join(base, args.out)

    if args.url:
        from_url(args.url, out)
    elif args.base64:
        from_base64_string(args.base64, out)
    elif args.base64_file:
        from_base64_file(args.base64_file, out)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
