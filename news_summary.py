def generate_news_summary(article_text, max_words=None):
    """
    Generate a concise, meaningful extractive summary of a news article.

    Prioritizes key facts and valuable sentences that provide core understanding
    of the topic, even under a strict word limit.
    """
    import re
    from collections import Counter
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize

    # Ensure resources
    for res in ['punkt', 'stopwords']:
        try:
            nltk.data.find(f'tokenizers/{res}') if res == 'punkt' else nltk.data.find(f'corpora/{res}')
        except LookupError:
            nltk.download(res)

    # Clean and tokenize
    article_text = re.sub(r'\s+', ' ', article_text)
    article_text = re.sub(r'[^\w\s.,?!]', '', article_text)
    sentences = sent_tokenize(article_text)
    if len(sentences) <= 2:
        return article_text.strip()

    stop_words = set(stopwords.words('english'))
    words = word_tokenize(article_text.lower())
    filtered_words = [w for w in words if w.isalnum() and w not in stop_words]
    word_freq = Counter(filtered_words)

    value_keywords = [
        'announced', 'confirmed', 'revealed', 'report', 'reports',
        'officials', 'statement', 'warned', 'according to',
        'update', 'data', 'study', 'survey', 'found'
    ]

    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()
        score = sum(word_freq.get(w, 0) for w in word_tokenize(sentence_lower))
        bonus = sum(1 for kw in value_keywords if kw in sentence_lower) * 2
        sentence_scores[i] = score + bonus

    # Select top sentences preserving order
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    selected = []
    total_words = 0
    used_indexes = set()

    for idx, _ in top_sentences:
        if idx in used_indexes:
            continue
        sent = sentences[idx]
        wc = len(word_tokenize(sent))
        if max_words and total_words + wc > max_words:
            continue
        selected.append(sent.strip())
        total_words += wc
        used_indexes.add(idx)
        if max_words and total_words >= max_words:
            break

    return ' '.join(selected).strip()



def generate_news_headline(article_text, article_title=""):
    """
    Generate a clean, short, and informative headline from article text or title.
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize

    if article_title:
        clean_title = re.sub(r'[^\w\s]', '', article_title).strip()
        words = clean_title.split()
        return ' '.join(words[:8]) + ('...' if len(words) > 8 else '')

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    sentences = sent_tokenize(article_text)
    if not sentences:
        return "Latest Update"

    first_sentence = re.sub(r'[^\w\s]', '', sentences[0]).strip()
    words = first_sentence.split()
    return ' '.join(words[:8]) + ('...' if len(words) > 8 else '')

def generate_voice_optimized_text(text, word_limit=None):
    """
    Generate a voice-friendly version of a news summary with contextual intro and outro.

    - Picks a natural-sounding intro/outro based on tone.
    - Adds commas to improve flow.
    - Cleans the text for narration.
    - Limits total words to improve pacing and control.

    Args:
        text (str): Original article or summary.
        word_limit (int): Optional max word limit.

    Returns:
        str: Narration-optimized text.
    """
    import re
    import nltk
    import random
    from nltk.tokenize import sent_tokenize, word_tokenize

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    # Possible intros and outros to vary toneeeeeeeeeeeeeeeeeeeeeeeeeeeee
    intros = [
        "Here’s what you need to know.",
        "Let’s break it down.",
        "Here’s what’s unfolding.",
        "Take a moment to catch up.",
        "A quick look at what’s happening:"
    ]

    outros = [
        "Check the full article for more information.",
        "That’s the latest for now.",
        "For full context, read the complete report.",
        "More details are available in the full article.",
        "Stay tuned for further updates."
    ]

    # Analyze text to adjust tone
    def is_serious(text):
        serious_words = ['died', 'crisis', 'warning', 'emergency', 'conflict', 'breaking', 'fatal', 'evacuated']
        return any(word in text.lower() for word in serious_words)

    intro = "Here’s what you need to know."
    outro = "Check the full article for more information."
    if is_serious(text):
        intro = "Here’s what’s unfolding."
        outro = "More details are available in the full article."
    else:
        intro = random.choice(intros)
        outro = random.choice(outros)

    # Extract core sentences
    sentences = sent_tokenize(text)
    output, total_words = [], 0

    for sent in sentences:
        wc = len(word_tokenize(sent.strip()))
        if wc < 5:
            continue
        if word_limit and total_words + wc > word_limit:
            break
        output.append(sent.strip())
        total_words += wc

    if not output:
        return f"{intro} {outro}"

    # Add commas for flow every 2–3 sentences
    core = ''
    for i, sentence in enumerate(output):
        if i > 0 and i % random.choice([2, 3]) == 0:
            core += ', '
        elif i > 0:
            core += ' '
        core += sentence

    # Clean unwanted patterns
    core = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', core, flags=re.IGNORECASE)
    core = re.sub(r'\b\d+\b[^\.\!\?]*$', '', core).strip()
    core = re.sub(r'\[.*?\]|\(.*?\)', '', core)
    core = re.sub(r'\s+', ' ', core).strip()

    # Capitalize first word if needed
    if core and not core[0].isupper():
        core = core[0].upper() + core[1:]

    if not core.endswith(('.', '!', '?')):
        core += '.'

    return f"{intro} {core} {outro}" 
