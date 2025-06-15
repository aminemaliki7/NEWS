// Global variables
let articles = [];
let currentCategory = 'general';
let currentLanguage = 'en';
let currentQuery = '';

// DOM elements
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const newsList = document.getElementById('newsList');
const newsTemplate = document.getElementById('newsArticleTemplate');

// Keep track of active audio elements for stopping
let activeAudio = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentDate();
    setupEventListeners();
    loadNews(); // Load initial news
});

// Set up event listeners
function setupEventListeners() {
    // Category navigation
    document.querySelectorAll('.category-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.category-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            loadNews();
        });
    });

    // Search functionality
    document.getElementById('searchBtn').addEventListener('click', function() {
        currentQuery = document.getElementById('searchQuery').value;
        currentCategory = document.getElementById('category').value;
        currentLanguage = document.getElementById('language').value;
        loadNews();
    });

    document.getElementById('searchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });
}

function updateCurrentDate() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDateDisplay').textContent = now.toLocaleDateString('en-US', options);
}

function showLoading() {
    loadingIndicator.classList.remove('d-none');
    emptyState.classList.add('d-none');
    errorState.classList.add('d-none');
    newsList.innerHTML = '';
}

function showError(message = 'An error occurred. Please try again later.') {
    loadingIndicator.classList.add('d-none');
    emptyState.classList.add('d-none');
    errorState.classList.remove('d-none');
    errorState.textContent = message;
}

function showEmpty() {
    loadingIndicator.classList.add('d-none');
    errorState.classList.add('d-none');
    emptyState.classList.remove('d-none');
}

function hideStates() {
    loadingIndicator.classList.add('d-none');
    emptyState.classList.add('d-none');
    errorState.classList.add('d-none');
}

async function loadNews() {
    showLoading();
    try {
        const params = new URLSearchParams({ category: currentCategory, language: currentLanguage });
        if (currentQuery) params.append('query', currentQuery);
        const response = await fetch(`/api/news?${params}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        articles = data.articles || [];
        if (articles.length === 0) {
            showEmpty();
            return;
        }
        displayNews(articles);
        hideStates();
    } catch (error) {
        console.error('Error loading news:', error);
        showError(error.message);
    }
}

function displayNews(articlesData) {
    newsList.innerHTML = '';
    articlesData.forEach((article, index) => {
        const articleElement = createArticleElement(article, index);
        newsList.appendChild(articleElement);
    });
}

function createArticleElement(article, index) {
    const template = newsTemplate.content.cloneNode(true);
    template.querySelector('.article-title').textContent = article.title || 'No Title';
    template.querySelector('.source-name').textContent = article.source?.name || 'Unknown Source';
    template.querySelector('.publish-date').textContent = formatDate(article.publishedAt);
    template.querySelector('.article-description').textContent = article.description || 'No description available.';
    
    const imageEl = template.querySelector('.article-image');
    if (article.image && article.image.startsWith('http')) {
        imageEl.src = article.image;
        imageEl.alt = article.title;
        imageEl.style.display = '';
        imageEl.onerror = () => {
            imageEl.src = 'https://placehold.co/600x400/cccccc/333333?text=No+Image';
            imageEl.alt = 'Image not available';
            imageEl.onerror = null;
        };
    } else {
        imageEl.src = 'https://placehold.co/600x400/cccccc/333333?text=No+Image';
        imageEl.alt = 'Image not available';
        imageEl.style.display = '';
    }
    
    template.querySelector('.article-read-btn').href = article.url;
    
    const listenBtn = template.querySelector('.article-listen-btn');
    listenBtn.dataset.index = index;
    listenBtn.onclick = () => listenToSummary(index);
    
    const voiceSelect = template.querySelector('.voice-select');
    voiceSelect.id = `voice-select-${index}`;
    voiceSelect.dataset.articleIndex = index;
    
    return template;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown Date';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
}

document.addEventListener('change', function(e) {
    if (e.target.classList.contains('voice-select')) {
        const articleIndex = e.target.dataset.articleIndex;
        console.log(`Voice changed for article ${articleIndex}: ${e.target.value}`);
    }
});

async function listenToSummary(index) {
    const article = articles[index];
    const voiceSelect = document.getElementById(`voice-select-${index}`);
    const selectedVoice = voiceSelect?.value;

    if (!article || !selectedVoice) {
        console.warn("Missing article or voice.");
        return;
    }

    const langCode = selectedVoice.split('-')[0];  // e.g., "en" from "en-CA-LiamNeural"

    // ✅ Step 1: Build fallback text to avoid empty inputs
    const rawText = article.content || article.description || article.full_content || article.title || '';

    if (!rawText.trim()) {
        alert("This article does not contain any usable text.");
        return;
    }

    // ✅ Step 2: Fetch and cache voice-optimized summary if not already present
    if (!article.voiceOptimizedContent || article.voiceOptimizedContent.trim().length < 30) {
        try {
            const res = await fetch('/api/news/voice-optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: rawText,
                    title: article.title || ''
                })
            });

            const result = await res.json();
            article.voiceOptimizedContent = result.optimized_content?.trim() || rawText;
        } catch (err) {
            console.error("Voice optimization failed:", err);
            alert("Could not optimize article for voice. Using fallback.");
            article.voiceOptimizedContent = rawText;
        }
    }

    let summaryText = article.voiceOptimizedContent;

    if (!summaryText.trim()) {
        alert("No summary available for this article.");
        return;
    }

    // ✅ Step 3: Translate if necessary
    if (langCode !== 'en') {
        try {
            const res = await fetch('/api/news/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: summaryText, target_language: langCode })
            });

            const result = await res.json();
            if (result.translated_text?.trim()) {
                summaryText = result.translated_text.trim();
            } else {
                console.warn("Translation returned empty. Using English.");
            }
        } catch (err) {
            console.error("Translation error:", err);
            alert("Error during translation.");
        }
    }

    // ✅ Step 4: Send to TTS
    try {
        const ttsRes = await fetch('/api/news/summary-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: summaryText,
                title: article.title || 'summary',
                voice_id: selectedVoice,
                speed: 1.0,
                depth: 1
            })
        });

        const result = await ttsRes.json();

        if (result.audio_url) {
            const audio = new Audio(result.audio_url);
            audio.play();
            activeAudio = audio;
        } else {
            console.error("TTS generation failed:", result.error);
            alert("Failed to generate audio.");
        }
    } catch (err) {
        console.error("TTS request error:", err);
        alert("An error occurred while generating audio.");
    }
}



// Function to stop audio playback
function stopListening(buttonElement, originalText) {
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        activeAudio = null;
    }
    if (buttonElement) {
        buttonElement.textContent = originalText;
        buttonElement.disabled = false;
        // Restore the original listen function
        const articleIndex = buttonElement.dataset.index;
        buttonElement.onclick = () => listenToSummary(articleIndex);
    }
}




// Expose for debugging if needed
window.articles = articles;