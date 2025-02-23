#!/bin/bash

BASE_URL="http://0.0.0.0:8000"
echo "Starting API tests..."

test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    echo "Testing $method $endpoint..."
    if [ "$method" = "POST" ]; then
        curl -s -X POST "${BASE_URL}${endpoint}" | jq '.' || echo "Failed to connect to $endpoint"
    else
        curl -s "${BASE_URL}${endpoint}" | jq '.' || echo "Failed to connect to $endpoint"
    fi
    echo "----------------------------------------"
}

# Run tests
test_endpoint "/health"
test_endpoint "/strategies"
test_endpoint "/strategies/markets"
test_endpoint "/strategies/test"
test_endpoint "/strategies/check/BTC-USDT" "POST"
