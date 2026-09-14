#!/usr/bin/env python3
import os
import sys
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_PASSCODE = "zap2026@internal"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(SCRIPT_DIR, "index_source.html")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "index.html")

def build_encrypted_html(passcode=DEFAULT_PASSCODE):
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: Source file {SOURCE_FILE} not found!")
        sys.exit(1)

    with open(SOURCE_FILE, "rb") as f:
        plaintext = f.read()

    print(f"🔒 Encrypting {len(plaintext):,} bytes of System Architecture documentation with AES-256-GCM...")

    salt = os.urandom(16)
    iv = os.urandom(12)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    key = kdf.derive(passcode.encode("utf-8"))
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    # Packed payload: salt (16) + iv (12) + ciphertext+tag
    payload_b64 = base64.b64encode(salt + iv + ciphertext).decode("utf-8")

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ZAP Internal Engineering Docs - Protected</title>
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
    <p class="auth-desc">This documentation is encrypted with military-grade <strong>AES-256-GCM</strong>. Please enter the team key to decrypt and view.</p>
    
    <div id="error-box" class="error-msg">❌ Invalid Passcode. Decryption failed.</div>

    <form id="unlock-form" onsubmit="event.preventDefault(); handleUnlock();">
      <div class="input-group">
        <input type="password" id="passcode-field" class="pass-input" placeholder="Enter Internal Passcode..." autofocus required autocomplete="off">
      </div>
      <button type="submit" id="submit-btn" class="unlock-btn">Decrypt Documentation 🔓</button>
    </form>

    <div class="footer-links">
      Looking for Public Policies? <a href="/privacy">Privacy Policy</a> &bull; <a href="/terms">Terms of Service</a>
    </div>
  </div>

  <script>
    const CIPHER_PAYLOAD = "{payload_b64}";

    function base64ToBytes(b64) {{
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return bytes;
    }}

    async function decryptDoc(passcode) {{
      const raw = base64ToBytes(CIPHER_PAYLOAD);
      const salt = raw.slice(0, 16);
      const iv = raw.slice(16, 28);
      const data = raw.slice(28);

      const enc = new TextEncoder();
      const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(passcode), "PBKDF2", false, ["deriveKey"]);
      const key = await crypto.subtle.deriveKey(
        {{ name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" }},
        keyMaterial,
        {{ name: "AES-GCM", length: 256 }},
        false,
        ["decrypt"]
      );

      const decrypted = await crypto.subtle.decrypt({{ name: "AES-GCM", iv: iv }}, key, data);
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
        btn.textContent = "Decrypting...";
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
          err.textContent = "❌ Invalid Passcode. Decryption failed.";
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

    // Auto unlock if active session exists
    (function() {{
      const saved = sessionStorage.getItem("zap_docs_session_key");
      if (saved) {{
        handleUnlock(saved);
      }}
    }})();
  </script>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"✅ Generated encrypted index.html ({len(template):,} bytes).")
    print(f"🔑 Passcode: {passcode}")

if __name__ == "__main__":
    passcode = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PASSCODE
    build_encrypted_html(passcode)
