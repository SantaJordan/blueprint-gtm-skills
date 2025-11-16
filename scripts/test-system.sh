#!/bin/bash

# Blueprint Turbo Mobile Trigger System Test Script
# This script tests all components to verify the system is working

set -e

echo "🧪 Blueprint Turbo Mobile Trigger System Test"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
PASSED=0
FAILED=0

# Test function
test_component() {
    local name="$1"
    local command="$2"

    echo -n "Testing $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1️⃣  Checking Prerequisites"
echo "-------------------------"

test_component "Node.js installed" "which node"
test_component "npm installed" "which npm"
test_component "Claude Code CLI" "which claude"
test_component "Supabase npm package" "test -f scripts/node_modules/@supabase/supabase-js/package.json"

echo ""
echo "2️⃣  Checking Configuration Files"
echo "--------------------------------"

test_component "Auto-approval settings" "grep -q 'mcp__browser-mcp__' .claude/settings.local.json"
test_component "Worker script exists" "test -x scripts/blueprint-worker.js"
test_component "LaunchAgent plist exists" "test -f scripts/com.blueprint.worker.plist"
test_component "Vercel API exists" "test -f blueprint-trigger-api/api/queue-job.js"

echo ""
echo "3️⃣  Checking Supabase Connection"
echo "---------------------------------"

if [ -f scripts/node_modules/@supabase/supabase-js/package.json ]; then
    echo -n "Testing Supabase connection... "

    # Create a simple test script
    cat > /tmp/test-supabase.js << 'EOF'
import { createClient } from '@supabase/supabase-js';
const supabase = createClient(
  'https://hvuwlhdaswixbkglnrxu.supabase.co',
  'sb_secret_0cX7akELvjfchOXhqNBe8g_XcLu22co'
);
const { data, error } = await supabase.from('blueprint_jobs').select('count').limit(1);
if (error) {
  console.error(error);
  process.exit(1);
}
console.log('Connected successfully');
EOF

    if (cd scripts && node /tmp/test-supabase.js) > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "   Could not connect to Supabase. Check your keys."
        ((FAILED++))
    fi

    rm /tmp/test-supabase.js
else
    echo -e "${YELLOW}⊘ SKIP - Dependencies not installed${NC}"
fi

echo ""
echo "4️⃣  Checking LaunchAgent Status"
echo "--------------------------------"

echo -n "Checking if worker is running... "
if launchctl list | grep -q "com.blueprint.worker"; then
    echo -e "${GREEN}✓ RUNNING${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⊘ NOT RUNNING${NC}"
    echo "   Run: cd scripts && npm run install-service"
fi

echo ""
echo "5️⃣  Checking Log Files"
echo "----------------------"

if [ -d logs ]; then
    echo -e "${GREEN}✓${NC} Logs directory exists"

    if [ -f logs/blueprint-worker.log ]; then
        echo -e "${GREEN}✓${NC} Worker log file exists"
        LINES=$(wc -l < logs/blueprint-worker.log)
        echo "   Log has $LINES lines"
    else
        echo -e "${YELLOW}⊘${NC} Worker log file not created yet (will be created when worker starts)"
    fi
else
    echo -e "${YELLOW}⊘${NC} Logs directory doesn't exist yet"
fi

echo ""
echo "📊 Test Results"
echo "==============="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy Vercel API: cd blueprint-trigger-api && vercel"
    echo "2. Install worker: cd scripts && npm run install-service"
    echo "3. Create iOS Shortcut: See PHONE_SETUP.md"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please fix the failed tests before proceeding."
    echo "See PHONE_SETUP.md for detailed setup instructions."
    echo ""
    exit 1
fi
