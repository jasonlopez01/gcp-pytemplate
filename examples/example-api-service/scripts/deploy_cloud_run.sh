#!/usr/bin/env bash

# Deploy Example API Service to Cloud Run using Google Cloud Buildpacks (Procfile).
#
# Usage:
#   ./scripts/deploy_cloud_run.sh <deploy_env_file> <app_env_file>
#
# Examples:
#   ./scripts/deploy_cloud_run.sh prod.deploy.env prod.env
#   ./scripts/deploy_cloud_run.sh prod.mega_deploy.env prod.env
#
# Requirements:
#   - gcloud CLI installed and authenticated
#   - Deploy config file present in deploy_configs/
#   - App config file present in config/app_configs/

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────

DEPLOY_ENV_FILENAME=${1:-}
APP_ENV_FILENAME=${2:-}

if [[ -z "${DEPLOY_ENV_FILENAME}" || -z "${APP_ENV_FILENAME}" ]]; then
    echo "Error: both arguments required."
    echo "Usage: $0 <deploy_env_file> <app_env_file>"
    echo "Example: $0 prod.deploy.env prod.env"
    exit 1
fi

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
DEPLOY_ENV_FILE="${PROJECT_ROOT}/deploy_configs/${DEPLOY_ENV_FILENAME}"

# ── Validate deploy config exists ─────────────────────────────────────────────

if [[ ! -f "${DEPLOY_ENV_FILE}" ]]; then
    echo "Error: Deploy config not found at ${DEPLOY_ENV_FILE}"
    exit 1
fi

# ── Load deploy config ────────────────────────────────────────────────────────

echo "Loading deploy config: ${DEPLOY_ENV_FILE}"
source "${DEPLOY_ENV_FILE}"

# ── Apply defaults for optional config values ─────────────────────────────────

GCR_MIN_INSTANCES="${GCR_MIN_INSTANCES:-0}"
GCR_MAX_INSTANCES="${GCR_MAX_INSTANCES:-10}"
GCR_CPU="${GCR_CPU:-1}"
GCR_MEMORY="${GCR_MEMORY:-512Mi}"
GCR_CONCURRENCY="${GCR_CONCURRENCY:-80}"
GCR_TIMEOUT="${GCR_TIMEOUT:-300}"

# ── Confirm ───────────────────────────────────────────────────────────────────

echo ""
echo "  Service:    ${GCR_SERVICE_NAME}"
echo "  Project:    ${GCP_PROJECT}"
echo "  Region:     ${GCP_REGION}"
echo "  Image:      ${GCR_CPU} CPU  ${GCR_MEMORY}  concurrency=${GCR_CONCURRENCY}"
echo "  Scaling:    min=${GCR_MIN_INSTANCES}  max=${GCR_MAX_INSTANCES}"
echo "  App config: ${APP_ENV_FILENAME}"
echo ""

# ── Deploy ────────────────────────────────────────────────────────────────────

echo ""
echo "Deploying ${GCR_SERVICE_NAME} to Cloud Run..."

gcloud run deploy "${GCR_SERVICE_NAME}" \
    --source="${PROJECT_ROOT}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --service-account="${SERVICE_ACCOUNT_EMAIL}" \
    --min-instances="${GCR_MIN_INSTANCES}" \
    --max-instances="${GCR_MAX_INSTANCES}" \
    --cpu="${GCR_CPU}" \
    --memory="${GCR_MEMORY}" \
    --concurrency="${GCR_CONCURRENCY}" \
    --timeout="${GCR_TIMEOUT}s" \
    --set-env-vars="APP_CONFIG_FILE=${APP_ENV_FILENAME}" \
    --no-allow-unauthenticated

echo ""
echo "Done! Service URL:"
gcloud run services describe "${GCR_SERVICE_NAME}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --format="value(status.url)"