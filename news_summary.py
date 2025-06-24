import re
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_voice_optimized_text(text, title="", word_limit=180, include_intro=True, include_outro=True):
    """
    Generate professional voice narration for YouTube or Reels news.
    Shortens content to the key points, removes fluff, and formats for natural news voiceover.

    Args:
        text (str): The main content of the article.
        title (str): The title of the article, used for more specific intros.
        word_limit (int): The maximum number of words for the optimized text.
        include_intro (bool): Whether to include a generated intro.
        include_outro (bool): Whether to include a generated outro.
    """

    logger.info(f"Input text length: {len(text)} characters")
    logger.info(f"Input preview: {text[:100]}...")
    logger.info(f"Article title: {title}")

    # Step 1: Clean HTML, noise, and handle punctuation spacing
    original_text = text
    text = re.sub(r'<[^>]*?>', '', text) # Remove HTML tags

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Specific cleanups for voice optimization
    text = re.sub(r'\bIn Brief\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\[\s*\]', '', text).strip()
    text = re.sub(r'\[\s*\.\.\.\s*\]', '', text).strip()
    text = re.sub(r'\b(read|continue|full story|page|story|article|report)\s+(more|here|now|today)\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\s*\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpage\s+\d+\s*$', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s*\(.*?\)\s*', ' ', text) # Remove text in parentheses
    text = re.sub(r'(\w+), (and \w+)', r'\1 \2', text) # "word, and word" -> "word and word" for better flow
    text = re.sub(r'\.{3,}', '.', text) # Collapse multiple dots to a single period

    # --- Punctuation Handling Improvement (Existing) ---
    # 1. Add space after punctuation if not already present
    text = re.sub(r'([.,!?;:])(?=[^\s.,!?;:0-9]|$)', r'\1 ', text)
    # 2. Remove extra spaces around punctuation (e.g., "word , word" -> "word, word")
    text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
    # 3. Ensure no space before comma/period (e.g., "word , " -> "word,")
    text = re.sub(r'\s*([,.;:])', r'\1', text)

    # --- NEW: Remove hash symbols ---
    text = re.sub(r'#', '', text) # Remove hash symbols

    text = re.sub(r'\s+', ' ', text).strip() # Final normalization of whitespace

    logger.info(f"After cleaning and punctuation handling text length: {len(text)} characters")
    logger.info(f"Cleaned preview: {text[:100]}...")

    # Heuristic to check if cleaning was too aggressive
    if len(text) < len(original_text) * 0.3 and len(original_text) > 100: # Only apply if original was substantial
        logger.warning("Cleaning removed too much content, potentially using original text for base.")
        # Re-evaluate, maybe just remove HTML and excess spaces, but keep the core.
        cleaned_original_simple = re.sub(r'<[^>]*?>', '', original_text)
        cleaned_original_simple = re.sub(r'\s+', ' ', cleaned_original_simple).strip()
        
        # Also remove hash symbols from the less aggressive cleaning path
        cleaned_original_simple = re.sub(r'#', '', cleaned_original_simple)

        if len(cleaned_original_simple) > len(text):
            text = cleaned_original_simple
            logger.info("Switched to less aggressive cleaning result.")


    trimmed_text = text

    # Step 2: Adapt Intro and Outro
    serious_keywords = ['died', 'crisis', 'emergency', 'fatal', 'evacuated', 'conflict', 'breaking', 'tragedy', 'attack', 'warning', 'disaster', 'protest', 'fire', 'flood', 'investigation', 'arrest', 'charges']
    
    # Check for serious keywords in both text and title
    is_serious = any(word in text.lower() for word in serious_keywords) or \
                 any(word in title.lower() for word in serious_keywords)

    intros = {
        'serious': [
            "Here is the latest breaking news.",
            "An important update from our newsroom.",
            "Developing story:"
        ],
        'neutral': [
            "Here is today’s top story.",
            "This is the latest update.",
            "Today’s headline news:"
        ]
    }
    
    # Generate a more specific intro if a title is available
    base_intro_phrase = random.choice(intros['serious' if is_serious else 'neutral'])
    
    if title:
        # Simple title adaptation: remove common news prefixes/suffixes
        clean_title = re.sub(r'^(breaking news|update|report on|analysis of|the latest on):?\s*', '', title, flags=re.IGNORECASE).strip()
        clean_title = re.sub(r'\s*-\s*.*?(news|report|update)$', '', clean_title, flags=re.IGNORECASE).strip()
        
        # Capitalize first letter of clean_title for natural flow
        if clean_title:
            clean_title = clean_title[0].upper() + clean_title[1:]

        if is_serious:
            intro = f"Breaking news: {clean_title}." if clean_title else base_intro_phrase
        else:
            intro = f"In today's headlines: {clean_title}." if clean_title else base_intro_phrase
    else:
        intro = base_intro_phrase

    # Specific outro as requested
    outro = "Check the full article for more information."

    # Step 3: Expand acronyms
    acronym_expansions = {
        "NAHB": "the National Association of Home Builders",
        "WHO": "the World Health Organization",
        "UNESCO": "UNESCO, the United Nations Educational, Scientific and Cultural Organization",
        "NASA": "the U.S. space agency NASA",
        "FBI": "the Federal Bureau of Investigation",
        "CEO": "Chief Executive Officer",
        "AI": "Artificial Intelligence",
        "UN": "United Nations",
        "GDP": "Gross Domestic Product",
        "COVID": "COVID-19",
        "NYC": "New York City",
        "US": "United States",
        "UK": "United Kingdom",
        "EU": "European Union"
    }

    for acro, expansion in acronym_expansions.items():
        trimmed_text = re.sub(rf'\b{acro}\b', expansion, trimmed_text)

    # Step 4: Word limit (actual summarization step)
    words = trimmed_text.split()
    if word_limit and len(words) > word_limit:
        logger.info(f"Applying word limit: {word_limit} words (from {len(words)})")
        trimmed_text = ' '.join(words[:word_limit])

        # Try to end at a natural sentence boundary (period, exclamation, question mark)
        # Search backward from the end of the trimmed text for a sentence-ending punctuation
        sentence_end_match = re.search(r'[.!?](?=[^.!?]*$)', trimmed_text)
        if sentence_end_match and sentence_end_match.start() > len(trimmed_text) * 0.7:
             # If a sentence end is found in the latter part, cut there.
            trimmed_text = trimmed_text[:sentence_end_match.end()]
        else:
            # Otherwise, just append a period if not ending with one
            if not trimmed_text.rstrip().endswith(('.', '!', '?')):
                trimmed_text = trimmed_text.rstrip() + '.'


    # Step 5: Final result assembly
    result = trimmed_text
    if include_intro:
        result = f"{intro} {result}"
    if include_outro:
        result = f"{result} {outro}"

    # Ensure final result ends with punctuation, unless it's already a question or exclamation
    if result and not result.rstrip().endswith(('.', '!', '?')):
        result = result.rstrip() + '.'

    # Clean up any double spaces that might occur from intro/outro additions or cleaning
    result = re.sub(r'\s+', ' ', result).strip()

    logger.info(f"Final result length: {len(result)} characters")
    logger.info(f"Final result preview: {result[:50]}...{result[-50:]}")
    
    print("[Voice Optimized Text]", result)
    return result