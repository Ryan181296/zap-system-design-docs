#!/bin/bash
# ==============================================================================
# ZAP Documentation & Legal Portal — Argon2id + AES-256 Deployment Script
# ==============================================================================

set -eo pipefail

PROJECT_ID="zap-ecosystem-production-2f7e9"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGAL_PORTAL_DIR="$(cd "$SCRIPT_DIR/../legal-portal" 2>/dev/null && pwd || echo "")"

# Helper function to read single keypress from /dev/tty
read_key() {
  local key rest
  IFS= read -rsn1 key < /dev/tty 2>/dev/null
  if [[ $key == $'\x1b' ]]; then
    read -rsn2 -t 1 rest < /dev/tty 2>/dev/null
    case "$rest" in
      "[A" | "OA") echo "UP" ;;
      "[B" | "OB") echo "DOWN" ;;
      "[C" | "OC") echo "RIGHT" ;;
      "[D" | "OD") echo "LEFT" ;;
      *) echo "ESC" ;;
    esac
  elif [[ $key == "" ]]; then
    echo "ENTER"
  elif [[ $key == " " ]]; then
    echo "SPACE"
  elif [[ $key == "k" || $key == "K" ]]; then
    echo "UP"
  elif [[ $key == "j" || $key == "J" ]]; then
    echo "DOWN"
  else
    echo "$key"
  fi
}

prompt_select() {
  local prompt_title="$1"
  shift
  local options=("$@")
  local current=0
  local count=${#options[@]}

  local old_stty
  old_stty=$(stty -g < /dev/tty 2>/dev/null || true)
  stty -echo -icanon min 1 time 0 < /dev/tty 2>/dev/null
  printf "\033[?25l" > /dev/tty

  cleanup_select() {
    printf "\033[?25h" > /dev/tty
    if [ -n "$old_stty" ]; then
      stty "$old_stty" < /dev/tty 2>/dev/null || true
    fi
  }
  trap 'cleanup_select; exit 1' INT TERM

  printf "\033[36m?\033[0m \033[1m%s:\033[0m \033[2m(Use arrow keys ↑/↓ or j/k, Enter to select)\033[0m\n" "$prompt_title" > /dev/tty

  render_select() {
    for i in "${!options[@]}"; do
      if [ "$i" -eq "$current" ]; then
        printf " \033[36m❯ ${options[$i]}\033[0m\n" > /dev/tty
      else
        printf "   ${options[$i]}\n" > /dev/tty
      fi
    done
  }

  render_select

  while true; do
    local key
    key=$(read_key)
    case "$key" in
      UP)
        ((current--))
        if [ "$current" -lt 0 ]; then current=$((count - 1)); fi
        ;;
      DOWN)
        ((current++))
        if [ "$current" -ge "$count" ]; then current=0; fi
        ;;
      ENTER)
        break
        ;;
    esac

    printf "\033[%dA" "$count" > /dev/tty
    render_select
  done

  # Clear options and show choice
  printf "\033[%dA" "$count" > /dev/tty
  for i in "${!options[@]}"; do
    printf "\033[K\n" > /dev/tty
  done
  printf "\033[%dA" "$count" > /dev/tty

  printf "\033[32m✔\033[0m \033[1mSelected:\033[0m \033[36m${options[$current]}\033[0m\n\n" > /dev/tty

  cleanup_select
  trap - INT TERM

  SELECTED_INDEX="$current"
}

# Check Firebase CLI
if ! command -v firebase &> /dev/null; then
    echo "❌ Error: 'firebase' CLI is not installed or not in PATH."
    echo "👉 Please install: npm install -g firebase-tools"
    exit 1
fi

echo "======================================================================"
echo "🚀 ZAP DEPLOYMENT — FIREBASE HOSTING ($PROJECT_ID)"
echo "======================================================================"

prompt_select "Select Deployment Target" \
  "1) Deploy ALL (Argon2id Encrypted Portal + Privacy + Terms + Delete Account)" \
  "2) Deploy Legal Pages only (Privacy Policy, Terms of Service, Delete Account)" \
  "3) Deploy Architecture Docs only (Argon2id Encrypted Portal)"

cd "$SCRIPT_DIR"

case $SELECTED_INDEX in
  0)
    echo "🔐 [1/2] Encrypting Architecture Portal with Argon2id & AES-256-GCM..."
    python3 "$SCRIPT_DIR/build_encrypted.py"

    echo "📦 [2/2] Deploying ALL to Firebase Hosting ($PROJECT_ID)..."
    firebase deploy --only hosting --project "$PROJECT_ID"
    echo ""
    echo "======================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL (ALL)!"
    echo "🔒 Architecture Portal (Argon2id Encrypted): https://$PROJECT_ID.web.app"
    echo "🔓 Privacy Policy (Public 100%):            https://$PROJECT_ID.web.app/privacy"
    echo "🔓 Terms of Service (Public 100%):          https://$PROJECT_ID.web.app/terms"
    echo "🔓 Delete Account Request (Public 100%):    https://$PROJECT_ID.web.app/delete-account"
    echo "======================================================================"
    ;;

  1)
    echo "📦 Deploying Legal Pages only (Privacy, Terms, Delete Account) to Firebase Hosting..."
    TMP_DIR=$(mktemp -d)
    mkdir -p "$TMP_DIR/public/css"
    cp "$SCRIPT_DIR/privacy-policy.html" "$TMP_DIR/public/"
    cp "$SCRIPT_DIR/terms-and-conditions.html" "$TMP_DIR/public/"
    cp "$SCRIPT_DIR/delete-account.html" "$TMP_DIR/public/"
    if [ -f "$LEGAL_PORTAL_DIR/public/index.html" ]; then
        cp "$LEGAL_PORTAL_DIR/public/index.html" "$TMP_DIR/public/index.html"
    else
        cp "$SCRIPT_DIR/privacy-policy.html" "$TMP_DIR/public/index.html"
    fi
    cp -r "$SCRIPT_DIR/css" "$TMP_DIR/public/" 2>/dev/null || true
    
    cat <<EOF > "$TMP_DIR/firebase.json"
{
  "hosting": {
    "public": "public",
    "rewrites": [
      { "source": "/privacy", "destination": "/privacy-policy.html" },
      { "source": "/privacy-policy", "destination": "/privacy-policy.html" },
      { "source": "/terms", "destination": "/terms-and-conditions.html" },
      { "source": "/terms-and-conditions", "destination": "/terms-and-conditions.html" },
      { "source": "/terms-of-service", "destination": "/terms-and-conditions.html" },
      { "source": "/delete-account", "destination": "/delete-account.html" },
      { "source": "/account-deletion", "destination": "/delete-account.html" }
    ]
  }
}
EOF
    cat <<EOF > "$TMP_DIR/.firebaserc"
{
  "projects": { "default": "$PROJECT_ID" }
}
EOF
    (cd "$TMP_DIR" && firebase deploy --only hosting --project "$PROJECT_ID")
    rm -rf "$TMP_DIR"

    echo ""
    echo "======================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL (LEGAL PAGES)!"
    echo "🔓 Privacy Policy:   https://$PROJECT_ID.web.app/privacy"
    echo "🔓 Terms of Service: https://$PROJECT_ID.web.app/terms"
    echo "🔓 Delete Account:   https://$PROJECT_ID.web.app/delete-account"
    echo "======================================================================"
    ;;

  2)
    echo "🔐 [1/2] Encrypting Architecture Portal with Argon2id & AES-256-GCM..."
    python3 "$SCRIPT_DIR/build_encrypted.py"

    echo "📦 [2/2] Deploying Encrypted Architecture Docs to Firebase Hosting..."
    firebase deploy --only hosting --project "$PROJECT_ID"
    echo ""
    echo "======================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL (ARCHITECTURE DOCS)!"
    echo "🔒 Architecture Portal (Argon2id Encrypted): https://$PROJECT_ID.web.app"
    echo "======================================================================"
    ;;
esac
