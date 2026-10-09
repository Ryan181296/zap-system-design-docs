#!/usr/bin/env python3
import os
import sys
import base64
import argon2
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(SCRIPT_DIR, "index_source.html")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "index.html")

def build_encrypted_html(passcode=None):
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: {SOURCE_FILE} not found!")
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
    ph = argon2.PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, type=Type.ID)
    argon2_verify_hash = ph.hash(passcode)
    ciphertext = AESGCM(key).encrypt(iv, plaintext, None)
    payload_b64 = base64.b64encode(salt + iv + ciphertext).decode("utf-8")

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ZAP Architecture Portal - Protected</title>
  <script src="https://cdn.jsdelivr.net/npm/hash-wasm@4.12.0/dist/argon2.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0b1120; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
    .auth-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 36px 28px; max-width: 440px; width: 100%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6); }}
    .auth-title {{ font-size: 22px; font-weight: 700; margin-bottom: 8px; }}
    .auth-desc {{ font-size: 13.5px; color: #94a3b8; margin-bottom: 20px; }}
    .pass-input {{ width: 100%; padding: 12px 16px; background: #0f172a; border: 1px solid #475569; border-radius: 10px; color: #f8fafc; font-size: 15px; outline: none; margin-bottom: 12px; }}
    .unlock-btn {{ width: 100%; padding: 12px; background: #2563eb; color: #fff; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; }}
    .error-msg {{ color: #f87171; font-size: 13px; margin-bottom: 12px; display: none; }}
  </style>
</head>
<body>
  <div class="auth-card">
    <div style="font-size: 32px; margin-bottom: 10px;">🛡️</div>
    <h1 class="auth-title">ZAP Architecture Portal</h1>
    <p class="auth-desc">Protected by <strong>Argon2id &amp; AES-256-GCM</strong>. Enter passcode to decrypt.</p>
    <div id="error-box" class="error-msg">❌ Invalid Passcode.</div>
    <form onsubmit="event.preventDefault(); handleUnlock();">
      <input type="password" id="passcode-field" class="pass-input" placeholder="Enter Secret Passcode..." autofocus required autocomplete="off">
      <button type="submit" id="submit-btn" class="unlock-btn">Decrypt Documentation 🔓</button>
    </form>
  </div>
  <script>
    const CIPHER_PAYLOAD = "{payload_b64}";
    function b64ToBytes(b64) {{ const bin = atob(b64); return Uint8Array.from(bin, c => c.charCodeAt(0)); }}
    async function deriveArgon2Key(passcode, salt) {{
      const keyHex = await hashwasm.argon2id({{ password: passcode, salt: salt, parallelism: 1, iterations: 2, memorySize: 19456, hashLength: 32, outputType: "hex" }});
      return new Uint8Array(keyHex.match(/.{{1,2}}/g).map(byte => parseInt(byte, 16)));
    }}
    async function decryptDoc(passcode) {{
      const raw = b64ToBytes(CIPHER_PAYLOAD);
      const salt = raw.slice(0, 16), iv = raw.slice(16, 28), data = raw.slice(28);
      const rawKey = await deriveArgon2Key(passcode, salt);
      const cryptoKey = await crypto.subtle.importKey("raw", rawKey, {{ name: "AES-GCM" }}, false, ["decrypt"]);
      const decrypted = await crypto.subtle.decrypt({{ name: "AES-GCM", iv: iv }}, cryptoKey, data);
      return new TextDecoder().decode(decrypted);
    }}
    async function handleUnlock(preset) {{
      const input = document.getElementById("passcode-field"), btn = document.getElementById("submit-btn"), err = document.getElementById("error-box");
      const code = preset || (input ? input.value : "").trim();
      if (!code) return;
      if (btn) {{ btn.disabled = true; btn.textContent = "Verifying..."; }}
      try {{
        const html = await decryptDoc(code);
        sessionStorage.setItem("zap_docs_session_key", code);
        document.open(); document.write(html); document.close();
      }} catch (e) {{
        if (err) err.style.display = "block";
        if (btn) {{ btn.disabled = false; btn.textContent = "Decrypt Documentation 🔓"; }}
      }}
    }}
    (function() {{
      const saved = sessionStorage.getItem("zap_docs_session_key");
      if (saved) window.addEventListener("DOMContentLoaded", () => handleUnlock(saved));
    }})();
  </script>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"✅ Generated encrypted index.html ({len(template):,} bytes).")

if __name__ == "__main__":
    passcode = sys.argv[1] if len(sys.argv) > 1 else None
    build_encrypted_html(passcode)
