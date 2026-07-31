#!/usr/bin/env bash

# Execute an existing {{ project_name }} Cloud Run Job.
#
# Optionally pass CLI args to the job container via positional args.
#
# Usage:
#   ./scripts/execute_cloud_run_job.sh <deploy_config_file> [<cli args>]
#
# Examples:
#   ./scripts/execute_cloud_run_job.sh prod.deploy.env
#   ./scripts/execute_cloud_run_job.sh stage.deploy.env items
#
# Requirements:
#   - gcloud CLI installed and authenticated
#   - Cloud Run Job already deployed (run deploy_cloud_run_job.sh first)
#   - Deploy config file present in deploy_configs/

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────

DEPLOY_CONFIG_FILENAME=${1:-}

if [[ -z "${DEPLOY_CONFIG_FILENAME}" ]]; then
    echo "Error: deploy config argument required."
    echo "Usage: $0 <deploy_config_file> [<cli args>]"
    echo "Example: $0 prod.deploy.env"
    exit 1
fi

shift
HAS_ARGS=false
JOB_ARGS=()
if [[ $# -gt 0 ]]; then
    JOB_ARGS=("$@")
    HAS_ARGS=true
fi

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
DEPLOY_CONFIG_FILE="${PROJECT_ROOT}/deploy_configs/${DEPLOY_CONFIG_FILENAME}"

# ── Validate config file exists ───────────────────────────────────────────────

if [[ ! -f "${DEPLOY_CONFIG_FILE}" ]]; then
    echo "Error: Deploy config not found at ${DEPLOY_CONFIG_FILE}"
    exit 1
fi

# ── Load deploy config ────────────────────────────────────────────────────────

echo "Loading deploy config: ${DEPLOY_CONFIG_FILE}"
source "${DEPLOY_CONFIG_FILE}"

# ── Confirm ───────────────────────────────────────────────────────────────────

echo ""
echo "  Job:     ${GCRJ_JOB_NAME}"
echo "  Project: ${GCP_PROJECT}"
echo "  Region:  ${GCP_REGION}"
if [[ "${HAS_ARGS}" == "true" ]]; then
    echo "  Args:    ${JOB_ARGS[*]}"
fi
echo ""

# ── Execute ───────────────────────────────────────────────────────────────────

echo ""
echo "Executing ${GCRJ_JOB_NAME}..."

EXECUTE_CMD=(
    gcloud run jobs execute "${GCRJ_JOB_NAME}"
    --project="${GCP_PROJECT}"
    --region="${GCP_REGION}"
    --wait
)

if [[ "${HAS_ARGS}" == "true" ]]; then
    # Args travel in an env var because Procfile processes are shell-expanded and ignore
    # container CMD args. On 'jobs execute' this flag is a per-execution override, merged with
    # the job's existing env vars, so it does not change the deployed job definition.
    EXECUTE_CMD+=(--update-env-vars="CLI_ARGS=${JOB_ARGS[*]}")
fi

echo "Running: ${EXECUTE_CMD[*]}"
"${EXECUTE_CMD[@]}"

echo ""
echo "Done!"
