from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

# Import db from app.py will be handled through imports
db = None  # Will be set by app.py

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
    
    # Progress tracking
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
    
    def start_analysis(self):
        """Mark analysis as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.current_stage = 'initializing'
    
    def update_progress(self, stage, completed_stages=None):
        """Update analysis progress"""
        self.current_stage = stage
        if completed_stages:
            self.completed_stages = completed_stages
    
    def complete_analysis(self, report_data):
        """Mark analysis as completed with report data"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.report_data = report_data
        self.current_stage = 'completed'
        self.completed_stages = ['analyst_team', 'research_team', 'trader', 'risk_management', 'portfolio_decision']
    
    def fail_analysis(self, error_message):
        """Mark analysis as failed with error message"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def get_stage_names(self):
        """Get human-readable stage names"""
        stages = {
            'initializing': 'Initializing Analysis',
            'analyst_team': 'Analyst Team Working',
            'research_team': 'Research Team Debating',
            'trader': 'Trader Planning',
            'risk_management': 'Risk Assessment',
            'portfolio_decision': 'Portfolio Manager Decision',
            'completed': 'Analysis Complete'
        }
        return stages
    
    def get_estimated_time_remaining(self):
        """Estimate remaining time based on current progress"""
        if not self.started_at or self.status in ['completed', 'failed']:
            return 0
        
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        progress_percentage = len(self.completed_stages or []) / self.total_stages
        
        if progress_percentage > 0:
            total_estimated = elapsed / progress_percentage
            remaining = max(0, total_estimated - elapsed)
            return int(remaining)
        
        # Default estimates per stage (in seconds)
        stage_estimates = {
            'initializing': 30,
            'analyst_team': 180,  # 3 minutes
            'research_team': 120,  # 2 minutes
            'trader': 90,  # 1.5 minutes
            'risk_management': 120,  # 2 minutes
            'portfolio_decision': 60  # 1 minute
        }
        
        remaining_stages = [s for s in stage_estimates.keys() if s not in (self.completed_stages or [])]
        return sum(stage_estimates.get(stage, 60) for stage in remaining_stages)


class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    analysis_id = db.Column(db.String(36), db.ForeignKey('analyses.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    credits_consumed = db.Column(db.Integer, default=0)
    llm_calls = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, action, analysis_id=None, credits_consumed=0, llm_calls=0):
        self.user_id = user_id
        self.action = action
        self.analysis_id = analysis_id
        self.credits_consumed = credits_consumed
        self.llm_calls = llm_calls
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'analysis_id': self.analysis_id,
            'credits_consumed': self.credits_consumed,
            'llm_calls': self.llm_calls,
            'timestamp': self.timestamp.isoformat()
        }