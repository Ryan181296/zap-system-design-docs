#!/bin/bash
# ==============================================================================
# ZAP System Documentation Portal — Google Cloud Platform (GCP) Deploy Script
# ==============================================================================

set -e

SERVICE_NAME="zap-docs-portal"
REGION="asia-southeast1" # Singapore region (low latency for Vietnam)

echo "======================================================================"
echo "🚀 ZAP System Architecture & API Documentation GCP Deployment"
echo "======================================================================"

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

echo "Select GCP Deployment Option:"
echo "1) Google Cloud Run (Recommended — Serverless Nginx, Auto SSL, Custom Domain)"
echo "2) Google App Engine (gcloud app deploy — Managed Static Hosting)"
echo "3) Google Cloud Storage Bucket (GCS Static Web Bucket)"
read -p "Enter choice [1-3]: " CHOICE

case $CHOICE in
  1)
    echo "🔨 [1/2] Building container image and deploying to Cloud Run..."
    gcloud services enable run.googleapis.com cloudbuild.googleapis.com --project "$PROJECT_ID"
    
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
    echo "🔨 Deploying to App Engine..."
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
    BUCKET_NAME="${PROJECT_ID}-zap-docs"
    echo "🔨 Creating GCS Bucket: gs://$BUCKET_NAME..."
    gcloud storage buckets create "gs://$BUCKET_NAME" --location="$REGION" --web-main-page-suffix="index.html" || true
    
    echo "🔓 Setting public read access..."
    gcloud storage buckets add-iam-policy-binding "gs://$BUCKET_NAME" --member="allUsers" --role="roles/storage.objectViewer" || true

    echo "📤 Uploading static site assets..."
    gcloud storage rsyn . "gs://$BUCKET_NAME" --recursive --exclude=".*" --exclude="*.sh" --exclude="Dockerfile"

    echo "======================================================================"
    echo "✅ GCS BUCKET DEPLOYMENT SUCCESSFUL!"
    echo "🌐 Direct GCS URL: https://storage.googleapis.com/$BUCKET_NAME/index.html"
    echo "======================================================================"
    ;;

  *)
    echo "❌ Invalid choice. Aborting."
    exit 1
    ;;
esac
