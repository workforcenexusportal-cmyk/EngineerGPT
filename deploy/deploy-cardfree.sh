#!/usr/bin/env bash
# =============================================================================
# One-command, card-free production deploy for EngineerGPT.
#
#   Backend  -> Hugging Face Spaces (Docker, free, no credit card)
#   Database -> Neon Postgres (free, no credit card)
#   Frontend -> GitHub Pages (free, uses your existing gh login)
#
# Usage:
#   1. Create two accounts with GitHub sign-in (no card anywhere):
#        - https://huggingface.co  -> token at huggingface.co/settings/tokens
#        - https://neon.tech       -> key at console.neon.tech/settings/keys
#   2. Create deploy/.env.deploy with:
#        HF_TOKEN=hf_...
#        NEON_TOKEN=...
#        ADMIN_PASSWORD=...
#        # optional:
#        AI_PROVIDER=openai        # or mock (default) / azure
#        OPENAI_API_KEY=sk-...
#        ADMIN_EMAIL=admin@example.com
#   3. Run:  bash deploy/deploy-cardfree.sh
#
# Outputs the live URLs. The frontend (GitHub Pages) calls the backend on HF.
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."          # repo root
ENV_FILE="deploy/.env.deploy"
if [ -f "$ENV_FILE" ]; then set -a; source "$ENV_FILE"; set +a; fi

: "${HF_TOKEN:?Set HF_TOKEN in $ENV_FILE (https://huggingface.co/settings/tokens)}"
: "${NEON_TOKEN:?Set NEON_TOKEN in $ENV_FILE (https://console.neon.tech/settings/keys)}"
: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD in $ENV_FILE}"

AI_PROVIDER="${AI_PROVIDER:-mock}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@engineergpt.local}"
ADMIN_FULL_NAME="${ADMIN_FULL_NAME:-EngineerGPT Admin}"
SPACE_NAME="${SPACE_NAME:-engineergpt-api}"

step() { echo; echo "=== $1 ==="; }

# --- 1. Create the HF Space ------------------------------------------------
step "Hugging Face Space ($SPACE_NAME)"
HF_USER=$(curl -s https://huggingface.co/api/whoami-v2 -H "Authorization: Bearer $HF_TOKEN" \
    | python -c "import sys,json;print(json.load(sys.stdin)['name'])")
SPACE_ID="$HF_USER/$SPACE_NAME"
echo "HF user: $HF_USER"
# 409 (already exists) is fine.
curl -s -X POST "https://huggingface.co/api/repos/create" \
    -H "Authorization: Bearer $HF_TOKEN" -H "Content-Type: application/json" \
    -d "{\"type\":\"space\",\"name\":\"$SPACE_NAME\",\"sdk\":\"docker\"}" >/dev/null || true

# --- 2. Push the backend source to the Space -------------------------------
step "Pushing backend source"
bash deploy/hf-space/sync.sh
PUSH_DIR=$(mktemp -d)
git clone --quiet "https://user:$HF_TOKEN@huggingface.co/spaces/$SPACE_ID" "$PUSH_DIR"
cp -r deploy/hf-space/. "$PUSH_DIR/"
( cd "$PUSH_DIR" \
  && git add -A \
  && git -c user.email="deploy@localhost" -c user.name="engineergpt-deploy" commit --quiet -m "deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true \
  && git push --quiet origin main )
rm -rf "$PUSH_DIR"

# --- 3. Neon Postgres -------------------------------------------------------
# Skip provisioning when DATABASE_URL is already provided (e.g. you created the
# DB yourself or reused an existing one).
if [ -z "${DATABASE_URL:-}" ]; then
    step "Neon database"
    # Neon moved its API to console.neon.tech/api/v2 and personal API keys need
    # an org_id (auto-detected below).
    NEON_BASE="https://console.neon.tech/api/v2"
    ORG_ID=$(curl -s "$NEON_BASE/users/me/organizations" \
        -H "Authorization: Bearer $NEON_TOKEN" \
        | python -c "import sys,json;print(json.load(sys.stdin)['organizations'][0]['id'])" \
        || true)
    NEON_JSON=$(curl -s -X POST "$NEON_BASE/projects?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" -H "Content-Type: application/json" \
        -d '{"project":{"name":"engineergpt"}}')
    PROJECT_ID=$(echo "$NEON_JSON" | python -c \
        "import sys,json;print(json.load(sys.stdin).get('project',{}).get('id',''))" 2>/dev/null || true)
    if [ -z "$PROJECT_ID" ]; then
        echo "Neon auto-provisioning failed:"
        echo "$NEON_JSON" | head -c 500
        echo
        echo "Create a free project manually at console.neon.tech and set"
        echo "DATABASE_URL=postgresql://user:pass@host/db?sslmode=require in $ENV_FILE, then re-run."
        exit 1
    fi
    BRANCH_ID=$(curl -s "$NEON_BASE/projects/$PROJECT_ID/branches?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" \
        | python -c "import sys,json;print(json.load(sys.stdin)['branches'][0]['id'])")
    ROLE=$(curl -s "$NEON_BASE/projects/$PROJECT_ID/branches/$BRANCH_ID/roles?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" \
        | python -c "import sys,json;print(json.load(sys.stdin)['roles'][0]['name'])")
    DBNAME=$(curl -s "$NEON_BASE/projects/$PROJECT_ID/branches/$BRANCH_ID/databases?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" \
        | python -c "import sys,json;print(json.load(sys.stdin)['databases'][0]['name'])")
    HOST=$(curl -s "$NEON_BASE/projects/$PROJECT_ID/endpoints?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" \
        | python -c "import sys,json;print(json.load(sys.stdin)['endpoints'][0]['host'])")
    PASS=$(curl -s -X POST "$NEON_BASE/projects/$PROJECT_ID/branches/$BRANCH_ID/roles/$ROLE/reset_password?org_id=$ORG_ID" \
        -H "Authorization: Bearer $NEON_TOKEN" -H "accept: application/json" \
        | python -c "import sys,json;print(json.load(sys.stdin)['password'])")
    DATABASE_URL="postgresql://$ROLE:$PASS@$HOST/$DBNAME?sslmode=require"
    echo "Created Neon project ($PROJECT_ID)."
else
    echo "Using DATABASE_URL from $ENV_FILE (skipping Neon provisioning)."
fi

# --- 4. Backend secrets on the Space ----------------------------------------
step "Setting Space secrets"
set_secret() { # key value
    curl -s -X POST "https://huggingface.co/api/spaces/$SPACE_ID/secrets" \
        -H "Authorization: Bearer $HF_TOKEN" -H "Content-Type: application/json" \
        -d "{\"key\":\"$1\",\"value\":\"$2\"}" >/dev/null || echo "  !! failed to set $1"
}
SECRET_KEY=$(openssl rand -base64 48)
BACKEND_URL="https://$HF_USER-$SPACE_NAME.hf.space"
CORS_ORIGINS="[\"https://$HF_USER.github.io/EngineerGPT\",\"http://localhost:3000\"]"
set_secret ENVIRONMENT      production
set_secret SECRET_KEY       "$SECRET_KEY"
set_secret DATABASE_URL     "$DATABASE_URL"
set_secret AI_PROVIDER      "$AI_PROVIDER"
set_secret ADMIN_EMAIL      "$ADMIN_EMAIL"
set_secret ADMIN_PASSWORD   "$ADMIN_PASSWORD"
set_secret ADMIN_FULL_NAME  "$ADMIN_FULL_NAME"
set_secret CORS_ORIGINS     "$CORS_ORIGINS"
[ -n "${OPENAI_API_KEY:-}" ] && set_secret OPENAI_API_KEY "$OPENAI_API_KEY"

# --- 5. Frontend -> GitHub Pages (needs gh) ----------------------------------
step "Frontend (GitHub Pages)"
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
    echo "Building static export for $REPO (API: $BACKEND_URL)"
    if ! ( cd frontend && EXPORT_STATIC=1 NEXT_PUBLIC_API_BASE_URL="$BACKEND_URL" npm run build ); then
        echo "!! Frontend static export build failed — backend is deployed, but the"
        echo "   frontend was not published. Check the build output above."
        exit 0
    fi
    GH_PAGES=$(mktemp -d)
    git worktree add --quiet "$GH_PAGES" gh-pages 2>/dev/null || git worktree add --quiet --detach "$GH_PAGES"
    rm -rf "$GH_PAGES"/*
    cp -r frontend/out/* "$GH_PAGES/" 2>/dev/null || true
    ( cd "$GH_PAGES" \
      && git add -A \
      && git -c user.email="deploy@localhost" -c user.name="engineergpt-deploy" commit --quiet -m "deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true \
      && git push --quiet --force origin gh-pages )
    git worktree remove --force "$GH_PAGES"
    gh api -X POST "repos/$REPO/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null 2>&1 \
        || echo "Pages may already be enabled for $REPO."
    echo "Frontend: https://$HF_USER.github.io/EngineerGPT/"
else
    echo "gh CLI not authenticated — deploy the frontend manually (Vercel/Render/any static host)."
fi

# --- Done --------------------------------------------------------------------
step "Deployed (card-free)"
echo "Backend API : $BACKEND_URL/docs"
echo "Health      : $BACKEND_URL/health"
echo "Sign in     : $ADMIN_EMAIL"
echo
echo "First request after a cold start may take 30-60s (free tier sleep)."
