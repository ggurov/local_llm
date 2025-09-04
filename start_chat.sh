#!/bin/bash

# Local LLM Chat Interface Launcher
# This script helps you choose and start a chat interface

echo "🤖 Local LLM Chat Interface Launcher"
echo "======================================"
echo ""

# Configuration
ORCHESTRATOR_IP="192.168.1.30"
ORCHESTRATOR_PORT="8001"
STREAMLIT_PORT="8502"
WEB_SERVER_PORT="9090"

# Check if services are running
echo "🔍 Checking if services are running..."
if curl -s http://${ORCHESTRATOR_IP}:${ORCHESTRATOR_PORT}/health > /dev/null 2>&1; then
    echo "✅ Orchestrator is running on ${ORCHESTRATOR_IP}:${ORCHESTRATOR_PORT}"
else
    echo "❌ Orchestrator is not running on ${ORCHESTRATOR_IP}:${ORCHESTRATOR_PORT}"
    echo ""
    echo "Please start the services first:"
    echo "  make up"
    echo ""
    exit 1
fi

echo ""
echo "Choose your chat interface:"
echo ""
echo "1) 🌐 Web Interface (HTML/JavaScript)"
echo "   - Simple HTTP server"
echo "   - No additional dependencies"
echo "   - Fast and lightweight"
echo "   - Accessible at: http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
echo ""
echo "2) 🐍 Streamlit Interface (Python)"
echo "   - Rich interface with sidebar"
echo "   - System status monitoring"
echo "   - Requires: pip install streamlit"
echo "   - Accessible at: http://${ORCHESTRATOR_IP}:${STREAMLIT_PORT}"
echo ""
echo "3) 📱 Both (open web interface and start Streamlit)"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting Web Interface Server..."
        echo "Starting HTTP server on ${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}..."
        
        # Start the web server in background
        python3 serve_chat.py &
        WEB_SERVER_PID=$!
        
        # Wait a moment for server to start
        sleep 2
        
        # Try to open in browser
        if command -v xdg-open > /dev/null; then
            xdg-open "http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        elif command -v open > /dev/null; then
            open "http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        else
            echo "Please open the following URL in your browser:"
            echo "http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        fi
        
        echo ""
        echo "✅ Web interface server is running!"
        echo "🌍 Access URL: http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        echo "🆔 Server PID: $WEB_SERVER_PID"
        echo ""
        echo "Press Ctrl+C to stop the server"
        
        # Wait for user to stop
        wait $WEB_SERVER_PID
        ;;
        
    2)
        echo ""
        echo "🐍 Starting Streamlit Interface..."
        
        # Check if streamlit is installed
        if ! command -v streamlit > /dev/null; then
            echo "❌ Streamlit is not installed"
            echo ""
            echo "Installing Streamlit..."
            pip install streamlit
        fi
        
        echo "Starting Streamlit server on ${ORCHESTRATOR_IP}:${STREAMLIT_PORT}..."
        streamlit run chat_interface.py --server.port ${STREAMLIT_PORT} --server.address ${ORCHESTRATOR_IP}
        ;;
        
    3)
        echo ""
        echo "🚀 Starting both interfaces..."
        
        # Start Streamlit in background
        if command -v streamlit > /dev/null; then
            echo "Starting Streamlit server in background..."
            streamlit run chat_interface.py --server.port ${STREAMLIT_PORT} --server.address ${ORCHESTRATOR_IP} &
            STREAMLIT_PID=$!
            echo "Streamlit PID: $STREAMLIT_PID"
        else
            echo "Installing and starting Streamlit..."
            pip install streamlit
            streamlit run chat_interface.py --server.port ${STREAMLIT_PORT} --server.address ${ORCHESTRATOR_IP} &
            STREAMLIT_PID=$!
        fi
        
        # Start web server in background
        echo "Starting web server in background..."
        python3 serve_chat.py &
        WEB_SERVER_PID=$!
        
        # Wait a moment for servers to start
        sleep 3
        
        # Open web interface
        echo "Opening web interface..."
        if command -v xdg-open > /dev/null; then
            xdg-open "http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        elif command -v open > /dev/null; then
            open "http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        fi
        
        echo ""
        echo "✅ Both interfaces are starting!"
        echo "🌐 Web Interface: http://${ORCHESTRATOR_IP}:${WEB_SERVER_PORT}"
        echo "🐍 Streamlit Interface: http://${ORCHESTRATOR_IP}:${STREAMLIT_PORT}"
        echo "🆔 Web Server PID: $WEB_SERVER_PID"
        echo "🆔 Streamlit PID: $STREAMLIT_PID"
        echo ""
        echo "Press Ctrl+C to stop Streamlit when done"
        
        # Wait for user to stop
        wait $STREAMLIT_PID
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac
