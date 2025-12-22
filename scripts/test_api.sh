#!/bin/bash

# Script to test API endpoints
# Usage: ./scripts/test_api.sh [base_url]

BASE_URL="${1:-http://127.0.0.1:8000}"

echo "=========================================="
echo "Testing PIKA Memory API"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "  $method $endpoint"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "  ${GREEN}✓ Status: $http_code${NC}"
        echo "  Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "  ${RED}✗ Status: $http_code${NC}"
        echo "  Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
    echo ""
}

# Test 1: Root endpoint
test_endpoint "GET" "/" "" "Root endpoint"

# Test 2: Health check
test_endpoint "GET" "/api/v1/health" "" "Health check"

# Test 3: Liveness probe
test_endpoint "GET" "/api/v1/health/live" "" "Liveness probe"

# Test 4: Readiness probe
test_endpoint "GET" "/api/v1/health/ready" "" "Readiness probe"

# Test 5: Extract facts
EXTRACT_DATA='{
  "user_id": "test-user-123",
  "conversation_id": "test-conv-456",
  "conversation": [
    {"role": "user", "content": "I love playing tennis on weekends"},
    {"role": "assistant", "content": "That is great! Tennis is a wonderful sport."},
    {"role": "user", "content": "I have a cat named Whiskers"}
  ],
  "metadata": {"source": "test"}
}'
test_endpoint "POST" "/api/v1/extract_facts" "$EXTRACT_DATA" "Extract facts"

# Test 6: Search facts
SEARCH_DATA='{
  "user_id": "test-user-123",
  "query": "user favorite activities",
  "limit": 10,
  "score_threshold": 0.4
}'
test_endpoint "POST" "/api/v1/search_facts" "$SEARCH_DATA" "Search facts"

echo "=========================================="
echo "Testing completed!"
echo "=========================================="


