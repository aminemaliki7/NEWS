import os
import asyncio
import tempfile
import time
import json
import threading
import uuid
from flask import Flask, Response, request, render_template, redirect, url_for, send_file, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime
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
import os
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from flask import request, session
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secure-random-key-here')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client() 
# Initialize Redis
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_broker = RedisBroker(url=redis_url)
result_backend = RedisBackend(url=redis_url)
redis_broker.add_middleware(Results(backend=result_backend))
# Set the broker globally
dramatiq.set_broker(redis_broker)

# Export for easy importing
broker = redis_broker
gnews_client = GNewsClient() 
COMMENTS = {}


load_dotenv()

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
    "databaseURL": ""  # Not needed now unless you use Realtime DB
}




# Add this route to your Flask app (around line 70, after the comments routes)

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """API endpoint to submit user feedback"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        feedback_text = data.get('feedback', '').strip()
        
        if not feedback_text:
            return jsonify({"error": "Feedback text is required"}), 400
        
        if len(feedback_text) < 5:
            return jsonify({"error": "Feedback must be at least 5 characters long"}), 400
        
        if len(feedback_text) > 1000:
            return jsonify({"error": "Feedback must be less than 1000 characters"}), 400
        
        # Prepare feedback document
        feedback_doc = {
            'feedback': feedback_text,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'source': data.get('source', 'unknown'),
            'page': data.get('page', ''),
            'user_ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
            'user_agent': request.headers.get('User-Agent', '')[:200]  # Truncate for storage
        }
        
        # Add optional fields if provided
        if 'timestamp' in data:
            feedback_doc['client_timestamp'] = data['timestamp']
        
        # Save to Firestore
        db.collection('feedback').add(feedback_doc)
        
        app.logger.info(f"Feedback submitted successfully from {request.environ.get('REMOTE_ADDR')}")
        
        return jsonify({
            "message": "Feedback submitted successfully", 
            "success": True
        })
        
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({"error": "Failed to submit feedback. Please try again."}), 500


# Optional: Add an admin route to view feedback (add this if you want to see feedback in browser)
@app.route('/admin/feedback')
def view_feedback():
    """Admin route to view submitted feedback (optional)"""
    try:
        # Get recent feedback (last 50 entries)
        feedback_ref = db.collection('feedback')
        feedback_docs = feedback_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()
        
        feedback_list = []
        for doc in feedback_docs:
            feedback_data = doc.to_dict()
            feedback_data['id'] = doc.id
            feedback_list.append(feedback_data)
        
        # You can create a simple template or return JSON
        return jsonify({"feedback": feedback_list})
        
    except Exception as e:
        app.logger.error(f"Error retrieving feedback: {str(e)}")
        return jsonify({"error": "Failed to retrieve feedback"}), 500
@app.route('/api/comment-like', methods=['POST'])
def handle_comment_like():
    """Handle heart like/unlike for comments"""
    try:
        data = request.get_json()
        comment_id = data.get('comment_id')
        article_id = data.get('article_id')
        
        if not comment_id or not article_id:
            return jsonify({'error': 'Missing comment_id or article_id'}), 400
        
        # Get user identifier (using your existing get_user_id function)
        user_id = get_user_id()
        
        # Reference to the comment document
        comment_ref = db.collection('comments').document(article_id).collection('comments').document(comment_id)
        
        # Use a transaction to ensure consistency
        @firestore.transactional
        def update_like(transaction):
            # Get current comment data
            comment_doc = comment_ref.get(transaction=transaction)
            if not comment_doc.exists:
                raise ValueError("Comment not found")
            
            comment_data = comment_doc.to_dict()
            
            # Initialize likes data if not present
            if 'likes' not in comment_data:
                comment_data['likes'] = 0
            if 'liked_by' not in comment_data:
                comment_data['liked_by'] = []
            
            liked_by = comment_data['liked_by']
            current_likes = comment_data['likes']
            user_liked = user_id in liked_by
            
            # Toggle like status
            if user_liked:
                # Unlike: remove user from liked_by and decrease count
                liked_by.remove(user_id)
                current_likes = max(0, current_likes - 1)
                new_user_liked = False
            else:
                # Like: add user to liked_by and increase count
                if user_id not in liked_by:
                    liked_by.append(user_id)
                current_likes += 1
                new_user_liked = True
            
            # Update the comment document
            transaction.update(comment_ref, {
                'likes': current_likes,
                'liked_by': liked_by,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            return {
                'likes': current_likes,
                'user_liked': new_user_liked
            }
        
        # Execute the transaction
        transaction = db.transaction()
        result = update_like(transaction)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        app.logger.error(f"Error handling comment like: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
# API — Article Comment
@app.route('/api/article-comment', methods=['POST'])
def post_comment():
    data = request.json
    article_id = data.get('article_id')
    comment_text = data.get('comment_text', '').strip()
    nickname = data.get('nickname', '').strip()

    if not article_id or not comment_text:
        return jsonify({"error": "Missing article_id or comment_text"}), 400

    # If no nickname provided — generate a subtle reference nickname
    if not nickname:
        import random
        random_names = [
            "Orwellian", "Tarkovsky", "Aletheia", "NovaScript", "ShinjukuEcho",
            "Casablanca27", "InkRunner", "Byzantium", "Satori", "Hikari",
            "Rocinante", "Arcadia", "Zephyr42", "Athenaeum", "Obsidian",
            "LisboaVox", "TwelveMonkeys", "Monolith", "OsloMind", "Halcyon",
            "Cinephile", "NeoNomad", "NorthByWest", "Palimpsest", "LouvreLens",
            "Kafkaesque", "GhibliWaves", "Mirage", "VeronaCall", "Ozymandias",
            "ElysiumTrace", "EdoRunner", "PolarisPoint", "HelsinkiTone", "MemphisInk"
        ]
        nickname = random.choice(random_names)

    try:
        # Each article will be a collection
        doc_ref = db.collection('comments').document(article_id).collection('comments').document()

        # Updated comment structure with heart likes
        comment_data = {
            'nickname': nickname,
            'comment': comment_text,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'likes': 0,
            'liked_by': []  # Array of user_ids who liked this comment
        }

        doc_ref.set(comment_data)

        return jsonify({"message": "Comment posted", "nickname": nickname})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
def get_user_id():
    """Generate a consistent user ID based on IP address for voting"""
    user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    # Create a hash of IP + user agent for better uniqueness while maintaining anonymity
    user_agent = request.headers.get('User-Agent', '')
    user_string = f"{user_ip}:{user_agent}"
    return hashlib.sha256(user_string.encode()).hexdigest()[:16]
# API — Article Comment
@app.route('/api/article-comments', methods=['GET'])
def get_comments():
    article_id = request.args.get('article_id')
    if not article_id:
        return jsonify({"error": "Missing article_id"}), 400

    try:
        user_id = get_user_id()  # Get current user's ID for like state
        
        comments_ref = db.collection('comments').document(article_id).collection('comments')
        comments_snapshot = comments_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

        comments = []
        for doc in comments_snapshot:
            comment = doc.to_dict()
            comment['id'] = doc.id
            
            # Add user's current like state
            liked_by = comment.get('liked_by', [])
            comment['userLiked'] = user_id in liked_by
            
            # Ensure likes count exists
            comment['likes'] = comment.get('likes', 0)
            
            # Remove the liked_by array from response for privacy
            comment.pop('liked_by', None)
            
            comments.append(comment)

        # Sort comments by likes count (highest first), then by timestamp
        comments.sort(key=lambda x: (x.get('likes', 0), x.get('timestamp', 0)), reverse=True)

        return jsonify({"comments": comments})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/migrate-to-heart-likes', methods=['POST'])
def migrate_to_heart_likes():
    """One-time migration to convert upvote/downvote system to heart likes"""
    try:
        # This is a utility endpoint - you should protect it or remove it after migration
        password = request.json.get('password') if request.json else None
        if password != 'your_migration_password':  # Set a secure password
            return jsonify({"error": "Unauthorized"}), 401
        
        updated_count = 0
        
        # Get all articles that have comments
        comments_collection = db.collection('comments')
        articles = comments_collection.stream()
        
        for article_doc in articles:
            article_id = article_doc.id
            # Get all comments for this article
            comments_ref = comments_collection.document(article_id).collection('comments')
            comments = comments_ref.stream()
            
            for comment_doc in comments:
                comment_data = comment_doc.to_dict()
                
                # Check if this comment has the old voting system
                if 'upvotes' in comment_data or 'downvotes' in comment_data:
                    upvotes = comment_data.get('upvotes', 0)
                    downvotes = comment_data.get('downvotes', 0)
                    user_votes = comment_data.get('user_votes', {})
                    
                    # Convert to heart likes: only count users who upvoted
                    liked_by = [user_id for user_id, vote in user_votes.items() if vote == 'up']
                    likes_count = len(liked_by)
                    
                    # Update the comment with new structure
                    update_data = {
                        'likes': likes_count,
                        'liked_by': liked_by
                    }
                    
                    # Remove old fields
                    comment_doc.reference.update(update_data)
                    
                    # Remove old fields (Firestore doesn't have a direct way to delete fields in update)
                    # You might want to do this manually or in a separate operation
                    
                    updated_count += 1
        
        return jsonify({
            "message": f"Migration completed. Updated {updated_count} comments to heart like system.",
            "updated_count": updated_count
        })
        
    except Exception as e:
        app.logger.error(f"Migration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add a migration function to update existing comments (run this once)
@app.route('/api/article-like', methods=['POST'])
def handle_article_like():
    """Handle heart like/unlike for articles (Instagram style)"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({'error': 'Missing article_id'}), 400
        
        user_id = get_user_id()
        
        # Reference to the article likes document
        article_ref = db.collection('article_likes').document(article_id)
        
        # Use a transaction to ensure consistency
        @firestore.transactional
        def update_article_like(transaction):
            # Get current article data
            article_doc = article_ref.get(transaction=transaction)
            
            if not article_doc.exists:
                # Create new article likes document
                article_data = {
                    'likes': 0,
                    'liked_by': []
                }
            else:
                article_data = article_doc.to_dict()
            
            # Initialize likes data if not present
            if 'likes' not in article_data:
                article_data['likes'] = 0
            if 'liked_by' not in article_data:
                article_data['liked_by'] = []
            
            liked_by = article_data['liked_by']
            current_likes = article_data['likes']
            user_liked = user_id in liked_by
            
            # Toggle like status
            if user_liked:
                # Unlike: remove user from liked_by and decrease count
                liked_by.remove(user_id)
                current_likes = max(0, current_likes - 1)
                new_user_liked = False
            else:
                # Like: add user to liked_by and increase count
                if user_id not in liked_by:
                    liked_by.append(user_id)
                current_likes += 1
                new_user_liked = True
            
            # Update the document
            transaction.set(article_ref, {
                'likes': current_likes,
                'liked_by': liked_by,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
            return {
                'likes': current_likes,
                'user_liked': new_user_liked
            }
        
        # Execute the transaction
        transaction = db.transaction()
        result = update_article_like(transaction)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        app.logger.error(f"Error handling article like: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/article-likes', methods=['GET'])
def get_article_likes():
    """Get like count and user like status for an article"""
    try:
        article_id = request.args.get('article_id')
        if not article_id:
            return jsonify({'error': 'Missing article_id parameter'}), 400
        
        user_id = get_user_id()
        
        # Get article likes document
        article_ref = db.collection('article_likes').document(article_id)
        article_doc = article_ref.get()
        
        if not article_doc.exists:
            return jsonify({
                'likes': 0,
                'user_liked': False
            })
        
        article_data = article_doc.to_dict()
        liked_by = article_data.get('liked_by', [])
        
        return jsonify({
            'likes': article_data.get('likes', 0),
            'user_liked': user_id in liked_by
        })
        
    except Exception as e:
        app.logger.error(f"Error getting article likes: {str(e)}")
        return jsonify({'error': 'Failed to get article likes'}), 500
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')
@app.route('/terms-of-service')
def terms():
    return render_template('terms.html')


# 404 / 500 handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', message="Internal server error."), 500


def setup_gemini_api(api_key):
    genai.configure(api_key=api_key)
# Add this to your app initialization
app.config['GEMINI_API_KEY'] = os.getenv("GEMINI_API_KEY")
# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
ALLOWED_EXTENSIONS = {'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Dictionary to store job statuses
jobs = {}

# Define available voices with language grouping
AVAILABLE_VOICES = [
    # English voices
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
    
    # Arabic voices
    {"id": "ar-MA-JamalNeural", "name": "Jamal (Male, Moroccan)", "language": "Arabic"},
    {"id": "ar-EG-ShakirNeural", "name": "Shakir (Male, Egyptian)", "language": "Arabic"},
    {"id": "ar-SA-FahdNeural", "name": "Fahd (Male, Saudi)", "language": "Arabic"},
    
    # French voices
    {"id": "fr-FR-HenriNeural", "name": "Henri (Male)", "language": "French"},
    {"id": "fr-FR-DeniseNeural", "name": "Denise (Female)", "language": "French"},
    
    # German voices
    {"id": "de-DE-ConradNeural", "name": "Conrad (Male)", "language": "German"},
    {"id": "de-DE-KatjaNeural", "name": "Katja (Female)", "language": "German"},
    
    # Spanish voices
    {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Male)", "language": "Spanish"},
    {"id": "es-ES-ElviraNeural", "name": "Elvira (Female)", "language": "Spanish"},
    
    # Italian voices
    {"id": "it-IT-DiegoNeural", "name": "Diego (Male)", "language": "Italian"},
    {"id": "it-IT-ElsaNeural", "name": "Elsa (Female)", "language": "Italian"},
    
    # Portuguese voices
    {"id": "pt-BR-AntonioNeural", "name": "Antonio (Male, Brazilian)", "language": "Portuguese"},
    {"id": "pt-BR-FranciscaNeural", "name": "Francisca (Female, Brazilian)", "language": "Portuguese"}
]

# Define languages from available voices
AVAILABLE_LANGUAGES = sorted(list(set([voice["language"] for voice in AVAILABLE_VOICES])))
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_id():
    return f"{int(time.time())}_{os.urandom(4).hex()}"

# Custom function to run async tasks in the background
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
            print(f"Error in job {job_id}: {str(e)}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(wrapper())
    loop.close()

# Routes
@app.route('/')
def index():
    """Render the home page with latest news (default = general)"""
    prefill = request.args.get('prefill', '')

    try:
        first_articles = gnews_client.get_top_headlines(category='general', language='en')
        articles = first_articles.get('articles', [])
    except Exception as e:
        app.logger.error(f"GNews API error on index: {e}")
        articles = []

    return render_template(
        'news.html',
        voices=AVAILABLE_VOICES,
        languages=AVAILABLE_LANGUAGES,
        articles=articles,
        prefill=prefill
    )


# Update the upload route to store the title
@app.route('/upload', methods=['POST'])
def upload_file():
    # Get the input method (text or file)
    input_method = request.form.get('input-method', 'text')
    
    # Process form data for voice/speed/depth
    voice_id = request.form.get('voice', 'en-US-JennyNeural')
    speed = float(request.form.get('speed', 1.0))
    depth = int(request.form.get('depth', 1))
    
    # Get title for the file if provided
    title = request.form.get('title', '')
    
    # Generate a unique job ID
    job_id = generate_unique_id()
    
    # Create temp directories if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Handle text input
    if input_method == 'text':
        text_content = request.form.get('text-content', '').strip()
        
        if not text_content:
            return render_template('error.html', message="No text provided. Please enter some text to convert to speech.")
        
        # Save the text to a temporary file
        script_filename = f"text_input_{job_id}.txt"
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    # Handle file upload
    else:
        # ... (existing file upload code)
        if 'script' not in request.files:
            return jsonify({'error': 'No script file provided'}), 400
        
        script_file = request.files['script']
        if script_file.filename == '':
            return jsonify({'error': 'No script file selected'}), 400
        
        if not script_file or not allowed_file(script_file.filename):
            return jsonify({'error': 'Invalid file format. Please upload a .txt file for scripts'}), 400
        
        # Save the uploaded file
        script_filename = secure_filename(script_file.filename)
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
        script_file.save(script_path)
        
        # If no title was provided, use the filename (without extension) as title
        if not title and script_filename:
            title = os.path.splitext(script_filename)[0]
    
    # Generate safe filename from title if available
    output_filename = f"tts_{job_id}.mp3"
    if title:
        # Create a safe filename from the title
        safe_title = secure_filename(title)
        if safe_title:
            output_filename = f"{safe_title}_{job_id}.mp3"
    
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    # Store title and other values in job info for reference
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
    
    # Start the processing task in a background thread
    process_task = generate_simple_tts(
        script_path, output_path, voice_id, speed, depth
    )
    
    thread = threading.Thread(
        target=run_async_task,
        args=(process_task, job_id)
    )
    thread.daemon = True
    thread.start()
    
    # Store job ID in session
    if 'jobs' not in session:
        session['jobs'] = []
    session['jobs'].append(job_id)
    session.modified = True
    
    return redirect(url_for('job_status', job_id=job_id))



@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in jobs:
        return render_template('error.html', message="Job not found.")
    
    job = jobs[job_id]
    # Pass the AVAILABLE_VOICES list to the template
    return render_template('status.html', job_id=job_id, job=job, voices=AVAILABLE_VOICES)

@app.route('/api/status/<job_id>')
def api_job_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id].copy()
    # Calculate elapsed time
    elapsed = time.time() - job['start_time']
    job['elapsed_time'] = elapsed
    
    return jsonify(job)

@app.route('/download/<job_id>')
def download_file(job_id):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return render_template('error.html', message="File not available for download.")
    
    output_file = jobs[job_id]['result']
    # Get the custom filename from the job info
    filename = jobs[job_id].get('filename', f"voiceover_{job_id}.mp3")
    
    return send_file(output_file, as_attachment=True, download_name=filename)

@app.route('/stream-audio/<job_id>')
def stream_audio(job_id):
    # Get the job data from your jobs dictionary
    job = jobs.get(job_id)
    
    if not job:
        return "Job not found", 404
    
    # Check if job is completed
    if job['status'] != 'completed':
        return "Audio not ready for streaming", 404
    
    # For completed jobs, your app stores the output path in different ways
    # When a job completes successfully, sometimes it stores the path in 'result'
    # and sometimes in 'output_file'
    if 'result' in job and job['result']:
        audio_file = job['result']
    else:
        audio_file = job['output_file']
    
    # Return the file as a streaming response
    return send_file(
        audio_file, 
        mimetype='audio/mpeg',
        as_attachment=False,
        conditional=True
    )
@app.route('/dashboard')
def dashboard():
    user_jobs = session.get('jobs', [])
    user_job_data = {}
    
    for job_id in user_jobs:
        if job_id in jobs:
            user_job_data[job_id] = jobs[job_id]
    
    # Pass the AVAILABLE_VOICES list to the template
    return render_template('dashboard.html', jobs=user_job_data, voices=AVAILABLE_VOICES)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message="Internal server error. Please try again later."), 500

# Add this after creating your Flask app
@app.template_filter('strftime')
def _jinja2_filter_datetime(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M')


@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

# Add a conversion option to send downloaded audio to voice generator
@app.route('/convert-to-voice/<download_id>')
def convert_to_voice(download_id):
    if not hasattr(app, 'media_downloads'):
        app.media_downloads = {}
        
    if download_id not in app.media_downloads or app.media_downloads[download_id]['type'] != 'audio':
        return render_template('error.html', message="Audio file not found.")
    
    # Get the file path
    audio_file = app.media_downloads[download_id]['file_path']
    
    # Redirect to the main voice generator page with a parameter
    # to indicate we want to use this audio file
    return redirect(url_for('index', audio_source=download_id))
@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Disallow:
Sitemap: https://newsnap.space/sitemap.xml"""
    return Response(content, mimetype='text/plain')
@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml', mimetype='application/xml')


@app.route('/news')
def news_page():
    """Render the news reader page"""
    try:
        first_articles = gnews_client.get_top_headlines(category='general', language='en')
        articles = first_articles.get('articles', [])
    except Exception as e:
        app.logger.error(f"GNews API error: {e}")
        articles = []

    # Get the same voice and language data
    languages = AVAILABLE_LANGUAGES
    voices = AVAILABLE_VOICES
    
    # Render the template (even if articles = [])
    return render_template('news.html', languages=languages, voices=voices, articles=articles)


@app.route('/api/news')
def get_news():
    """API endpoint to fetch news from GNews"""
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'en')
    query = request.args.get('query', '').strip()

    try:
        # If query exists and is not just whitespace, use search
        if query:
            results = gnews_client.search_news(query=query, language=language)
        else:
            results = gnews_client.get_top_headlines(category=category, language=language)

        return jsonify(results)

    except Exception:
        # Return clean error message to user
        return jsonify({
            "error": "Sorry, we couldn't load news articles at the moment. Please try again later .",
            "articles": []
        }), 500


@app.route('/api/news/content')
def get_article_content():
    """API endpoint to fetch and extract content from a news article"""
    # Get the article URL
    url = request.args.get('url', '')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    try:
        # Use our GNewsClient to fetch article content
        result = gnews_client.fetch_article_content(url)
        
        # Add a fallback content if extraction failed but we didn't get an exception
        if not result.get('content') or len(result.get('content', '').strip()) < 100:
            app.logger.warning(f"Content extraction returned minimal/no content for {url}")
            result['extraction_error'] = "Could not extract sufficient content from this article"
            result['content'] = result.get('content', '') or "This article's content couldn't be extracted automatically. Please try visiting the original article."
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching article content: {str(e)}")
        return jsonify({
            "error": str(e), 
            "content": "Failed to extract article content. Some websites prevent automatic content extraction.",
            "url": url
        }), 200  # Return 200 to handle the error on the client side

@app.route('/api/newsletter-subscribe', methods=['POST'])
def newsletter_subscribe():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    categories = data.get('categories', [])

    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email address.'}), 400

    try:
        db.collection('newsletter_subscribers').add({
            'email': email,
            'categories': categories,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return jsonify({'message': 'Subscription successful!'})
    except Exception as e:
        print(f'Error saving newsletter subscription: {e}')
        return jsonify({'error': 'Failed to save subscription.'}), 500


@app.route('/api/news/voice-optimize', methods=['POST'])
def optimize_article_for_voice():
    data = request.json

    if not data or 'description' not in data:
        return jsonify({"error": "No description provided"}), 400

    try:
        # Simply return the description as-is, no processing needed
        description = data.get('description', '').strip()
        
        if not description:
            return jsonify({"error": "Empty description provided"}), 400
        
        # Optional: Clean up any HTML tags if present
        import re
        clean_description = re.sub(r'<[^>]*?>', '', description)
        clean_description = re.sub(r'\s+', ' ', clean_description).strip()
        
        return jsonify({
            "optimized_content": clean_description
        })
    except Exception as e:
        app.logger.error(f"Error processing description: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/stream-temp-audio/<path:path>')
def stream_temp_audio(path):
    """Stream temporary audio files with proper error handling"""
    audio_path = os.path.join(app.config['OUTPUT_FOLDER'], path)
    
    # Check if file exists
    if not os.path.exists(audio_path):
        app.logger.error(f"Audio file not found: {audio_path}")
        return jsonify({"error": "Audio file not found"}), 404
    
    # Check file size (optional - helps identify empty files)
    try:
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            app.logger.error(f"Audio file is empty: {audio_path}")
            return jsonify({"error": "Audio file is empty"}), 404
    except OSError as e:
        app.logger.error(f"Error checking file size: {e}")
        return jsonify({"error": "Error accessing audio file"}), 500
    
    try:
        return send_file(audio_path, mimetype="audio/mpeg")
    except Exception as e:
        app.logger.error(f"Error serving audio file {audio_path}: {e}")
        return jsonify({"error": "Error serving audio file"}), 500


@app.route('/api/news/summary-audio', methods=['POST'])
def summary_audio():
    data = request.json
    # Change from 'content' to 'description' 
    text = data.get("description", "") or data.get("content", "")  # fallback for backward compatibility
    voice_id = data.get("voice_id", "en-CA-LiamNeural")
    speed = float(data.get("speed", 1.0))
    depth = int(data.get("depth", 1))

    if not text.strip():
        return jsonify({"error": "No description provided"}), 400

    try:
        # Optional: Quick cleanup
        import re
        text = re.sub(r'<[^>]*?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Write text to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp:
            temp.write(text)
            script_path = temp.name

        # Output file path
        output_filename = f"{int(time.time())}_{voice_id}.mp3"
        output_audio = os.path.join("static/audio", output_filename)

        # Generate audio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_simple_tts(script_path, output_audio, voice_id, speed, depth))

        return jsonify({"audio_url": f"/static/audio/{output_filename}"})

    except Exception as e:
        app.logger.error(f"TTS error: {e}")
        return jsonify({"error": str(e)}), 500

# Optional: Add a cleanup function to remove old temp filesssssssssssssssssssssss
def cleanup_old_files():
    """Clean up old temporary files (older than 1 hour)"""
    import time
    current_time = time.time()
    cutoff_time = current_time - 3600  # 1 hour ago
    
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        try:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        app.logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            app.logger.error(f"Error during cleanup: {e}")


@app.route('/api/news/translate', methods=['POST'])
def translate_text():
    """API endpoint to translate text using Gemini."""
    data = request.json
    text_to_translate = data.get('text')
    target_language_code = data.get('target_language') # e.g., 'ar', 'fr', 'es'

    if not text_to_translate or not target_language_code:
        return jsonify({"error": "Missing 'text' or 'target_language' in request"}), 400

    try:
        # Use Gemini for translation
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Craft a prompt for translation
        prompt = f"Translate the following English text to {target_language_code} without adding any extra information or conversational filler. Only provide the translated text:\n\n{text_to_translate}"
        
        # For simplicity, let's assume direct translation.
        # For more complex scenarios, you might need to handle context better.
        response = model.generate_content(prompt)
        
        # Extract the translated text. Handle potential errors or empty responses from Gemini.
        translated_text = response.text.strip()
        
        # Simple check for cases where Gemini might return something unexpected
        if not translated_text:
            raise ValueError("Gemini returned empty or unparseable translation.")

        return jsonify({"translated_text": translated_text})

    except Exception as e:
        app.logger.error(f"Error translating text with Gemini: {e}")
        return jsonify({"error": f"Failed to translate text: {str(e)}"}), 500
    
@app.route('/api/news/test-keys')
def test_gnews_keys():
    current_key_index = gnews_client.api_index + 1  # Human-readable (1-5)
    total_keys = len(gnews_client.api_keys)
    
    return jsonify({
        "current_api_key_index": current_key_index,
        "total_api_keys": total_keys,
        "status": "OK"
    })
# Async TTS endpoint
@app.route('/api/news/summary-audio-async', methods=['POST'])
def summary_audio_async():
    data = request.json
    text = data.get("description", "") or data.get("content", "")
    voice_id = data.get("voice_id", "en-CA-LiamNeural")
    speed = float(data.get("speed", 1.0))
    depth = int(data.get("depth", 1))

    if not text.strip():
        return jsonify({"error": "No description provided"}), 400

    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Start background task
    message = generate_tts_task.send(text, voice_id, speed, depth, task_id)
    
    return jsonify({
        "task_id": task_id,
        "message_id": message.message_id,
        "status": "processing",
        "message": "Audio generation started"
    })
@app.route('/api/news-cached')
def get_news_cached():
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'en')
    
    cache_key = f"news:{category}:{language}"
    cached_news = redis_client.get(cache_key)
    
    if cached_news:
        return jsonify(json.loads(cached_news))
    
    # If not cached, start background caching task and return fresh data
    try:
        results = gnews_client.get_top_headlines(category=category, language=language)
        # Start background caching
        cache_news_task.send(category, language)
        return jsonify(results)
    except Exception:
        return jsonify({"error": "Failed to fetch news", "articles": []}), 500
# Task status endpoint
@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    try:
        # Check if result is cached
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
        
        # If not cached, task might still be processing
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


# Call cleanup periodically (you can set this up with a scheduler)
# cleanup_old_files()
if __name__ == '__main__':
    app.run(debug=True)