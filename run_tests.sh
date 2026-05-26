#!/bin/bash

# ============================================================
#  Bizify — Full Test Suite Runner
#  Run this file to execute ALL 102 integration tests at once
#  Usage: bash run_tests.sh
# ============================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║        Bizify — Automation Test Suite        ║${NC}"
echo -e "${CYAN}${BOLD}║              129 Integration Tests           ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Navigate to project root (the folder containing this script)
cd "$(dirname "$0")"

# Check that the virtual environment exists
if [ ! -f ".venv/bin/pytest" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
    echo "Please run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

echo -e "${YELLOW}Starting tests...${NC}"
echo ""

# Run ALL tests with verbose output, suppressing deprecation warnings
.venv/bin/pytest tests/ \
    -W ignore \
    -v \
    --tb=short \
    --no-header \
    -q

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅  ALL TESTS PASSED — System is healthy!${NC}"
else
    echo -e "${RED}${BOLD}❌  SOME TESTS FAILED — Check output above.${NC}"
fi
echo ""

exit $EXIT_CODE
