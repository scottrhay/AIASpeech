from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, bcrypt
from app.models import User
import os
import requests
from urllib.parse import urlencode
import secrets

bp = Blueprint('auth', __name__)

# Microsoft OAuth configuration
MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
MICROSOFT_TENANT_ID = os.getenv('MICROSOFT_TENANT_ID', 'consumers')  # 'consumers' for personal accounts
MICROSOFT_REDIRECT_URI = os.getenv('MICROSOFT_REDIRECT_URI', 'https://speech.aiacopilot.com/api/v1/auth/microsoft/callback')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://speech.aiacopilot.com')


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    # Validate required fields
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email, and password are required'}), 400

    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    # Create new user
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=password_hash
    )

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    # Find user
    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.password_hash or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    # Create access token
    access_token = create_access_token(identity=user.id)

    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (for admin or team view)."""
    users = User.query.filter_by(is_active=True).all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200


# ============ Microsoft OAuth Routes ============

@bp.route('/microsoft/login', methods=['GET'])
def microsoft_login():
    """Redirect to Microsoft OAuth login page."""
    if not MICROSOFT_CLIENT_ID:
        return jsonify({'error': 'Microsoft OAuth is not configured'}), 500

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build authorization URL
    auth_params = {
        'client_id': MICROSOFT_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': MICROSOFT_REDIRECT_URI,
        'response_mode': 'query',
        'scope': 'openid email profile User.Read',
        'state': state
    }

    # Use 'consumers' endpoint for personal Microsoft accounts
    auth_url = f'https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(auth_params)}'

    return redirect(auth_url)


@bp.route('/microsoft/callback', methods=['GET'])
def microsoft_callback():
    """Handle Microsoft OAuth callback."""
    error = request.args.get('error')
    if error:
        error_desc = request.args.get('error_description', 'Unknown error')
        current_app.logger.error(f"Microsoft OAuth error: {error} - {error_desc}")
        return redirect(f'{FRONTEND_URL}?error=oauth_failed&message={error_desc}')

    code = request.args.get('code')
    if not code:
        return redirect(f'{FRONTEND_URL}?error=no_code')

    try:
        # Exchange code for tokens
        token_url = f'https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token'
        token_data = {
            'client_id': MICROSOFT_CLIENT_ID,
            'client_secret': MICROSOFT_CLIENT_SECRET,
            'code': code,
            'redirect_uri': MICROSOFT_REDIRECT_URI,
            'grant_type': 'authorization_code',
            'scope': 'openid email profile User.Read'
        }

        token_response = requests.post(token_url, data=token_data, timeout=30)
        token_response.raise_for_status()
        tokens = token_response.json()

        access_token = tokens.get('access_token')
        if not access_token:
            current_app.logger.error("No access token in response")
            return redirect(f'{FRONTEND_URL}?error=no_token')

        # Get user info from Microsoft Graph API
        graph_url = 'https://graph.microsoft.com/v1.0/me'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(graph_url, headers=headers, timeout=30)
        user_response.raise_for_status()
        ms_user = user_response.json()

        ms_id = ms_user.get('id')
        email = ms_user.get('mail') or ms_user.get('userPrincipalName')
        display_name = ms_user.get('displayName') or email.split('@')[0]

        current_app.logger.info(f"Microsoft user info: id={ms_id}, email={email}, name={display_name}")

        # Find or create user
        user = User.query.filter_by(oauth_provider='microsoft', oauth_id=ms_id).first()

        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link existing account to Microsoft
                user.oauth_provider = 'microsoft'
                user.oauth_id = ms_id
                db.session.commit()
            else:
                # Create new user
                # Generate unique username from display name
                base_username = display_name.replace(' ', '_').lower()[:50]
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1

                user = User(
                    username=username,
                    email=email,
                    oauth_provider='microsoft',
                    oauth_id=ms_id,
                    password_hash=None  # OAuth users don't have passwords
                )
                db.session.add(user)
                db.session.commit()
                current_app.logger.info(f"Created new user from Microsoft: {username}")

        if not user.is_active:
            return redirect(f'{FRONTEND_URL}?error=account_deactivated')

        # Create JWT token
        jwt_token = create_access_token(identity=user.id)

        # Redirect to frontend with token
        return redirect(f'{FRONTEND_URL}?token={jwt_token}&user_id={user.id}&username={user.username}')

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Microsoft OAuth request error: {str(e)}")
        return redirect(f'{FRONTEND_URL}?error=oauth_request_failed')
    except Exception as e:
        current_app.logger.error(f"Microsoft OAuth error: {str(e)}", exc_info=True)
        db.session.rollback()
        return redirect(f'{FRONTEND_URL}?error=oauth_failed')
