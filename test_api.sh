#!/bin/bash

BASE_URL="http://0.0.0.0:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Wait for API to be ready
wait_for_api() {
    echo "Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -s "http://0.0.0.0:8000/health" > /dev/null; then
            echo -e "${GREEN}API is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo -e "\n${RED}API failed to start within 30 seconds${NC}"
    return 1
}

echo -e "${GREEN}Starting API Tests...${NC}\n"

test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3

    echo -e "${YELLOW}Testing ${method} ${endpoint}...${NC}"
    echo "Request: ${method} ${BASE_URL}${endpoint}"

    if [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "${BASE_URL}${endpoint}")
        else
            response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}${endpoint}")
        fi
    else
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    echo -e "\nResponse Status Code: ${http_code}"
    echo -e "Response Body:"
    if [ $http_code -eq 200 ]; then
        echo "$body" | jq '.' || echo "$body"
        echo -e "${GREEN}✓ Test passed${NC}"
    else
        echo "$body" | jq '.' || echo "$body"
        echo -e "${RED}✗ Test failed${NC}"
    fi
    echo "----------------------------------------"
}

# Main execution
echo -e "${YELLOW}Running API Tests...${NC}\n"

if ! wait_for_api; then
    echo -e "${RED}Cannot proceed with tests - API is not responding${NC}"
    exit 1
fi

# Run tests
test_endpoint "/health"
test_endpoint "/strategies/active"
test_endpoint "/strategies/test"
test_endpoint "/strategies/markets"
test_endpoint "/strategies/start/rsi_strategy" "POST"
test_endpoint "/strategies/performance/rsi_strategy"

echo -e "\n${GREEN}All tests completed${NC}"
