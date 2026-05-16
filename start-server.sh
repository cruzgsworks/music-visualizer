#!/bin/bash
# AI Cover Visualizer - Linux Startup Script
# Usage: ./start-server.sh [start|stop|restart|status]

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_DIR="$APP_DIR/src/node"
PID_FILE="$APP_DIR/server.pid"
LOG_FILE="$APP_DIR/server.log"

check_dependencies() {
    echo "Checking dependencies..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js 18+"
        echo "   Run: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs"
        exit 1
    fi
    echo "✅ Node.js: $(node --version)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Please install Python3"
        exit 1
    fi
    echo "✅ Python: $(python3 --version)"
    
    # Check ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo "❌ ffmpeg not found. Please install ffmpeg"
        echo "   Run: sudo apt install -y ffmpeg"
        exit 1
    fi
    echo "✅ ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)"
    
    # Check for GPU support (optional but recommended)
    if ffmpeg -encoders 2>/dev/null | grep -q nvenc; then
        echo "✅ NVIDIA NVENC available (GPU encoding supported)"
    elif ffmpeg -encoders 2>/dev/null | grep -q amf; then
        echo "✅ AMD AMF available (GPU encoding supported)"
    else
        echo "⚠️  No GPU encoder found. Will use CPU encoding (slower)"
    fi
    
    echo ""
}

check_directories() {
    # Create necessary directories
    mkdir -p "$APP_DIR/uploads" "$APP_DIR/output" "$APP_DIR/temp"
    chmod 755 "$APP_DIR/uploads" "$APP_DIR/output" "$APP_DIR/temp"
}

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Server is already running (PID: $(cat $PID_FILE))"
        echo "Access at: http://localhost:3000"
        return
    fi
    
    check_dependencies
    check_directories
    
    echo "Starting AI Cover Visualizer Server..."
    echo "Working directory: $NODE_DIR"
    
    cd "$NODE_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing Node.js dependencies..."
        npm install
    fi
    
    # Start server in background
    nohup node server.js > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ Server started successfully!"
        echo ""
        echo "🌐 Access the web interface at:"
        echo "   Local: http://localhost:3000"
        
        # Get IP addresses
        IP_ADDRESSES=$(hostname -I 2>/dev/null | tr ' ' '\n' | head -3)
        if [ -n "$IP_ADDRESSES" ]; then
            echo "   Network:"
            for ip in $IP_ADDRESSES; do
                echo "      http://$ip:3000"
            done
        fi
        echo ""
        echo "📊 GPU Status:"
        if command -v nvidia-smi &> /dev/null; then
            nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | while read line; do
                echo "   GPU: $line"
            done
        else
            echo "   No NVIDIA GPU detected"
        fi
        echo ""
        echo "📝 Logs: tail -f $LOG_FILE"
        echo "🛑 Stop: $0 stop"
    else
        echo "❌ Failed to start server. Check logs: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping server (PID: $PID)..."
            kill "$PID"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                echo "Force stopping..."
                kill -9 "$PID"
            fi
            
            rm -f "$PID_FILE"
            echo "✅ Server stopped"
        else
            echo "Server not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "Server not running (no PID file found)"
    fi
}

restart_server() {
    stop_server
    sleep 1
    start_server
}

server_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✅ Server is running (PID: $PID)"
            echo "   Log file: $LOG_FILE"
            echo "   Access: http://localhost:3000"
            
            # Show recent log
            if [ -f "$LOG_FILE" ]; then
                echo ""
                echo "📝 Recent log entries:"
                tail -5 "$LOG_FILE"
            fi
        else
            echo "❌ Server not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Server not running"
    fi
}

test_server() {
    echo "Testing server connectivity..."
    
    if [ ! -f "$PID_FILE" ] || ! kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "❌ Server not running. Start it first with: $0 start"
        exit 1
    fi
    
    # Test local connection
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
        echo "✅ Server responding on http://localhost:3000"
    else
        echo "❌ Server not responding"
        exit 1
    fi
    
    # Test static files
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/css/style.css | grep -q "200"; then
        echo "✅ CSS files accessible"
    else
        echo "❌ CSS files not accessible"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/js/app.js | grep -q "200"; then
        echo "✅ JavaScript files accessible"
    else
        echo "❌ JavaScript files not accessible"
    fi
    
    echo ""
    echo "🎉 All tests passed! Server is ready."
}

show_help() {
    echo "AI Cover Visualizer - Linux Control Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    Start the server"
    echo "  stop     Stop the server"
    echo "  restart  Restart the server"
    echo "  status   Check server status"
    echo "  test     Test server connectivity"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start      # Start the server"
    echo "  $0 status     # Check if running"
    echo "  $0 test       # Test connectivity"
    echo "  $0 stop       # Stop the server"
}

# Main script
case "${1:-help}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        server_status
        ;;
    test)
        test_server
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
