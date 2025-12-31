#!/bin/bash

# Start All Services for Local QWEN3-8B Integration
# This script starts the model server, backend, and frontend in sequence

echo "🚀 Starting All Services for Local QWEN3-8B Integration"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running on a port
check_service() {
    local port=$1
    local service_name=$2
    local health_url=$3

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        # Port is in use, check if service is responding
        if curl -s "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is already running${NC}"
            return 2  # Service is running
        else
            echo -e "${YELLOW}⚠️  Port $port is in use but $service_name not responding${NC}"
            return 1  # Port occupied but service not responding
        fi
    else
        echo -e "${BLUE}⏳ $service_name not running${NC}"
        return 0  # Service not running
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${BLUE}⏳ Waiting for $service_name to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi

        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - $service_name not ready yet...${NC}"
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}❌ $service_name failed to start within expected time${NC}"
    return 1
}

# Check services and start missing ones
echo "🔍 Checking service status..."

# Check and start Model Server
check_service 8001 "Model Server" "http://127.0.0.1:8001/health"
MODEL_STATUS=$?

if [ $MODEL_STATUS -eq 2 ]; then
    echo "Model Server already running, skipping..."
    MODEL_PID=""
elif [ $MODEL_STATUS -eq 1 ]; then
    echo "Port 8001 occupied by unresponsive service, please free it first"
    exit 1
else
    echo "🤖 Starting Python Model Server..."
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -r requirements.txt

    echo "Starting model server on port 8001..."
    python model_server.py &
    MODEL_PID=$!
    echo "Model server started with PID: $MODEL_PID"

    # Wait for model server to be ready
    wait_for_service "http://127.0.0.1:8001/health" "Model Server"
fi
echo ""

# Check and start Backend
check_service 3000 "Backend API" "http://localhost:3000/health"
BACKEND_STATUS=$?

if [ $BACKEND_STATUS -eq 2 ]; then
    echo "Backend API already running, skipping..."
    BACKEND_PID=""
elif [ $BACKEND_STATUS -eq 1 ]; then
    echo "Port 3000 occupied by unresponsive service, please free it first"
    exit 1
else
    echo "🔧 Starting Node.js Backend..."
    cd ZJU-SEM-Project-master/backend

    if [ ! -d "node_modules" ]; then
        echo "Installing backend dependencies..."
        npm install
    fi

    echo "Starting backend on port 3000..."
    npm start &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"

    cd ../..
    # Wait for backend to be ready
    wait_for_service "http://localhost:3000/health" "Backend API"
fi
echo ""

# Check and start Frontend
check_service 5173 "Frontend" "http://localhost:5173"
FRONTEND_STATUS=$?

if [ $FRONTEND_STATUS -eq 2 ]; then
    echo "Frontend already running, skipping..."
    FRONTEND_PID=""
elif [ $FRONTEND_STATUS -eq 1 ]; then
    echo "Port 5173 occupied by unresponsive service, please free it first"
    exit 1
else
    echo "🎨 Starting Vue.js Frontend..."
    cd ZJU-SEM-Project-master/frontend/final-project

    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    echo "Starting frontend dev server on port 5173..."
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"

    cd ../../..
    # Wait a bit for frontend to start
    sleep 3
fi
echo ""

# Final status
echo "======================================================="
echo -e "${GREEN}🎉 Services checked/started successfully!${NC}"
echo ""
echo "📊 Service Status:"

# Check final status
echo -n "  🤖 Model Server: "
if curl -s "http://127.0.0.1:8001/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC} (http://127.0.0.1:8001/health)"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo -n "  🔧 Backend API:  "
if curl -s "http://localhost:3000/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC} (http://localhost:3000/health)"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo -n "  🎨 Frontend:     "
if curl -s "http://localhost:5173" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC} (http://localhost:5173)"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo ""
echo "🧪 To test the integration:"
echo "  python test_integration.py"
echo ""

# Build kill command for running services
KILL_CMD=""
[ -n "$MODEL_PID" ] && KILL_CMD="$KILL_CMD $MODEL_PID"
[ -n "$BACKEND_PID" ] && KILL_CMD="$KILL_CMD $BACKEND_PID"
[ -n "$FRONTEND_PID" ] && KILL_CMD="$KILL_CMD $FRONTEND_PID"

if [ -n "$KILL_CMD" ]; then
    echo "🛑 To stop newly started services:"
    echo "  kill $KILL_CMD"
    echo ""
    echo "📖 See README_INTEGRATION.md for detailed usage instructions"

    # Keep script running to show logs
    echo -e "${BLUE}📋 Services are running. Press Ctrl+C to stop newly started services.${NC}"
    trap "echo -e '\n${YELLOW}🛑 Stopping newly started services...${NC}'; kill $KILL_CMD 2>/dev/null; exit" INT
    wait
else
    echo "📖 All services were already running. See README_INTEGRATION.md for usage instructions"
fi
