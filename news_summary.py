def generate_voice_optimized_text(text, word_limit=400, include_intro=True, include_outro=True):
    """
    Generate clean, natural-sounding voice narration from news text.

    🔹 Removes HTML, extra whitespace, and irrelevant word/char count references.
    🔹 Limits output by sentence count, ensuring complete thoughts (not mid-sentence).
    🔹 Expands common acronyms for clarity in TTS (e.g., 'NAHB' → 'National Association of Home Builders').
    🔹 Dynamically adds intro and outro phrases based on tone (serious, light, neutral).
    🔹 Logs the result for debugging and voice script validation.

    Params:
        text (str): Raw news article or excerpt
        word_limit (int): Max number of words (by complete sentences)
        include_intro (bool): If True, prepends a tone-matching intro
        include_outro (bool): If True, appends a tone-matching outro

    Returns:
        str: Cleaned, optimized narration-ready text string
    """
    import re
    import random

    # Step 1: Clean raw HTML and whitespace
    text = re.sub(r'<[^>]*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d+\b[^\.\!\?]*$', '', text).strip()

    # Step 2: Limit to complete sentences within word count
    sentences = re.split(r'(?<=[\.\?!])\s+', text)
    selected_sentences, total_words = [], 0
    for sentence in sentences:
        wc = len(sentence.split())
        if total_words + wc <= word_limit:
            selected_sentences.append(sentence)
            total_words += wc
        else:
            break
    trimmed_text = ' '.join(selected_sentences)

    # Step 3: Tone detection for intro/outro
    serious_keywords = ['died', 'crisis', 'emergency', 'fatal', 'evacuated', 'conflict', 'breaking']
    light_keywords = ['celebration', 'festival', 'launch', 'award', 'fun']
    is_serious = any(word in text.lower() for word in serious_keywords)
    is_light = any(word in text.lower() for word in light_keywords)

    intros = {
        'serious': ["Here's what’s unfolding:", "Urgent update:", "What you need to know now:"],
        'light': ["Let’s break it down:", "Catch up on this:", "Here's the latest:"],
        'neutral': ["Here’s what you need to know:", "Quick summary:", "The key points are:"]
    }

    outros = {
        'serious': ["Stay alert for more updates.", "More details in the full article.", "Follow developments closely."],
        'light': ["That’s the scoop.", "Check the full article for more fun.", "Enjoy the full story online."],
        'neutral': ["For more details, check the full article.", "You can read the full article for more.", "That’s the main idea."]
    }

    tone = 'serious' if is_serious else 'light' if is_light else 'neutral'
    intro = random.choice(intros[tone])
    outro = random.choice(outros[tone])

    # Step 4: Expand known acronyms
    acronym_expansions = {
        "NAHB": "the National Association of Home Builders",
        "WHO": "the World Health Organization",
        "UNESCO": "UNESCO, the United Nations Educational, Scientific and Cultural Organization",
        "NASA": "the U.S. space agency NASA",
        "FBI": "the Federal Bureau of Investigation"
    }
    for acro, expansion in acronym_expansions.items():
        trimmed_text = re.sub(rf'\b{acro}\b', expansion, trimmed_text)

    # Step 5: Build final result
    result = trimmed_text
    if include_intro:
        result = f"{intro} {result}"
    if include_outro:
        result = f"{result} {outro}"

    # Log the result
    return result
