<#
.SYNOPSIS
    One-command production deploy of EngineerGPT (backend + frontend + Postgres) to Fly.io.

.DESCRIPTION
    Run this from the repo root: .\deploy\fly-deploy.ps1
    It provisions two Fly apps and a managed Postgres, wires DATABASE_URL,
    sets secrets (prompted securely on THIS machine - never transmitted anywhere
    else), then deploys both services. Fly builds the Docker images on remote
    builders, so you do NOT need Docker installed locally.

    Prerequisites:
      1. Install flyctl:  iwr https://fly.io/install.ps1 -useb | iex
      2. Sign in:         fly auth login   (or: fly auth signup)

.PARAMETER ApiApp   Globally-unique name for the backend app.
.PARAMETER WebApp   Globally-unique name for the frontend app.
.PARAMETER PgApp    Globally-unique name for the Postgres app.
.PARAMETER Region   Fly region (iad, lhr, fra, sjc, syd, ...).
.PARAMETER Org      Fly organization (default: personal).
.PARAMETER AiProvider  azure | openai | mock
#>
[CmdletBinding()]
param(
    [string]$ApiApp = "engineergpt-api",
    [string]$WebApp = "engineergpt-web",
    [string]$PgApp  = "engineergpt-db",
    [string]$Region = "iad",
    [string]$Org    = "personal",
    [string]$AdminEmail = "admin@engineergpt.local",
    [string]$AdminFullName = "EngineerGPT Admin",
    [ValidateSet("azure", "openai", "mock")]
    [string]$AiProvider = "azure",
    # SaaS: public URL of the frontend (defaults to the Fly web app). Set this to
    # your Vercel URL if the frontend is hosted there instead.
    [string]$FrontendUrl = "",
    # Allow open self-service signup. Set to $false for invite-only instances.
    [bool]$AllowPublicSignup = $true,
    # Billing: enable Stripe by passing -Stripe (keys are read securely below).
    [switch]$Stripe
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Fly {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    Write-Host "fly $($Args -join ' ')" -ForegroundColor DarkGray
    & fly @Args
    if ($LASTEXITCODE -ne 0) { throw "fly $($Args -join ' ') failed (exit $LASTEXITCODE)" }
}
function Read-Secret($prompt) {
    $sec = Read-Host $prompt -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

# --- Preconditions ---------------------------------------------------------
Step "Checking flyctl"
if (-not (Get-Command fly -ErrorAction SilentlyContinue)) {
    Write-Host "flyctl not found. Install it, then re-run:" -ForegroundColor Yellow
    Write-Host "  iwr https://fly.io/install.ps1 -useb | iex" -ForegroundColor Yellow
    exit 1
}
& fly auth whoami *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Run 'fly auth login' first." -ForegroundColor Yellow; exit 1 }

# --- Collect secrets locally ----------------------------------------------
Step "Collecting configuration (input stays on this machine)"
# Values can come from environment variables (non-interactive deploys, CI) or
# from secure prompts. Env vars win when both are present.
$adminPassword = if ($env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD } else { Read-Secret "Admin password for $AdminEmail" }
$azureEndpoint = ""; $azureKey = ""; $chatDeployment = ""; $embedDeployment = ""
if ($AiProvider -eq "azure") {
    $azureEndpoint   = if ($env:AZURE_OPENAI_ENDPOINT)   { $env:AZURE_OPENAI_ENDPOINT }   else { Read-Host   "Azure OpenAI endpoint (https://<name>.openai.azure.com)" }
    $azureKey        = if ($env:AZURE_OPENAI_API_KEY)    { $env:AZURE_OPENAI_API_KEY }    else { Read-Secret "Azure OpenAI API key" }
    $chatDeployment  = if ($env:OPENAI_CHAT_MODEL)       { $env:OPENAI_CHAT_MODEL }       else { Read-Host   "Azure chat *deployment* name (e.g. gpt-4o-mini)" }
    $embedDeployment = if ($env:OPENAI_EMBEDDING_MODEL)  { $env:OPENAI_EMBEDDING_MODEL }  else { Read-Host   "Azure embedding *deployment* name (e.g. text-embedding-3-small)" }
}
elseif ($AiProvider -eq "openai") {
    $azureKey = if ($env:OPENAI_API_KEY) { $env:OPENAI_API_KEY } else { Read-Secret "OpenAI API key" }
}

# Billing (Stripe) is optional. Keys can come from env vars or secure prompts.
$stripeSecret = ""; $stripeWebhook = ""; $stripePricePro = ""; $stripePriceTeam = ""
if ($Stripe) {
    $stripeSecret    = if ($env:STRIPE_SECRET_KEY)     { $env:STRIPE_SECRET_KEY }     else { Read-Secret "Stripe secret key (sk_...)" }
    $stripeWebhook   = if ($env:STRIPE_WEBHOOK_SECRET) { $env:STRIPE_WEBHOOK_SECRET } else { Read-Secret "Stripe webhook signing secret (whsec_...)" }
    $stripePricePro  = if ($env:STRIPE_PRICE_PRO)      { $env:STRIPE_PRICE_PRO }      else { Read-Host   "Stripe Price ID for Pro plan (price_...)" }
    $stripePriceTeam = if ($env:STRIPE_PRICE_TEAM)     { $env:STRIPE_PRICE_TEAM }     else { Read-Host   "Stripe Price ID for Team plan (price_...)" }
}

$bytes = New-Object 'System.Byte[]' 48
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$secretKey = [Convert]::ToBase64String($bytes)

$apiUrl = "https://$ApiApp.fly.dev"
$webUrl = "https://$WebApp.fly.dev"
# The public frontend URL used for Stripe redirects and CORS. Defaults to the Fly
# web app, but is overridden when -FrontendUrl (e.g. a Vercel URL) is provided.
$publicWebUrl = if ($FrontendUrl) { $FrontendUrl.TrimEnd('/') } else { $webUrl }

# --- Backend app + Postgres -----------------------------------------------
Step "Creating backend app '$ApiApp'"
& fly apps create $ApiApp --org $Org 2>$null | Out-Null  # ignore 'already exists'

Step "Creating managed Postgres '$PgApp' (superuser creds print ONCE - save them)"
& fly postgres create --name $PgApp --region $Region --org $Org `
    --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1 2>$null
# (If it already exists this is a no-op failure we can ignore.)

Step "Attaching Postgres to backend (sets DATABASE_URL secret)"
& fly postgres attach $PgApp --app $ApiApp 2>$null

# --- Backend secrets -------------------------------------------------------
Step "Setting backend secrets"
$secretArgs = @(
    "SECRET_KEY=$secretKey",
    "ADMIN_EMAIL=$AdminEmail",
    "ADMIN_PASSWORD=$adminPassword",
    "ADMIN_FULL_NAME=$AdminFullName",
    "AI_PROVIDER=$AiProvider",
    "CORS_ORIGINS=[""$publicWebUrl""]",
    "FRONTEND_URL=$publicWebUrl",
    "ALLOW_PUBLIC_SIGNUP=$($AllowPublicSignup.ToString().ToLower())"
)
if ($Stripe) {
    $secretArgs += @(
        "STRIPE_SECRET_KEY=$stripeSecret",
        "STRIPE_WEBHOOK_SECRET=$stripeWebhook",
        "STRIPE_PRICE_PRO=$stripePricePro",
        "STRIPE_PRICE_TEAM=$stripePriceTeam"
    )
}
if ($AiProvider -eq "azure") {
    $secretArgs += @(
        "AZURE_OPENAI_ENDPOINT=$azureEndpoint",
        "AZURE_OPENAI_API_KEY=$azureKey",
        "OPENAI_CHAT_MODEL=$chatDeployment",
        "OPENAI_EMBEDDING_MODEL=$embedDeployment"
    )
}
elseif ($AiProvider -eq "openai") {
    $secretArgs += "OPENAI_API_KEY=$azureKey"
}
Fly secrets set --app $ApiApp --stage @secretArgs

# --- Deploy backend --------------------------------------------------------
Step "Deploying backend (remote build)"
Push-Location "$repoRoot\backend"
try { Fly deploy --config fly.toml --app $ApiApp --remote-only }
finally { Pop-Location }

# --- Frontend app + deploy -------------------------------------------------
Step "Creating frontend app '$WebApp'"
& fly apps create $WebApp --org $Org 2>$null | Out-Null

Step "Deploying frontend (baking API URL $apiUrl)"
Push-Location "$repoRoot\frontend"
try {
    Fly deploy --config fly.toml --app $WebApp --remote-only `
        --build-arg "NEXT_PUBLIC_API_BASE_URL=$apiUrl"
}
finally { Pop-Location }

# --- Done ------------------------------------------------------------------
Step "Deployed"
Write-Host "Frontend : $publicWebUrl" -ForegroundColor Green
Write-Host "Backend  : $apiUrl/docs"  -ForegroundColor Green
Write-Host "Sign in  : $AdminEmail"   -ForegroundColor Green
if ($Stripe) {
    Write-Host "`nStripe billing enabled. In the Stripe Dashboard, add a webhook endpoint:" -ForegroundColor Green
    Write-Host "  $apiUrl/api/v1/billing/webhook" -ForegroundColor Green
    Write-Host "  Events: checkout.session.completed, customer.subscription.*" -ForegroundColor DarkGray
}
Write-Host "`nIf the frontend runs on Vercel, set NEXT_PUBLIC_API_BASE_URL=$apiUrl there" -ForegroundColor DarkGray
Write-Host "and pass -FrontendUrl <your-vercel-url> so backend CORS/redirects match." -ForegroundColor DarkGray
Write-Host "`nTo enable native pgvector later: connect as the Postgres superuser," -ForegroundColor DarkGray
Write-Host "run 'CREATE EXTENSION vector;' in the app database, then:" -ForegroundColor DarkGray
Write-Host "  fly secrets set --app $ApiApp USE_PGVECTOR=true" -ForegroundColor DarkGray
