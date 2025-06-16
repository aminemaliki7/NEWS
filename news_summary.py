def generate_news_summary(article_text, max_words=None):
    """
    Generate a high-value extractive summary of a news article, based on sentence scoring.

    This function selects the most informative and relevant sentences from the article, 
    ensuring that the summary delivers clear, concise, and meaningful content to the reader.

    Key principles:
    - Focus on the most value-rich sentences that convey critical facts or insight.
    - Prioritize clarity, informativeness, and context (who, what, when, where, why).
    - Preserve the original meaning and tone while maximizing information density.
    - Avoid trivial, redundant, or overly short phrases.

    Args:
        article_text (str): The full original text of the article.
        max_words (int): The maximum number of words to include in the summary.

    Returns:
        str: A concise and content-rich summary that captures the core of the article.
    """
    import re
    from collections import Counter
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize

    # Ensure NLTK resources are available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    # Clean text
    article_text = re.sub(r'\s+', ' ', article_text)
    article_text = re.sub(r'[^\w\s.,?!]', '', article_text)

    # Sentence tokenization
    sentences = sent_tokenize(article_text)
    if len(sentences) <= 3:
        return article_text

    # Word frequency scoring
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(article_text.lower())
    filtered_words = [w for w in words if w.isalnum() and w not in stop_words]
    word_freq = Counter(filtered_words)

    # Score sentences (with keyword bonus)
    value_keywords = [
        'announced', 'confirmed', 'revealed', 'report', 'reports',
        'officials', 'statement', 'warned', 'according to',
        'update', 'data', 'study', 'survey', 'found'
    ]

    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()
        base_score = sum(word_freq.get(word, 0) for word in word_tokenize(sentence_lower))
        keyword_bonus = sum(1 for kw in value_keywords if kw in sentence_lower) * 2
        sentence_scores[i] = base_score + keyword_bonus

    # Select top sentences in original order
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    selected = []
    total_words = 0
    for i, _ in sorted(top_sentences, key=lambda x: x[0]):
        word_count = len(word_tokenize(sentences[i]))
        if total_words + word_count > max_words:
            break
        selected.append(sentences[i])
        total_words += word_count

    return ' '.join(selected)



def generate_news_headline(article_text, article_title=""):
    """
    Generate a short, clean headline for a news article.
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize

    if article_title:
        words = re.findall(r'\w+', article_title)
        return ' '.join(words[:8]) + '...' if len(words) > 8 else article_title

    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    sentences = sent_tokenize(article_text)
    if not sentences:
        return "News Update"
    first_sentence = sentences[0]
    return ' '.join(first_sentence.split()[:8]) + '...' if len(first_sentence.split()) > 8 else first_sentence


def generate_voice_optimized_text(text, word_limit=None):
    """
    Prepare a news article or summary for voice narration.

    This function ensures the content:
    - Focuses on the most important facts (who, what, when, where, why).
    - Brings value to the listener by delivering accurate, high-impact information.
    - Is clear and well-structured for spoken delivery, following natural speech flow.
    - Uses fluent, conversational language — no bullet points, fragmented phrases, or awkward transitions.
    - Removes numbers, metadata, or references that may confuse or distract audio listeners.
    - Ends smoothly with a soft closure if the content was truncated for length.

    Args:
        text (str): The full article or summary to optimize.
        word_limit (int): The maximum number of words to include in the voice output.

    Returns:
        str: A voice-friendly, cleaned, and structured version of the text, ready for TTS generation.
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize

    # Ensure sentence tokenizer is available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    # Sentence segmentation
    sentences = sent_tokenize(text)
    output = []
    total_words = 0

    # Select sentences until reaching word limit
    for sent in sentences:
        words = word_tokenize(sent)
        word_count = len(words)
        if total_words + word_count > word_limit:
            break
        output.append(sent.strip())
        total_words += word_count

    final_text = ' '.join(output).strip()

    # Remove counts and metadata not needed in voice
    final_text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', final_text, flags=re.IGNORECASE)
    final_text = re.sub(r'\b\d+\b[^\.\!\?]*$', '', final_text).strip()
    final_text = re.sub(r'\[.*?\]', '', final_text)
    final_text = re.sub(r'\(.*?\)', '', final_text)
    final_text = re.sub(r'\s+', ' ', final_text).strip()

    # Capitalize if needed
    if final_text and not final_text[0].isupper():
        final_text = final_text[0].upper() + final_text[1:]

    # Ensure it ends properly
    if not final_text.endswith(('.', '!', '?')):
        final_text += '.'

    # Add soft closure if the content was cut short
    if total_words < len(word_tokenize(text)):
        final_text += " That's the latest."

    return final_text
