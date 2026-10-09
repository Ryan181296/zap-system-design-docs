#!/usr/bin/env python3
"""
ZAP Architecture Portal — Argon2id + AES-256-GCM Secure Compiler
"""

import os
import sys
import base64
import argon2
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(SCRIPT_DIR, "index_source.html")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "index.html")
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "templates", "unlock_template.html")
LOGO_FILE = os.path.join(SCRIPT_DIR, "images", "logo.png")

def get_logo_base64():
    if os.path.exists(LOGO_FILE):
        with open(LOGO_FILE, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    return "images/logo.png"

def build_encrypted_html(passcode=None):
    if not os.path.exists(SOURCE_FILE) or not os.path.exists(TEMPLATE_FILE):
        print(f"❌ Error: Required template files not found!")
        sys.exit(1)

    if not passcode:
        passcode = os.environ.get("DOCS_PASSCODE") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not passcode:
        passcode = input("🔑 Enter Secret Passcode to Encrypt: ")

    with open(SOURCE_FILE, "rb") as f:
        plaintext = f.read()

    print(f"🔒 Deriving AES-256 key with Argon2id and encrypting {len(plaintext):,} bytes...")
    salt, iv = os.urandom(16), os.urandom(12)
    key = hash_secret_raw(passcode.encode("utf-8"), salt, time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, type=Type.ID)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, None)
    payload_b64 = base64.b64encode(salt + iv + ciphertext).decode("utf-8")
    logo_src = get_logo_base64()

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    html = template.replace("__CIPHER_PAYLOAD__", payload_b64).replace("__LOGO_SRC__", logo_src)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Generated Grok-styled encrypted index.html ({len(html):,} bytes).")

if __name__ == "__main__":
    passcode = sys.argv[1] if len(sys.argv) > 1 else None
    build_encrypted_html(passcode)
