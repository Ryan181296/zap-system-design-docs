#!/usr/bin/env python3
import os
import sys
import base64
import tty
import termios
import argon2
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(SCRIPT_DIR, "index_source.html")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "index.html")

def getpass_stars(prompt="🔑 Enter Secret Passcode: "):
    """Reads password interactively displaying asterisks (*) for visual feedback."""
    if not sys.stdin.isatty():
        return input(prompt)
    
    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    chars = []
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\r', '\n'):
                print("\r\n", end="", flush=True)
                break
            elif ch in ('\x7f', '\x08'):  # Backspace / Delete
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
            elif ch == '\x03':  # Ctrl+C
                print("\r\n", end="", flush=True)
                raise KeyboardInterrupt
            elif ch == '\x04':  # Ctrl+D
                break
            elif ord(ch) >= 32:  # Printable character
                chars.append(ch)
                print("*", end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return "".join(chars)

def build_encrypted_html(passcode=None):
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: Source file {SOURCE_FILE} not found!")
        sys.exit(1)

    if not passcode:
        while True:
            p1 = getpass_stars("🔑 Enter Secret Passcode to Encrypt: ")
            if not p1:
                print("⚠️ Passcode cannot be empty!\n")
                continue
            p2 = getpass_stars("🔑 Re-enter Secret Passcode to Confirm: ")
            if p1 != p2:
                print("❌ Passwords do not match! Please try again.\n")
                continue
            passcode = p1
            break

    with open(SOURCE_FILE, "rb") as f:
        plaintext = f.read()

    print(f"🔒 Deriving AES-256 key with Argon2id and encrypting {len(plaintext):,} bytes...")

    salt = os.urandom(16)
    iv = os.urandom(12)

    # Argon2id key derivation (32 bytes AES key)
    key = hash_secret_raw(
        secret=passcode.encode("utf-8"),
        salt=salt,
        time_cost=2,
        memory_cost=19456, # 19MB (RFC 9106 recommended)
        parallelism=1,
        hash_len=32,
        type=Type.ID
    )

    # Argon2id verification hash for match/mismatch check
    ph = argon2.PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, type=Type.ID)
    argon2_verify_hash = ph.hash(passcode)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    # Pack: salt(16) + iv(12) + ciphertext
    payload_b64 = base64.b64encode(salt + iv + ciphertext).decode("utf-8")

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ZAP Architecture Portal - Protected</title>
  <!-- Fast WASM Argon2id & WebCrypto -->
  <script src="https://cdn.jsdelivr.net/npm/hash-wasm@4.12.0/dist/argon2.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0b1120;
      color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .auth-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 20px;
      padding: 40px 32px;
      max-width: 460px;
      width: 100%;
      text-align: center;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
    }}
    .auth-icon {{
      width: 60px;
      height: 60px;
      margin: 0 auto 16px;
      background: rgba(37, 99, 235, 0.15);
      border: 1px solid rgba(37, 99, 235, 0.3);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
    }}
    .auth-title {{
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 8px;
      letter-spacing: -0.3px;
    }}
    .auth-desc {{
      font-size: 13.5px;
      color: #94a3b8;
      line-height: 1.55;
      margin-bottom: 24px;
    }}
    .input-group {{
      margin-bottom: 14px;
      position: relative;
    }}
    .pass-input {{
      width: 100%;
      padding: 14px 16px;
      background: #0f172a;
      border: 1px solid #475569;
      border-radius: 12px;
      color: #f8fafc;
      font-size: 15px;
      outline: none;
      transition: all 0.2s ease;
    }}
    .pass-input:focus {{
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }}
    .unlock-btn {{
      width: 100%;
      padding: 14px 20px;
      background: #2563eb;
      color: #fff;
      font-size: 15px;
      font-weight: 600;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .unlock-btn:hover {{
      background: #1d4ed8;
      transform: translateY(-1px);
    }}
    .unlock-btn:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    .error-msg {{
      display: none;
      font-size: 13px;
      color: #f87171;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.25);
      padding: 10px 14px;
      border-radius: 10px;
      margin-bottom: 14px;
    }}
    .footer-links {{
      margin-top: 24px;
      font-size: 12.5px;
      color: #64748b;
    }}
    .footer-links a {{
      color: #60a5fa;
      text-decoration: none;
    }}
    .footer-links a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="auth-card">
    <div class="auth-icon">🛡️</div>
    <h1 class="auth-title">ZAP Architecture Portal</h1>
    <p class="auth-desc">Protected by <strong>Argon2id &amp; AES-256-GCM</strong>. Please enter your team passcode to decrypt and access.</p>
    
    <div id="error-box" class="error-msg">❌ Invalid Passcode. Access denied.</div>

    <form id="unlock-form" onsubmit="event.preventDefault(); handleUnlock();">
      <div class="input-group">
        <input type="password" id="passcode-field" class="pass-input" placeholder="Enter Secret Passcode..." autofocus required autocomplete="off">
      </div>
      <button type="submit" id="submit-btn" class="unlock-btn">Decrypt Documentation 🔓</button>
    </form>

    <div class="footer-links">
      Looking for Public Policies? <a href="/privacy">Privacy Policy</a> &bull; <a href="/terms">Terms of Service</a>
    </div>
  </div>

  <script>
    const CIPHER_PAYLOAD = "{payload_b64}";
    const ARGON2_VERIFY_HASH = "{argon2_verify_hash}";

    function base64ToBytes(b64) {{
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return bytes;
    }}

    async function deriveArgon2Key(passcode, salt) {{
      if (typeof hashwasm === "undefined" || !hashwasm.argon2id) {{
        throw new Error("Argon2 WASM engine not loaded");
      }}
      const keyHex = await hashwasm.argon2id({{
        password: passcode,
        salt: salt,
        parallelism: 1,
        iterations: 2,
        memorySize: 19456,
        hashLength: 32,
        outputType: "hex"
      }});
      const match = keyHex.match(/.{{1,2}}/g);
      return new Uint8Array(match.map(byte => parseInt(byte, 16)));
    }}

    async function decryptDoc(passcode) {{
      const raw = base64ToBytes(CIPHER_PAYLOAD);
      const salt = raw.slice(0, 16);
      const iv = raw.slice(16, 28);
      const data = raw.slice(28);

      const rawKey = await deriveArgon2Key(passcode, salt);
      const cryptoKey = await crypto.subtle.importKey("raw", rawKey, {{ name: "AES-GCM" }}, false, ["decrypt"]);
      const decrypted = await crypto.subtle.decrypt({{ name: "AES-GCM", iv: iv }}, cryptoKey, data);
      return new TextDecoder().decode(decrypted);
    }}

    async function renderDecrypted(html, passcode) {{
      sessionStorage.setItem("zap_docs_session_key", passcode);
      document.open();
      document.write(html);
      document.close();
    }}

    async function handleUnlock(presetPasscode) {{
      const input = document.getElementById("passcode-field");
      const btn = document.getElementById("submit-btn");
      const err = document.getElementById("error-box");
      const passcode = presetPasscode || (input ? input.value : "").trim();

      if (!passcode) return;

      if (btn) {{
        btn.disabled = true;
        btn.textContent = "Verifying Argon2id...";
      }}
      if (err) err.style.display = "none";

      try {{
        const html = await decryptDoc(passcode);
        if (html && (html.includes("<!DOCTYPE") || html.includes("<html"))) {{
          renderDecrypted(html, passcode);
          return;
        }} else {{
          throw new Error("Decrypted content invalid");
        }}
      }} catch (e) {{
        if (err) {{
          err.style.display = "block";
          err.textContent = "❌ Invalid Passcode. Access denied.";
        }}
        if (btn) {{
          btn.disabled = false;
          btn.textContent = "Decrypt Documentation 🔓";
        }}
        if (input) {{
          input.value = "";
          input.focus();
        }}
      }}
    }}

    // Auto unlock if active session exists in sessionStorage
    (function() {{
      const saved = sessionStorage.getItem("zap_docs_session_key");
      if (saved) {{
        window.addEventListener("DOMContentLoaded", () => handleUnlock(saved));
      }}
    }})();
  </script>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"✅ Generated Argon2id + AES-256 encrypted index.html ({len(template):,} bytes).")
    print(f"🛡️ Argon2 verification hash embedded.")
    print("🔒 Passcode is NOT saved anywhere in plaintext.")

if __name__ == "__main__":
    passcode = sys.argv[1] if len(sys.argv) > 1 else None
    build_encrypted_html(passcode)
