#!/bin/bash

# Comprehensive Frontend-Backend Connectivity Test
# Tests all API endpoints using curl

BACKEND_URL="http://localhost:8080"
FRONTEND_URL="http://localhost:3015"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Starting Frontend-Backend Connectivity Tests...${NC}"
echo ""

passed=0
total=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    
    echo -e "${YELLOW}📡 Testing: $name${NC}"
    
    total=$((total + 1))
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            --connect-timeout 5 \
            "$url" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" \
            --connect-timeout 5 \
            "$url" 2>/dev/null)
    fi
    
    # Extract status code (last line) and body (everything else)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✅ $name: $status_code${NC}"
        if [ ${#body} -lt 200 ]; then
            echo "   Response: $body"
        else
            echo "   Response size: ${#body} bytes"
        fi
        passed=$((passed + 1))
    else
        echo -e "${RED}❌ $name: $status_code${NC}"
        if [ -n "$body" ]; then
            echo "   Error: $body"
        fi
    fi
    echo ""
}

# Test 1: Backend Health
test_endpoint "Health Check" "GET" "$BACKEND_URL/health"

# Test 2: Frontend Availability  
test_endpoint "Frontend Check" "GET" "$FRONTEND_URL"

# Test 3: Path Validation
test_endpoint "Validate Path" "POST" "$BACKEND_URL/api/filesystem/validate" \
    '{"path": ".", "include_hidden": false, "python_only": false}'

# Test 4: File Listing
test_endpoint "List Files" "GET" "$BACKEND_URL/api/files?path=.&python_only=true&limit=5"

# Test 5: Directory Browsing
test_endpoint "Browse Directory" "GET" "$BACKEND_URL/api/filesystem/browse?path=.&show_hidden=false"

# Test 6: Copy for Analysis
test_endpoint "Copy for Analysis" "POST" "$BACKEND_URL/api/analysis/copy-for-analysis" \
    '{"source_path": ".", "python_only": true}'

# Summary
echo -e "${BLUE}📊 Test Summary:${NC}"
echo -e "${GREEN}✅ Passed: $passed/$total${NC}"

failed=$((total - passed))
if [ $failed -gt 0 ]; then
    echo -e "${RED}❌ Failed: $failed/$total${NC}"
fi

echo ""
echo -e "${BLUE}🔍 System Status:${NC}"

# Check if backend is running
if pgrep -f "python main.py" > /dev/null; then
    echo -e "${GREEN}✅ Backend process is running${NC}"
else
    echo -e "${RED}❌ Backend process not found${NC}"
    echo -e "${YELLOW}💡 Try: npm run start:backend${NC}"
fi

# Check if frontend is running
if pgrep -f "vite" > /dev/null; then
    echo -e "${GREEN}✅ Frontend process is running${NC}"
else
    echo -e "${RED}❌ Frontend process not found${NC}"
    echo -e "${YELLOW}💡 Try: cd frontend && npm run dev${NC}"
fi

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Restart backend: npm run start:backend"
echo "2. Test frontend: Open http://localhost:3015 in browser"  
echo "3. Check browser console for frontend errors"
echo "4. Monitor backend logs for API calls"

exit $failed 