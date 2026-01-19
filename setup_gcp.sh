#!/bin/bash
# GCP Infrastructure Setup Script
# Run this in Google Cloud Shell

set -e  # Exit on error

echo "🚀 Starting GCP Infrastructure Setup for Multi-AI Orchestrator"
echo "================================================================"

# ===== 1. BigQuery Table 생성 =====
echo ""
echo "📊 Step 1/5: Creating BigQuery Table..."
bq mk --table \
  --schema='[
    {"name":"content","type":"STRING","mode":"REQUIRED"},
    {"name":"embedding","type":"FLOAT64","mode":"REPEATED"},
    {"name":"metadata","type":"JSON","mode":"NULLABLE"},
    {"name":"created_at","type":"TIMESTAMP","mode":"NULLABLE"},
    {"name":"source","type":"STRING","mode":"NULLABLE"}
  ]' \
  phsysics:knowledge_base.embeddings

echo "✅ BigQuery Table created"
bq show phsysics:knowledge_base.embeddings

# ===== 2. GCS Bucket 확인/생성 =====
echo ""
echo "📦 Step 2/5: Setting up GCS Bucket..."
gsutil ls gs://multi-ai-memory-bank-phsysics/ 2>/dev/null || \
  gsutil mb -p phsysics -l us-central1 gs://multi-ai-memory-bank-phsysics/

# 폴더 생성
echo "Creating folders..."
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/context/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/decisions/.keep
echo "" | gsutil cp - gs://multi-ai-memory-bank-phsysics/session_logs/.keep

echo "✅ GCS Bucket ready"
gsutil ls gs://multi-ai-memory-bank-phsysics/

# ===== 3. Service Account 생성 =====
echo ""
echo "🔐 Step 3/5: Creating Service Account..."
gcloud iam service-accounts create multi-ai-orchestrator \
  --project=phsysics \
  --display-name="Multi-AI Orchestrator" 2>/dev/null || \
  echo "Service Account already exists, continuing..."

echo "✅ Service Account created"

# ===== 4. 권한 부여 =====
echo ""
echo "🔑 Step 4/5: Granting permissions..."
gcloud projects add-iam-policy-binding phsysics \
  --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor" \
  --condition=None

gcloud projects add-iam-policy-binding phsysics \
  --member="serviceAccount:multi-ai-orchestrator@phsysics.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --condition=None

echo "✅ Permissions granted"

# ===== 5. Service Account Key 생성 =====
echo ""
echo "🔑 Step 5/5: Creating Service Account Key..."
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=multi-ai-orchestrator@phsysics.iam.gserviceaccount.com

echo "✅ Service Account Key created: sa-key.json"
echo ""
echo "================================================================"
echo "🎉 GCP Infrastructure Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Copy sa-key.json content for GitHub Secrets:"
echo "   cat sa-key.json"
echo ""
echo "2. Delete sa-key.json after copying (for security):"
echo "   rm sa-key.json"
echo ""
echo "3. Proceed to GitHub repository setup"
echo "================================================================"
