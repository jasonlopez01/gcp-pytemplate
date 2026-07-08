#!/usr/bin/env bash

# Call the deployed {{ project_name }} Cloud Run *service* (the API) behind IAM.
#
# The service is deployed with --no-allow-unauthenticated, so every request needs a Google-signed
# identity token. This resolves the service URL from the deploy config, mints a token for the
# caller (who must hold roles/run.invoker), and curls the endpoint.
#
# Usage:
#   ./scripts/invoke_cloud_run.sh <deploy_config_file> --health
#   ./scripts/invoke_cloud_run.sh <deploy_config_file> <METHOD> <PATH>
#
# Examples:
#   ./scripts/invoke_cloud_run.sh stage.deploy.env --health
#   ./scripts/invoke_cloud_run.sh stage.deploy.env GET /api/list
#   ./scripts/invoke_cloud_run.sh stage.deploy.env POST '/api/things?limit=10'
#
# Requirements:
#   - gcloud CLI installed and authenticated (caller has run.invoker on the service)
#   - Service already deployed (run deploy_cloud_run.sh first)
#   - Deploy config file present in deploy_configs/

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────

DEPLOY_CONFIG_FILENAME=${1:-}

if [[ -z "${DEPLOY_CONFIG_FILENAME}" ]]; then
    echo "Error: deploy config argument required."
    echo "Usage: $0 <deploy_config_file> [--health | <METHOD> <PATH>]"
    echo "Example: $0 stage.deploy.env GET /api/list"
    exit 1
fi
shift

# ── Build the request (method + path) from the remaining args ─────────────────

case "${1:-}" in
    --health)
        METHOD="GET"
        REQUEST_PATH="/healthcheck"
        ;;
    "" | -*)
        echo "Error: expected --health or '<METHOD> <PATH>', got '${1:-}'."
        exit 1
        ;;
    *)
        METHOD=$1
        REQUEST_PATH=${2:?"Error: a request PATH is required (e.g. GET /api/list)."}
        ;;
esac

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

# ── Resolve service URL + identity token ──────────────────────────────────────

SERVICE_URL="$(gcloud run services describe "${GCR_SERVICE_NAME}" \
    --project="${GCP_PROJECT}" \
    --region="${GCP_REGION}" \
    --format="value(status.url)" 2>/dev/null || true)"

if [[ -z "${SERVICE_URL}" ]]; then
    echo "Error: could not resolve URL for service '${GCR_SERVICE_NAME}' (is it deployed?)."
    exit 1
fi

TOKEN="$(gcloud auth print-identity-token)"

# ── Confirm ───────────────────────────────────────────────────────────────────

echo ""
echo "  Service: ${GCR_SERVICE_NAME}"
echo "  Project: ${GCP_PROJECT}"
echo "  Region:  ${GCP_REGION}"
echo "  Request: ${METHOD} ${SERVICE_URL}${REQUEST_PATH}"
echo ""

# ── Invoke ────────────────────────────────────────────────────────────────────

# A synchronous handler can take a while; let it run to the service timeout rather than curl's
# default. --fail-with-body surfaces non-2xx as a failing exit.
curl --silent --show-error --fail-with-body --max-time 3600 \
    --request "${METHOD}" \
    --header "Authorization: Bearer ${TOKEN}" \
    --write-out $'\nHTTP %{http_code}  (%{time_total}s)\n' \
    "${SERVICE_URL}${REQUEST_PATH}"
