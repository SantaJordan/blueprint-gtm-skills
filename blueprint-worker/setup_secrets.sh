#!/bin/bash
# Blueprint GTM Worker - Modal Secrets Setup
# Run this script to configure all required secrets for the Modal worker

echo "=== Blueprint GTM Worker - Secrets Setup ==="
echo ""
echo "You'll need the following API keys:"
echo "  1. ANTHROPIC_API_KEY - From console.anthropic.com"
echo "  2. SERPER_API_KEY - From serper.dev"
echo "  3. SUPABASE_URL - From your Supabase project settings"
echo "  4. SUPABASE_SERVICE_KEY - From Supabase > Settings > API > service_role key"
echo "  5. GITHUB_TOKEN - From github.com/settings/tokens (needs repo scope)"
echo ""

# Check if modal CLI is installed
if ! command -v modal &> /dev/null; then
    echo "Modal CLI not found. Installing..."
    pip install modal
fi

# Check if authenticated
if ! modal token show &> /dev/null; then
    echo "Please authenticate with Modal first:"
    echo "  modal token set --token-id YOUR_TOKEN_ID --token-secret YOUR_TOKEN_SECRET"
    exit 1
fi

echo "Enter your API keys (press Enter to skip and use existing value):"
echo ""

read -p "ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY
read -p "SERPER_API_KEY: " SERPER_API_KEY
read -p "SUPABASE_URL: " SUPABASE_URL
read -p "SUPABASE_SERVICE_KEY: " SUPABASE_SERVICE_KEY
read -p "GITHUB_TOKEN: " GITHUB_TOKEN
read -p "GITHUB_OWNER (default: SantaJordan): " GITHUB_OWNER
read -p "GITHUB_REPO (default: blueprint-gtm-playbooks): " GITHUB_REPO

# Set defaults
GITHUB_OWNER=${GITHUB_OWNER:-SantaJordan}
GITHUB_REPO=${GITHUB_REPO:-blueprint-gtm-playbooks}

echo ""
echo "Creating Modal secret 'blueprint-secrets'..."

modal secret create blueprint-secrets \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    SERPER_API_KEY="$SERPER_API_KEY" \
    SUPABASE_URL="$SUPABASE_URL" \
    SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
    GITHUB_TOKEN="$GITHUB_TOKEN" \
    GITHUB_OWNER="$GITHUB_OWNER" \
    GITHUB_REPO="$GITHUB_REPO"

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Secrets created successfully! ==="
    echo ""
    echo "Next steps:"
    echo "  1. Deploy the worker: modal deploy main.py"
    echo "  2. Copy the endpoint URL from the output"
    echo "  3. Configure Supabase webhook to call that URL"
    echo ""
else
    echo ""
    echo "Failed to create secrets. Please check your Modal authentication."
fi
