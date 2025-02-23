#!/bin/bash

BASE_URL="http://0.0.0.0:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Testing Trading Endpoints...${NC}\n"

# Test strategy endpoints
echo "Testing strategy activation..."
curl -X POST "${BASE_URL}/strategies/start/rsi_strategy"
echo -e "\n"

# Test market data
echo "Testing market data..."
curl "${BASE_URL}/strategies/markets"
echo -e "\n"

# Test performance metrics
echo "Testing strategy performance..."
curl "${BASE_URL}/strategies/performance/rsi_strategy"
echo -e "\n"

echo -e "${GREEN}Tests completed${NC}"
