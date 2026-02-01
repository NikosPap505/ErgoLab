#!/bin/bash

# ErgoLab Security Check Script
# Ελέγχει για πιθανά θέματα ασφαλείας πριν το commit

set -e

echo "🔒 ErgoLab Security Check"
echo "========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# 1. Check for .env files
echo "1. Έλεγχος για .env αρχεία..."
ENV_FILES=$(git status --short | grep -E "^\?\?" | grep -E "\.env$|\.env\.local$|\.env\.production$|\.env\.development$" || true)
if [ -n "$ENV_FILES" ]; then
    echo -e "${RED}❌ Βρέθηκαν .env αρχεία που δεν είναι στο .gitignore:${NC}"
    echo "$ENV_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✓ Δεν βρέθηκαν .env αρχεία${NC}"
fi
echo ""

# 2. Check for certificates and keys
echo "2. Έλεγχος για πιστοποιητικά και keys..."
KEY_FILES=$(git status --short | grep -E "^\?\?" | grep -E "\.(key|pem|pfx|p12|crt|cer)$" || true)
if [ -n "$KEY_FILES" ]; then
    echo -e "${RED}❌ Βρέθηκαν πιστοποιητικά/keys:${NC}"
    echo "$KEY_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✓ Δεν βρέθηκαν πιστοποιητικά${NC}"
fi
echo ""

# 3. Check for backup files
echo "3. Έλεγχος για backup αρχεία..."
BACKUP_FILES=$(git status --short | grep -E "^\?\?" | grep -E "\.(backup|bak|old|dump|sql)$" || true)
if [ -n "$BACKUP_FILES" ]; then
    echo -e "${YELLOW}⚠️  Βρέθηκαν backup αρχεία:${NC}"
    echo "$BACKUP_FILES"
    echo "   Βεβαιωθείτε ότι δεν περιέχουν ευαίσθητα δεδομένα"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✓ Δεν βρέθηκαν backup αρχεία${NC}"
fi
echo ""

# 4. Check for hardcoded passwords in staged files
echo "4. Έλεγχος για hardcoded passwords σε staged αρχεία..."
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "\.(py|js|jsx|ts|tsx|yml|yaml|json)$" || true)
if [ -n "$STAGED_FILES" ]; then
    SUSPICIOUS_PATTERNS=0
    for FILE in $STAGED_FILES; do
        # Check for common password patterns
        MATCHES=$(git diff --cached "$FILE" | grep -iE "password\s*[:=]\s*['\"][^'\"]{8,}['\"]|secret\s*[:=]\s*['\"][^'\"]{8,}['\"]|api[_-]?key\s*[:=]\s*['\"][^'\"]{8,}['\"]" | grep -v "example\|sample\|template\|your_" || true)
        if [ -n "$MATCHES" ]; then
            echo -e "${RED}❌ Πιθανό hardcoded password σε: $FILE${NC}"
            echo "$MATCHES"
            SUSPICIOUS_PATTERNS=$((SUSPICIOUS_PATTERNS + 1))
        fi
    done
    
    if [ $SUSPICIOUS_PATTERNS -eq 0 ]; then
        echo -e "${GREEN}✓ Δεν βρέθηκαν hardcoded passwords${NC}"
    else
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${GREEN}✓ Δεν υπάρχουν staged αρχεία για έλεγχο${NC}"
fi
echo ""

# 5. Check .env.example files don't contain real credentials
echo "5. Έλεγχος .env.example αρχείων..."
ENV_EXAMPLES=$(git diff --cached --name-only --diff-filter=ACM | grep "\.env\.example$" || true)
if [ -n "$ENV_EXAMPLES" ]; then
    for FILE in $ENV_EXAMPLES; do
        # Check for patterns that look like real credentials (not placeholders)
        REAL_CREDS=$(git diff --cached "$FILE" | grep -E "^\+.*[:=]" | grep -viE "your_|example|changeme|placeholder|xxx|<.*>|sample|template|\[.*\]|{.*}|password123" || true)
        if [ -n "$REAL_CREDS" ]; then
            echo -e "${YELLOW}⚠️  Το $FILE μπορεί να περιέχει πραγματικά credentials:${NC}"
            echo "$REAL_CREDS"
            echo "   Βεβαιωθείτε ότι χρησιμοποιείτε placeholders"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    done
else
    echo -e "${GREEN}✓ Δεν υπάρχουν αλλαγές σε .env.example${NC}"
fi
echo ""

# 6. Check for secrets/ directories
echo "6. Έλεγχος για secrets/ directories..."
SECRETS_DIRS=$(git status --short | grep -E "^\?\?" | grep -i "secret" || true)
if [ -n "$SECRETS_DIRS" ]; then
    echo -e "${RED}❌ Βρέθηκαν directories/files με 'secret' στο όνομα:${NC}"
    echo "$SECRETS_DIRS"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✓ Δεν βρέθηκαν secrets directories${NC}"
fi
echo ""

# 7. Check for large files (might be data dumps)
echo "7. Έλεγχος για μεγάλα αρχεία..."
LARGE_FILES=$(git status --short | grep -E "^\?\?" | awk '{print $2}' | while read -r f; do du -h "$f" 2>/dev/null; done | awk '$1 ~ /[MG]$/ {print}' || true)
if [ -n "$LARGE_FILES" ]; then
    echo -e "${YELLOW}⚠️  Βρέθηκαν μεγάλα αρχεία (>1MB):${NC}"
    echo "$LARGE_FILES"
    echo "   Βεβαιωθείτε ότι δεν είναι database dumps ή logs με ευαίσθητα δεδομένα"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# Summary
echo "========================="
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ Όλοι οι έλεγχοι ασφαλείας πέρασαν!${NC}"
    exit 0
else
    echo -e "${RED}❌ Βρέθηκαν $ISSUES_FOUND πιθανά θέματα ασφαλείας${NC}"
    echo ""
    echo "Παρακαλώ διορθώστε τα παραπάνω πριν κάνετε commit."
    echo "Για περισσότερες πληροφορίες, δείτε το SECURITY_CHECKLIST.md"
    exit 1
fi
