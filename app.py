import os
import asyncio
import tempfile
import time
import json
import threading
import uuid
import logging
from flask import Flask, Response, request, render_template, redirect, url_for, send_file, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import google.generativeai as genai
from tasks import cache_news_task, generate_tts_task
from tts import generate_simple_tts
from gnews_client import GNewsClient
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from flask import send_file
import dramatiq
import redis
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from flask import request, session
import hashlib
from functools import wraps
from typing import Dict, Optional
import html
import re
# Add these imports to your existing imports section
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Load environment variables first
load_dotenv()

# Initialize Flask app with production settings
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# PRODUCTION CONFIGURATION
app.config['DEBUG'] = False
app.config['TESTING'] = False
app.config['PROPAGATE_EXCEPTIONS'] = False
app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")
app.config['GOOGLE_ADS_CLIENT'] = os.getenv('GOOGLE_ADS_CLIENT', 'ca-pub-1955463530202020')

# Configure logging for production
if not app.debug:
    app.logger.setLevel(logging.WARNING)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client() 

# Initialize Redis
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_broker = RedisBroker(url=redis_url)
result_backend = RedisBackend(url=redis_url)
redis_broker.add_middleware(Results(backend=result_backend))
dramatiq.set_broker(redis_broker)

# Export for easy importing
broker = redis_broker
gnews_client = GNewsClient() 

NEWSLETTER_CATEGORIES = [
    {'id': 'general', 'name': 'General News', 'description': 'Top stories and headlines'},
    {'id': 'technology', 'name': 'Technology', 'description': 'Tech news and innovations'},
    {'id': 'business', 'name': 'Business', 'description': 'Business and finance updates'},
    {'id': 'sports', 'name': 'Sports', 'description': 'Sports news and scores'},
    {'id': 'entertainment', 'name': 'Entertainment', 'description': 'Entertainment and celebrity news'},
    {'id': 'health', 'name': 'Health', 'description': 'Health and wellness news'},
    {'id': 'science', 'name': 'Science', 'description': 'Scientific discoveries and research'},
    {'id': 'world', 'name': 'World News', 'description': 'International news and events'}
]


def get_user_from_session():
    """Get user data from session if subscribed"""
    if 'subscriber_id' in session:
        try:
            user_doc = db.collection('newsletter_subscribers').document(session['subscriber_id']).get()
            if user_doc.exists:
                return user_doc.to_dict()
        except Exception as e:
            if app.debug:
                app.logger.error(f"Error getting user from session: {e}")
    return None

def get_subscriber_by_email(email):
    """Get subscriber by email"""
    try:
        subscribers = db.collection('newsletter_subscribers').where('email', '==', email).limit(1).get()
        for doc in subscribers:
            return {'id': doc.id, **doc.to_dict()}
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error getting subscriber by email: {e}")
    return None

def generate_user_token():
    """Generate secure token for user identification"""
    return secrets.token_urlsafe(32)
# ============================================
# SECURITY HEADERS & MIDDLEWARE
# ============================================

@app.after_request
def add_security_headers(response):
    """Enhanced security headers - FINAL VERSION"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Server'] = 'WebServer'
    
    # Remove potential information disclosure headers
    response.headers.pop('X-Powered-By', None)
    
    # CLEANED UP CSP - no more conflicts
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        # Production CSP - more restrictive
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://pagead2.googlesyndication.com "
            "https://googleads.g.doubleclick.net "
            "https://www.googletagmanager.com "
            "https://www.google.com "
            "https://partner.googleadservices.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "media-src 'self' blob: data:; "
            "connect-src 'self' "
            "https://pagead2.googlesyndication.com "
            "https://www.google-analytics.com; "
            "frame-src 'self' "
            "https://www.google.com "
            "https://googleads.g.doubleclick.net; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
    else:
        # Development CSP - more permissive
        csp_policy = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: blob: https: http:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "media-src 'self' blob: data:; "
            "frame-src 'self' https:; "
            "object-src 'none'"
        )
    
    response.headers['Content-Security-Policy'] = csp_policy
    return response
# ============================================
# INPUT VALIDATION & SANITIZATION
# ============================================

def sanitize_html_input(text: str) -> str:
    """Sanitize HTML input to prevent XSS"""
    if not text:
        return ""
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove potentially dangerous content
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()

def validate_text_length(text: str, min_len: int = 1, max_len: int = 1000) -> tuple[bool, str]:
    """Validate text length and return (is_valid, error_message)"""
    if not text or len(text.strip()) < min_len:
        return False, f"Text must be at least {min_len} characters long"
    
    if len(text) > max_len:
        return False, f"Text must be less than {max_len} characters"
    
    return True, ""

# ============================================
# ENHANCED RATE LIMITING
# ============================================

class RateLimiter:
    """Redis-based rate limiter for API endpoints"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        """Check if request is allowed based on rate limits"""
        current_time = int(time.time())
        pipeline = self.redis.pipeline()
        
        pipeline.zremrangebyscore(key, 0, current_time - window)
        pipeline.zcard(key)
        pipeline.zadd(key, {str(uuid.uuid4()): current_time})
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        current_requests = results[1]
        
        rate_limit_info = {
            'limit': limit,
            'remaining': max(0, limit - current_requests),
            'reset': current_time + window,
            'retry_after': window if current_requests >= limit else None
        }
        
        return current_requests < limit, rate_limit_info

# Initialize rate limiter
rate_limiter = RateLimiter(redis_client)

# Production-ready rate limits
RATE_LIMITS = {
    'api_general': {'limit': 50, 'window': 3600},
    'api_tts': {'limit': 10, 'window': 3600},
    'api_news': {'limit': 100, 'window': 3600},
    'api_comments': {'limit': 25, 'window': 3600},
    'api_feedback': {'limit': 5, 'window': 3600},
    'api_upload': {'limit': 5, 'window': 3600},
    'api_translate': {'limit': 15, 'window': 3600},
}

def get_client_id() -> str:
    """Enhanced client identification for security"""
    # Use only REMOTE_ADDR to prevent bypass attacks
    real_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    # Session-based identification
    if 'client_session' not in session:
        session['client_session'] = str(uuid.uuid4())
    
    # User agent hash for additional uniqueness
    user_agent_hash = hashlib.md5(
        request.headers.get('User-Agent', '').encode()
    ).hexdigest()[:8]
    
    return f"{real_ip}:{session['client_session']}:{user_agent_hash}"

def rate_limit(category: str = 'api_general'):
    """Enhanced rate limiting decorator with production logging"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if category not in RATE_LIMITS:
                if app.debug:
                    app.logger.warning(f"Unknown rate limit category: {category}")
                return f(*args, **kwargs)
            
            config = RATE_LIMITS[category]
            client_id = get_client_id()
            rate_key = f"rate_limit:{category}:{client_id}"
            
            is_allowed, rate_info = rate_limiter.is_allowed(
                rate_key, config['limit'], config['window']
            )
            
            def add_rate_limit_headers(response):
                if hasattr(response, 'headers'):
                    # Only show detailed headers in development
                    if app.debug:
                        response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                        response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                        response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                    if rate_info['retry_after']:
                        response.headers['Retry-After'] = str(rate_info['retry_after'])
                return response
            
            if not is_allowed:
                # Minimal logging in production
                if app.debug:
                    app.logger.warning(f"Rate limit exceeded for {client_id} on {category}")
                
                error_response = jsonify({
                    'error': 'Too many requests',
                    'message': 'Please try again later'
                })
                error_response.status_code = 429
                return add_rate_limit_headers(error_response)
            
            response = f(*args, **kwargs)
            return add_rate_limit_headers(response) if hasattr(response, 'headers') else response
                
        return decorated_function
    return decorator

def is_admin_request() -> bool:
    """Check if request should bypass rate limiting"""
    admin_ips = os.getenv('ADMIN_IPS', '').split(',')
    admin_api_key = request.headers.get('X-Admin-API-Key')
    client_ip = get_client_id().split(':')[0]
    
    return (
        client_ip in admin_ips or 
        admin_api_key == os.getenv('ADMIN_API_KEY') or
        request.headers.get('User-Agent', '').startswith('Health-Check')
    )

def conditional_rate_limit(category: str = 'api_general'):
    """Rate limiting decorator that bypasses for admin requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if is_admin_request():
                return f(*args, **kwargs)
            return rate_limit(category)(f)(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# ENHANCED ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    if app.debug:
        app.logger.error(f"Server error: {str(e)}")
    return render_template('error.html', message="Service temporarily unavailable."), 500

@app.errorhandler(429)
def rate_limit_error(e):
    return render_template('error.html', message="Too many requests. Please try again later."), 429

@app.errorhandler(Exception)
def handle_exception(e):
    if app.debug:
        app.logger.error(f"Unhandled exception: {str(e)}")
    return render_template('error.html', message="Something went wrong."), 500

# ============================================
# SECURED API ENDPOINTS
# ============================================

@app.route('/api/feedback', methods=['POST'])
@rate_limit('api_feedback')
def submit_feedback():
    """SECURED feedback endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        feedback_text = data.get('feedback', '').strip()
        
        # Enhanced validation
        is_valid, error_msg = validate_text_length(feedback_text, min_len=5, max_len=500)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Sanitize input
        feedback_text = sanitize_html_input(feedback_text)
        
        # Security checks
        if any(word in feedback_text.lower() for word in ['<script', 'javascript:', 'data:text/html']):
            return jsonify({"error": "Invalid input detected"}), 400
        
        feedback_doc = {
            'feedback': feedback_text,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'source': sanitize_html_input(data.get('source', 'unknown')[:50]),
            'page': sanitize_html_input(data.get('page', '')[:100]),
            'user_ip': request.environ.get('REMOTE_ADDR', 'unknown'),
            'user_agent': request.headers.get('User-Agent', '')[:200]
        }
        
        db.collection('feedback').add(feedback_doc)
        
        if app.debug:
            app.logger.info(f"Feedback submitted from {request.environ.get('REMOTE_ADDR')}")
        
        return jsonify({
            "message": "Feedback submitted successfully", 
            "success": True
        })
        
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({"error": "Failed to submit feedback"}), 500

@app.route('/api/article-comment', methods=['POST'])
@rate_limit('api_comments')
def post_comment():
    """SECURED comment posting with subscriber tracking"""
    try:
        # DEBUG: Log request details
        print("=== DEBUG COMMENT REQUEST ===")
        print(f"Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        
        # Get JSON data
        data = request.get_json()
        print(f"Parsed JSON: {data}")
        print(f"JSON type: {type(data)}")
        
        if not data:
            print("ERROR: No JSON data received")
            return jsonify({"error": "No data provided"}), 400
        
        # Extract fields
        article_id = data.get('article_id')
        comment_text = data.get('comment_text', '').strip()
        
        print(f"article_id: '{article_id}' (type: {type(article_id)})")
        print(f"comment_text: '{comment_text}' (type: {type(comment_text)})")
        print("===========================")

        # Validation
        if not article_id:
            print("ERROR: Missing article_id")
            return jsonify({"error": "Missing article ID"}), 400
            
        if not comment_text:
            print("ERROR: Missing or empty comment_text")
            return jsonify({"error": "Missing comment text"}), 400

        # Validate text length
        is_valid, error_msg = validate_text_length(comment_text, min_len=1, max_len=500)
        if not is_valid:
            print(f"ERROR: Text validation failed: {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        # Sanitize inputs
        comment_text = sanitize_html_input(comment_text)
        article_id = sanitize_html_input(article_id)
        
        # Validate article_id format (basic check)
        if len(article_id) > 500:  # Reasonable limit
            print(f"ERROR: Article ID too long: {len(article_id)}")
            return jsonify({"error": "Invalid article ID"}), 400

        # Check if user is subscribed
        user = get_user_from_session()
        if user:
            # Use subscriber name
            nickname = user['name']
            is_subscriber = True
            subscriber_id = session['subscriber_id']
            print(f"Subscriber comment from: {nickname}")
        else:
            # Generate anonymous nickname
            nickname_input = data.get('nickname', '').strip()
            if nickname_input:
                nickname = sanitize_html_input(nickname_input[:50])
            else:
                import random
                random_names = ["Anonymous", "Reader", "Observer", "Visitor", "User"]
                nickname = random.choice(random_names) + str(random.randint(100, 999))
            is_subscriber = False
            subscriber_id = None
            print(f"Anonymous comment from: {nickname}")

        # Prepare comment data
        comment_data = {
            'nickname': nickname,
            'comment': comment_text,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'likes': 0,
            'liked_by': [],
            'is_subscriber': is_subscriber,
            'subscriber_id': subscriber_id
        }
        
        print(f"Saving comment to collection: comments/{article_id}/comments")
        print(f"Comment data: {comment_data}")

        # Save comment to Firestore
        doc_ref = db.collection('comments').document(article_id).collection('comments').document()
        doc_ref.set(comment_data)
        
        print(f"Comment saved with ID: {doc_ref.id}")
        
        # Update subscriber comment count
        if is_subscriber:
            try:
                db.collection('newsletter_subscribers').document(subscriber_id).update({
                    'total_comments': firestore.Increment(1),
                    'last_activity': firestore.SERVER_TIMESTAMP
                })
                print(f"Updated subscriber {subscriber_id} comment count")
            except Exception as e:
                print(f"Warning: Failed to update subscriber comment count: {e}")

        # Prepare response
        response_data = {
            "message": "Comment posted successfully", 
            "nickname": nickname,
            "is_subscriber": is_subscriber,
            "comment_id": doc_ref.id
        }
        
        print(f"Sending response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR in post_comment: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({"error": "Failed to post comment"}), 500

def get_user_id():
    """Generate consistent user ID for voting"""
    user_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', '')
    user_string = f"{user_ip}:{user_agent}"
    return hashlib.sha256(user_string.encode()).hexdigest()[:16]

@app.route('/api/article-comments', methods=['GET'])
@rate_limit('api_general')
def get_comments():
    """Get comments for an article"""
    article_id = request.args.get('article_id')
    if not article_id:
        return jsonify({"error": "Invalid request"}), 400

    try:
        user_id = get_user_id()
        comments_ref = db.collection('comments').document(article_id).collection('comments')
        comments_snapshot = comments_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

        comments = []
        for doc in comments_snapshot:
            comment = doc.to_dict()
            comment['id'] = doc.id
            
            liked_by = comment.get('liked_by', [])
            comment['userLiked'] = user_id in liked_by
            comment['likes'] = comment.get('likes', 0)
            comment.pop('liked_by', None)
            
            comments.append(comment)

        comments.sort(key=lambda x: (x.get('likes', 0), x.get('timestamp', 0)), reverse=True)
        return jsonify({"comments": comments})

    except Exception as e:
        if app.debug:
            app.logger.error(f"Error getting comments: {str(e)}")
        return jsonify({"error": "Service error"}), 500

@app.route('/api/comment-like', methods=['POST'])
@rate_limit('api_comments')
def handle_comment_like():
    """Handle comment likes"""
    try:
        data = request.get_json()
        comment_id = data.get('comment_id')
        article_id = data.get('article_id')
        
        if not comment_id or not article_id:
            return jsonify({'error': 'Invalid request'}), 400
        
        user_id = get_user_id()
        comment_ref = db.collection('comments').document(article_id).collection('comments').document(comment_id)
        
        @firestore.transactional
        def update_like(transaction):
            comment_doc = comment_ref.get(transaction=transaction)
            if not comment_doc.exists:
                raise ValueError("Comment not found")
            
            comment_data = comment_doc.to_dict()
            
            if 'likes' not in comment_data:
                comment_data['likes'] = 0
            if 'liked_by' not in comment_data:
                comment_data['liked_by'] = []
            
            liked_by = comment_data['liked_by']
            current_likes = comment_data['likes']
            user_liked = user_id in liked_by
            
            if user_liked:
                liked_by.remove(user_id)
                current_likes = max(0, current_likes - 1)
                new_user_liked = False
            else:
                if user_id not in liked_by:
                    liked_by.append(user_id)
                current_likes += 1
                new_user_liked = True
            
            transaction.update(comment_ref, {
                'likes': current_likes,
                'liked_by': liked_by,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            return {
                'likes': current_likes,
                'user_liked': new_user_liked
            }
        
        transaction = db.transaction()
        result = update_like(transaction)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except ValueError as e:
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error handling comment like: {str(e)}")
        return jsonify({'error': 'Service error'}), 500

# Replace your existing handle_article_like function:
@app.route('/api/article-like', methods=['POST'])
@rate_limit('api_comments')
def handle_article_like():
    """Handle article likes with subscriber tracking"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({'error': 'Invalid request'}), 400
        
        user_id = get_user_id()
        user = get_user_from_session()
        article_ref = db.collection('article_likes').document(article_id)
        
        @firestore.transactional
        def update_article_like(transaction):
            article_doc = article_ref.get(transaction=transaction)
            
            if not article_doc.exists:
                article_data = {'likes': 0, 'liked_by': [], 'subscriber_likes': {}}
            else:
                article_data = article_doc.to_dict()
                if 'subscriber_likes' not in article_data:
                    article_data['subscriber_likes'] = {}
            
            if 'likes' not in article_data:
                article_data['likes'] = 0
            if 'liked_by' not in article_data:
                article_data['liked_by'] = []
            
            liked_by = article_data['liked_by']
            subscriber_likes = article_data['subscriber_likes']
            current_likes = article_data['likes']
            user_liked = user_id in liked_by
            
            if user_liked:
                liked_by.remove(user_id)
                current_likes = max(0, current_likes - 1)
                new_user_liked = False
                
                # Remove from subscriber likes if applicable
                if user and session['subscriber_id'] in subscriber_likes:
                    del subscriber_likes[session['subscriber_id']]
                    
            else:
                if user_id not in liked_by:
                    liked_by.append(user_id)
                current_likes += 1
                new_user_liked = True
                
                # Add to subscriber likes if applicable
                if user:
                    subscriber_likes[session['subscriber_id']] = {
                        'name': user['name'],
                        'timestamp': firestore.SERVER_TIMESTAMP
                    }
            
            # Update article likes
            transaction.set(article_ref, {
                'likes': current_likes,
                'liked_by': liked_by,
                'subscriber_likes': subscriber_likes,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            # Update subscriber total likes count
            if user and new_user_liked:
                try:
                    subscriber_ref = db.collection('newsletter_subscribers').document(session['subscriber_id'])
                    transaction.update(subscriber_ref, {
                        'total_likes': firestore.Increment(1),
                        'last_activity': firestore.SERVER_TIMESTAMP
                    })
                except Exception:
                    pass  # Don't fail if subscriber update fails
            elif user and not new_user_liked:
                try:
                    subscriber_ref = db.collection('newsletter_subscribers').document(session['subscriber_id'])
                    transaction.update(subscriber_ref, {
                        'total_likes': firestore.Increment(-1),
                        'last_activity': firestore.SERVER_TIMESTAMP
                    })
                except Exception:
                    pass
            
            return {
                'likes': current_likes,
                'user_liked': new_user_liked
            }
        
        transaction = db.transaction()
        result = update_article_like(transaction)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error handling article like: {str(e)}")
        return jsonify({'error': 'Service error'}), 500
@app.route('/api/subscriber-leaderboard')
@rate_limit('api_general')
def subscriber_leaderboard():
    """Get top subscribers by engagement"""
    try:
        # Get top 10 subscribers by total engagement (likes + comments)
        subscribers = db.collection('newsletter_subscribers')\
            .where('active', '==', True)\
            .order_by('total_likes', direction=firestore.Query.DESCENDING)\
            .limit(10)\
            .get()
        
        leaderboard = []
        for doc in subscribers:
            data = doc.to_dict()
            total_engagement = (data.get('total_likes', 0) + data.get('total_comments', 0))
            if total_engagement > 0:  # Only show users with activity
                leaderboard.append({
                    'name': data.get('name', 'Anonymous'),
                    'total_likes': data.get('total_likes', 0),
                    'total_comments': data.get('total_comments', 0),
                    'total_engagement': total_engagement
                })
        
        # Sort by total engagement
        leaderboard.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return jsonify({'leaderboard': leaderboard[:10]})
        
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500

@app.route('/api/article-likes', methods=['GET'])
@rate_limit('api_general')
def get_article_likes():
    """Get article like count and user status"""
    try:
        article_id = request.args.get('article_id')
        if not article_id:
            return jsonify({'error': 'Invalid request'}), 400
        
        user_id = get_user_id()
        article_ref = db.collection('article_likes').document(article_id)
        article_doc = article_ref.get()
        
        if not article_doc.exists:
            return jsonify({'likes': 0, 'user_liked': False})
        
        article_data = article_doc.to_dict()
        liked_by = article_data.get('liked_by', [])
        
        return jsonify({
            'likes': article_data.get('likes', 0),
            'user_liked': user_id in liked_by
        })
        
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error getting article likes: {str(e)}")
        return jsonify({'error': 'Service error'}), 500

@app.route('/api/news/translate', methods=['POST'])
@rate_limit('api_translate')
def translate_text():
    """SECURED translation endpoint"""
    try:
        data = request.json
        text_to_translate = data.get('text', '').strip()
        target_language_code = data.get('target_language', '').strip()

        if not text_to_translate or not target_language_code:
            return jsonify({"error": "Missing required fields"}), 400

        # Validate input
        is_valid, error_msg = validate_text_length(text_to_translate, min_len=1, max_len=1000)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        text_to_translate = sanitize_html_input(text_to_translate)
        
        # Validate language code
        if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', target_language_code):
            return jsonify({"error": "Invalid language code"}), 400

        # Use Gemini for translation
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"Translate the following text to {target_language_code}. Only provide the translation:\n\n{text_to_translate}"
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        if not translated_text:
            raise ValueError("Translation failed")

        return jsonify({"translated_text": translated_text})

    except Exception as e:
        if app.debug:
            app.logger.error(f"Error translating text: {e}")
        return jsonify({"error": "Translation failed"}), 500

# ============================================
# CORE APPLICATION ROUTES
# ============================================

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
ALLOWED_EXTENSIONS = {'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

jobs = {}

# Voice configuration
AVAILABLE_VOICES = [
    {"id": "en-US-GuyNeural", "name": "Guy (Male, US)", "language": "English"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher (Male, US)", "language": "English"},
    {"id": "en-US-EricNeural", "name": "Eric (Male, US)", "language": "English"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (Male, UK)", "language": "English"},
    {"id": "en-GB-ThomasNeural", "name": "Thomas (Male, UK)", "language": "English"},
    {"id": "en-AU-WilliamNeural", "name": "William (Male, Australian)", "language": "English"},
    {"id": "en-CA-LiamNeural", "name": "Liam (Male, Canadian)", "language": "English"},
    {"id": "en-US-JennyNeural", "name": "Jenny (Female, US)", "language": "English"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (Female, UK)", "language": "English"},
    {"id": "en-AU-NatashaNeural", "name": "Natasha (Female, Australian)", "language": "English"},
    {"id": "ar-MA-JamalNeural", "name": "Jamal (Male, Moroccan)", "language": "Arabic"},
    {"id": "ar-EG-ShakirNeural", "name": "Shakir (Male, Egyptian)", "language": "Arabic"},
    {"id": "ar-SA-FahdNeural", "name": "Fahd (Male, Saudi)", "language": "Arabic"},
    {"id": "fr-FR-HenriNeural", "name": "Henri (Male)", "language": "French"},
    {"id": "fr-FR-DeniseNeural", "name": "Denise (Female)", "language": "French"},
    {"id": "de-DE-ConradNeural", "name": "Conrad (Male)", "language": "German"},
    {"id": "de-DE-KatjaNeural", "name": "Katja (Female)", "language": "German"},
    {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Male)", "language": "Spanish"},
    {"id": "es-ES-ElviraNeural", "name": "Elvira (Female)", "language": "Spanish"},
    {"id": "it-IT-DiegoNeural", "name": "Diego (Male)", "language": "Italian"},
    {"id": "it-IT-ElsaNeural", "name": "Elsa (Female)", "language": "Italian"},
    {"id": "pt-BR-AntonioNeural", "name": "Antonio (Male, Brazilian)", "language": "Portuguese"},
    {"id": "pt-BR-FranciscaNeural", "name": "Francisca (Female, Brazilian)", "language": "Portuguese"}
]

AVAILABLE_LANGUAGES = sorted(list(set([voice["language"] for voice in AVAILABLE_VOICES])))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_id():
    return f"{int(time.time())}_{os.urandom(4).hex()}"

def run_async_task(coroutine, job_id):
    async def wrapper():
        try:
            jobs[job_id]['status'] = 'processing'
            result = await coroutine
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['result'] = result
        except Exception as e:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            if app.debug:
                print(f"Error in job {job_id}: {str(e)}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(wrapper())
    loop.close()

def setup_gemini_api(api_key):
    genai.configure(api_key=api_key)

# ============================================
# MAIN APPLICATION ROUTES
# ============================================

@app.route('/')
def index():
    """Main page with news"""
    prefill = request.args.get('prefill', '')

    try:
        first_articles = gnews_client.get_top_headlines(category='general', language='en')
        articles = first_articles.get('articles', [])
    except Exception as e:
        if app.debug:
            app.logger.error(f"GNews API error on index: {e}")
        articles = []

    return render_template(
        'news.html',
        voices=AVAILABLE_VOICES,
        languages=AVAILABLE_LANGUAGES,
        articles=articles,
        prefill=prefill
    )

@app.route('/upload', methods=['POST'])
@rate_limit('api_upload')
def upload_file():
    """Handle file uploads for TTS"""
    input_method = request.form.get('input-method', 'text')
    voice_id = request.form.get('voice', 'en-US-JennyNeural')
    speed = float(request.form.get('speed', 1.0))
    depth = int(request.form.get('depth', 1))
    title = request.form.get('title', '')
    
    job_id = generate_unique_id()
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    if input_method == 'text':
        text_content = request.form.get('text-content', '').strip()
        
        if not text_content:
            return render_template('error.html', message="No text provided.")
        
        script_filename = f"text_input_{job_id}.txt"
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    else:
        if 'script' not in request.files:
            return jsonify({'error': 'No script file provided'}), 400
        
        script_file = request.files['script']
        if script_file.filename == '':
            return jsonify({'error': 'No script file selected'}), 400
        
        if not script_file or not allowed_file(script_file.filename):
            return jsonify({'error': 'Invalid file format'}), 400
        
        script_filename = secure_filename(script_file.filename)
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
        script_file.save(script_path)
        
        if not title and script_filename:
            title = os.path.splitext(script_filename)[0]
    
    output_filename = f"tts_{job_id}.mp3"
    if title:
        safe_title = secure_filename(title)
        if safe_title:
            output_filename = f"{safe_title}_{job_id}.mp3"
    
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    jobs[job_id] = {
        'status': 'pending',
        'script_file': script_path,
        'output_file': output_path,
        'start_time': time.time(),
        'input_type': input_method,
        'voice_id': voice_id,
        'speed': speed,
        'depth': depth,
        'title': title,
        'filename': output_filename
    }
    
    process_task = generate_simple_tts(script_path, output_path, voice_id, speed, depth)
    
    thread = threading.Thread(target=run_async_task, args=(process_task, job_id))
    thread.daemon = True
    thread.start()
    
    if 'jobs' not in session:
        session['jobs'] = []
    session['jobs'].append(job_id)
    session.modified = True
    
    return redirect(url_for('job_status', job_id=job_id))

@app.route('/status/<job_id>')
def job_status(job_id):
    """Job status page"""
    if job_id not in jobs:
        return render_template('error.html', message="Job not found."), 404
    
    job = jobs[job_id]
    return render_template('status.html', job_id=job_id, job=job, voices=AVAILABLE_VOICES)

@app.route('/api/status/<job_id>')
@rate_limit('api_general')
def api_job_status(job_id):
    """API endpoint for job status"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id].copy()
    elapsed = time.time() - job['start_time']
    job['elapsed_time'] = elapsed
    
    return jsonify(job)

@app.route('/download/<job_id>')
def download_file(job_id):
    """Download completed audio file"""
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return render_template('error.html', message="File not available."), 404
    
    output_file = jobs[job_id]['result']
    filename = jobs[job_id].get('filename', f"voiceover_{job_id}.mp3")
    
    return send_file(output_file, as_attachment=True, download_name=filename)

@app.route('/stream-audio/<job_id>')
def stream_audio(job_id):
    """Stream audio file"""
    job = jobs.get(job_id)
    
    if not job:
        return "Job not found", 404
    
    if job['status'] != 'completed':
        return "Audio not ready", 404
    
    audio_file = job.get('result') or job.get('output_file')
    
    return send_file(
        audio_file, 
        mimetype='audio/mpeg',
        as_attachment=False,
        conditional=True
    )

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    user_jobs = session.get('jobs', [])
    user_job_data = {}
    
    for job_id in user_jobs:
        if job_id in jobs:
            user_job_data[job_id] = jobs[job_id]
    
    return render_template('dashboard.html', jobs=user_job_data, voices=AVAILABLE_VOICES)

# ============================================
# NEWS API ROUTES
# ============================================

@app.route('/news')
def news_page():
    """News page"""
    try:
        first_articles = gnews_client.get_top_headlines(category='general', language='en')
        articles = first_articles.get('articles', [])
    except Exception as e:
        if app.debug:
            app.logger.error(f"GNews API error: {e}")
        articles = []

    return render_template('news.html', languages=AVAILABLE_LANGUAGES, voices=AVAILABLE_VOICES, articles=articles)

@app.route('/api/news')
@rate_limit('api_news')
def get_news():
    """API endpoint to fetch news"""
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'en')
    query = request.args.get('query', '').strip()

    try:
        if query:
            results = gnews_client.search_news(query=query, language=language)
        else:
            results = gnews_client.get_top_headlines(category=category, language=language)

        return jsonify(results)

    except Exception as e:
        if app.debug:
            app.logger.error(f"News API error: {e}")
        return jsonify({
            "error": "Unable to load news at the moment",
            "articles": []
        }), 500

@app.route('/api/news/content')
@rate_limit('api_news')
def get_article_content():
    """Extract article content"""
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        result = gnews_client.fetch_article_content(url)
        
        if not result.get('content') or len(result.get('content', '').strip()) < 100:
            if app.debug:
                app.logger.warning(f"Minimal content extracted for {url}")
            result['extraction_error'] = "Could not extract sufficient content"
            result['content'] = result.get('content', '') or "Content extraction failed"
        
        return jsonify(result)
    except Exception as e:
        if app.debug:
            app.logger.error(f"Content extraction error: {str(e)}")
        return jsonify({
            "error": "Content extraction failed",
            "content": "Unable to extract content from this article",
            "url": url
        }), 200

@app.route('/api/news/summary-audio', methods=['POST'])
@rate_limit('api_tts')
def summary_audio():
    """Generate audio from text"""
    data = request.json
    text = data.get("description", "") or data.get("content", "")
    voice_id = data.get("voice_id", "en-CA-LiamNeural")
    speed = float(data.get("speed", 1.0))
    depth = int(data.get("depth", 1))

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    try:
        # Clean text
        text = re.sub(r'<[^>]*?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp:
            temp.write(text)
            script_path = temp.name

        # Generate audio
        output_filename = f"{int(time.time())}_{voice_id}.mp3"
        output_audio = os.path.join("static/audio", output_filename)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_simple_tts(script_path, output_audio, voice_id, speed, depth))

        return jsonify({"audio_url": f"/static/audio/{output_filename}"})

    except Exception as e:
        if app.debug:
            app.logger.error(f"TTS error: {e}")
        return jsonify({"error": "Audio generation failed"}), 500

@app.route('/api/news/summary-audio-async', methods=['POST'])
@rate_limit('api_tts')
def summary_audio_async():
    """Async audio generation"""
    data = request.json
    text = data.get("description", "") or data.get("content", "")
    voice_id = data.get("voice_id", "en-CA-LiamNeural")
    speed = float(data.get("speed", 1.0))
    depth = int(data.get("depth", 1))

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    task_id = str(uuid.uuid4())
    message = generate_tts_task.send(text, voice_id, speed, depth, task_id)
    
    return jsonify({
        "task_id": task_id,
        "message_id": message.message_id,
        "status": "processing",
        "message": "Audio generation started"
    })

@app.route('/api/news/voice-optimize', methods=['POST'])
@rate_limit('api_general')
def optimize_article_for_voice():
    """Optimize text for voice"""
    data = request.json

    if not data or 'description' not in data:
        return jsonify({"error": "No description provided"}), 400

    try:
        description = data.get('description', '').strip()
        
        if not description:
            return jsonify({"error": "Empty description"}), 400
        
        # Clean HTML
        clean_description = re.sub(r'<[^>]*?>', '', description)
        clean_description = re.sub(r'\s+', ' ', clean_description).strip()
        
        return jsonify({"optimized_content": clean_description})
    except Exception as e:
        if app.debug:
            app.logger.error(f"Voice optimization error: {str(e)}")
        return jsonify({"error": "Optimization failed"}), 500

@app.route('/api/news-cached')
@rate_limit('api_news')
def get_news_cached():
    """Cached news endpoint"""
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'en')
    
    cache_key = f"news:{category}:{language}"
    cached_news = redis_client.get(cache_key)
    
    if cached_news:
        return jsonify(json.loads(cached_news))
    
    try:
        results = gnews_client.get_top_headlines(category=category, language=language)
        cache_news_task.send(category, language)
        return jsonify(results)
    except Exception:
        return jsonify({"error": "Failed to fetch news", "articles": []}), 500

@app.route('/api/task-status/<task_id>')
@rate_limit('api_general')
def get_task_status(task_id):
    """Get background task status"""
    try:
        cache_key = f"tts:{task_id}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            result = json.loads(cached_result)
            return jsonify({
                'state': 'SUCCESS',
                'progress': 100,
                'result': result,
                'message': 'Audio generation completed!'
            })
        
        return jsonify({
            'state': 'PROCESSING',
            'progress': 50,
            'message': 'Generating audio...'
        })
        
    except Exception as e:
        return jsonify({
            'state': 'FAILURE',
            'error': str(e),
            'message': 'Task failed'
        })

# ============================================
# OTHER ROUTES
# ============================================

# Replace the existing newsletter_subscribe route with this enhanced version
@app.route('/api/newsletter-subscribe', methods=['POST'])
@rate_limit('api_general')
def newsletter_subscribe():
    """Enhanced newsletter subscription with user tracking"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        categories = data.get('categories', [])
        
        # Validation
        if not name or len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        
        if not email or '@' not in email or len(email) < 5:
            return jsonify({'error': 'Invalid email address'}), 400
        
        if not categories or not isinstance(categories, list):
            return jsonify({'error': 'Please select at least one category'}), 400
        
        # Sanitize inputs
        name = sanitize_html_input(name)[:100]
        email = sanitize_html_input(email)[:255]
        
        # Validate categories
        valid_category_ids = [cat['id'] for cat in NEWSLETTER_CATEGORIES]
        categories = [cat for cat in categories if cat in valid_category_ids]
        
        if not categories:
            return jsonify({'error': 'Please select valid categories'}), 400
        
        # Check if user already exists
        existing_subscriber = get_subscriber_by_email(email)
        
        if existing_subscriber:
            # Update existing subscriber
            doc_ref = db.collection('newsletter_subscribers').document(existing_subscriber['id'])
            doc_ref.update({
                'name': name,
                'categories': categories,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'active': True
            })
            
            # Set session
            session['subscriber_id'] = existing_subscriber['id']
            session['subscriber_name'] = name
            session['subscriber_email'] = email
            session.permanent = True
            
            return jsonify({
                'message': 'Subscription updated successfully!',
                'subscriber_name': name,
                'existing_user': True
            })
        else:
            # Create new subscriber
            user_token = generate_user_token()
            subscriber_data = {
                'name': name,
                'email': email,
                'categories': categories,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'active': True,
                'user_token': user_token,
                'total_likes': 0,
                'total_comments': 0,
                'user_ip': request.environ.get('REMOTE_ADDR', 'unknown')
            }
            
            doc_ref = db.collection('newsletter_subscribers').add(subscriber_data)
            subscriber_id = doc_ref[1].id
            
            # Set session
            session['subscriber_id'] = subscriber_id
            session['subscriber_name'] = name
            session['subscriber_email'] = email
            session.permanent = True
            
            return jsonify({
                'message': 'Subscription successful! You can now like and comment with your name.',
                'subscriber_name': name,
                'existing_user': False
            })
            
    except Exception as e:
        if app.debug:
            app.logger.error(f'Newsletter subscription error: {e}')
        return jsonify({'error': 'Subscription failed. Please try again.'}), 500
# Add this new route for newsletter management
@app.route('/newsletter')
def newsletter_page():
    """Newsletter subscription page"""
    user = get_user_from_session()
    return render_template('newsletter.html', 
                         categories=NEWSLETTER_CATEGORIES,
                         user=user)

@app.route('/api/newsletter-unsubscribe', methods=['POST'])
@rate_limit('api_general')
def newsletter_unsubscribe():
    """Unsubscribe from newsletter"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({'error': 'Not subscribed'}), 400
        
        # Deactivate subscription instead of deleting
        db.collection('newsletter_subscribers').document(session['subscriber_id']).update({
            'active': False,
            'unsubscribed_at': firestore.SERVER_TIMESTAMP
        })
        
        # Clear session
        session.pop('subscriber_id', None)
        session.pop('subscriber_name', None)
        session.pop('subscriber_email', None)
        
        return jsonify({'message': 'Successfully unsubscribed'})
        
    except Exception as e:
        if app.debug:
            app.logger.error(f'Newsletter unsubscribe error: {e}')
        return jsonify({'error': 'Unsubscribe failed'}), 500
@app.route('/api/subscriber-status')
@rate_limit('api_general')
def subscriber_status():
    """Get current subscriber status"""
    user = get_user_from_session()
    if user:
        return jsonify({
            'subscribed': True,
            'name': user.get('name'),
            'email': user.get('email'),
            'categories': user.get('categories', []),
            'total_likes': user.get('total_likes', 0),
            'total_comments': user.get('total_comments', 0)
        })
    return jsonify({'subscribed': False})


@app.context_processor
def inject_subscriber_status():
    """Inject subscriber status into all templates"""
    user = get_user_from_session()
    return {
        'subscriber': user,
        'newsletter_categories': NEWSLETTER_CATEGORIES
    }
@app.route('/stream-temp-audio/<path:path>')
def stream_temp_audio(path):
    """Stream temporary audio files"""
    audio_path = os.path.join(app.config['OUTPUT_FOLDER'], path)
    
    if not os.path.exists(audio_path):
        if app.debug:
            app.logger.error(f"Audio file not found: {audio_path}")
        return jsonify({"error": "Audio file not found"}), 404
    
    try:
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            if app.debug:
                app.logger.error(f"Audio file is empty: {audio_path}")
            return jsonify({"error": "Audio file is empty"}), 404
    except OSError as e:
        if app.debug:
            app.logger.error(f"Error checking file size: {e}")
        return jsonify({"error": "Error accessing file"}), 500
    
    try:
        return send_file(audio_path, mimetype="audio/mpeg")
    except Exception as e:
        if app.debug:
            app.logger.error(f"Error serving audio file: {e}")
        return jsonify({"error": "Error serving file"}), 500

@app.route('/api/rate-limit/status')
@conditional_rate_limit('api_general')
def rate_limit_status():
    """Get rate limit status"""
    client_id = get_client_id()
    status = {}
    
    for category, config in RATE_LIMITS.items():
        rate_key = f"rate_limit:{category}:{client_id}"
        current_time = int(time.time())
        
        redis_client.zremrangebyscore(rate_key, 0, current_time - config['window'])
        current_requests = redis_client.zcard(rate_key)
        
        status[category] = {
            'limit': config['limit'],
            'window': config['window'],
            'current_requests': current_requests,
            'remaining': max(0, config['limit'] - current_requests),
            'reset_time': current_time + config['window']
        }
    
    return jsonify({
        'client_id': client_id[:8] + '...',
        'rate_limits': status
    })

# Static pages
@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms-of-service')
def terms():
    return render_template('terms.html')

# SEO routes
@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Disallow:
Sitemap: https://newsnap.space/sitemap.xml"""
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml', mimetype='application/xml')

# Health check
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0'
    })

# Template filters
@app.template_filter('strftime')
def _jinja2_filter_datetime(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M')

# Cleanup function
def cleanup_old_files():
    """Clean up old temporary files"""
    current_time = time.time()
    cutoff_time = current_time - 3600
    
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        try:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        if app.debug:
                            app.logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            if app.debug:
                app.logger.error(f"Error during cleanup: {e}")

# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    # Environment-based startup
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    if debug_mode:
        print("🚨 WARNING: Running in development mode!")
        print("🔧 Debug logging enabled")
        print("🔓 Permissive CSP active")
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        print("🚀 Starting in production mode...")
        print("🔒 Security headers active")
        print("🛡️  Rate limiting enforced")
        print("🔇 Minimal logging enabled")
        
        # Setup Gemini API
        setup_gemini_api(app.config['GEMINI_API_KEY'])
        
        # Run production server
        app.run(debug=False, host='0.0.0.0', port=port)