#!/bin/bash
set -e

echo "🧪 Phase 2: Offline-First Testing Script"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Failure counter for non-fatal checks
FAILURE_COUNT=0

echo -e "\n${BLUE}📱 ErgoLab Mobile Offline-First Testing${NC}"
echo "=========================================="

# Test 1: Check if offline database exists
echo -e "\n${YELLOW}Test 1: Offline Database Setup${NC}"

SCRIPT_DIR="$(pwd)"
APP_DIR="mobile_app/field_app"

if [ ! -d "$APP_DIR" ]; then
  echo -e "${RED}✗${NC} Directory $APP_DIR not found. Run this script from the repository root."
  exit 1
fi

cd "$APP_DIR"
trap "cd '$SCRIPT_DIR'" EXIT

if grep -q "sqflite" pubspec.yaml; then
  echo -e "${GREEN}✓${NC} SQLite dependency found"
else
  echo -e "${RED}✗${NC} SQLite dependency missing"
  exit 1
fi

# Test 2: Verify sync service
echo -e "\n${YELLOW}Test 2: Sync Service${NC}"
if [ -f "lib/services/sync_service.dart" ]; then
  echo -e "${GREEN}✓${NC} Sync service exists"
  if grep -q "syncAll" lib/services/sync_service.dart; then
    echo -e "${GREEN}✓${NC} syncAll() method found"
  fi
  if grep -q "syncPendingTransactions" lib/services/sync_service.dart; then
    echo -e "${GREEN}✓${NC} syncPendingTransactions() method found"
  fi
else
  echo -e "${RED}✗${NC} Sync service missing"
  exit 1
fi

# Test 3: Connectivity service
echo -e "\n${YELLOW}Test 3: Connectivity Service${NC}"
if [ -f "lib/services/connectivity_service.dart" ]; then
  echo -e "${GREEN}✓${NC} Connectivity service exists"
  if grep -q "isOnline" lib/services/connectivity_service.dart; then
    echo -e "${GREEN}✓${NC} isOnline property found"
  fi
else
  echo -e "${RED}✗${NC} Connectivity service missing"
  exit 1
fi

# Test 4: Image compression
echo -e "\n${YELLOW}Test 4: Image Compression Service${NC}"
if [ -f "lib/services/image_compression_service.dart" ]; then
  echo -e "${GREEN}✓${NC} Image compression service exists"
# Test 5: Offline database schema
echo -e "\n${YELLOW}Test 5: Database Schema${NC}"
if [ ! -f "lib/services/offline_database.dart" ]; then
  echo -e "${RED}✗${NC} offline_database.dart not found"
  exit 1
fi

if grep -q "cached_materials" lib/services/offline_database.dart; then
  echo -e "${GREEN}✓${NC} cached_materials table defined"
else
  echo -e "${RED}✗${NC} cached_materials table missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if grep -q "pending_transactions" lib/services/offline_database.dart; then
  echo -e "${GREEN}✓${NC} pending_transactions table defined"
else
  echo -e "${RED}✗${NC} pending_transactions table missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if grep -q "cached_warehouses" lib/services/offline_database.dart; then
  echo -e "${GREEN}✓${NC} cached_warehouses table defined"
else
  echo -e "${RED}✗${NC} cached_warehouses table missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if grep -q "cached_inventory" lib/services/offline_database.dart; then
  echo -e "${GREEN}✓${NC} cached_inventory table defined"
else
  echo -e "${RED}✗${NC} cached_inventory table missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

if grep -q "pending_uploads" lib/services/offline_database.dart; then
  echo -e "${GREEN}✓${NC} pending_uploads table defined"
else
  echo -e "${RED}✗${NC} pending_uploads table missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

# Test 6: Offline UI widgets
echo -e "\n${YELLOW}Test 6: Offline UI Components${NC}"
if [ -f "lib/widgets/offline_widgets.dart" ]; then
  echo -e "${GREEN}✓${NC} Offline widgets file exists"
  if grep -q "OfflineBanner" lib/widgets/offline_widgets.dart; then
    echo -e "${GREEN}✓${NC} OfflineBanner widget found"
  else
    echo -e "${RED}✗${NC} OfflineBanner widget missing"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
  fi
  if grep -q "SyncStatusIndicator" lib/widgets/offline_widgets.dart; then
    echo -e "${GREEN}✓${NC} SyncStatusIndicator widget found"
  else
    echo -e "${RED}✗${NC} SyncStatusIndicator widget missing"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
  fi
else
  echo -e "${RED}✗${NC} Offline widgets missing"
  FAILURE_COUNT=$((FAILURE_COUNT + 1))
fi

# Test 7: Check screens for offline support
echo -e "\n${YELLOW}Test 7: Screen Offline Integration${NC}"

# Home Screen
if grep -q "ConnectivityService" lib/screens/home_screen.dart 2>/dev/null; then
  echo -e "${GREEN}✓${NC} HomeScreen has connectivity support"
else
  echo -e "${YELLOW}⚠${NC} HomeScreen may need connectivity integration"
fi

# Inventory Screen
if grep -q "isOnline\|ConnectivityService" lib/screens/inventory_screen.dart 2>/dev/null; then
  echo -e "${GREEN}✓${NC} InventoryScreen has offline support"
else
  echo -e "${YELLOW}⚠${NC} InventoryScreen may need offline support"
fi

# Scanner Screen
if grep -q "getCachedMaterialBySku\|isOnline" lib/screens/scanner_screen.dart 2>/dev/null; then
  echo -e "${GREEN}✓${NC} ScannerScreen has offline SKU lookup"
else
  echo -e "${YELLOW}⚠${NC} ScannerScreen may need offline lookup"
fi

# Capture Screen
if grep -q "addPendingUpload\|pending_uploads" lib/screens/capture_screen.dart 2>/dev/null; then
  echo -e "${GREEN}✓${NC} CaptureScreen has offline upload queue"
else
  echo -e "${YELLOW}⚠${NC} CaptureScreen may need offline upload support"
fi

# Summary
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}Summary:${NC}"
echo -e "${BLUE}================================================${NC}"

if [ $FAILURE_COUNT -eq 0 ]; then
  echo -e "\n${GREEN}✓ All Automated Tests Passed!${NC}"
else
  echo -e "\n${RED}✗ Automated Tests Failed: $FAILURE_COUNT check(s) failed${NC}"
  echo -e "${YELLOW}Review the failures above before proceeding.${NC}"
fi
echo ""
echo -e "${YELLOW}Manual Testing Checklist:${NC}"
echo "  1. [ ] Start app with backend running"
echo "  2. [ ] Login as user"
echo "  3. [ ] Navigate to inventory - verify data loads"
echo "  4. [ ] Enable Airplane Mode on device"
echo "  5. [ ] Verify 'Offline' indicator appears"
echo "  6. [ ] Try to scan barcode - should use local lookup"
echo "  7. [ ] Add stock transaction - should queue for sync"
echo "  8. [ ] View inventory - should show cached data"
echo "  9. [ ] Take photo - should save for later upload"
echo " 10. [ ] Disable Airplane Mode"
echo " 11. [ ] Verify auto-sync triggered"
echo " 12. [ ] Check pending count decreases"
echo ""

if [ $FAILURE_COUNT -eq 0 ]; then
  echo -e "${GREEN}🎉 Phase 2 Offline-First Tests Complete!${NC}"
  echo "All automated checks passed. Complete manual tests above."
else
  echo -e "${RED}⚠ Phase 2 Offline-First Tests Completed with Failures${NC}"
  echo "$FAILURE_COUNT automated check(s) failed. Fix issues before manual testing."
fi
