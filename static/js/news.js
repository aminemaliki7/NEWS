// Global variables
let articles = [];
let currentCategory = 'general';
let currentLanguage = 'en';
let currentQuery = '';

// Global variable to keep track of the currently playing audio and its associated button
let activeAudio = null;
let currentPlayButton = null;

// DOM elements
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const newsList = document.getElementById('newsList');
const newsTemplate = document.getElementById('newsArticleTemplate');

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
    // Set initial icon to 'Play'
    listenBtn.innerHTML = '▶︎ ';
    listenBtn.onclick = () => listenToSummary(index); // Assign click handler

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
    const listenBtn = document.querySelector(`.article-listen-btn[data-index="${index}"]`);

    if (!article || !selectedVoice || !listenBtn) {
        console.warn("Missing article, voice, or listen button.");
        return;
    }

    const card = listenBtn.closest('.card'); // Get the parent card for loading UI
    const loadingUI = card.querySelector('.audio-loading');

    // Scenario 1: User clicks the currently playing button (toggle play/pause)
    if (activeAudio && currentPlayButton === listenBtn) {
        if (activeAudio.paused) {
            activeAudio.play();
            listenBtn.innerHTML = '‖ '; // Change to pause icon
        } else {
            activeAudio.pause();
            listenBtn.innerHTML = '▶︎ '; // Change to play icon
        }
        return; // Exit, as we've handled the toggle
    }

    // Scenario 2: User clicks a *different* button OR no audio is currently playing.
    // Stop any existing audio and reset its button before playing new audio.
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        if (currentPlayButton) {
            currentPlayButton.innerHTML = '▶︎ '; // Reset the previously playing button
        }
        activeAudio = null; // Clear active audio
        currentPlayButton = null; // Clear active button
    }

    // Show loading indicator for the new audio
    loadingUI.classList.remove('d-none');
    listenBtn.disabled = true; // Disable button during loading

    const langCode = selectedVoice.split('-')[0];
    const rawText = article.content || article.description || article.full_content || article.title || '';

    if (!rawText.trim()) {
        alert("This article does not contain any usable text.");
        loadingUI.classList.add('d-none');
        listenBtn.disabled = false;
        return;
    }

    try {
        // Optimize content for voice if not already done or if too short
        if (!article.voiceOptimizedContent || article.voiceOptimizedContent.trim().length < 30) {
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
        }

        let summaryText = article.voiceOptimizedContent;

        // Translate content if the selected language is not English
        if (langCode !== 'en') {
            const res = await fetch('/api/news/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: summaryText, target_language: langCode })
            });
            const result = await res.json();
            if (result.translated_text?.trim()) {
                summaryText = result.translated_text.trim();
            }
        }

        // Generate audio from the (optimized and translated) summary text
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
            // Create and play new audio
            activeAudio = new Audio(result.audio_url);
            currentPlayButton = listenBtn; // Set the current button as active

            activeAudio.play();
            listenBtn.innerHTML = '‖ '; // Change to pause icon
            listenBtn.disabled = false; // Enable button now that audio is playing

            // Event listener for when the audio finishes playing
            activeAudio.onended = () => {
                loadingUI.classList.add('d-none'); // Hide loading UI
                listenBtn.innerHTML = '▶︎ '; // Reset button to play icon
                activeAudio = null; // Clear active audio
                currentPlayButton = null; // Clear active button
            };
        } else {
            alert("Failed to generate audio.");
            loadingUI.classList.add('d-none');
            listenBtn.disabled = false;
        }

    } catch (err) {
        console.error(err);
        alert("An error occurred during voice generation.");
        loadingUI.classList.add('d-none');
        listenBtn.disabled = false;
    }
}

// Expose for debugging if needed
window.articles = articles;