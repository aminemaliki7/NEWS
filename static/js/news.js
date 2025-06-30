// Global variables
let articles = [];
let currentCategory = localStorage.getItem('lastCategory') || 'general';
// currentLanguage is primarily for the news fetching API, audio language is handled per article.
let currentLanguage = 'en'; // Keep for news fetching API, but not for audio TTS language parameter.
let currentQuery = '';
let siteLanguage = 'en'; // Force English for general interface texts
let darkMode = localStorage.getItem('darkMode') === 'true';

// Audio state
let activeAudio = null;
let currentPlayButton = null;
let currentArticleIndex = null;
let audioCache = new Map(); // Cache for faster audio loading

// DOM elements
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const newsList = document.getElementById('newsList');
const newsTemplate = document.getElementById('newsArticleTemplate');

// Language translations - Only keep English for UI texts, but audio can be multi-language
const translations = {
    en: {
        title: "📰 News Reader",
        search: "Search keywords...",
        searchBtn: "Apply Filters",
        categories: {
            general: "General",
            world: "World",
            nation: "Nation",
            business: "Business",
            technology: "Technology",
            sports: "Sports",
            health: "Health",
            entertainment: "Entertainment",
            Fashion: "Fashion" // Added Fashion to translations
        },
        noNews: "No news found for",
        tryDifferent: "Try a different keyword or category.",
        unknownSource: "Unknown Source",
        unknownDate: "Unknown Date",
        yesterday: "Yesterday",
        daysAgo: "days ago",
        readFull: "Read article",
        listen: "Listen", // This will be replaced by play/pause icons
        selectVoice: "Select Voice", // Not explicitly used in this HTML version, but good to keep
        darkMode: "Dark Mode",
        lightMode: "Light Mode",
        language: "Language", // Not explicitly used in this HTML version, but good to keep
        noDescription: "No description available.",
        noText: "This article does not contain any usable text.",
        audioFailed: "Failed to generate audio.",
        audioError: "An error occurred during voice generation.",
        audioLoadError: "Error loading audio. Please try again.",
        loading: "Loading...",
        error: "An error occurred. Please try again later."
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Apply saved preferences
    document.getElementById('category').value = currentCategory;

    // Initialize theme and language
    initializeTheme();
    updateInterfaceLanguage(); // Call directly to set English texts
    addThemeControl();
    updateCurrentDate();
    setupEventListeners();
    loadNews();
});

// Event listeners
function setupEventListeners() {
    document.querySelectorAll('.category-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.category-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            localStorage.setItem('lastCategory', currentCategory);
            stopActiveAudio();
            loadNews();
        });
    });

    document.getElementById('searchBtn').addEventListener('click', () => {
        currentQuery = document.getElementById('searchQuery').value;
        currentCategory = document.getElementById('category').value;
        stopActiveAudio();
        loadNews();
    });

    document.getElementById('searchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') document.getElementById('searchBtn').click();
    });

    document.getElementById('searchQuery').addEventListener('input', debounce(() => {
        currentQuery = document.getElementById('searchQuery').value;
        loadNews();
    }, 600));
}

function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
    };
}

function updateCurrentDate() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDateDisplay').textContent = now.toLocaleDateString('en-US', options); // Force en-US locale
}

// Theme Functions
function initializeTheme() {
    if (darkMode) {
        document.body.classList.add('dark-mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        document.documentElement.setAttribute('data-bs-theme', 'light');
    }
}

function addThemeControl() {
    const header = document.querySelector('.container-fluid') || document.body;
    const controlsHTML = `
        <div class="theme-controls d-flex justify-content-between align-items-center mb-3 px-3" style="width: 100%;">
            <div class="theme-toggle">
                <button id="themeToggle" class="btn btn-outline-secondary btn-sm">
                    <span class="theme-icon">${darkMode ? '☀️' : '🌙'}</span>
                    <span class="theme-text">${translations.en[darkMode ? 'lightMode' : 'darkMode']}</span>
                </button>
            </div>

            <div class="newsletter-subscribe">
                <button id="newsletterBtn" class="btn btn-outline-primary btn-sm">
                    Newsletter
                </button>
            </div>
        </div>
    `;

    if (!document.getElementById('themeToggle')) {
        if (header.firstChild) {
            header.insertAdjacentHTML('afterbegin', controlsHTML);
        } else {
            header.innerHTML = controlsHTML + header.innerHTML;
        }

        document.getElementById('themeToggle').addEventListener('click', toggleTheme);
        document.getElementById('newsletterBtn').addEventListener('click', openNewsletterPopup);
    }
}

function openNewsletterPopup() {
    const modal = new bootstrap.Modal(document.getElementById('newsletterModal'));
    modal.show();
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('newsletterForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const email = document.getElementById('newsletterEmail').value.trim();
            if (!email || !email.includes('@')) {
                alert('Please enter a valid email address.');
                return;
            }

            const categories = [];
            document.querySelectorAll('#newsletterForm input[type="checkbox"]:checked').forEach(checkbox => {
                categories.push(checkbox.value);
            });

            fetch('/api/newsletter-subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    categories: categories
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Subscription failed: ' + data.error);
                } else {
                    alert('Thank you for subscribing! 📬');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('newsletterModal'));
                    modal.hide();
                    form.reset();
                }
            })
            .catch(err => {
                console.error('Subscription error:', err);
                alert('An error occurred. Please try again later.');
            });
        });
    }
});

function toggleTheme() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode.toString());
    initializeTheme();

    const themeButton = document.getElementById('themeToggle');
    const themeIcon = themeButton.querySelector('.theme-icon');
    const themeText = themeButton.querySelector('.theme-text');

    if (themeIcon) themeIcon.textContent = darkMode ? '☀️' : '🌙';
    if (themeText) themeText.textContent = translations.en[darkMode ? 'lightMode' : 'darkMode'];
}

// Simplified language update function, always using English for UI
function updateInterfaceLanguage() {
    const t = translations.en; // Always use English translations for UI

    // Update title
    const titleElement = document.querySelector('.journal-title'); // Corrected selector for H1
    if (titleElement) titleElement.textContent = t.title;

    // Update search placeholder
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) searchInput.placeholder = t.search;

    // Update search button
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) searchBtn.textContent = t.searchBtn;

    // Update category links
    document.querySelectorAll('.category-link').forEach(link => {
        const category = link.dataset.category;
        if (t.categories[category]) {
            link.textContent = t.categories[category];
        }
    });

    // Language label and select are removed from HTML, so no need to hide/remove them here.
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
    const t = translations.en; // Always use English translations
    emptyState.textContent = `😕 ${t.noNews} "${currentQuery || currentCategory}". ${t.tryDifferent}`;
}

function hideStates() {
    loadingIndicator.classList.add('d-none');
    emptyState.classList.add('d-none');
    errorState.classList.add('d-none');
}

async function loadNews() {
    showLoading();
    try {
        const params = new URLSearchParams({ category: currentCategory, language: currentLanguage }); // currentLanguage defaults to 'en' for news API
        if (currentQuery) params.append('query', currentQuery);
        const response = await fetch(`/api/news?${params}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        articles = data.articles || [];
        if (!articles.length) return showEmpty();
        
        displayNews(articles);  // Render articles

        setupCommentForms();    // Load comments for each article ⬅️ VERY IMPORTANT

        hideStates();
    } catch (error) {
        console.error('Error loading news:', error);
        showError(error.message);
    }
}

// Add CSS styles for full-width articles
function addFullWidthArticleStyles() {
    if (!document.getElementById('fullWidthArticleStyles')) {
        const style = document.createElement('style');
        style.id = 'fullWidthArticleStyles';
        style.textContent = `
            .full-width-article {
                transition: all 0.3s ease;
            }
            
            .full-width-article .row {
                margin: 0;
            }
            
            .full-width-article .article-image {
                border-radius: 8px !important;
                height: 200px !important;
                object-fit: cover !important;
            }
            
            .full-width-article .article-title {
                font-size: 1.25rem !important;
                font-weight: 600 !important;
                margin-bottom: 0.5rem !important;
                min-height: auto !important;
            }
            
            .full-width-article .article-description {
                font-size: 1rem !important;
                line-height: 1.5 !important;
                margin-bottom: 1rem !important;
                min-height: auto !important;
            }
            
            @media (max-width: 768px) {
                .full-width-article .row {
                    flex-direction: column !important;
                }
                
                .full-width-article .article-image {
                    height: 150px !important;
                    margin-bottom: 1rem;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Check if article should be full width
function shouldArticleBeFullWidth(index, totalArticles) {
    const isLastArticle = index === totalArticles - 1;
    
    // Get current screen size
    const screenWidth = window.innerWidth;
    let articlesPerRow;
    
    if (screenWidth >= 992) { // lg breakpoint
        articlesPerRow = 3;
    } else if (screenWidth >= 768) { // md breakpoint
        articlesPerRow = 2;
    } else { // sm and below
        articlesPerRow = 1;
        return false; // No need for full width on mobile
    }
    
    const remainder = totalArticles % articlesPerRow;
    
    // Make last article full width if it would be alone in the row
    return isLastArticle && remainder === 1 && totalArticles > articlesPerRow;
}

// Make article full width
function makeArticleFullWidth(articleElement) {
    const articleDiv = articleElement.querySelector('.news-article');
    if (!articleDiv) return;
    
    // Change to full width
    articleDiv.className = 'news-article col-12 mb-3 d-flex';
    
    const card = articleDiv.querySelector('.card');
    if (!card) return;
    
    card.classList.add('full-width-article');
    
    // Get all the elements we need to restructure
    const elements = {
        audioLoading: card.querySelector('.audio-loading'),
        title: card.querySelector('.article-title'),
        source: card.querySelector('.article-source'),
        image: card.querySelector('.article-image'),
        description: card.querySelector('.article-description'),
        listenLabel: card.querySelector('.text-muted.small.mb-1'),
        actions: card.querySelector('.article-actions'),
        comments: card.querySelector('.article-comments')
    };
    
    // Create new horizontal layout
    card.innerHTML = `
        <div class="row g-0 h-100 w-100">
            <div class="col-md-4 d-flex align-items-center p-2">
                ${elements.audioLoading ? elements.audioLoading.outerHTML : ''}
                ${elements.image ? elements.image.outerHTML : ''}
            </div>
            <div class="col-md-8 d-flex flex-column justify-content-between p-3">
                <div class="content-section">
                    ${elements.title ? elements.title.outerHTML : ''}
                    ${elements.source ? elements.source.outerHTML : ''}
                    ${elements.description ? elements.description.outerHTML : ''}
                </div>
                <div class="actions-section mt-auto">
                    ${elements.listenLabel ? elements.listenLabel.outerHTML : ''}
                    ${elements.actions ? elements.actions.outerHTML : ''}
                    ${elements.comments ? elements.comments.outerHTML : ''}
                </div>
            </div>
        </div>
    `;
}

// Enhanced displayNews function with full-width last article
function displayNews(articlesData) {
    newsList.innerHTML = '';
    
    articlesData.forEach((article, index) => {
        const articleElement = createArticleElement(article, index);
        
        // Check if this is the last article and if it would be alone in its row
        const isLastArticle = index === articlesData.length - 1;
        const screenWidth = window.innerWidth;
        
        let articlesPerRow;
        if (screenWidth >= 992) { // lg breakpoint
            articlesPerRow = 3;
        } else if (screenWidth >= 768) { // md breakpoint
            articlesPerRow = 2;
        } else { // sm and below
            articlesPerRow = 1;
        }
        
        const remainder = articlesData.length % articlesPerRow;
        
        // If it's the last article and it would be alone (remainder = 1), make it full width
        if (isLastArticle && remainder === 1 && articlesData.length > articlesPerRow) {
            // Modify the article element classes for full width
            const articleDiv = articleElement.querySelector('.news-article');
            if (articleDiv) {
                // Just change the column classes to make it full width, keep everything else the same
                articleDiv.className = 'news-article col-12 mb-3 d-flex';
            }
        }
        
        newsList.appendChild(articleElement);
    });
}

function createArticleElement(article, index) {
    const template = newsTemplate.content.cloneNode(true);
    const t = translations.en; // Always use English translations for UI text within the article card

    template.querySelector('.article-title').textContent = article.title || 'No Title';
    template.querySelector('.source-name').textContent = article.source?.name || t.unknownSource;
    template.querySelector('.publish-date').textContent = formatDate(article.publishedAt);
    template.querySelector('.article-description').textContent = article.description || t.noDescription;

    const imageEl = template.querySelector('.article-image');
    imageEl.src = article.image?.startsWith('http') ? article.image : 'https://placehold.co/600x400/cccccc/333333?text=No+Image';
    imageEl.alt = article.title || 'Image not available';
    imageEl.onerror = () => {
        imageEl.src = 'https://placehold.co/600x400/cccccc/333333?text=No+Image';
        imageEl.alt = 'Image not available';
        imageEl.onerror = null;
    };

    const readBtn = template.querySelector('.article-read-btn');
    readBtn.href = article.url;
    readBtn.title = t.readFull; // Using title for tooltip

    const listenBtn = template.querySelector('.article-listen-btn');
    listenBtn.dataset.index = index;
    listenBtn.innerHTML = '▶︎ '; // Ensure space for icon
    listenBtn.title = t.listen; // Set tooltip
    listenBtn.onclick = () => listenToSummary(index);

    const voiceSelect = template.querySelector('.voice-select');
    voiceSelect.id = `voice-select-${index}`;
    voiceSelect.dataset.articleIndex = index;
    voiceSelect.value = localStorage.getItem('lastVoice') || 'en-CA-LiamNeural'; // Default to an English voice

    const progress = template.querySelector('.audio-progress');
    progress.style.display = 'none';
    progress.value = 0;

    // Generate unique article_id based on URL (safe for Firestore)
    const articleId = btoa(article.url || article.title || article.publishedAt || `${index}`);
    template.querySelector('.article-comments').dataset.articleId = articleId;

    return template;
}

function stopActiveAudio() {
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        if (currentPlayButton) {
            currentPlayButton.innerHTML = '▶︎ '; // Reset to play icon
            currentPlayButton.disabled = false;
        }

        if (currentArticleIndex !== null) {
            const card = document.querySelector(`.article-listen-btn[data-index="${currentArticleIndex}"]`)?.closest('.card');
            if (card) {
                const loadingUI = card.querySelector('.audio-loading');
                const progressBar = card.querySelector('.audio-progress');
                if (loadingUI) loadingUI.classList.add('d-none');
                if (progressBar) progressBar.style.display = 'none';
            }
        }

        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
    }
}

document.addEventListener('change', function(e) {
    if (e.target.classList.contains('voice-select')) {
        const articleIndex = parseInt(e.target.dataset.articleIndex);
        const newVoice = e.target.value;
        localStorage.setItem('lastVoice', newVoice); // Save the last selected voice

        console.log(`Voice changed for article ${articleIndex}: ${newVoice}`);

        // Invalidate cache for this article with the new voice
        const cacheKey = `${articleIndex}-${newVoice}`;
        audioCache.delete(cacheKey);

        // If the voice was changed for the currently playing/active article,
        // stop it and try to regenerate/play with the new voice.
        if (currentArticleIndex === articleIndex) {
            console.log('Voice changed for active article, regenerating immediately...');

            const wasPlaying = activeAudio && !activeAudio.paused; // Check if it was playing

            stopActiveAudio(); // Stop current audio
            // Start playing the new audio immediately if it was previously playing
            listenToSummary(articleIndex, wasPlaying);
        }
    }
});

function formatDate(dateString) {
    const t = translations.en; // Always use English translations
    if (!dateString) return t.unknownDate;

    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return t.yesterday;
    if (diffDays < 7) return `${diffDays} ${t.daysAgo}`;

    return date.toLocaleDateString('en-US'); // Force en-US locale
}

// UPDATED FUNCTION: Use description directly instead of fetching full content
async function listenToSummary(index, autoPlay = true) {
    const article = articles[index];
    const voiceSelect = document.getElementById(`voice-select-${index}`);
    const selectedVoice = voiceSelect?.value;
    const listenBtn = document.querySelector(`.article-listen-btn[data-index="${index}"]`);
    const card = listenBtn.closest('.card');
    const loadingUI = card.querySelector('.audio-loading');
    const progressBar = card.querySelector('.audio-progress');
    const t = translations[siteLanguage];

    if (!article || !selectedVoice || !listenBtn) return;

    // Stop any other playing audio first (only one at a time)
    if (activeAudio && currentArticleIndex !== index) {
        stopActiveAudio();
    }

    // Handle play/pause for same article
    if (activeAudio && currentArticleIndex === index) {
        if (activeAudio.paused) {
            activeAudio.play();
            listenBtn.innerHTML = '‖';
        } else {
            activeAudio.pause();
            listenBtn.innerHTML = '▶︎';
        }
        return;
    }

    // Check cache first for faster loading
    const cacheKey = `${index}-${selectedVoice}`;
    const cachedAudioUrl = audioCache.get(cacheKey);

    if (cachedAudioUrl) {
        console.log('Using cached audio for faster loading');
        playAudio(cachedAudioUrl, index, listenBtn, loadingUI, progressBar, autoPlay);
        return;
    }

    stopActiveAudio();
    currentArticleIndex = index;

    loadingUI.classList.remove('d-none');
    progressBar.style.display = 'block';
    progressBar.value = 0;
    listenBtn.disabled = true;
    listenBtn.innerHTML = '⏳';

    card.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const langCode = selectedVoice.split('-')[0];

    // SIMPLIFIED: Use description directly from GNews API
    const description = article.description || article.title || '';

    if (!description.trim()) {
        alert(t.noText);
        resetAudioUI(listenBtn, loadingUI, progressBar);
        return;
    }

    try {
        let summaryText = description;

        // Translate if needed (only if not English)
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

        // Generate TTS directly from description
        const ttsRes = await fetch('/api/news/summary-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: summaryText, // Changed from 'content' to 'description'
                title: article.title,
                voice_id: selectedVoice,
                speed: 1.0,
                depth: 1
            })
        });

        const result = await ttsRes.json();

        if (result.audio_url) {
            audioCache.set(cacheKey, result.audio_url);

            if (audioCache.size > 20) {
                const firstKey = audioCache.keys().next().value;
                audioCache.delete(firstKey);
            }

            playAudio(result.audio_url, index, listenBtn, loadingUI, progressBar, autoPlay);
        } else {
            alert(t.audioFailed);
            resetAudioUI(listenBtn, loadingUI, progressBar);
        }

    } catch (err) {
        console.error(err);
        alert(t.audioError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
    }
}

function playAudio(audioUrl, index, listenBtn, loadingUI, progressBar, autoPlay = true) {
    const t = translations.en;

    // Si un autre audio joue, l'arrêter
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        resetAudioUI(currentPlayButton, null, null);
    }

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

    currentPlayButton = listenBtn;
    currentArticleIndex = index;

    // Préparer l'interface
    loadingUI.classList.add('d-none');
    listenBtn.disabled = false;

    // iOS nécessite une interaction utilisateur : instancier l'audio DANS le clic
    if (isIOS || !autoPlay) {
        listenBtn.innerHTML = '🔊 Tap to play';
        listenBtn.onclick = () => {
            activeAudio = new Audio(audioUrl);

            // Ajouter les events une fois l'audio créé
            setupAudioEvents(activeAudio, listenBtn, loadingUI, progressBar);

            activeAudio.play().then(() => {
                listenBtn.innerHTML = '‖';
            }).catch(err => {
                console.error('Playback error:', err);
                alert(t.audioLoadError);
            });

            // Gestion pause/reprise
            listenBtn.onclick = () => {
                if (activeAudio.paused) {
                    activeAudio.play();
                    listenBtn.innerHTML = '‖';
                } else {
                    activeAudio.pause();
                    listenBtn.innerHTML = '▶︎';
                }
            };
        };
    } else {
        // Desktop : autoplay autorisé
        activeAudio = new Audio(audioUrl);
        setupAudioEvents(activeAudio, listenBtn, loadingUI, progressBar);
        activeAudio.play().then(() => {
            listenBtn.innerHTML = '‖';
        }).catch(err => {
            console.warn('Autoplay blocked, switching to manual:', err);
            listenBtn.innerHTML = '🔊 Tap to play';
            listenBtn.onclick = () => {
                activeAudio.play().then(() => {
                    listenBtn.innerHTML = '‖';
                }).catch(err => {
                    alert(t.audioLoadError);
                });
            };
        });
    }
}

function setupAudioEvents(audio, listenBtn, loadingUI, progressBar) {
    const t = translations.en;

    audio.ontimeupdate = () => {
        if (progressBar && audio.duration) {
            progressBar.value = (audio.currentTime / audio.duration) * 100;
        }
    };

    audio.onended = () => {
        resetAudioUI(listenBtn, loadingUI, progressBar);
        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
    };

    audio.onerror = () => {
        console.error("Audio error:", audio.error);
        alert(t.audioLoadError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
    };
}

function resetAudioUI(listenBtn, loadingUI, progressBar) {
    if (loadingUI) loadingUI.classList.add('d-none');
    if (progressBar) progressBar.style.display = 'none';
    if (listenBtn) {
        listenBtn.disabled = false;
        listenBtn.innerHTML = '▶︎ '; // Reset to play icon
    }
}

// Function to highlight the currently playing article (optional, but good for UX)
function highlightCurrentArticle(index) {
    document.querySelectorAll('.card').forEach(card => {
        card.classList.remove('border-primary', 'shadow-lg');
        card.style.transform = '';
    });

    const currentCard = document.querySelector(`.article-listen-btn[data-index="${index}"]`)?.closest('.card');
    if (currentCard) {
        currentCard.classList.add('border-primary', 'shadow-lg');
        currentCard.style.transform = 'scale(1.02)';
        currentCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Load comments for one article - FIXED VERSION
function loadComments(articleId, container) {
    fetch(`/api/article-comments?article_id=${encodeURIComponent(articleId)}`)
        .then(response => response.json())
        .then(data => {
            const commentsList = container.querySelector('.comments-list');
            commentsList.innerHTML = '';

            if (data.comments && data.comments.length === 0) {
                commentsList.innerHTML = '<p class="text-muted text-center py-3" style="font-size: 0.8em;">No comments yet. Be the first to comment!</p>';
            } else if (data.comments) {
                data.comments.forEach(comment => {
                    const commentEl = document.createElement('div');
                    commentEl.className = 'comment text-start mb-2 px-2';
                    
                    // Handle timestamp properly
                    let formattedDate = 'Just now';
                    if (comment.timestamp) {
                        try {
                            // Handle Firestore timestamp format
                            const date = new Date(comment.timestamp.seconds ? comment.timestamp.seconds * 1000 : comment.timestamp);
                            formattedDate = date.toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        } catch (e) {
                            console.warn('Error parsing timestamp:', e);
                        }
                    }
                    
                    commentEl.innerHTML = `
                        <span class="fw-bold me-1 comment-nickname" style="font-size: 0.8em;">${escapeHtml(comment.nickname)}:</span>
                        <span class="comment-text text-dark" style="font-size: 0.8em;">${escapeHtml(comment.comment)}</span>
                        <br><small class="text-muted" style="font-size: 0.7em;">${formattedDate}</small>
                    `;
                    commentsList.appendChild(commentEl);
                });
            }
        })
        .catch(err => {
            console.error('Error loading comments:', err);
            const commentsList = container.querySelector('.comments-list');
            commentsList.innerHTML = '<p class="text-muted text-center py-3" style="font-size: 0.8em;">Error loading comments.</p>';
        });
}

// Helper function to escape HTML and prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Setup comment form submit - IMPROVED VERSION (without success message)
function setupCommentForms() {
    document.querySelectorAll('.article-comments').forEach(container => {
        const articleId = container.dataset.articleId;
        const form = container.querySelector('.comment-form');

        // Load comments on page load
        loadComments(articleId, container);

        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        newForm.addEventListener('submit', e => {
            e.preventDefault();

            const nickname = newForm.nickname.value.trim();
            const commentText = newForm.comment.value.trim();
            const submitBtn = newForm.querySelector('button[type="submit"]');

            if (!commentText) {
                alert('Please enter a comment before posting.');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Posting...';

            // Build payload
            const payload = {
                article_id: articleId,
                comment_text: commentText
            };

            if (nickname) {
                payload.nickname = nickname;  // only send if filled
            }

            fetch('/api/article-comment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                newForm.reset();
                loadComments(articleId, container);
            })
            .catch(err => {
                console.error('Error posting comment:', err);
                alert('Error posting comment. Please try again.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Post';
            });
        });
    });
}

// Add window resize listener to recalculate layout when screen size changes
window.addEventListener('resize', debounce(() => {
    if (articles.length > 0) {
        displayNews(articles);
        setupCommentForms(); // Re-setup comment forms after re-rendering
    }
}, 300));

