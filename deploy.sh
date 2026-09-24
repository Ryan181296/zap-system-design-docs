#!/bin/bash
# ==============================================================================
# ZAP Documentation & Legal Portal — Argon2id + AES-256 Deployment Script
# ==============================================================================

set -eo pipefail

PROJECT_ID="zap-ecosystem-production-2f7e9"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEGAL_PORTAL_DIR="$(cd "$SCRIPT_DIR/../legal-portal" 2>/dev/null && pwd || echo "")"

prompt_select() {
  local prompt_title="$1"
  shift
  local options=("$@")
  local current=0
  local count=${#options[@]}

  # Save terminal state
  local old_stty
  old_stty=$(stty -g 2>/dev/null || true)

  cleanup_select() {
    printf "\033[?25h" # Show cursor
    if [ -n "$old_stty" ]; then
      stty "$old_stty" 2>/dev/null || true
    fi
  }
  trap 'cleanup_select; echo ""; exit 1' INT TERM

  # Hide cursor and disable echo
  printf "\033[?25l"
  stty -icanon -echo min 1 time 0 2>/dev/null || true

  render_menu() {
    for i in "${!options[@]}"; do
      if [ "$i" -eq "$current" ]; then
        printf "\r\033[2K \033[1;36m❯\033[0m \033[1;37m${options[$i]}\033[0m\n"
      else
        printf "\r\033[2K   \033[2;37m${options[$i]}\033[0m\n"
      fi
    done
  }

  printf "\n\033[1;32m?\033[0m \033[1m%s\033[0m \033[2m(Use ↑/↓ arrows, 1-%d, or Enter to select)\033[0m\n" "$prompt_title" "$count"
  render_menu

  while true; do
    local key=""
    # Read 1-3 bytes for raw key handling (handles escape sequences reliably on macOS bash & zsh)
    IFS= read -r -s -n 1 key 2>/dev/null || true
    if [[ "$key" == $'\x1b' ]]; then
      local rest=""
      IFS= read -r -s -n 2 rest 2>/dev/null || true
      key="$key$rest"
    fi

    case "$key" in
      $'\x1b[A'|$'\x1bOA'|[kK]) # UP Arrow
        ((current--)) || true
        if [ "$current" -lt 0 ]; then current=$((count - 1)); fi
        ;;
      $'\x1b[B'|$'\x1bOB'|[jJ]) # DOWN Arrow
        ((current++)) || true
        if [ "$current" -ge "$count" ]; then current=0; fi
        ;;
      [1-9]) # Direct number selection (e.g. 1, 2, 3)
        local num=$((key - 1))
        if [ "$num" -ge 0 ] && [ "$num" -lt "$count" ]; then
          current="$num"
          break
        fi
        ;;
      ""|$'\n'|$'\r') # Enter / Return
        break
        ;;
    esac

    # Move cursor back up to re-render without clearing text artifacts
    printf "\033[%dA" "$count"
    render_menu
  done

  # Clear menu options and print clean result
  printf "\033[%dA" "$count"
  for ((i=0; i<count; i++)); do
    printf "\r\033[2K\n"
  done
  printf "\033[%dA" "$count"

  printf "\r\033[2K\033[1;32m✔\033[0m \033[1mSelected:\033[0m \033[1;36m${options[$current]}\033[0m\n\n"

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

case "$SELECTED_INDEX" in
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
