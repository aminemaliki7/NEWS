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
    Prepare a news article or summary for voice narration with a natural intro and closure.

    This function ensures the content:
    - Starts with a gentle, engaging phrase.
    - Focuses on key facts (who, what, when, where, why).
    - Uses fluent, conversational structure for voice delivery.
    - Excludes numbers, references, or data not suited for audio.
    - Ends smoothly with a conclusive phrase, even if truncated.

    Args:
        text (str): Full article or summary to optimize.
        word_limit (int): Max number of words allowed in the output.

    Returns:
        str: Cleaned, voice-ready text with natural flow and framing.
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize

    # Ensure required tokenizer is available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    intro_phrase = "Here’s what you need to know."
    closing_phrase = "And that’s the story for now."

    # Segment into sentences
    sentences = sent_tokenize(text)
    output = []
    total_words = 0

    # Select sentences until reaching word limit
    for sent in sentences:
        words = word_tokenize(sent)
        word_count = len(words)
        if word_limit and total_words + word_count > word_limit:
            break
        output.append(sent.strip())
        total_words += word_count

    # Join selected sentences
    core_text = ' '.join(output).strip()

    # Clean metadata and numbers
    core_text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', core_text, flags=re.IGNORECASE)
    core_text = re.sub(r'\b\d+\b[^\.\!\?]*$', '', core_text).strip()
    core_text = re.sub(r'\[.*?\]', '', core_text)
    core_text = re.sub(r'\(.*?\)', '', core_text)
    core_text = re.sub(r'\s+', ' ', core_text).strip()

    # Capitalize first character if needed
    if core_text and not core_text[0].isupper():
        core_text = core_text[0].upper() + core_text[1:]

    # Ensure proper punctuation at end
    if not core_text.endswith(('.', '!', '?')):
        core_text += '.'

    # Combine full output with intro and outro
    final_output = f"{intro_phrase} {core_text} {closing_phrase}"
    return final_output