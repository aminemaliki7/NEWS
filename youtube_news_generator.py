"""
YouTube News Generator for REALTALK platform.

This module provides functions to generate YouTube-style news scripts
that adapt to the tone and content of news articles.
"""

import re
import random
from collections import Counter

def analyze_article_tone(article_content, article_title=""):
    """
    Analyze the tone of an article to determine the appropriate YouTube script style.
    
    Args:
        article_content (str): The content of the article
        article_title (str): The title of the article
        
    Returns:
        dict: Tone analysis results with tone categories and intensity
    """
    # Clean content for analysis
    content = article_title + " " + article_content
    content = content.lower()
    
    # Define tone indicators (keywords that suggest different tones)
    tone_indicators = {
        "urgent": ["breaking", "urgent", "emergency", "critical", "crisis", "immediately", "danger", 
                   "warning", "alert", "catastrophe", "disaster", "death", "fatal", "tragedy", "crash"],
        
        "positive": ["success", "breakthrough", "achievement", "win", "celebrate", "victory", "progress", 
                     "improvement", "growth", "recovery", "opportunity", "hope", "promising", "benefit"],
        
        "negative": ["failure", "problem", "issue", "conflict", "controversy", "loss", "decline", "damage", 
                     "threat", "risk", "concern", "worry", "fear", "trouble", "difficult", "challenge"],
        
        "analytical": ["research", "study", "analysis", "data", "report", "evidence", "findings", "statistics", 
                       "experts", "scientists", "investigation", "examine", "according to", "resulted"],
        
        "emotional": ["shocking", "surprising", "amazing", "incredible", "heartbreaking", "moving", "touching", 
                      "devastating", "outrageous", "controversial", "unbelievable", "dramatic", "stunning"],
                      
        "tech": ["technology", "digital", "software", "hardware", "app", "device", "platform", "internet", 
                 "online", "cyber", "innovation", "startup", "ai", "artificial intelligence", "blockchain"],
                 
        "business": ["market", "company", "industry", "business", "corporate", "investor", "stocks", "financial", 
                     "economy", "economic", "trade", "commercial", "profit", "revenue", "growth"],
                     
        "entertainment": ["celebrity", "star", "movie", "film", "tv", "television", "show", "music", "album", 
                         "concert", "performance", "award", "entertainment", "actor", "actress"],
                         
        "sports": ["game", "match", "tournament", "championship", "player", "team", "score", "win", "lose", 
                  "victory", "defeat", "competition", "athlete", "sports", "league"]
    }
    
    # Count occurrences of each tone's keywords
    tone_scores = {tone: 0 for tone in tone_indicators}
    
    for tone, keywords in tone_indicators.items():
        for keyword in keywords:
            # Count keyword occurrences considering word boundaries
            matches = re.findall(r'\b' + re.escape(keyword) + r'\b', content)
            tone_scores[tone] += len(matches)
    
    # Determine the primary and secondary tones
    sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate total tone mentions
    total_mentions = sum(tone_scores.values()) or 1  # Avoid division by zero
    
    # Calculate the intensity of each tone (normalized)
    tone_intensity = {tone: score / total_mentions for tone, score in tone_scores.items()}
    
    # Determine primary and secondary tones
    primary_tone = sorted_tones[0][0] if sorted_tones[0][1] > 0 else "neutral"
    secondary_tone = sorted_tones[1][0] if len(sorted_tones) > 1 and sorted_tones[1][1] > 0 else "neutral"
    
    # If no strong signals, default to neutral
    if sorted_tones[0][1] == 0:
        primary_tone = "neutral"
        
    # Get the content category (topic)
    category_tones = ["tech", "business", "entertainment", "sports"]
    content_category = next((tone for tone in category_tones if tone_scores[tone] > 0), "general")
    
    return {
        "primary_tone": primary_tone,
        "secondary_tone": secondary_tone,
        "tone_scores": tone_scores,
        "tone_intensity": tone_intensity,
        "content_category": content_category
    }


def extract_key_points(article_content, max_points=5):
    """
    Extract key points from the article content.
    
    Args:
        article_content (str): The content of the article
        max_points (int): Maximum number of key points to extract
        
    Returns:
        list: Extracted key points
    """
    # Split into sentences
    sentences = [s.strip() for s in article_content.split('.') if s.strip()]
    
    if not sentences:
        return []
    
    # Skip sentences that are too short
    sentences = [s for s in sentences if len(s.split()) >= 5]
    
    # If we have very few sentences, return them all
    if len(sentences) <= max_points:
        return sentences
    
    # Simple extractive summarization using word frequency
    # Step 1: Tokenize and remove stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 
                 'by', 'about', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
                 'has', 'had', 'do', 'does', 'did', 'of', 'from', 'that', 'this', 'these', 
                 'those', 'it', 'its', 'they', 'them', 'their', 'he', 'him', 'his', 'she', 
                 'her', 'we', 'us', 'our', 'you', 'your'}
    
    all_words = []
    for sentence in sentences:
        words = [word.lower() for word in re.findall(r'\b\w+\b', sentence) if word.lower() not in stop_words]
        all_words.extend(words)
    
    # Step 2: Count word frequencies
    word_freq = Counter(all_words)
    
    # Step 3: Score sentences based on word frequency
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        words = [word.lower() for word in re.findall(r'\b\w+\b', sentence)]
        score = sum(word_freq[word] for word in words if word not in stop_words)
        # Normalize by sentence length to avoid favoring very long sentences
        score = score / (len(words) + 1)  # +1 to avoid division by zero
        sentence_scores.append((i, score))
    
    # Step 4: Get top-scoring sentences
    top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_points]
    
    # Step 5: Reorder sentences to maintain original flow
    top_sentences = sorted(top_sentences, key=lambda x: x[0])
    
    # Return the selected sentences
    return [sentences[idx] for idx, _ in top_sentences]


def generate_youtube_intro(tone_analysis, article_title, source=""):
    """
    Generate a YouTube-style introduction based on the article tone.
    
    Args:
        tone_analysis (dict): Results from tone analysis
        article_title (str): The title of the article
        source (str): The source of the article
        
    Returns:
        str: YouTube-style introduction
    """
    primary_tone = tone_analysis["primary_tone"]
    content_category = tone_analysis["content_category"]
    
    # Intro templates by tone
    intro_templates = {
        "urgent": [
            "BREAKING NEWS! {title}. This urgent story is developing right now.",
            "We interrupt our regular content with BREAKING NEWS. {title}.",
            "URGENT UPDATE: {title}. We're bringing you the latest information as it comes in.",
            "Breaking news alert! {title}. This story is unfolding as we speak."
        ],
        "positive": [
            "Amazing news today! {title}. This exciting development has everyone talking.",
            "Great news to share with you! {title}. Let's dive into this positive story.",
            "You won't believe this incredible news! {title}. This is a game-changer!",
            "Here's some good news to brighten your day! {title}. Let's get into the details."
        ],
        "negative": [
            "Concerning developments today. {title}. We'll break down what this means.",
            "Troubling news has emerged. {title}. Here's what you need to know.",
            "An unfortunate situation has developed. {title}. Let's analyze the implications.",
            "Difficult news to report today. {title}. We'll explain the situation."
        ],
        "analytical": [
            "Let's analyze an important development. {title}. The data tells an interesting story.",
            "Today we're examining a significant report. {title}. The findings are noteworthy.",
            "An in-depth look at recent developments. {title}. The analysis reveals important trends.",
            "We're breaking down the facts about {title}. The evidence provides clear insights."
        ],
        "emotional": [
            "You won't believe what just happened! {title}. This story has shocked everyone.",
            "This story has everyone talking! {title}. The reactions have been incredible.",
            "I'm absolutely stunned by this news. {title}. This is truly unbelievable.",
            "This might be the most surprising story of the year. {title}. I'm still processing it."
        ],
        "tech": [
            "Tech enthusiasts, you'll want to hear this. {title}. This could change the industry.",
            "A major tech development has just been announced. {title}. Let's break it down.",
            "Tech news alert! {title}. This innovation is worth your attention.",
            "The tech world is buzzing about this news. {title}. Here's why it matters."
        ],
        "business": [
            "Major business news today. {title}. This will impact markets worldwide.",
            "Business insiders are closely watching this story. {title}. Let's analyze the implications.",
            "A significant development in the business world. {title}. Here's what investors need to know.",
            "Market-moving news just announced. {title}. This could affect your investments."
        ],
        "entertainment": [
            "Entertainment news flash! {title}. Fans are going wild over this development.",
            "The entertainment world is abuzz with this story. {title}. Here's the inside scoop.",
            "Celebrity news alert! {title}. This has social media in a frenzy.",
            "Huge entertainment story breaking now. {title}. You won't want to miss these details."
        ],
        "sports": [
            "Sports fans, huge news just dropped. {title}. This changes everything.",
            "Breaking sports update! {title}. This is game-changing news.",
            "Major development in the sports world. {title}. Fans are reacting strongly.",
            "Sports news that has everyone talking. {title}. Let's break down what happened."
        ],
        "neutral": [
            "Today we're covering an important story. {title}. Let's get into the details.",
            "An interesting development to share with you today. {title}. Here's what we know.",
            "We're bringing you coverage of {title}. This story deserves your attention.",
            "Let's talk about a significant recent event. {title}. There's a lot to unpack here."
        ]
    }
    
    # Fallback to neutral if primary tone doesn't have templates
    templates = intro_templates.get(primary_tone, intro_templates["neutral"])
    
    # Select a random template (weighted if we have content category match)
    if content_category in intro_templates and primary_tone != content_category:
        # Add category-specific templates to increase variety
        templates.extend(intro_templates[content_category])
    
    intro = random.choice(templates)
    
    # Fill in the template
    intro = intro.format(title=article_title)
    
    # Add source attribution if provided
    if source:
        attribution_phrases = [
            f"According to {source},",
            f"As reported by {source},",
            f"{source} just published that",
            f"This news comes from {source}, which states"
        ]
        intro = f"{intro} {random.choice(attribution_phrases)}"
    
    return intro


def generate_youtube_outro(tone_analysis, article_title):
    """
    Generate a YouTube-style outro based on the article tone.
    
    Args:
        tone_analysis (dict): Results from tone analysis
        article_title (str): The title of the article
        
    Returns:
        str: YouTube-style outro
    """
    primary_tone = tone_analysis["primary_tone"]
    
    # Outro templates by tone
    outro_templates = {
        "urgent": [
            "We'll continue to monitor this breaking situation and bring you updates as they develop. Stay tuned.",
            "This is an evolving story and we'll update you with new information as soon as it becomes available.",
            "Make sure to subscribe for the latest updates on this critical situation as it unfolds.",
            "We're keeping a close eye on this developing story. Check back for important updates."
        ],
        "positive": [
            "That's the exciting news for today! If you enjoyed this update, give this video a thumbs up.",
            "What an amazing development! Share your thoughts in the comments below.",
            "That's all for this positive update. Hit subscribe for more good news in your feed.",
            "What do you think about this great news? Let me know in the comments!"
        ],
        "negative": [
            "We'll continue to follow this concerning situation. Subscribe for further updates.",
            "That's where things stand with this troubling development. Let me know your thoughts below.",
            "We'll keep you informed as this difficult situation evolves. Stay tuned for updates.",
            "These are challenging developments to report. Join the discussion in the comments section."
        ],
        "analytical": [
            "That's our analysis of the situation. What insights would you add? Comment below.",
            "Those are the facts as we currently understand them. Subscribe for follow-up analysis.",
            "This analytical breakdown gives us a clearer picture of the situation. More updates coming soon.",
            "That concludes our data-driven examination of this story. Like and subscribe for more in-depth analysis."
        ],
        "emotional": [
            "I'm still processing this incredible story! Let me know if you're as shocked as I am in the comments.",
            "What an unbelievable development! Hit like if this surprised you too!",
            "I can't believe what we just covered! Share your reactions in the comments section.",
            "This story has left me speechless! Let me know what you think about these amazing developments."
        ],
        "tech": [
            "That's the latest tech news! Subscribe for more updates from the world of technology.",
            "What do you think about this tech development? Leave your thoughts in the comments.",
            "That's all for this tech update. Hit the notification bell to stay on top of breaking tech news.",
            "The tech landscape is constantly evolving. Subscribe to stay informed about the latest innovations."
        ],
        "business": [
            "That's the latest from the business world. Subscribe for regular market updates.",
            "Keep an eye on how these developments affect the market. More business news coming soon.",
            "That's all for this business update. Hit subscribe for more financial insights.",
            "Stay ahead of market trends by subscribing to our channel for regular business updates."
        ],
        "entertainment": [
            "That's the latest gossip from the entertainment world! Subscribe for more celebrity news.",
            "What do you think about this entertainment bombshell? Let me know in the comments!",
            "Stay tuned for more juicy stories from the world of entertainment. Don't forget to subscribe!",
            "That's all for this entertainment update. Hit the notification bell for the latest celebrity news."
        ],
        "sports": [
            "That's the latest from the world of sports. Let me know your predictions in the comments!",
            "What an incredible development in sports news! Subscribe for more updates as this story unfolds.",
            "That's all for this sports update. Don't forget to share your reactions below!",
            "The sports world is always full of surprises. Hit subscribe to stay on top of the latest developments."
        ],
        "neutral": [
            "That's all for this update. Thanks for watching and don't forget to subscribe.",
            "Thanks for tuning in to this news update. More videos coming soon.",
            "That concludes our coverage of this story. Like and subscribe for more updates.",
            "That's where things stand with this developing story. Stay tuned for further updates."
        ]
    }
    
    # Fallback to neutral if primary tone doesn't have templates
    templates = outro_templates.get(primary_tone, outro_templates["neutral"])
    
    # Select a random template
    outro = random.choice(templates)
    
    return outro


def format_key_points(key_points, tone_analysis):
    """
    Format key points into a YouTube-style script section.
    
    Args:
        key_points (list): The key points to format
        tone_analysis (dict): Results from tone analysis
        
    Returns:
        str: Formatted key points section
    """
    primary_tone = tone_analysis["primary_tone"]
    
    # Define transition phrases by tone
    transition_phrases = {
        "urgent": [
            "Here's what we know so far:",
            "These are the critical details:",
            "The key developments are:",
            "Here are the urgent facts:",
            "What we know right now:"
        ],
        "positive": [
            "Here are the exciting details:",
            "The highlights of this great news include:",
            "The best parts of this story are:",
            "Here's why this is such good news:",
            "These positive developments include:"
        ],
        "negative": [
            "Here are the concerning details:",
            "The troubling aspects include:",
            "These are the issues at hand:",
            "Here's what's worrying about this situation:",
            "The problematic details include:"
        ],
        "analytical": [
            "The key findings include:",
            "Analysis reveals the following points:",
            "The data shows these important factors:",
            "Research indicates the following:",
            "The evidence points to these conclusions:"
        ],
        "emotional": [
            "The shocking details include:",
            "Here's what's making everyone talk:",
            "These incredible developments include:",
            "The most surprising elements are:",
            "Here's what's causing such a reaction:"
        ],
        "tech": [
            "The technical details include:",
            "Here's what makes this innovation significant:",
            "The key tech specs include:",
            "These technological advances include:",
            "The technical breakthroughs involve:"
        ],
        "business": [
            "The market implications include:",
            "Here's what investors should know:",
            "The business impact involves:",
            "These financial developments include:",
            "The economic factors at play are:"
        ],
        "entertainment": [
            "The juicy details include:",
            "Here's the inside scoop:",
            "The entertainment highlights include:",
            "These celebrity developments involve:",
            "Here's what fans are talking about:"
        ],
        "sports": [
            "The game-changing details include:",
            "Here's what sports fans should know:",
            "The key plays include:",
            "These athletic developments involve:",
            "The sporting implications are:"
        ],
        "neutral": [
            "Here are the main points:",
            "The key details include:",
            "Here's what we know:",
            "These are the important facts:",
            "The situation involves these elements:"
        ]
    }
    
    # Point prefixes based on tone
    point_prefixes = {
        "urgent": ["Crucially, ", "Urgently, ", "Importantly, ", "Critically, ", ""],
        "positive": ["Excitingly, ", "Remarkably, ", "Impressively, ", "Wonderfully, ", ""],
        "negative": ["Unfortunately, ", "Concerningly, ", "Troublingly, ", "Sadly, ", ""],
        "analytical": ["Analysis shows ", "Data indicates ", "Research reveals ", "Evidence suggests ", ""],
        "emotional": ["Shockingly, ", "Incredibly, ", "Amazingly, ", "Surprisingly, ", ""],
        "tech": ["Technologically, ", "Innovatively, ", "In tech terms, ", "Digitally speaking, ", ""],
        "business": ["Financially, ", "Economically, ", "Market-wise, ", "Business-wise, ", ""],
        "entertainment": ["In entertainment news, ", "For fans, ", "Celebrities say ", "In showbiz terms, ", ""],
        "sports": ["In sports terms, ", "For the game, ", "Athletically, ", "In the match, ", ""],
        "neutral": ["Notably, ", "Specifically, ", "In detail, ", "To clarify, ", ""]
    }
    
    # Get transition phrase based on tone
    transition = random.choice(transition_phrases.get(primary_tone, transition_phrases["neutral"]))
    
    # Format each key point with appropriate tone
    formatted_points = []
    prefixes = point_prefixes.get(primary_tone, point_prefixes["neutral"])
    
    for point in key_points:
        # Add a prefix sometimes (70% chance)
        if random.random() < 0.7:
            prefix = random.choice(prefixes)
            # Ensure we don't start with a capital letter after the prefix
            if prefix and point[0].isupper():
                point = point[0].lower() + point[1:]
            formatted_point = f"• {prefix}{point}."
        else:
            formatted_point = f"• {point}."
        
        formatted_points.append(formatted_point)
    
    # Combine into a section
    points_section = f"{transition}\n\n" + "\n\n".join(formatted_points)
    
    return points_section


def generate_emphasis_section(tone_analysis, article_content):
    """
    Generate an emphasis section to highlight the importance or impact of the news.
    
    Args:
        tone_analysis (dict): Results from tone analysis
        article_content (str): The article content
        
    Returns:
        str: Emphasis section
    """
    primary_tone = tone_analysis["primary_tone"]
    
    # Emphasis templates by tone
    emphasis_templates = {
        "urgent": [
            "This is a rapidly developing situation with potential wide-ranging consequences.",
            "The urgency of this situation cannot be overstated as events continue to unfold.",
            "Officials are urging people to stay informed as this critical situation develops.",
            "This breaking news could have immediate impacts that everyone should be aware of."
        ],
        "positive": [
            "This positive development represents a significant step forward for everyone involved.",
            "The good news here has far-reaching implications that could benefit many people.",
            "This achievement marks an important milestone that deserves to be celebrated.",
            "The positive impact of this news could be felt for years to come."
        ],
        "negative": [
            "The concerning nature of this situation requires careful attention moving forward.",
            "These developments raise serious questions that will need to be addressed soon.",
            "The negative implications of this news could be far-reaching if not properly managed.",
            "This troubling situation may continue to develop in ways that affect many people."
        ],
        "analytical": [
            "Analyzing the data reveals patterns that experts find particularly significant.",
            "The statistical evidence suggests conclusions that merit further investigation.",
            "Researchers point to these findings as potentially transformative in the field.",
            "The analytical perspective on this news highlights several key considerations."
        ],
        "emotional": [
            "The emotional response to this news has been overwhelming across social media.",
            "People everywhere are reacting strongly to these shocking developments.",
            "The surprising nature of this story has captured the public's imagination.",
            "This incredible situation has everyone talking about what might happen next."
        ],
        "tech": [
            "The technological implications of this development could reshape the industry landscape.",
            "Tech experts are closely watching how this innovation might disrupt current paradigms.",
            "This advancement represents a potential turning point in how technology evolves.",
            "The tech community is already speculating about the next developments in this space."
        ],
        "business": [
            "Market analysts are carefully evaluating how this news will affect related investments.",
            "The business impact could extend throughout the industry and related sectors.",
            "Investors are repositioning in response to these significant market developments.",
            "Economic experts suggest this could influence broader market trends moving forward."
        ],
        "entertainment": [
            "Fans and critics alike are discussing what this means for the entertainment industry.",
            "Social media is buzzing with reactions to this major entertainment news.",
            "This could change the trajectory of careers and projects throughout the industry.",
            "Entertainment insiders suggest this is just the beginning of a larger story."
        ],
        "sports": [
            "Sports analysts are debating the long-term impact this will have on the game.",
            "This development could change the competitive landscape for the entire season.",
            "Fans across the world are reacting to this major sports news.",
            "The ripple effects of this sports development will be felt throughout the league."
        ],
        "neutral": [
            "The significance of this news extends beyond the immediate details.",
            "Context is important when considering the broader implications of this story.",
            "Looking at the bigger picture helps understand why this news matters.",
            "There are several factors that make this development noteworthy."
        ]
    }
    
    # Fallback to neutral if primary tone doesn't have templates
    templates = emphasis_templates.get(primary_tone, emphasis_templates["neutral"])
    
    # Select a random template
    emphasis = random.choice(templates)
    
    return emphasis


def generate_youtube_news_script(article_content, article_title="", source_name="", word_limit=300):
    """
    Generate a complete YouTube-style news script based on article content.
    
    Args:
        article_content (str): The content of the article
        article_title (str): The title of the article
        source_name (str): The name of the source
        word_limit (int): Maximum word limit for the generated script
        
    Returns:
        dict: Generated script and analysis info
    """
    # Analyze the tone of the article
    tone_analysis = analyze_article_tone(article_content, article_title)
    
    # Extract key points from the article
    key_points = extract_key_points(article_content, max_points=5)
    
    # Generate script components
    intro = generate_youtube_intro(tone_analysis, article_title, source_name)
    points_section = format_key_points(key_points, tone_analysis) if key_points else ""
    emphasis = generate_emphasis_section(tone_analysis, article_content)
    outro = generate_youtube_outro(tone_analysis, article_title)
    
    # Combine components into a complete script
    script_parts = [
        intro,
        points_section,
        emphasis,
        outro
    ]
    
    script = "\n\n".join(filter(None, script_parts))
    
    # Ensure the script respects the word limit
    words = script.split()
    if len(words) > word_limit:
        script = ' '.join(words[:word_limit]) + "..."
    
    return {
        "script": script,
        "word_count": len(script.split()),
        "tone_analysis": tone_analysis,
        "title": article_title
    }


# Example usage
if __name__ == "__main__":
    sample_article = """
    Scientists have discovered a new species of deep-sea fish that can survive at extreme depths. 
    The discovery was made during an expedition to the Mariana Trench, the deepest part of the world's oceans.
    The fish, named Pseudoliparis swirei, can survive at depths of up to 8,000 meters below the surface.
    
    Researchers were surprised by the fish's unique adaptations, including a specialized enzyme system that allows it to function under immense pressure.
    "This discovery challenges our understanding of the limits of vertebrate life," said Dr. Jane Smith, lead researcher on the expedition.
    
    The findings, published in the journal Nature, could have implications for understanding how life might exist in extreme environments on other planets.
    """
    
    article_title = "New Deep-Sea Fish Species Discovered in Mariana Trench"
    source_name = "Marine Biology Institute"
    
    # Generate a YouTube news script
    result = generate_youtube_news_script(sample_article, article_title, source_name)
    
    print("Tone Analysis:")
    print(f"Primary Tone: {result['tone_analysis']['primary_tone']}")
    print(f"Secondary Tone: {result['tone_analysis']['secondary_tone']}")
    print(f"Content Category: {result['tone_analysis']['content_category']}")
    print("\nGenerated YouTube Script:")
    print(result['script'])
    print(f"\nWord Count: {result['word_count']}")


def wrap_script_with_ssml(script_text, default_rate="medium", default_pitch="0%"):
    """
    Wraps a plain script with basic SSML prosody, structure, and pauses.
    
    Args:
        script_text (str): The raw script to enhance
        default_rate (str): SSML rate (e.g. "medium", "slow")
        default_pitch (str): SSML pitch (e.g. "0%", "-2%")
    
    Returns:
        str: SSML-enhanced version of the script
    """
    # Break script into paragraphs
    paragraphs = script_text.strip().split("\n\n")
    
    ssml_parts = ['<speak>']
    
    for para in paragraphs:
        # Slight pause between paragraphs
        ssml_parts.append('<p>')
        
        # Wrap paragraph with prosody for tone control
        ssml_parts.append(f'<prosody rate="{default_rate}" pitch="{default_pitch}">')
        
        # Add a pause after bullet lists
        if para.strip().startswith("•"):
            lines = para.splitlines()
            for line in lines:
                clean = line.lstrip("•").strip()
                ssml_parts.append(f'<s>{clean}</s><break time="300ms"/>')
        else:
            ssml_parts.append(f"{para.strip()}")
        
        ssml_parts.append('</prosody>')
        ssml_parts.append('</p>')
    
    ssml_parts.append('</speak>')
    return "\n".join(ssml_parts)
