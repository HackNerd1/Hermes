#!/usr/bin/env bash
# trend-orchestrator dependency verification script
# Usage: bash scripts/verify_deps.sh
set -euo pipefail

SKILLS_DIR="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/workspace/skills}"
EXIT_CODE=0

check() {
    local name="$1"
    local path="$2"
    if [ -d "$path" ] || [ -f "$path" ]; then
        echo "  ✓ $name"
    else
        echo "  ✗ $name — missing"
        EXIT_CODE=1
    fi
}

echo "=== trend-orchestrator dependency check ==="
echo "Skills directory: $SKILLS_DIR"
echo ""

echo "Required skills:"
check "okx/agent-skills"       "$SKILLS_DIR/okx"
check "technical-indicator-pro" "$SKILLS_DIR/technical-indicators"
check "market-structure"       "$SKILLS_DIR/market-structure"
check "openmobius-skill"       "$SKILLS_DIR/openmobius"
check "rootdata-crypto"        "$SKILLS_DIR/rootdata-crypto"

echo ""
echo "Optional skills:"
check "game-theory"                  "$SKILLS_DIR/game-theory"
check "onchain-contract-token-analysis" "$SKILLS_DIR/onchain-contract-token-analysis"
check "heurist-mesh"                 "$SKILLS_DIR/heurist-mesh"
check "ccxt-python"                  "$HOME/.agents/skills/ccxt-python"

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "All required dependencies present."
else
    echo "Missing dependencies detected. See references/environment-setup.md for details."
fi

exit $EXIT_CODE
