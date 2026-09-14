#!/bin/bash
# ==============================================================================
# ZAP System Documentation Portal — Deployment Script
# ==============================================================================

set -eo pipefail

SERVICE_NAME="zap-docs-portal"
REGION="asia-southeast1" # Singapore region (low latency for Vietnam)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

echo "======================================================================"
echo "🚀 ZAP System Architecture & API Documentation Deployment"
echo "======================================================================"

prompt_select "Select Deployment Target" \
  "Firebase Hosting (Deploy ALL: System Design Portal + Privacy + Terms)" \
  "Google Cloud Run (Recommended — Serverless Nginx, Auto SSL, Custom Domain)" \
  "Google App Engine (gcloud app deploy — Managed Static Hosting)" \
  "Google Cloud Storage Bucket (GCS Static Web Bucket)"

case $SELECTED_INDEX in
  0)
    echo "📦 Deploying all documentation & legal pages to Firebase Hosting ($PROJECT_ID)..."
    cd "$SCRIPT_DIR"
    firebase deploy --only hosting --project "zap-ecosystem-production-2f7e9"

    echo "======================================================================"
    echo "✅ DEPLOYMENT TO FIREBASE HOSTING SUCCESSFUL!"
    echo "🌐 System Design Portal: https://zap-ecosystem-production-2f7e9.web.app"
    echo "🌐 Privacy Policy:       https://zap-ecosystem-production-2f7e9.web.app/privacy"
    echo "🌐 Terms & Conditions:   https://zap-ecosystem-production-2f7e9.web.app/terms"
    echo "======================================================================"
    exit 0
    ;;

  1)
    # Check if gcloud CLI is installed
    if ! command -v gcloud &> /dev/null; then
        echo "❌ Error: 'gcloud' CLI is not installed or not in PATH."
        echo "👉 Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo "⚠️ No GCP project currently active in gcloud config."
        read -p "Enter your GCP Project ID: " INPUT_PROJECT_ID
        gcloud config set project "$INPUT_PROJECT_ID"
        PROJECT_ID="$INPUT_PROJECT_ID"
    fi

    echo "📌 Active GCP Project: $PROJECT_ID"
    echo "📌 Deployment Region: $REGION"
    echo "----------------------------------------------------------------------"

    echo "🔨 [1/2] Building container image and deploying to Cloud Run..."
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project "$PROJECT_ID"
    
    cd "$SCRIPT_DIR"
    gcloud run deploy "$SERVICE_NAME" \
        --source . \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --port 8080

    CLOUD_RUN_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)')
    echo "======================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo "🌐 Cloud Run Live URL: $CLOUD_RUN_URL"
    echo ""
    echo "🔗 CUSTOM DOMAIN MAPPING INSTRUCTIONS:"
    echo "Run the following command to map your custom domain e.g. docs.zap.com:"
    echo "  gcloud beta run domain-mappings create --service=$SERVICE_NAME --domain=YOUR_DOMAIN --region=$REGION"
    echo "======================================================================"
    ;;

  2)
    # Check if gcloud CLI is installed
    if ! command -v gcloud &> /dev/null; then
        echo "❌ Error: 'gcloud' CLI is not installed or not in PATH."
        echo "👉 Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo "⚠️ No GCP project currently active in gcloud config."
        read -p "Enter your GCP Project ID: " INPUT_PROJECT_ID
        gcloud config set project "$INPUT_PROJECT_ID"
        PROJECT_ID="$INPUT_PROJECT_ID"
    fi

    echo "📌 Active GCP Project: $PROJECT_ID"
    echo "----------------------------------------------------------------------"

    echo "🔨 Deploying to App Engine..."
    cd "$SCRIPT_DIR"
    gcloud app deploy app.yaml --quiet
    
    APP_URL=$(gcloud app browse --no-launch-browser 2>&1 | grep "http" || echo "https://$PROJECT_ID.appspot.com")
    echo "======================================================================"
    echo "✅ APPSPOT DEPLOYMENT SUCCESSFUL!"
    echo "🌐 App Engine Live URL: $APP_URL"
    echo ""
    echo "🔗 CUSTOM DOMAIN MAPPING INSTRUCTIONS:"
    echo "  gcloud app domain-mappings create YOUR_DOMAIN"
    echo "======================================================================"
    ;;

  3)
    # Check if gcloud CLI is installed
    if ! command -v gcloud &> /dev/null; then
        echo "❌ Error: 'gcloud' CLI is not installed or not in PATH."
        echo "👉 Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo "⚠️ No GCP project currently active in gcloud config."
        read -p "Enter your GCP Project ID: " INPUT_PROJECT_ID
        gcloud config set project "$INPUT_PROJECT_ID"
        PROJECT_ID="$INPUT_PROJECT_ID"
    fi

    BUCKET_NAME="${PROJECT_ID}-zap-docs"
    echo "🔨 Creating GCS Bucket: gs://$BUCKET_NAME..."
    gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION" --web-main-page-suffix="index.html" || true
    
    echo "🔓 Setting public read access..."
    gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" --member="allUsers" --role="roles/storage.objectViewer" || true

    echo "📤 Uploading static site assets..."
    cd "$SCRIPT_DIR"
    gcloud storage rsync . "gs://$BUCKET_NAME" --recursive --exclude=".*" --exclude="*.sh" --exclude="Dockerfile"

    echo "======================================================================"
    echo "✅ GCS BUCKET DEPLOYMENT SUCCESSFUL!"
    echo "🌐 Direct GCS URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
    echo "======================================================================"
    ;;
esac
