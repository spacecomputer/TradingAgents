from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tradingagents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app, origins=["*"])  # Configure for production
socketio = SocketIO(app, cors_allowed_origins="*")

# Set up database reference for models
import models.user as user_module
import models.analysis as analysis_module
user_module.db = db
analysis_module.db = db

# Import models after setting db reference
from models.user import User, UserAPIKey
from models.analysis import Analysis, UsageLog

# Set up route dependencies
import routes.auth as auth_module
import routes.api as api_module
auth_module.db = db
auth_module.User = User
api_module.db = db
api_module.User = User
api_module.Analysis = Analysis
api_module.UsageLog = UsageLog
api_module.socketio = socketio

# Import routes
from routes.auth import auth_bp
from routes.api import api_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def home():
    return jsonify({
        "message": "TradingAgents SaaS API",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db.engine.dialect.name else "disconnected"
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to TradingAgents'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('subscribe_analysis')
def handle_analysis_subscription(data):
    analysis_id = data.get('analysis_id')
    if analysis_id:
        join_room(f"analysis_{analysis_id}")
        emit('subscribed', {'analysis_id': analysis_id})

@socketio.on('unsubscribe_analysis')
def handle_analysis_unsubscription(data):
    analysis_id = data.get('analysis_id')
    if analysis_id:
        leave_room(f"analysis_{analysis_id}")
        emit('unsubscribed', {'analysis_id': analysis_id})

def create_tables():
    """Create database tables if they don't exist"""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)