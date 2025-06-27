import re
import random
import logging
import asyncio
import time
import google.generativeai as genai
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None

# Gemini model instance (will be initialized by app)
gemini_model = None

def initialize_gemini(api_key: str):
    """Initialize Gemini API with the provided key"""
    global gemini_model
    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        return False

async def generate_voice_optimized_text(text, word_limit=180, include_intro=True, include_outro=False, use_gemini=True):
    """
    Generate SHORT but VALUABLE audio content using Gemini AI.
    Focus: MAXIMUM NEWS VALUE in 40-60 seconds
    No outro by default - pure content value
    """
    
    logger.info(f"Input text length: {len(text)} characters, using Gemini: {use_gemini}")

    # 🚀 CHECK CACHE FIRST
    cache_key = f"voice_opt_v2:{hash(text)}:{word_limit}:{include_intro}:{include_outro}:{use_gemini}"
    if REDIS_AVAILABLE:
        try:
            cached_result = redis_client.redis_client.get(cache_key)
            if cached_result:
                logger.info("🎯 Cache HIT: Returning cached optimized content")
                return cached_result.decode('utf-8')
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

    logger.info("❌ Cache MISS: Creating valuable short content...")

    # Try Gemini first if available and enabled
    if use_gemini and gemini_model:
        try:
            optimized_content = await extract_content_with_gemini(text, word_limit, include_intro)
            if optimized_content and is_meaningful_content_enhanced(optimized_content):
                # Cache the result
                if REDIS_AVAILABLE:
                    try:
                        redis_client.redis_client.setex(cache_key, 3600, optimized_content)  # Cache for 1 hour
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")
                
                word_count = len(optimized_content.split())
                logger.info(f"✅ Gemini success: {word_count} words, ~{word_count * 0.6:.1f}s audio")
                return optimized_content
            else:
                logger.warning("⚠️ Gemini returned low-quality content, falling back to regex")
        except Exception as e:
            logger.error(f"❌ Gemini extraction failed: {e}, falling back to regex")

    # Fallback to original regex-based approach
    logger.info("🔄 Using regex-based extraction as fallback")
    
    # Step 1: Clean and prepare text
    clean_text = deep_clean_text(text)
    
    if len(clean_text.split()) < 10:
        return create_fallback_content(include_intro=include_intro)
    
    # Step 2: Extract using enhanced regex methods
    core_story = extract_core_story_enhanced(clean_text)
    key_details = extract_key_details_enhanced(clean_text, core_story)
    impact = extract_impact_enhanced(clean_text)
    
    # Step 3: Build complete story
    final_story = build_complete_story_enhanced(core_story, key_details, impact, word_limit)
    
    # Step 4: Add minimal intro only if requested
    if include_intro:
        result = add_minimal_intro(final_story, clean_text)
    else:
        result = final_story
    
    # Step 5: Clean for EdgeTTS
    result = clean_for_edgetts(result)

    # Validate and cache
    if is_meaningful_content_enhanced(result):
        if REDIS_AVAILABLE:
            try:
                redis_client.redis_client.setex(cache_key, 3600, result)
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        word_count = len(result.split())
        logger.info(f"📝 Regex result: {word_count} words, ~{word_count * 0.6:.1f}s audio")
        return result
    else:
        return create_smart_fallback_enhanced(clean_text, include_intro)

async def extract_content_with_gemini(text: str, word_limit: int = 180, include_intro: bool = True) -> Optional[str]:
    """Use Gemini to extract the most valuable content for audio"""
    
    if not gemini_model:
        raise Exception("Gemini model not initialized")
    
    # Calculate target words (reserve space for intro if needed)
    target_words = word_limit - (5 if include_intro else 0)
    
    prompt = f"""Extract the most newsworthy and valuable content from this article for audio narration.

REQUIREMENTS:
- Maximum {target_words} words (STRICT LIMIT)
- Focus on WHO did WHAT, financial numbers, key decisions, breaking developments
- Include specific names, companies, numbers, percentages when available
- Make it engaging and clear for audio listeners
- Remove all fluff, filler, and website clutter
- Prioritize recent/breaking developments over background information
- Use active voice and clear, concise language
- DO NOT add intro phrases like "Here's the news" or outro phrases
- Return ONLY the extracted content, nothing else
- Focus on the most important facts that would make someone stop and listen

PRIORITIZE IN THIS ORDER:
1. Breaking news or urgent developments
2. Financial data (revenue, profits, stock movements, percentages)
3. Major decisions or announcements by key figures
4. Legal rulings or government actions
5. Numbers that show impact (jobs, people affected, amounts)

Article text:
{text[:4000]}

Extracted content (max {target_words} words):"""

    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        
        if not response or not response.text:
            raise Exception("Gemini returned empty response")
        
        extracted = response.text.strip()
        
        # Clean up any unwanted additions
        extracted = re.sub(r'^(here\'s|this is|the news|breaking|update):\s*', '', extracted, flags=re.IGNORECASE)
        extracted = re.sub(r'\s*(that\'s all|more to come|stay tuned|end of update)\.?\s*$', '', extracted, flags=re.IGNORECASE)
        
        # Validate word count
        word_count = len(extracted.split())
        if word_count > target_words + 5:  # Allow small buffer
            # Truncate to word limit while preserving sentence structure
            words = extracted.split()[:target_words]
            extracted = ' '.join(words)
            
            # Try to end at a sentence boundary
            last_sentence_end = max(
                extracted.rfind('.'),
                extracted.rfind('!'),
                extracted.rfind('?')
            )
            
            if last_sentence_end > len(extracted) * 0.7:  # If we can trim to a sentence end without losing too much
                extracted = extracted[:last_sentence_end + 1]
            elif not extracted.endswith(('.', '!', '?')):
                extracted += '.'
        
        # Add intro if requested
        if include_intro:
            extracted = add_gemini_intro(extracted, text)
        
        # Final cleanup
        extracted = clean_for_edgetts(extracted)
        
        logger.info(f"🤖 Gemini extracted {len(extracted.split())} words")
        return extracted
        
    except Exception as e:
        logger.error(f"Gemini extraction error: {e}")
        raise

def add_gemini_intro(content: str, original_text: str) -> str:
    """Add smart intro based on content analysis"""
    
    content_lower = content.lower()
    original_lower = original_text.lower()
    
    # Analyze content for appropriate intro
    if any(word in content_lower for word in ['died', 'killed', 'arrested', 'convicted', 'sentenced']):
        return f"Breaking: {content}"
    elif any(word in original_lower for word in ['just', 'announced', 'breaking', 'urgent']):
        return f"News flash: {content}"
    elif re.search(r'\$[\d,]+(?:\s*(?:million|billion))?', content):
        return f"Market update: {content}"
    elif any(word in content_lower for word in ['court', 'ruled', 'decision', 'verdict']):
        return f"Legal news: {content}"
    elif any(word in content_lower for word in ['election', 'vote', 'president', 'congress']):
        return f"Politics: {content}"
    elif any(word in content_lower for word in ['stock', 'shares', 'trading', 'nasdaq', 'dow']):
        return f"Market alert: {content}"
    else:
        return f"News: {content}"

def deep_clean_text(text):
    """Deep clean text to extract meaningful content"""
    
    # Remove HTML
    text = re.sub(r'<[^>]*?>', '', text)
    
    # Remove common news website clutter
    clutter_patterns = [
        r'continue reading[^.]*\.?',
        r'read more[^.]*\.?',
        r'click here[^.]*\.?',
        r'subscribe[^.]*\.?',
        r'newsletter[^.]*\.?',
        r'follow us[^.]*\.?',
        r'share this[^.]*\.?',
        r'related articles?[^.]*\.?',
        r'advertisement[^.]*\.?',
        r'sponsored[^.]*\.?',
        r'©[^.]*\.?',
        r'all rights reserved[^.]*\.?',
        r'terms of service[^.]*\.?',
        r'privacy policy[^.]*\.?',
        r'cookie policy[^.]*\.?'
    ]
    
    for pattern in clutter_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove metadata patterns
    text = re.sub(r'published:?\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'updated:?\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'by:?\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
    
    # Clean numbered lists artifacts
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Clean spacing
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_core_story_enhanced(text):
    """Enhanced core story extraction with better value detection"""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if not sentences:
        return ""
    
    # Enhanced story patterns with higher value detection
    high_value_patterns = [
        # Financial/Economic impact (highest priority)
        r'(stock|shares|market|price)\s+(rose|fell|gained|lost|jumped|dropped|surged|plunged)\s+(\d+(?:\.\d+)?%?)',
        r'(revenue|profit|loss|earnings)\s+(increased|decreased|jumped|fell)\s+(\d+(?:\.\d+)?%?)',
        r'(\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)',
        
        # Legal/Political decisions (high priority)
        r'(court|judge|jury)\s+(ruled|decided|sentenced|convicted|acquitted|ordered)',
        r'(president|congress|senate|house)\s+(passed|signed|approved|rejected|voted)',
        r'(law|bill|legislation|regulation)\s+(passed|signed|enacted|blocked)',
        
        # Corporate actions (high priority)
        r'(company|corporation)\s+(announced|reported|posted|acquired|merged|filed)',
        r'(CEO|executive|founder)\s+(resigned|fired|appointed|hired|stepped down)',
        
        # Breaking events (highest priority)
        r'(died|killed|injured|arrested|charged|indicted)',
        r'(launched|released|unveiled|introduced|debuted)',
        r'(banned|restricted|suspended|halted|stopped)'
    ]
    
    best_sentence = ""
    max_score = 0
    
    for sentence in sentences[:10]:  # Check first 10 sentences
        if len(sentence.split()) < 8 or len(sentence.split()) > 35:
            continue
            
        score = 0
        sentence_lower = sentence.lower()
        
        # Check for high-value patterns
        for pattern in high_value_patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            if matches:
                score += 25  # Higher score for valuable patterns
        
        # Look for financial numbers (high value)
        financial_numbers = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?', sentence)
        score += len(financial_numbers) * 8
        
        # Look for percentages (often valuable)
        percentages = re.findall(r'\d+(?:\.\d+)?%', sentence)
        score += len(percentages) * 6
        
        # Look for proper nouns (companies, people, places)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\b', sentence)
        score += len(proper_nouns) * 3
        
        # Time sensitivity indicators
        time_indicators = ['today', 'yesterday', 'this week', 'announced', 'breaking', 'just']
        for indicator in time_indicators:
            if indicator in sentence_lower:
                score += 4
        
        # Position bonus (earlier = likely more important)
        position_bonus = max(0, 8 - sentences.index(sentence))
        score += position_bonus
        
        if score > max_score:
            max_score = score
            best_sentence = sentence.strip()
    
    return best_sentence

def extract_key_details_enhanced(text, core_story):
    """Enhanced detail extraction focusing on quantifiable value"""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # High-value detail patterns
    high_value_details = [
        r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion))?',  # Money amounts
        r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:percent|%)',  # Percentages
        r'\b\d+(?:,\d{3})*\s*(?:people|jobs|deaths|injuries|arrests|cases)',  # Impact numbers
        r'\b(?:q[1-4]|quarter)\s+\d{4}',  # Quarterly data
        r'\b\d{4}\s*(?:fiscal|calendar)?\s*year',  # Annual data
        r'\b(?:up|down|increased|decreased)\s+\d+(?:\.\d+)?%',  # Change percentages
    ]
    
    best_detail = ""
    max_score = 0
    
    for sentence in sentences[:15]:
        if sentence == core_story or len(sentence.split()) < 6:
            continue
            
        score = 0
        
        # Check for high-value details
        for pattern in high_value_details:
            if re.search(pattern, sentence, re.IGNORECASE):
                score += 10
        
        # Prefer shorter, more focused details
        word_count = len(sentence.split())
        if 8 <= word_count <= 20:
            score += 5
        elif word_count > 25:
            score -= 3
        
        if score > max_score:
            max_score = score
            best_detail = sentence.strip()
    
    return best_detail

def extract_impact_enhanced(text):
    """Enhanced impact extraction focusing on consequences and significance"""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    impact_patterns = [
        r'this (?:means|could|will|would|might|represents)',
        r'the (?:impact|effect|consequence|result|outcome)',
        r'(?:analysts|experts|officials)\s+(?:say|warn|predict|expect)',
        r'could (?:lead to|result in|cause|trigger)',
        r'first time (?:in|since)',
        r'(?:largest|biggest|smallest|highest|lowest|worst|best)\s+(?:in|since)',
        r'(?:significant|major|substantial|dramatic|unprecedented)'
    ]
    
    for sentence in sentences:
        if len(sentence.split()) < 10 or len(sentence.split()) > 25:
            continue
            
        sentence_lower = sentence.lower()
        for pattern in impact_patterns:
            if re.search(pattern, sentence_lower):
                return sentence.strip()
    
    return ""

def build_complete_story_enhanced(core_story, key_details, impact, word_limit):
    """Build complete story with enhanced value prioritization"""
    
    if not core_story:
        return "Breaking news update available."
    
    # Allocate more words since no outro
    target_words = word_limit - 5  # Only reserve 5 words for minimal intro
    
    # Start with core story
    story_parts = [core_story]
    word_count = len(core_story.split())
    
    # Prioritize key details if they add quantifiable value
    if key_details and word_count < target_words * 0.6:
        detail_words = len(key_details.split())
        if word_count + detail_words <= target_words:
            story_parts.append(key_details)
            word_count += detail_words
    
    # Add impact only if there's room and it adds real value
    if impact and word_count < target_words * 0.4:
        impact_words = len(impact.split())
        if word_count + impact_words <= target_words:
            story_parts.append(impact)
    
    # Join with minimal connectors
    if len(story_parts) == 1:
        story = story_parts[0]
    else:
        # Use concise connectors
        story = story_parts[0]
        for part in story_parts[1:]:
            story += f" {part}"
    
    # Clean and optimize
    story = re.sub(r'\s+', ' ', story).strip()
    story = make_voice_friendly(story)
    
    return story

def add_minimal_intro(story, original_text):
    """Add minimal, value-focused intro only"""
    
    content_lower = original_text.lower()
    
    # Only add intro if it adds genuine value
    if any(word in content_lower for word in ['breaking', 'urgent', 'just announced']):
        return f"Breaking: {story}"
    elif re.search(r'\$[\d,]+(?:\s*(?:million|billion))?', story):
        return f"Market alert: {story}"
    elif any(word in content_lower for word in ['died', 'killed', 'arrested', 'convicted']):
        return f"News: {story}"
    else:
        # No intro - pure content
        return story

def is_meaningful_content_enhanced(text):
    """Enhanced content value validation"""
    
    # Remove any remaining intro words
    clean_text = re.sub(r'^(?:Breaking:|Market alert:|News:|Market update:|Legal news:|Politics:|News flash:)\s*', '', text, flags=re.IGNORECASE)
    clean_text = clean_text.strip()
    
    # Must have substantial content
    if len(clean_text.split()) < 8:
        return False
    
    # Check for high-value indicators
    value_indicators = [
        r'\$[\d,]+',  # Money
        r'\d+(?:\.\d+)?%',  # Percentages
        r'\b(?:announced|reported|confirmed|revealed|signed|approved|launched)\b',  # Action verbs
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\b',  # Proper nouns
        r'\b\d+(?:,\d{3})*\s*(?:million|billion|people|jobs)\b'  # Significant numbers
    ]
    
    value_count = 0
    for pattern in value_indicators:
        if re.search(pattern, clean_text, re.IGNORECASE):
            value_count += 1
    
    return value_count >= 2  # Must have at least 2 value indicators

def create_fallback_content(include_intro=True):
    """Create fallback when content extraction fails"""
    base_content = "Developing story with updates expected."
    
    if include_intro:
        return f"News: {base_content}"
    return base_content

def create_smart_fallback_enhanced(text, include_intro=True):
    """Create better fallback using available content"""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Look for any sentence with value indicators
    for sentence in sentences[:5]:
        if (8 <= len(sentence.split()) <= 25 and
            (re.search(r'[A-Z][a-z]+', sentence) or 
             re.search(r'\d+', sentence))):
            
            clean_sentence = sentence.strip()
            if include_intro:
                return f"Update: {clean_sentence}"
            return clean_sentence
    
    return create_fallback_content(include_intro)

def make_voice_friendly(text):
    """Make text perfect for voice synthesis"""
    
    # Voice-optimized acronym replacements
    voice_fixes = {
        'FBI': 'F-B-I', 'CIA': 'C-I-A', 'CEO': 'C-E-O', 'AI': 'A-I',
        'US': 'U-S', 'USA': 'U-S-A', 'UK': 'U-K', 'EU': 'E-U',
        'NASA': 'N-A-S-A', 'WHO': 'W-H-O', 'GDP': 'G-D-P',
        'NYC': 'New York City', 'LA': 'Los Angeles', 'IPO': 'I-P-O',
        'CFO': 'C-F-O', 'CTO': 'C-T-O', 'VP': 'Vice President'
    }
    
    for acronym, voice_form in voice_fixes.items():
        text = re.sub(rf'\b{acronym}\b', voice_form, text)
    
    # Optimize numbers for voice
    text = re.sub(r'(\d+)%', r'\1 percent', text)
    text = re.sub(r'\$(\d+(?:,\d{3})*)B\b', r'\1 billion dollars', text)
    text = re.sub(r'\$(\d+(?:,\d{3})*)M\b', r'\1 million dollars', text)
    text = re.sub(r'\$(\d+(?:,\d{3})*)K\b', r'\1 thousand dollars', text)
    
    # Handle large numbers
    text = re.sub(r'\$(\d+(?:,\d{3})*)\b(?!\s*(?:million|billion|thousand))', r'\1 dollars', text)
    
    return text

def clean_for_edgetts(text):
    """Clean text for EdgeTTS compatibility"""
    
    # Remove all emojis and special characters that EdgeTTS can't handle
    text = re.sub(r'[^\w\s.,!?;:\-\'\"()]', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove problematic characters
    problematic_chars = ['*', '#', '@', '%', '^', '&', '+', '=', '|', '\\', '/', '<', '>', '[', ']', '{', '}', '~', '`']
    for char in problematic_chars:
        text = text.replace(char, ' ')
    
    # Clean up spacing again
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Ensure proper punctuation at the end
    if text and not text.rstrip().endswith(('.', '!', '?')):
        text = text.rstrip() + '.'
    
    return text

# Wrapper function for backward compatibility
def generate_voice_optimized_text_sync(text, word_limit=180, include_intro=True, include_outro=False):
    """Synchronous wrapper for the async function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            generate_voice_optimized_text(text, word_limit, include_intro, include_outro)
        )
        return result
    finally:
        loop.close()

# Legacy function for backward compatibility
def generate_voice_optimized_text_legacy(text, word_limit=180, include_intro=True, include_outro=True):
    """Legacy function - now defaults to no outro and uses Gemini"""
    return generate_voice_optimized_text_sync(text, word_limit, include_intro, False)