def generate_voice_optimized_text(text, word_limit=400, include_intro=True, include_outro=True):
    """
    Fast and adaptive voice-ready text generation.

    - Cleans basic formatting.
    - Limits the number of words.
    - Strips any HTML tags that might be spoken during TTS.
    - Ensures character counts or counts-related phrases are excluded.
    - Contextual intro/outro based on content.
    - Intro/outro can be toggled with parameters.
    """
    import re
    import random

    # Remove HTML tags
    text = re.sub(r'<[^>]*?>', '', text)

    # Basic cleanup: remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove patterns related to character or word counts
    text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b[^\.\!\?]*$', '', text).strip()

    # Word limit
    words = text.split()
    trimmed_text = ' '.join(words[:word_limit])

    # Context-aware intros/outros
    serious_keywords = ['died', 'crisis', 'emergency', 'fatal', 'evacuated', 'conflict', 'breaking']
    light_keywords = ['celebration', 'festival', 'launch', 'award', 'fun']

    is_serious = any(word in text.lower() for word in serious_keywords)
    is_light = any(word in text.lower() for word in light_keywords)

    intros_serious = ["Here's what’s unfolding:", "Urgent update:", "What you need to know now:"]
    intros_light = ["Let’s break it down:", "Catch up on this:", "Here's the latest:"]
    intros_neutral = ["Here’s what you need to know:", "Quick summary:", "The key points are:"]

    outros_serious = ["Stay alert for more updates.", "More details in the full article.", "Follow developments closely."]
    outros_light = ["That’s the scoop.", "Check the full article for more fun.", "Enjoy the full story online."]
    outros_neutral = ["For more details, check the full article.", "You can read the full article for more.", "That’s the main idea."]

    if is_serious:
        intro = random.choice(intros_serious)
        outro = random.choice(outros_serious)
    elif is_light:
        intro = random.choice(intros_light)
        outro = random.choice(outros_light)
    else:
        intro = random.choice(intros_neutral)
        outro = random.choice(outros_neutral)

    result = trimmed_text
    if include_intro:
        result = f"{intro} {result}"
    if include_outro:
        result = f"{result} {outro}"

    return result
