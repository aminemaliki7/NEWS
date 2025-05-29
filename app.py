import os
import asyncio
import tempfile
import time
import json
from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify, session
from werkzeug.utils import secure_filename
import threading
from datetime import datetime
from flask import send_file
from youtube_news_generator import generate_youtube_news_script

import google.generativeai as genai
from flask import request, jsonify
from dotenv import load_dotenv

# Import from our modules
from tts import generate_simple_tts
from gnews_client import GNewsClient

# Import the downloader modules at the top of your app.py file
import uuid

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "simple_tts_generator"  # for session management


gnews_client = GNewsClient() 

load_dotenv()

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
    # Check if there's a prefill parameter
    prefill = request.args.get('prefill', '')
    return render_template('index.html', voices=AVAILABLE_VOICES, languages=AVAILABLE_LANGUAGES, prefill=prefill)

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

@app.route('/ssml')
def ssml_page():
    return render_template('ssml.html', voices=AVAILABLE_VOICES)

@app.route('/upload-ssml', methods=['POST'])
def upload_ssml():
    # Get form data
    ssml_content = request.form.get('ssml-content', '').strip()
    voice_id = request.form.get('voice', 'en-US-JennyNeural')
    
    if not ssml_content:
        return render_template('error.html', message="No SSML provided. Please enter SSML markup to convert to speech.")
    
    # Make sure the SSML is properly formatted
    if not ssml_content.startswith('<speak') or not ssml_content.endswith('</speak>'):
        ssml_content = f'<speak>{ssml_content}</speak>'
    
    # Generate a unique job ID
    job_id = generate_unique_id()
    
    # Create temp directories if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Save the SSML to a temporary file
    script_filename = f"ssml_input_{job_id}.xml"
    script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(ssml_content)
    
    # Output file setup
    output_filename = f"tts_{job_id}.mp3"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    # Initialize job status
    jobs[job_id] = {
        'status': 'pending',
        'script_file': script_path,
        'output_file': output_path,
        'start_time': time.time(),
        'input_type': 'ssml',
        'is_ssml': True,
        'voice_id': voice_id
    }
    
    # Start the processing task in a background thread
    process_task = generate_simple_tts(
        script_path, output_path, voice_id, 1.0, 1, True
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

@app.route('/shorts-generator')
def shorts_generator():
    """Route for the AI shorts script generator page"""
    return render_template('shorts_generator.html', voices=AVAILABLE_VOICES, languages=AVAILABLE_LANGUAGES)

@app.route('/generate-shorts-script', methods=['POST'])
def generate_shorts_script():
    # Get data from request
    topic = request.form.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Please provide a topic'}), 400
    
    # Configure prompt for Gemini
    prompt = f"""
Write a short voiceover script for a YouTube Short (30–60 seconds) that feels deep, timeless, and quietly powerful — like a secret worth remembering. The style should feel calm and wise, similar to Robert Greene, but written in simple English that anyone at a B2 level can understand.

TOPIC: {topic}

Guidelines:

    Script must be between 60–75 words (about 30–60 seconds aloud)
    
    adapt the tone to be calm, wise, and reflective — like a quiet truth being shared

    use a simple, conversational style that feels like a friend sharing a secret

    adapte rick rubin's style: "The best way to get what you want is to help others get what they want."
    Use a calm, wise tone that feels timeless and deep but is easy to understand
    Use simple, relatable language that anyone can grasp

    Use very simple

    Start with a hook that feels mysterious, wise, or quietly intense — something that stops the scroll

    Speak like a calm, trusted voice — slow, thoughtful, like someone sharing a quiet truth

    Avoid clichés, hype, or big motivational phrases

    Use contrast, irony, or surprising insight — reveal something hidden in plain sight

    Keep flow natural and smooth — short sentences, no complex grammar

    End with a soft, reflective thought or a warm call to action that invites the viewer to think or feel something

    NO bullet points, formatting, brackets, or special characters — just clean voiceover text.no much pauses in the text

    The output must only be the spoken script, ready for an AI or human voiceover
    

It should feel cinematic, reflective, and easy to understand — like wisdom told simply.


"""
    
    try:
        # Configure the Gemini API with your key
        setup_gemini_api(app.config['GEMINI_API_KEY'])
           
        # Generate content with Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
       
        # Extract the generated text
        script_text = response.text
       
        # Return the generated script
        return jsonify({
            'success': True,
            'script': script_text
        })
    
    except Exception as e:
        print(f"Error generating shorts script: {e}")
        return jsonify({'error': 'Failed to generate script. Please try again later.'}), 500

@app.route('/generate-script', methods=['POST'])
def generate_script():
    # Get data from request
    title = request.form.get('title', '').strip()
    idea1 = request.form.get('idea1', '').strip()
    idea2 = request.form.get('idea2', '').strip()
    idea3 = request.form.get('idea3', '').strip()
    
    if not title:
        return jsonify({'error': 'Please provide a video title'}), 400
    
    # Configure prompt for Gemini
    prompt = f"""
Create a conversational, engaging script for a short educational video that:

1) Teaches a practical concept, hack, or mental model in a direct, no-fluff style
2) Uses simple language that flows naturally when spoken aloud
3) Follows a clear structure: hook → explanation → examples → application → call-to-action

TITLE: {title}

Script Requirements:
- Start with a striking hook that challenges assumptions (e.g., "You don't need to be creative to come up with creative ideas...")
- Speak directly to the viewer using "you" statements throughout
- Explain concepts using everyday language as if talking to a friend
- Include specific, relatable examples that prove your point (like Jobs/iPhone, Shakespeare/stories)
- Break down the concept into a simple process anyone can follow
- Add unexpected connections or surprising insights that create "aha" moments
- End with practical application advice that viewers can implement immediately

Style Guide:
- Write in short, punchy sentences that maintain momentum
- Create a natural speaking rhythm with varied sentence length
- Avoid all formatting (no lists, bullet points, headings, or special characters)
- Use contractions and casual phrasing for a conversational feel
- Include subtle transitions between ideas that flow logically
- Incorporate rhetorical questions that make viewers think
- Blend authoritative knowledge with friendly, accessible tone
- Include specific action steps within the natural flow of speech
- Keep the entire script between 300-400 words for a 2-3 minute video

CONTENT STRUCTURE:
1. Hook challenging a common belief about {idea1}
2. Simple explanation of the concept/process behind {idea2}
3. Real-world examples showing the concept in action
4. Step-by-step method viewers can apply to {idea3}
5. Quick demonstration of the method with a specific example
6. Final takeaway reinforcing how accessible/powerful this approach is

Return ONLY the clean, ready-to-record script with no additional text or formatting.
"""

    
    try:
        # Configure the Gemini API with your key
        # No need to check if API key is set - just configure it each time
        setup_gemini_api(app.config['GEMINI_API_KEY'])
           
        # Generate content with Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
       
        # Extract the generated text
        script_text = response.text
       
        # Return the generated script
        return jsonify({
            'success': True,
            'script': script_text
        })
    
    except Exception as e:
        print(f"Error generating script: {e}")
        return jsonify({'error': 'Failed to generate script. Please try again later.'}), 500

@app.route('/script-generator')
def script_generator():
    """Route for the AI script generator page"""
    return render_template('script_generator.html', voices=AVAILABLE_VOICES, languages=AVAILABLE_LANGUAGES)






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


@app.route('/media-downloader')
def media_downloader():
    """Route for the media downloader page"""
    return render_template('media_downloader.html')


@app.route('/marketing-generator')
def marketing_generator():
    """Route for the marketing script generator page"""
    return render_template('marketing_generator.html', voices=AVAILABLE_VOICES, languages=AVAILABLE_LANGUAGES)

@app.route('/generate-marketing-script', methods=['POST'])
def generate_marketing_script():
    # Get data from request
    content_type = request.form.get('contentType', '').strip()
    product_name = request.form.get('productName', '').strip()
    target_audience = request.form.get('targetAudience', '').strip()
    main_benefit = request.form.get('mainBenefit', '').strip()
    key_features = request.form.get('keyFeatures', '').strip()
    call_to_action = request.form.get('callToAction', '').strip()
    script_length = request.form.get('scriptLength', 'medium').strip()
    tone = request.form.get('tone', 'professional').strip()
    additional_info = request.form.get('additionalInfo', '').strip()
    
    # Validate required fields
    if not product_name or not target_audience or not main_benefit:
        return jsonify({'error': 'Please provide product name, target audience, and main benefit'}), 400
    
    # Map script length to word count and duration
    length_mapping = {
        'short': "80-120 words (30-60 seconds)",
        'medium': "150-250 words (1-2 minutes)",
        'long': "300-450 words (2-3 minutes)"
    }
    
    # Map tone to descriptive text
    tone_descriptions = {
        'professional': "professional, authoritative, and trustworthy",
        'conversational': "friendly, casual, and conversational",
        'enthusiastic': "energetic, passionate, and excited",
        'empathetic': "understanding, compassionate, and empathetic",
        'humorous': "light, engaging, and subtly humorous",
        'urgent': "urgent, compelling, and action-oriented"
    }
    
    # Configure prompt for Gemini based on script type
    prompt_prefix = ""
    
    if content_type == "product_explainer":
        prompt_prefix = "Create a persuasive product explainer script that demonstrates features and benefits"
    elif content_type == "lead_generation":
        prompt_prefix = "Create a lead generation script focused on collecting contact information in exchange for value"
    elif content_type == "sales_pitch":
        prompt_prefix = "Create a direct sales pitch script designed to convert viewers into customers"
    elif content_type == "testimonial_style":
        prompt_prefix = "Create a testimonial-style script that tells a success story about using this product"
    elif content_type == "educational":
        prompt_prefix = "Create a compelling science-backed explainer script that simplifies complex concepts, hooks viewers with relatable scenarios, and ends with a clear takeaway"
    
    # Build the complete prompt
    prompt = f"""
{prompt_prefix} for a {tone_descriptions.get(tone, "professional")} marketing video.

PRODUCT: {product_name}
TARGET AUDIENCE: {target_audience}
PRIMARY BENEFIT: {main_benefit}
KEY FEATURES: {key_features}
CALL TO ACTION: {call_to_action}
ADDITIONAL CONTEXT: {additional_info}

Guidelines:
- Script should be {length_mapping.get(script_length, "150-250 words (1-2 minutes)")} when spoken aloud
- Use a {tone_descriptions.get(tone, "professional")} tone throughout
- Start with a strong hook that grabs attention
- Focus on benefits to the audience, not just features
- Address pain points and how the product solves them
- Include the call to action clearly and persuasively
- Use conversational language (avoid jargon unless necessary for the audience)
- Make the value proposition crystal clear
- Create emotional connection with the audience when appropriate
- Use social proof elements if relevant
- Write in a natural speaking voice with smooth transitions
- IMPORTANT: Output ONLY the script text, nothing else
- NO bullet points, NO formatting, NO notes - just clean voiceover text

The script should feel persuasive and compelling, with a clear focus on how {product_name} helps {target_audience} achieve {main_benefit}.
"""
    
    try:
        # Configure the Gemini API with your key
        setup_gemini_api(app.config['GEMINI_API_KEY'])
           
        # Generate content with Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
       
        # Extract the generated text
        script_text = response.text
       
        # Return the generated script
        return jsonify({
            'success': True,
            'script': script_text
        })
    
    except Exception as e:
        print(f"Error generating marketing script: {e}")
        return jsonify({'error': 'Failed to generate script. Please try again later.'}), 500
    

@app.route('/news')
def news_page():
    """Render the news reader page"""
    # Get the same voice and language data you use for your main page
    languages = AVAILABLE_LANGUAGES  # Use the existing AVAILABLE_LANGUAGES variable
    voices = AVAILABLE_VOICES  # Use the existing AVAILABLE_VOICES variable
    
    return render_template('news.html', languages=languages, voices=voices)

@app.route('/api/news')
def get_news():
    """API endpoint to fetch news from GNews"""
    # Get query parameters
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'en')
    query = request.args.get('query', '')
    
    try:
        # Use our GNewsClient to fetch news
        if query:
            # If there's a search query, use search function
            results = gnews_client.search_news(query=query, language=language)
        else:
            # Otherwise fetch top headlines
            results = gnews_client.get_top_headlines(category=category, language=language)
        
        return jsonify(results)
    
    except Exception as e:
        app.logger.error(f"Error fetching news: {str(e)}")
        return jsonify({"error": str(e), "articles": []}), 500

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



@app.route('/api/news/summary', methods=['POST'])
def generate_article_summary():
    """Generate a summary of a news article"""
    # Get request data
    data = request.json
    
    if not data or 'content' not in data:
        return jsonify({"error": "No content provided"}), 400
    
    try:
        # Generate summary
        content = data.get('content', '')
        title = data.get('title', '')
        
        # Placeholder function for generating a news summary
        def generate_news_summary(content, max_length=2000):
            return content[:max_length]  # Truncate content to max_length as a simple summary

        summary = generate_news_summary(content, max_length=2000)
        
        return jsonify({
            "summary": summary,
            "original_length": len(content),
            "summary_length": len(summary)
        })
        
    except Exception as e:
        app.logger.error(f"Error generating summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/voice-optimize', methods=['POST'])
def optimize_article_for_voice():
    """Optimize article content for voice narration"""
    # Get request data
    data = request.json
    
    if not data or 'content' not in data:
        return jsonify({"error": "No content provided"}), 400
    
    try:
        # Generate voice-optimized content
        content = data.get('content', '')
        title = data.get('title', '')
        
        # Define a placeholder function for voice optimization
        def generate_voice_optimized_text(content, word_limit=400):
            # Truncate content to the word limit as a simple optimization
            words = content.split()
            return ' '.join(words[:word_limit])
        
        optimized_content = generate_voice_optimized_text(content, word_limit=400)
        
        return jsonify({
            "optimized_content": optimized_content,
            "original_length": len(content),
            "optimized_length": len(optimized_content)
        })
        
    except Exception as e:
        app.logger.error(f"Error optimizing content: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/news/youtube-script', methods=['POST'])
def generate_news_youtube_script_route():
    """Generate a YouTube-style news script based on article content"""
    # Get request data
    data = request.json
    
    if not data or 'content' not in data:
        return jsonify({"error": "No content provided"}), 400
    
    try:
        # Extract parameters
        content = data.get('content', '')
        title = data.get('title', '')
        source = data.get('source', '')
        word_limit = data.get('word_limit', 300)
        
        # Validate word limit
        try:
            word_limit = int(word_limit)
            if word_limit < 100:
                word_limit = 100
            elif word_limit > 500:
                word_limit = 500
        except (ValueError, TypeError):
            word_limit = 300
        
        # Generate the YouTube news script
        result = generate_youtube_news_script(content, title, source, word_limit)
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error generating YouTube script: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
    except Exception as e:
        app.logger.error(f"Error generating YouTube script: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        app.logger.error(f"Error optimizing content: {str(e)}")
        return jsonify({"error": str(e)}), 500


    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
if __name__ == '__main__':
    app.run(debug=True)