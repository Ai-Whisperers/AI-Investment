#!/bin/bash
# Security check script to ensure no secrets are committed
# Run this before pushing to GitHub

set -e

echo "🔍 SECURITY CHECK: Scanning for sensitive files and data..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

echo "1. Checking for tracked sensitive files..."
SENSITIVE_FILES=$(git ls-files | grep -E "\.(db|sqlite|sqlite3|env|pem|key|crt|cert)$" | grep -v "\.example" | grep -v "\.production$" || true)
if [ ! -z "$SENSITIVE_FILES" ]; then
    echo -e "${RED}❌ DANGER: Sensitive files found in Git:${NC}"
    echo "$SENSITIVE_FILES"
    ERRORS=$((ERRORS + 1))
fi

echo "2. Checking for hardcoded secrets in code..."
SECRET_PATTERNS=(
    "sk_[a-zA-Z0-9]+"          # Stripe keys
    "pk_[a-zA-Z0-9]+"          # Stripe public keys  
    "AIza[0-9A-Za-z\\-_]{35}"   # Google API keys
    "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}" # UUIDs
    "password.*=.*[\"'][^\"']{8,}[\"']" # Hardcoded passwords
    "secret.*=.*[\"'][^\"']{8,}[\"']"   # Hardcoded secrets
    "token.*=.*[\"'][^\"']{8,}[\"']"    # Hardcoded tokens
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    MATCHES=$(git ls-files | xargs grep -l "$pattern" 2>/dev/null | grep -v ".gitignore" | grep -v "check-secrets.sh" || true)
    if [ ! -z "$MATCHES" ]; then
        echo -e "${YELLOW}⚠️ WARNING: Potential secrets found:${NC}"
        echo "$MATCHES"
        echo "  Pattern: $pattern"
        # Don't count as error since these might be examples
    fi
done

echo "3. Checking for database files..."
DB_FILES=$(find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) ! -path "./node_modules/*" ! -path "./.git/*" || true)
if [ ! -z "$DB_FILES" ]; then
    echo -e "${RED}❌ Database files found (should not be committed):${NC}"
    echo "$DB_FILES"
    ERRORS=$((ERRORS + 1))
fi

echo "4. Checking for local data directories..."
DATA_DIRS=$(find . -type d -name "*data*" ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./docs/*" || true)
if [ ! -z "$DATA_DIRS" ]; then
    echo -e "${YELLOW}⚠️ Data directories found:${NC}"
    echo "$DATA_DIRS"
    echo "  Ensure these don't contain sensitive data"
fi

echo "5. Checking .env files are ignored..."
ENV_FILES=$(git ls-files | grep "\.env$" || true)
if [ ! -z "$ENV_FILES" ]; then
    echo -e "${RED}❌ .env files are tracked (they should be ignored):${NC}"
    echo "$ENV_FILES"
    ERRORS=$((ERRORS + 1))
fi

echo "6. Checking for large files..."
LARGE_FILES=$(git ls-files | xargs ls -l 2>/dev/null | awk '$5 > 1048576 {print $5, $9}' || true)
if [ ! -z "$LARGE_FILES" ]; then
    echo -e "${YELLOW}⚠️ Large files found (>1MB):${NC}"
    echo "$LARGE_FILES"
    echo "  Consider using Git LFS or excluding from repo"
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ SECURITY CHECK PASSED${NC}"
    echo "✅ No sensitive data found"
    echo "✅ Repository is safe to push to GitHub"
else
    echo -e "${RED}❌ SECURITY CHECK FAILED${NC}"
    echo "❌ Found $ERRORS critical issues"
    echo "🚨 DO NOT PUSH until issues are resolved!"
    echo ""
    echo "To fix:"
    echo "1. Remove sensitive files: git rm --cached <file>"
    echo "2. Add to .gitignore and commit"
    echo "3. Rotate any exposed secrets"
    echo "4. Re-run this check"
    exit 1
fi
echo "=========================================="