#!/bin/bash

# TradingAgents SaaS Startup Script

echo "🚀 Starting TradingAgents SaaS Platform..."

# Check if we're in the right directory
if [ ! -d "webapp" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create database if it doesn't exist
echo "📄 Initializing database..."
cd webapp/backend
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database initialized successfully')
"

# Start backend server
echo "🔧 Starting backend server on port 5001..."
python app.py &
BACKEND_PID=$!

cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend development server
echo "🎨 Starting frontend server on port 5000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ TradingAgents SaaS Platform is starting up!"
echo "🌐 Frontend: http://localhost:5000"
echo "⚙️  Backend API: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all servers"

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

trap cleanup SIGINT

# Wait for servers
wait