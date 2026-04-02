#!/usr/bin/env bash

# Deploy {{ project_name }} as a Cloud Run Job (CLI entry point).
#
# Builds the container image from source using Google Cloud Buildpacks and
# deploys or updates the job definition. Use 'gcloud run jobs execute' to
# trigger a run after deployment.
#
# Usage:
#   ./scripts/deploy_cloud_run_job.sh <deploy_config_file> <app_config_file>
#
# Examples:
#   ./scripts/deploy_cloud_run_job.sh prod.deploy.env prod.env
#
# Requirements:
#   - gcloud CLI installed and authenticated
#   - Deploy config file present in deploy_configs/
#   - App config file present in config/app_configs/

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────

DEPLOY_CONFIG_FILENAME=${1:-}
APP_CONFIG_FILENAME=${2:-}

if [[ -z "${DEPLOY_CONFIG_FILENAME}" || -z "${APP_CONFIG_FILENAME}" ]]; then
    echo "Error: both arguments required."
    echo "Usage: $0 <deploy_config_file> <app_config_file>"
    echo "Example: $0 prod.deploy.env prod.env"
    exit 1
fi

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
DEPLOY_CONFIG_FILE="${PROJECT_ROOT}/deploy_configs/${DEPLOY_CONFIG_FILENAME}"

# ── Validate deploy config exists ─────────────────────────────────────────────

if [[ ! -f "${DEPLOY_CONFIG_FILE}" ]]; then
    echo "Error: Deploy config not found at ${DEPLOY_CONFIG_FILE}"
    exit 1
fi

# ── Load deploy config ────────────────────────────────────────────────────────

echo "Loading deploy config: ${DEPLOY_CONFIG_FILE}"
source "${DEPLOY_CONFIG_FILE}"

# ── Apply defaults for optional config values ─────────────────────────────────

GCRJ_CPU="${GCRJ_CPU:-1}"
GCRJ_MEMORY="${GCRJ_MEMORY:-512Mi}"
GCRJ_TASK_TIMEOUT="${GCRJ_TASK_TIMEOUT:-600s}"
GCRJ_TASKS="${GCRJ_TASKS:-1}"
GCRJ_PARALLELISM="${GCRJ_PARALLELISM:-0}"
GCRJ_MAX_RETRIES="${GCRJ_MAX_RETRIES:-3}"

# ── Confirm ───────────────────────────────────────────────────────────────────

echo ""
echo "  Job:        ${GCRJ_JOB_NAME}"
echo "  Project:    ${GCP_PROJECT}"
echo "  Region:     ${GCP_REGION}"
echo "  Resources:  ${GCRJ_CPU} CPU  ${GCRJ_MEMORY}"
echo "  Tasks:      count=${GCRJ_TASKS}  parallelism=${GCRJ_PARALLELISM}  max_retries=${GCRJ_MAX_RETRIES}"
echo "  Timeout:    ${GCRJ_TASK_TIMEOUT}"
echo "  App config: ${APP_CONFIG_FILENAME}"
echo ""

# ── Deploy ────────────────────────────────────────────────────────────────────

echo ""
echo "Deploying ${GCRJ_JOB_NAME} to Cloud Run Jobs..."

gcloud run jobs deploy "${GCRJ_JOB_NAME}" \
    --source="${PROJECT_ROOT}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --service-account="${SERVICE_ACCOUNT_EMAIL}" \
    --cpu="${GCRJ_CPU}" \
    --memory="${GCRJ_MEMORY}" \
    --task-timeout="${GCRJ_TASK_TIMEOUT}" \
    --tasks="${GCRJ_TASKS}" \
    --parallelism="${GCRJ_PARALLELISM}" \
    --max-retries="${GCRJ_MAX_RETRIES}" \
    --command=job \
    --set-env-vars="APP_CONFIG_FILE=${APP_CONFIG_FILENAME}"

echo ""
echo "Done! Job deployed:"
gcloud run jobs describe "${GCRJ_JOB_NAME}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --format="value(name)"

echo ""
echo "To execute the job, run:"
echo "  gcloud run jobs execute ${GCRJ_JOB_NAME} --region=${GCP_REGION} --project=${GCP_PROJECT}"
