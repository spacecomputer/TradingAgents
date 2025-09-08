from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from datetime import datetime
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///tradingagents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy()
db.init_app(app)

CORS(app, origins=["*"])  # Configure for production
socketio = SocketIO(app, cors_allowed_origins="*")

# Define models within this file to avoid circular imports
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    oauth_provider = db.Column(db.String(50))
    oauth_id = db.Column(db.String(255))
    subscription_tier = db.Column(db.String(20), default='free')
    credits_remaining = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, email, name=None, oauth_provider=None, oauth_id=None):
        self.email = email
        self.name = name
        self.oauth_provider = oauth_provider
        self.oauth_id = oauth_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'subscription_tier': self.subscription_tier,
            'credits_remaining': self.credits_remaining,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def has_credits(self, required_credits=1):
        return self.credits_remaining >= required_credits
    
    def consume_credits(self, amount=1):
        if self.has_credits(amount):
            self.credits_remaining -= amount
            return True
        return False
    
    def get_tier_limits(self):
        limits = {
            'free': {
                'monthly_analyses': 5,
                'concurrent_analyses': 1,
                'report_retention_days': 1,
                'api_calls_per_day': 0
            },
            'pro': {
                'monthly_analyses': 100,
                'concurrent_analyses': 3,
                'report_retention_days': -1,
                'api_calls_per_day': 100
            },
            'enterprise': {
                'monthly_analyses': -1,
                'concurrent_analyses': 10,
                'report_retention_days': -1,
                'api_calls_per_day': -1
            }
        }
        return limits.get(self.subscription_tier, limits['free'])

class Analysis(db.Model):
    __tablename__ = 'analyses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    analysis_date = db.Column(db.Date, nullable=False)
    configuration = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    report_data = db.Column(db.JSON)
    credits_consumed = db.Column(db.Integer, default=1)
    error_message = db.Column(db.Text)
    current_stage = db.Column(db.String(50))
    completed_stages = db.Column(db.JSON, default=list)
    total_stages = db.Column(db.Integer, default=5)
    
    def __init__(self, user_id, ticker, analysis_date, configuration=None):
        self.user_id = user_id
        self.ticker = ticker.upper()
        self.analysis_date = analysis_date
        self.configuration = configuration or {}
        self.completed_stages = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ticker': self.ticker,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'configuration': self.configuration,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'report_data': self.report_data,
            'credits_consumed': self.credits_consumed,
            'error_message': self.error_message,
            'progress': {
                'current_stage': self.current_stage,
                'completed_stages': self.completed_stages or [],
                'total_stages': self.total_stages,
                'percentage': len(self.completed_stages or []) / self.total_stages * 100 if self.total_stages > 0 else 0
            }
        }

# Set up route dependencies
import routes.auth as auth_module
import routes.api as api_module
auth_module.db = db
auth_module.User = User
api_module.db = db
api_module.User = User
api_module.Analysis = Analysis
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
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)