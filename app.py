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
from tts import generate_simple_tts
from gnews_client import GNewsClient
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from flask import send_file



# Initialize Flask app
app = Flask(__name__)
app.secret_key = "simple_tts_generator"  # for session management

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client() 

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


# REMOVE THESE DUPLICATE LINES:
# cred = credentials.Certificate('serviceAccountKey.json')  # You need to download serviceAccountKey.json from Firebase settings
# firebase_admin.initialize_app(cred)

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

        doc_ref.set({
            'nickname': nickname,
            'comment': comment_text,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Comment posted", "nickname": nickname})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API — Article Comment
@app.route('/api/article-comments', methods=['GET'])
def get_comments():
    article_id = request.args.get('article_id')
    if not article_id:
        return jsonify({"error": "Missing article_id"}), 400

    try:
        comments_ref = db.collection('comments').document(article_id).collection('comments')
        comments_snapshot = comments_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

        comments = []
        for doc in comments_snapshot:
            comment = doc.to_dict()
            comment['id'] = doc.id
            comments.append(comment)

        return jsonify({"comments": comments})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


app.route('/api/news/voice-optimize', methods=['POST'])
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


    

# Call cleanup periodically (you can set this up with a scheduler)
# cleanup_old_files()
if __name__ == '__main__':
    app.run(debug=True)