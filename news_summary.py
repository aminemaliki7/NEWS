def generate_news_summary(article_text, max_words=150):
    """
    Generate a concise extractive summary of a news article, based on sentence scoring.
    
    Args:
        article_text (str): The full text of the article
        max_words (int): Maximum number of words for the summary
    
    Returns:
        str: A summarized version of the article
        
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

    # Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        score = sum(word_freq.get(word, 0) for word in word_tokenize(sentence.lower()))
        sentence_scores[i] = score

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


def generate_voice_optimized_text(text, word_limit=400):
    import re
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    sentences = sent_tokenize(text)
    output = []
    total_words = 0
    
    for sent in sentences:
        words = word_tokenize(sent)
        word_count = len(words)
        if total_words + word_count > word_limit:
            break
        output.append(sent.strip())
        total_words += word_count
    
    final_text = ' '.join(output).strip()
    
    # NOUVEAU: Supprimer les patterns de comptage de caractères/mots
    final_text = re.sub(r'\b\d+\s*(chars?|characters?|words?|mots?)\b', '', final_text, flags=re.IGNORECASE)
    
    # Fix sentence fragments ending in numbers or mid-sentence  
    final_text = re.sub(r'\b\d+\b[^\.\!\?]*$', '', final_text).strip()
    
    # Supprimer les métadonnées communes
    final_text = re.sub(r'\[.*?\]', '', final_text)  # Texte entre crochets
    final_text = re.sub(r'\(.*?\)', '', final_text)  # Texte entre parenthèses si nécessaire
    
    # Nettoyer les espaces multiples
    final_text = re.sub(r'\s+', ' ', final_text).strip()
    
    # Ensure proper punctuation
    if not final_text.endswith(('.', '!', '?')):
        final_text += '.'
    
    # Optional close-off to signal voiceover end
    if total_words < len(word_tokenize(text)):
        final_text += ' That\'s the latest.'
    
    return final_text