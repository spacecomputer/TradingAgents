from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import os
import json
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# This will be properly imported in app.py
db = None
User = None

@auth_bp.route('/user', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with email/password or OAuth"""
    data = request.get_json()
    
    if 'email' in data:
        # Email login (for development/testing)
        email = data.get('email')
        name = data.get('name', email.split('@')[0])
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name)
            db.session.add(user)
            db.session.commit()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['email'] = user.email
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'message': 'Login successful'
        })
    
    return jsonify({'error': 'Invalid login data'}), 400

@auth_bp.route('/google', methods=['GET'])
def google_oauth():
    """Redirect to Google OAuth"""
    # This would be implemented with proper OAuth flow
    # For now, return the OAuth URL
    google_oauth_url = "https://accounts.google.com/o/oauth2/auth"
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = f"{request.host_url}api/auth/google/callback"
    
    if not client_id:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    oauth_url = f"{google_oauth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid email profile"
    
    return jsonify({'oauth_url': oauth_url})

@auth_bp.route('/google/callback', methods=['GET'])
def google_oauth_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({'error': 'No authorization code provided'}), 400
    
    try:
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = f"{request.host_url}api/auth/google/callback"
        
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            return jsonify({'error': 'Failed to obtain access token'}), 400
        
        # Get user info
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token_json['access_token']}"
        user_response = requests.get(user_info_url)
        user_info = user_response.json()
        
        # Find or create user
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                oauth_provider='google',
                oauth_id=user_info['id']
            )
            db.session.add(user)
        else:
            # Update user info
            user.name = user_info.get('name', user.name)
            user.oauth_provider = 'google'
            user.oauth_id = user_info['id']
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['email'] = user.email
        
        # Redirect to frontend
        return redirect(f"{request.host_url}?auth=success")
        
    except Exception as e:
        return jsonify({'error': f'OAuth error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/settings', methods=['PUT'])
def update_user_settings():
    """Update user settings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'name' in data:
        user.name = data['name']
    
    # Add other settings as needed
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'message': 'Settings updated successfully'
    })