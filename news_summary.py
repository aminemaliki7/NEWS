"""
News Summary Generator for REALTALK platform.
This module provides functions to generate concise summaries of news articles.
"""

def generate_news_summary(article_text, max_length=500):
    """
    Generate a concise summary of a news article.
    
    This is a simple extractive summary approach. For more advanced summarization,
    you might want to use an NLP library or API.
    
    Args:
        article_text (str): The full text of the article
        max_length (int): Maximum length of the summary in characters
        
    Returns:
        str: A summarized version of the article
    """
    import re
    from collections import Counter
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    
    # Download necessary NLTK data (run once)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    # Preprocess the text
    article_text = re.sub(r'\s+', ' ', article_text)  # Remove extra whitespace
    article_text = re.sub(r'[^\w\s.,?!]', '', article_text)  # Remove special characters
    
    # Tokenize into sentences
    sentences = sent_tokenize(article_text)
    
    # Skip summarization for short articles
    if len(sentences) <= 3:
        return article_text[:max_length]
    
    # Tokenize words and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(article_text.lower())
    filtered_words = [word for word in word_tokens if word.isalnum() and word not in stop_words]
    
    # Count word frequencies
    word_freq = Counter(filtered_words)
    
    # Score sentences based on word frequency
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        words = word_tokenize(sentence.lower())
        for word in words:
            if word in word_freq:
                if i in sentence_scores:
                    sentence_scores[i] += word_freq[word]
                else:
                    sentence_scores[i] = word_freq[word]
    
    # Get top sentences (approximately 1/3 of the original article)
    num_sentences = max(3, len(sentences) // 3)  # At least 3 sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
    
    # Create summary
    summary = ' '.join([sentences[i] for i, _ in top_sentences])
    
    # Truncate to max_length
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
    
    return summary


def generate_news_headline(article_text, article_title=""):
    """
    Generate a catchy headline for a news article.
    
    Args:
        article_text (str): The full text of the article
        article_title (str): The original title, if available
        
    Returns:
        str: A generated headline
    """
    # If we have an original title, modify it slightly for variety
    if article_title:
        # Simple transformation of existing title
        if len(article_title) > 50:
            # Shorten long titles
            import re
            words = re.findall(r'\w+', article_title)
            if len(words) > 8:
                return ' '.join(words[:7]) + '...'
            return article_title
        
        # If title is already good, use it
        return article_title
    
    # Without an original title, extract key information
    # This is a simple implementation - a more advanced version would use NLP
    import nltk
    from nltk.tokenize import sent_tokenize
    
    # Get first sentence as a basis
    sentences = sent_tokenize(article_text)
    if not sentences:
        return "News Update"
        
    first_sentence = sentences[0]
    
    # Truncate if too long
    if len(first_sentence) > 60:
        words = first_sentence.split()
        first_sentence = ' '.join(words[:8]) + '...'
    
    return first_sentence


def generate_voice_optimized_text(article_text, word_limit=300):
    """
    Optimize article text for voice reading by simplifying language
    and structure.
    
    Args:
        article_text (str): The original article text
        word_limit (int): Maximum number of words for the output
        
    Returns:
        str: Voice-optimized version of the article
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize

    # Ensure required NLTK data is available
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    # Step 1: Clean up the raw article text
    text = re.sub(r'\s+', ' ', article_text)  # Normalize whitespace
    text = re.sub(r'http\S+', '', text)  # Remove URLs

    # Step 2: Replace common abbreviations with their full forms for clarity in TTS
    abbreviations = {
        'Dr.': 'Doctor',
        'Mr.': 'Mister',
        'Mrs.': 'Misses',
        'Ms.': 'Miss',
        'St.': 'Street',
        'Apt.': 'Apartment',
        'vs.': 'versus',
        'etc.': 'etcetera',
        'e.g.': 'for example',
        'i.e.': 'that is',
        'approx.': 'approximately',
        'Corp.': 'Corporation',
        'Inc.': 'Incorporated',
        'Ltd.': 'Limited',
    }
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)

    # Step 3: Split into sentences for simplification
    sentences = sent_tokenize(text)

    simplified_sentences = []
    for sentence in sentences:
        # Break up overly long or complex sentences
        if sentence.count(',') > 3:
            parts = sentence.split(',')
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    simplified_sentences.append(parts[i].strip() + ', ' + parts[i + 1].strip() + '.')
                else:
                    simplified_sentences.append(parts[i].strip() + '.')
        else:
            simplified_sentences.append(sentence.strip())

    # Step 4: Concatenate and limit total word count
    combined_text = ' '.join(simplified_sentences)
    words = combined_text.split()

    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'

    return combined_text


if __name__ == "__main__":
    # Example usage
    sample_article = """
    Climate scientists have issued a new warning about the accelerating pace of climate change. 
    According to the latest research published in the journal Nature Climate Science, global temperatures 
    could rise by 1.5 degrees Celsius above pre-industrial levels within the next decade, much sooner than 
    previously anticipated. The study, conducted by an international team of researchers across 15 countries, 
    analyzed temperature data from the past 50 years along with advanced climate models.
    
    Dr. Maria Rodriguez, lead author of the study, emphasized the urgency of the situation. "The data is 
    clear and concerning. We're seeing feedback loops that are accelerating warming beyond our previous 
    models' predictions," she explained during a press conference on Monday.
    
    The research highlights several factors contributing to this acceleration, including decreased 
    reflectivity of Arctic ice, increased methane release from thawing permafrost, and higher than expected 
    emissions from developing economies. These factors combined create what the scientists term a 
    "compounding effect" that current climate policies do not adequately address.
    
    World leaders are expected to discuss these findings at the upcoming United Nations Climate Summit 
    next month in Geneva. Environmental activists are calling for immediate action and more aggressive 
    emission reduction targets in response to the study.
    """
    
    print("ORIGINAL TEXT:")
    print(sample_article)
    print("\n" + "-" * 50 + "\n")
    
    print("SUMMARY:")
    print(generate_news_summary(sample_article))
    print("\n" + "-" * 50 + "\n")
    
    print("HEADLINE:")
    print(generate_news_headline(sample_article))
    print("\n" + "-" * 50 + "\n")
    
    print("VOICE-OPTIMIZED TEXT:")
    print(generate_voice_optimized_text(sample_article))