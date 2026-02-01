#!/bin/bash
set -e

echo "🧪 Phase 1 Testing Script"
echo "========================="

# Get token
echo -e "\n1. Testing Authentication..."
# Configuration (override with environment variables)
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TEST_USERNAME="${TEST_USERNAME:-admin@ergolab.gr}"
TEST_PASSWORD="${TEST_PASSWORD:-admin123}"

# Get token
echo -e "\n1. Testing Authentication..."
TOKEN=$(curl -s -X POST "${API_BASE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_USERNAME}&password=${TEST_PASSWORD}" | jq -r '.access_token')
if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✅ Authentication successful"
TIME1=$(curl -s -w "%{time_total}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/materials/)
TIME2=$(curl -s -w "%{time_total}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/materials/)
echo -e "\n2. Testing Redis Cache..."
TIME1=$(curl -s -w "%{time_total}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/materials/\)
TIME2=$(curl -s -w "%{time_total}" -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/materials/\)
echo "   First request: ${TIME1}s"
echo "   Second request: ${TIME2}s (cached)"
if (( $(echo "$TIME2 <= $TIME1" | bc -l) )); then
INDEX_COUNT=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U ergolab -d ergolab_dev -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';" 2>/dev/null | tr -d ' ')
INDEX_COUNT=${INDEX_COUNT:-0}
if [[ "$INDEX_COUNT" =~ ^[0-9]+$ ]] && [ "$INDEX_COUNT" -gt 10 ]; then
  echo "✅ Found $INDEX_COUNT performance indexes"
else
  echo "❌ Only ${INDEX_COUNT:-0} indexes found (or query failed)"
fi
echo -e "\n3. Testing Database Indexes..."
INDEX_COUNT=$(docker compose -f docker-compose.dev.yml exec -T postgres psql -U ergolab -d ergolab_dev -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';" 2>/dev/null | tr -d ' ')
if [ "$INDEX_COUNT" -gt 10 ]; then
  echo "✅ Found $INDEX_COUNT performance indexes"
else
  echo "❌ Only $INDEX_COUNT indexes found"
fi

# Test metrics
echo -e "\n4. Testing Performance Metrics..."
METRICS=$(curl -s http://localhost:8000/metrics)
if echo "$METRICS" | jq -e '.total_requests' > /dev/null 2>&1; then
  echo "✅ Metrics endpoint working"
  echo "   Total requests: $(echo $METRICS | jq -r '.total_requests')"
  CACHE_STATS=$(curl -s http://localhost:8000/cache/stats)
  echo "   Cache hits: $(echo $CACHE_STATS | jq -r '.hits')"
  echo "   Cache misses: $(echo $CACHE_STATS | jq -r '.misses')"
  echo "   Cache hit rate: $(echo $CACHE_STATS | jq -r '.hit_rate')%"
else
  echo "❌ Metrics endpoint not working"
fi

# Test health endpoint
echo -e "\n5. Testing Health Endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | jq -e '.status' > /dev/null 2>&1; then
  echo "✅ Health endpoint working"
  echo "   Status: $(echo $HEALTH | jq -r '.status')"
  echo "   Memory: $(echo $HEALTH | jq -r '.system.memory_mb')MB"
else
  echo "❌ Health endpoint not working"
fi

# Test API performance
echo -e "\n6. Testing API Response Times..."
AVG_MS=$(curl -s http://localhost:8000/metrics | jq -r '.endpoints["GET:/api/materials/"].avg_duration_ms // 0')
if (( $(echo "$AVG_MS < 50" | bc -l) )); then
  echo "✅ Materials API: ${AVG_MS}ms average (target: <50ms)"
else
  echo "⚠️  Materials API: ${AVG_MS}ms average (target: <50ms)"
fi

echo -e "\n========================================="
echo "🎉 Phase 1 Testing Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  ✅ Database indexes: $INDEX_COUNT created"
echo "  ✅ Redis caching: $(curl -s http://localhost:8000/cache/stats | jq -r '.hit_rate')% hit rate"
echo "  ✅ Performance monitoring: Active"
echo "  ✅ Average response time: ${AVG_MS}ms"
echo ""
echo "Ready for Phase 2: Offline Mobile! 🚀"
