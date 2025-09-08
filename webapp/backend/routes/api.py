from flask import Blueprint, request, jsonify, session
from flask_socketio import emit
from datetime import datetime, date
import json
import traceback

api_bp = Blueprint('api', __name__)

# These will be properly imported in app.py
db = None
User = None
Analysis = None
UsageLog = None
socketio = None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@api_bp.route('/analysis/create', methods=['POST'])
@require_auth
def create_analysis():
    """Create a new analysis"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        analysis_date = data.get('analysis_date')
        configuration = data.get('configuration', {})
        
        # Validate input
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        if not analysis_date:
            analysis_date = date.today()
        else:
            try:
                analysis_date = datetime.strptime(analysis_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check if user has enough credits
        if not user.has_credits():
            return jsonify({'error': 'Insufficient credits'}), 402
        
        # Check user limits
        limits = user.get_tier_limits()
        
        # Check concurrent analyses
        running_analyses = Analysis.query.filter_by(
            user_id=user_id, 
            status='running'
        ).count()
        
        if running_analyses >= limits['concurrent_analyses']:
            return jsonify({'error': f'Maximum concurrent analyses reached ({limits["concurrent_analyses"]})'}), 429
        
        # Create analysis
        analysis = Analysis(
            user_id=user_id,
            ticker=ticker,
            analysis_date=analysis_date,
            configuration=configuration
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # Log usage
        usage_log = UsageLog(
            user_id=user_id,
            analysis_id=analysis.id,
            action='analysis_created'
        )
        db.session.add(usage_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis': analysis.to_dict(),
            'message': 'Analysis created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create analysis: {str(e)}'}), 500

@api_bp.route('/analysis/<analysis_id>', methods=['GET'])
@require_auth
def get_analysis(analysis_id):
    """Get analysis by ID"""
    user_id = session.get('user_id')
    
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify({'analysis': analysis.to_dict()})

@api_bp.route('/analysis/<analysis_id>/status', methods=['GET'])
@require_auth
def get_analysis_status(analysis_id):
    """Get analysis status and progress"""
    user_id = session.get('user_id')
    
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    status_data = {
        'id': analysis.id,
        'status': analysis.status,
        'progress': {
            'current_stage': analysis.current_stage,
            'completed_stages': analysis.completed_stages or [],
            'total_stages': analysis.total_stages,
            'percentage': len(analysis.completed_stages or []) / analysis.total_stages * 100,
            'estimated_time_remaining': analysis.get_estimated_time_remaining()
        },
        'started_at': analysis.started_at.isoformat() if analysis.started_at else None,
        'error_message': analysis.error_message
    }
    
    return jsonify(status_data)

@api_bp.route('/analysis/<analysis_id>/start', methods=['POST'])
@require_auth
def start_analysis(analysis_id):
    """Start an analysis"""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if analysis.status != 'pending':
            return jsonify({'error': 'Analysis is not in pending state'}), 400
        
        # Consume credits
        if not user.consume_credits():
            return jsonify({'error': 'Insufficient credits'}), 402
        
        # Start analysis
        analysis.start_analysis()
        analysis.credits_consumed = 1
        
        db.session.commit()
        
        # Emit status update via WebSocket
        if socketio:
            socketio.emit('analysis_started', {
                'analysis_id': analysis.id,
                'status': 'running'
            }, room=f"analysis_{analysis.id}")
        
        # TODO: Queue background job to run actual analysis
        # This would integrate with the TradingAgents framework
        
        return jsonify({
            'success': True,
            'analysis': analysis.to_dict(),
            'message': 'Analysis started successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@api_bp.route('/analysis/<analysis_id>/report', methods=['GET'])
@require_auth
def get_analysis_report(analysis_id):
    """Get analysis report"""
    user_id = session.get('user_id')
    
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    if analysis.status != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400
    
    return jsonify({
        'analysis_id': analysis.id,
        'ticker': analysis.ticker,
        'analysis_date': analysis.analysis_date.isoformat(),
        'report': analysis.report_data,
        'completed_at': analysis.completed_at.isoformat()
    })

@api_bp.route('/analysis/history', methods=['GET'])
@require_auth
def get_analysis_history():
    """Get user's analysis history"""
    user_id = session.get('user_id')
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    analyses = Analysis.query.filter_by(user_id=user_id)\
        .order_by(Analysis.started_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'analyses': [analysis.to_dict() for analysis in analyses.items],
        'total': analyses.total,
        'pages': analyses.pages,
        'current_page': page
    })

@api_bp.route('/analysis/<analysis_id>', methods=['DELETE'])
@require_auth
def delete_analysis(analysis_id):
    """Delete an analysis"""
    user_id = session.get('user_id')
    
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    if analysis.status == 'running':
        return jsonify({'error': 'Cannot delete running analysis'}), 400
    
    db.session.delete(analysis)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Analysis deleted successfully'})

@api_bp.route('/user/subscription', methods=['GET'])
@require_auth
def get_user_subscription():
    """Get user subscription information"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    limits = user.get_tier_limits()
    
    # Get usage statistics
    current_month_analyses = Analysis.query.filter_by(user_id=user_id)\
        .filter(Analysis.started_at >= datetime.now().replace(day=1))\
        .count()
    
    return jsonify({
        'subscription_tier': user.subscription_tier,
        'credits_remaining': user.credits_remaining,
        'limits': limits,
        'usage': {
            'current_month_analyses': current_month_analyses,
            'running_analyses': Analysis.query.filter_by(user_id=user_id, status='running').count()
        }
    })

@api_bp.route('/user/usage', methods=['GET'])
@require_auth
def get_user_usage():
    """Get detailed user usage statistics"""
    user_id = session.get('user_id')
    
    # Get usage logs for the current month
    current_month = datetime.now().replace(day=1)
    usage_logs = UsageLog.query.filter_by(user_id=user_id)\
        .filter(UsageLog.timestamp >= current_month)\
        .all()
    
    return jsonify({
        'usage_logs': [log.to_dict() for log in usage_logs],
        'summary': {
            'total_analyses': len([log for log in usage_logs if log.action == 'analysis_created']),
            'total_credits_consumed': sum(log.credits_consumed for log in usage_logs),
            'total_llm_calls': sum(log.llm_calls for log in usage_logs)
        }
    })