import re
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_voice_optimized_text(text, word_limit=180, include_intro=True, include_outro=True):
    """
    Generate professional voice narration for YouTube or Reels news.
    Shortens content to the key points, removes fluff, and formats for natural news voiceover.
    """

    logger.info(f"Input text length: {len(text)} characters")
    logger.info(f"Input preview: {text[:100]}...")

    # Step 1: Clean HTML and noise
    original_text = text
    text = re.sub(r'<[^>]*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\bIn Brief\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\[\s*\]', '', text).strip()
    text = re.sub(r'\[\s*\.\.\.\s*\]', '', text).strip()
    text = re.sub(r'\b(read|continue|full story|page|story|article|report)\s+(more|here|now|today)\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\s*\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpage\s+\d+\s*$', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s*\(.*?\)\s*', ' ', text)
    text = re.sub(r'(\w+), (and \w+)', r'\1 \2', text)
    text = re.sub(r'\.{3,}', '.', text)
    text = re.sub(r'\s*([,;:.!?])\s*', r'\1 ', text)
    text = re.sub(r'([.,!?;:])(?=\S)', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    logger.info(f"After cleaning text length: {len(text)} characters")
    logger.info(f"Cleaned preview: {text[:100]}...")

    if len(text) < len(original_text) * 0.3:
        logger.warning("Cleaning removed too much content, using original text")
        text = original_text.strip()

    trimmed_text = text

    # Step 2: Intro/Outro (more professional)
    serious_keywords = ['died', 'crisis', 'emergency', 'fatal', 'evacuated', 'conflict', 'breaking', 'tragedy', 'attack', 'warning', 'disaster', 'protest', 'fire', 'flood', 'investigation', 'arrest', 'charges']
    is_serious = any(word in text.lower() for word in serious_keywords)

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

    intro = random.choice(intros['serious' if is_serious else 'neutral'])
    outro = "For more updates, stay tuned."

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

        # Try to end at sentence boundary:
        last_period = trimmed_text.rfind('.')
        if last_period > word_limit * 3:  # reasonable cutoff
            trimmed_text = trimmed_text[:last_period + 1]
        else:
            trimmed_text += '.'

    # Step 5: Final result
    result = trimmed_text
    if include_intro:
        result = f"{intro} {result}"
    if include_outro:
        result = f"{result} {outro}"

    if result and not result.rstrip().endswith(('.', '!', '?')):
        result = result.rstrip() + '.'

    logger.info(f"Final result length: {len(result)} characters")
    logger.info(f"Final result preview: {result[:50]}...{result[-50:]}")
    
    print("[Voice Optimized Text]", result)
    return result
