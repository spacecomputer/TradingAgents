from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from app.py will be handled through imports
db = None  # Will be set by app.py

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
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    api_keys = db.relationship('UserAPIKey', backref='user', lazy=True)
    
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
        """Check if user has enough credits for an operation"""
        return self.credits_remaining >= required_credits
    
    def consume_credits(self, amount=1):
        """Consume credits for an operation"""
        if self.has_credits(amount):
            self.credits_remaining -= amount
            return True
        return False
    
    def get_tier_limits(self):
        """Get limits based on subscription tier"""
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
                'report_retention_days': -1,  # Unlimited
                'api_calls_per_day': 100
            },
            'enterprise': {
                'monthly_analyses': -1,  # Unlimited
                'concurrent_analyses': 10,
                'report_retention_days': -1,  # Unlimited
                'api_calls_per_day': -1  # Unlimited
            }
        }
        return limits.get(self.subscription_tier, limits['free'])


class UserAPIKey(db.Model):
    __tablename__ = 'user_api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __init__(self, user_id, provider, encrypted_key):
        self.user_id = user_id
        self.provider = provider
        self.encrypted_key = encrypted_key
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }