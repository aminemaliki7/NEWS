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
    
    // Inject voting styles
    injectVotingStyles();
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

// Updated createArticleElement function - REPLACE the existing one in your JavaScript file

// FIXED: Update createArticleElement to use correct selector
function createArticleElement(article, index) {
    const template = newsTemplate.content.cloneNode(true);
    const t = translations.en;

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
    readBtn.title = t.readFull;

    const listenBtn = template.querySelector('.article-listen-btn');
    listenBtn.dataset.index = index;
    listenBtn.innerHTML = '▶︎ ';
    listenBtn.title = t.listen;
    listenBtn.onclick = () => listenToSummary(index);

    const voiceSelect = template.querySelector('.voice-select');
    voiceSelect.id = `voice-select-${index}`;
    voiceSelect.dataset.articleIndex = index;
    voiceSelect.value = localStorage.getItem('lastVoice') || 'en-CA-LiamNeural';

    const progress = template.querySelector('.audio-progress');
    progress.style.display = 'none';
    progress.value = 0;

    // Generate unique article_id
    const articleId = btoa(article.url || article.title || article.publishedAt || `${index}`);
    
    // FIXED: Set article ID for the interactions section
    const interactionsSection = template.querySelector('.article-interactions');
    if (interactionsSection) {
        interactionsSection.dataset.articleId = articleId;
    }

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

    // Use description directly from GNews API
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

        // Decide whether to use sync or async TTS based on text length
        const useAsync = summaryText.length > 300; // Use async for longer texts

        if (useAsync) {
            // Use async TTS for longer texts
            await generateAsyncTTS(summaryText, article.title, selectedVoice, index, listenBtn, loadingUI, progressBar, autoPlay, cacheKey);
        } else {
            // Use sync TTS for shorter texts (faster)
            await generateSyncTTS(summaryText, article.title, selectedVoice, index, listenBtn, loadingUI, progressBar, autoPlay, cacheKey);
        }

    } catch (err) {
        console.error(err);
        alert(t.audioError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
    }
}
async function generateAsyncTTS(text, title, voiceId, index, listenBtn, loadingUI, progressBar, autoPlay, cacheKey) {
    const t = translations.en;

    try {
        // Start async TTS task
        const startRes = await fetch('/api/news/summary-audio-async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: text,
                title: title,
                voice_id: voiceId,
                speed: 1.0,
                depth: 1
            })
        });

        const taskInfo = await startRes.json();
        
        if (!taskInfo.task_id) {
            throw new Error('Failed to start audio generation');
        }

        console.log(`Started async TTS task: ${taskInfo.task_id}`);
        
        // Update UI to show we're generating
        listenBtn.innerHTML = '🔄';
        
        // Poll for completion
        const audioUrl = await pollTaskStatus(taskInfo.task_id, progressBar, listenBtn);
        
        if (audioUrl) {
            // Cache the result
            audioCache.set(cacheKey, audioUrl);
            
            // Play the audio
            playAudio(audioUrl, index, listenBtn, loadingUI, progressBar, autoPlay);
        } else {
            throw new Error('Audio generation failed');
        }

    } catch (error) {
        console.error('Async TTS error:', error);
        throw error;
    }
}
async function pollTaskStatus(taskId, progressBar, listenBtn, maxAttempts = 60) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            const statusRes = await fetch(`/api/task-status/${taskId}`);
            const status = await statusRes.json();
            
            console.log(`Task ${taskId} status:`, status.state, `(${status.progress || 0}%)`);
            
            // Update progress bar
            if (progressBar && status.progress) {
                progressBar.value = status.progress;
            }
            
            if (status.state === 'SUCCESS' && status.result?.audio_url) {
                return status.result.audio_url;
            } else if (status.state === 'FAILURE') {
                throw new Error(status.error || 'Task failed');
            }
            
            // Wait before next poll (2 seconds)
            await new Promise(resolve => setTimeout(resolve, 2000));
            
        } catch (error) {
            console.error('Error polling task status:', error);
            if (attempt === maxAttempts - 1) throw error;
        }
    }
    
    throw new Error('Task timeout - audio generation took too long');
}

// Sync TTS generation (for shorter texts)
async function generateSyncTTS(text, title, voiceId, index, listenBtn, loadingUI, progressBar, autoPlay, cacheKey) {
    const ttsRes = await fetch('/api/news/summary-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            description: text,
            title: title,
            voice_id: voiceId,
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
        throw new Error('Failed to generate audio');
    }
}

function playAudio(audioUrl, index, listenBtn, loadingUI, progressBar, autoPlay = true) {
    const t = translations.en;

    // Stop any other playing audio
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        resetAudioUI(currentPlayButton, null, null);
    }

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

    currentPlayButton = listenBtn;
    currentArticleIndex = index;

    // Prepare UI
    loadingUI.classList.add('d-none');
    progressBar.style.display = 'block';
    progressBar.value = 0;
    listenBtn.disabled = false;

    // iOS requires user interaction
    if (isIOS || !autoPlay) {
        listenBtn.innerHTML = '🔊 Tap to play';
        listenBtn.onclick = () => {
            activeAudio = new Audio(audioUrl);
            setupAudioEvents(activeAudio, listenBtn, loadingUI, progressBar);

            activeAudio.play().then(() => {
                listenBtn.innerHTML = '‖';
            }).catch(err => {
                console.error('Playback error:', err);
                alert(t.audioLoadError);
                resetAudioUI(listenBtn, loadingUI, progressBar);
            });

            // Handle pause/resume
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
        // Desktop: autoplay allowed
        activeAudio = new Audio(audioUrl);
        setupAudioEvents(activeAudio, listenBtn, loadingUI, progressBar);
        
        activeAudio.play().then(() => {
            listenBtn.innerHTML = '‖';
            listenBtn.onclick = () => {
                if (activeAudio.paused) {
                    activeAudio.play();
                    listenBtn.innerHTML = '‖';
                } else {
                    activeAudio.pause();
                    listenBtn.innerHTML = '▶︎';
                }
            };
        }).catch(err => {
            console.warn('Autoplay blocked, switching to manual:', err);
            listenBtn.innerHTML = '🔊 Tap to play';
            listenBtn.onclick = () => {
                activeAudio.play().then(() => {
                    listenBtn.innerHTML = '‖';
                }).catch(err => {
                    alert(t.audioLoadError);
                    resetAudioUI(listenBtn, loadingUI, progressBar);
                });
            };
        });
    }
}

function setupAudioEvents(audio, listenBtn, loadingUI, progressBar) {
    const t = translations.en;

    // Track audio progress
    audio.ontimeupdate = () => {
        if (progressBar && audio.duration) {
            const progress = (audio.currentTime / audio.duration) * 100;
            progressBar.value = progress;
        }
    };

    // Handle audio end
    audio.onended = () => {
        resetAudioUI(listenBtn, loadingUI, progressBar);
        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
        
        // Remove highlight from current article
        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('border-primary', 'shadow-lg');
            card.style.transform = '';
        });
    };

    // Handle audio errors
    audio.onerror = () => {
        console.error("Audio error:", audio.error);
        alert(t.audioLoadError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
    };

    // Handle successful load
    audio.onloadstart = () => {
        console.log('Audio loading started');
    };

    audio.oncanplay = () => {
        console.log('Audio ready to play');
        // Highlight the current article
        highlightCurrentArticle(currentArticleIndex);
    };
}

function resetAudioUI(listenBtn, loadingUI, progressBar) {
    if (loadingUI) loadingUI.classList.add('d-none');
    if (progressBar) {
        progressBar.style.display = 'none';
        progressBar.value = 0;
    }
    if (listenBtn) {
        listenBtn.disabled = false;
        listenBtn.innerHTML = '▶︎ ';
        listenBtn.onclick = () => listenToSummary(parseInt(listenBtn.dataset.index));
    }
}

// Function to highlight the currently playing article (optional, but good for UX)
function highlightCurrentArticle(index) {
    // Remove highlight from all articles
    document.querySelectorAll('.card').forEach(card => {
        card.classList.remove('border-primary', 'shadow-lg');
        card.style.transform = '';
    });

    // Highlight current article
    const currentCard = document.querySelector(`.article-listen-btn[data-index="${index}"]`)?.closest('.card');
    if (currentCard) {
        currentCard.classList.add('border-primary', 'shadow-lg');
        currentCard.style.transform = 'scale(1.02)';
        currentCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
async function retryAudioGeneration(index, attempt = 1, maxRetries = 2) {
    if (attempt > maxRetries) {
        throw new Error('Max retries exceeded');
    }

    console.log(`Audio generation attempt ${attempt}/${maxRetries} for article ${index}`);
    
    try {
        await listenToSummary(index);
    } catch (error) {
        console.warn(`Attempt ${attempt} failed:`, error);
        
        if (attempt < maxRetries) {
            // Wait before retry (exponential backoff)
            const delay = Math.pow(2, attempt) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            return retryAudioGeneration(index, attempt + 1, maxRetries);
        } else {
            throw error;
        }
    }
}

// Add performance monitoring
function logAudioPerformance(action, startTime, additionalData = {}) {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    console.log(`Audio ${action} took ${duration.toFixed(2)}ms`, additionalData);
    
    // You could send this data to analytics if needed
    // analytics.track('audio_performance', { action, duration, ...additionalData });
}
// Updated: Handle article like with number-only count
async function handleArticleLike(articleId, likeBtn, likeCountEl) {
    if (likeBtn.classList.contains('loading')) return;
    
    likeBtn.classList.add('loading');
    const heartIcon = likeBtn.querySelector('.heart-icon');
    const isLiked = likeBtn.classList.contains('liked');
    
    try {
        const response = await fetch('/api/article-like', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                article_id: articleId
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Update UI with Instagram-style animation
        if (result.user_liked) {
            likeBtn.classList.add('liked');
        } else {
            likeBtn.classList.remove('liked');
        }
        
        // Update like count - JUST THE NUMBER
        const likeCount = result.likes || 0;
        if (likeCountEl) {
            likeCountEl.textContent = likeCount;
        }
        
        // Show/hide like count text
        const likeText = likeCountEl ? likeCountEl.parentElement : null;
        if (likeText) {
            if (likeCount === 0) {
                likeText.style.display = 'none';
            } else {
                // Just show the number, no "like" or "likes" text
                likeCountEl.textContent = likeCount;
                likeText.style.display = 'inline';
            }
        }
        
    } catch (error) {
        console.error('Like error:', error);
        heartIcon.style.stroke = '#ff0000';
        setTimeout(() => {
            heartIcon.style.stroke = '';
        }, 1000);
        
    } finally {
        likeBtn.classList.remove('loading');
    }
}

// Updated: Load like count with number-only display
async function loadLikeCount(articleId, likeCountEl) {
    try {
        const response = await fetch(`/api/article-likes?article_id=${encodeURIComponent(articleId)}`);
        const data = await response.json();
        
        if (data.likes !== undefined) {
            const likeCount = data.likes || 0;
            if (likeCountEl) {
                likeCountEl.textContent = likeCount;
            }
            
            // Show/hide like count - JUST THE NUMBER
            const likeText = likeCountEl ? likeCountEl.parentElement : null;
            if (likeText) {
                if (likeCount === 0) {
                    likeText.style.display = 'none';
                } else {
                    // Just show the number
                    likeCountEl.textContent = likeCount;
                    likeText.style.display = 'inline';
                }
            }
            
            // Set heart state
            const container = likeCountEl ? likeCountEl.closest('.article-interactions') : null;
            if (container) {
                const likeBtn = container.querySelector('.like-btn');
                if (likeBtn) {
                    if (data.user_liked) {
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('liked');
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error loading like count:', error);
    }
}

// Updated: Setup with correct selector for new structure
function setupCommentForms() {
    document.querySelectorAll('.article-interactions').forEach(container => {
        const articleId = container.dataset.articleId;
        const likeBtn = container.querySelector('.like-btn');
        const commentBtn = container.querySelector('.comment-btn');
        const shareBtn = container.querySelector('.share-btn');
        const commentsContainer = container.querySelector('.comments-container');
        const form = container.querySelector('.comment-form');
        // Updated selector for new structure
        const likeCountEl = container.querySelector('.like-section .like-count');

        // Load initial like count
        if (likeCountEl) {
            loadLikeCount(articleId, likeCountEl);
        }

        // Setup like button
        if (likeBtn) {
            likeBtn.addEventListener('click', function() {
                handleArticleLike(articleId, likeBtn, likeCountEl);
            });
        }

        // ... rest of the function stays the same
        // (comment button, share button, form submission code)
    });
}

// NEW: Handle article share
async function handleArticleShare(articleId, shareBtn) {
    if (shareBtn.classList.contains('loading')) return;
    
    shareBtn.classList.add('loading');
    shareBtn.classList.add('sharing');
    
    try {
        // Get the article data for sharing
        const articleIndex = parseInt(articleId) || 0;
        const article = articles[articleIndex] || null;
        
        if (!article) {
            throw new Error('Article not found');
        }
        
        // Prepare share data
        const shareData = {
            title: article.title || 'Check out this news article',
            text: article.description || '',
            url: article.url || window.location.href
        };
        
        // Try native Web Share API first (mobile)
        if (navigator.share) {
            await navigator.share(shareData);
        } else {
            // Fallback to clipboard copy (desktop)
            const shareText = `${shareData.title}\n\n${shareData.text}\n\n${shareData.url}`;
            
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(shareData.url);
                showShareFeedback('Link copied to clipboard!');
            } else {
                // Final fallback - create temporary input
                const tempInput = document.createElement('input');
                tempInput.value = shareData.url;
                document.body.appendChild(tempInput);
                tempInput.select();
                document.execCommand('copy');
                document.body.removeChild(tempInput);
                showShareFeedback('Link copied!');
            }
        }
        
    } catch (error) {
        console.error('Share error:', error);
        
        // If user cancelled share, don't show error
        if (error.name !== 'AbortError') {
            showShareFeedback('Unable to share article', 'error');
        }
        
    } finally {
        shareBtn.classList.remove('loading');
        setTimeout(() => {
            shareBtn.classList.remove('sharing');
        }, 600);
    }
}

// NEW: Show share feedback
function showShareFeedback(message, type = 'success') {
    // Remove existing feedback
    const existingFeedback = document.querySelector('.share-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Create feedback element
    const feedback = document.createElement('div');
    feedback.className = `share-feedback ${type}`;
    feedback.textContent = message;
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ff4444' : '#28a745'};
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 600;
        z-index: 10000;
        animation: fadeInOut 3s ease-in-out forwards;
        font-family: 'Times New Roman', Times, serif;
    `;
    
    // Add CSS animation
    if (!document.getElementById('share-feedback-styles')) {
        const style = document.createElement('style');
        style.id = 'share-feedback-styles';
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translateY(-10px); }
                15% { opacity: 1; transform: translateY(0); }
                85% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-10px); }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(feedback);
    
    // Remove after animation
    setTimeout(() => {
        if (feedback.parentNode) {
            feedback.remove();
        }
    }, 3000);
}

// Updated: Load like count with SVG icon state
async function loadLikeCount(articleId, likeCountEl) {
    try {
        const response = await fetch(`/api/article-likes?article_id=${encodeURIComponent(articleId)}`);
        const data = await response.json();
        
        if (data.likes !== undefined) {
            const likeCount = data.likes || 0;
            if (likeCountEl) {
                likeCountEl.textContent = likeCount;
            }
            
            // Update like text and visibility
            const likeText = likeCountEl ? likeCountEl.parentElement : null;
            if (likeText) {
                if (likeCount === 0) {
                    likeText.style.display = 'none';
                } else if (likeCount === 1) {
                    likeText.innerHTML = `<span class="like-count">${likeCount}</span> like`;
                    likeText.style.display = 'block';
                } else {
                    likeText.innerHTML = `<span class="like-count">${likeCount}</span> likes`;
                    likeText.style.display = 'block';
                }
            }
            
            // Set heart state
            const container = likeCountEl ? likeCountEl.closest('.article-interactions') : null;
            if (container) {
                const likeBtn = container.querySelector('.like-btn');
                if (likeBtn) {
                    if (data.user_liked) {
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('liked');
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error loading like count:', error);
    }
}

function loadComments(articleId, container) {
    fetch(`/api/article-comments?article_id=${encodeURIComponent(articleId)}`)
        .then(response => response.json())
        .then(data => {
            const commentsList = container.querySelector('.comments-list');
            commentsList.innerHTML = '';

            if (data.comments && data.comments.length === 0) {
                commentsList.innerHTML = `
                    <p class="text-muted text-center py-3" style="font-size: 0.8em;">
                        No comments yet. Be the first to comment!
                    </p>`;
            } else if (data.comments) {
                data.comments.forEach(comment => {
                    const commentEl = createInstagramComment(comment);
                    commentsList.appendChild(commentEl);
                });
            }
        })
        .catch(err => {
            console.error('Error loading comments:', err);
        });
}
// Updated: Create Instagram-style comment element
function createInstagramComment(comment) {
    const commentEl = document.createElement('div');
    commentEl.className = 'comment';
    commentEl.dataset.commentId = comment.id;
    
    const likes = comment.likes || 0;
    const userLiked = comment.userLiked || false;
    
    // Handle timestamp (Instagram style - shorter)
    let formattedDate = 'now';
    if (comment.timestamp) {
        try {
            const date = new Date(comment.timestamp.seconds ? comment.timestamp.seconds * 1000 : comment.timestamp);
            const now = new Date();
            const diffMinutes = Math.floor((now - date) / (1000 * 60));
            
            if (diffMinutes < 1) {
                formattedDate = 'now';
            } else if (diffMinutes < 60) {
                formattedDate = `${diffMinutes}m`;
            } else if (diffMinutes < 1440) {
                formattedDate = `${Math.floor(diffMinutes / 60)}h`;
            } else {
                formattedDate = `${Math.floor(diffMinutes / 1440)}d`;
            }
        } catch (e) {
            formattedDate = 'now';
        }
    }
    
    commentEl.innerHTML = `
        <div class="comment-header">
            <span class="comment-nickname">${escapeHtml(comment.nickname || 'Anonymous')}</span>
            <span class="comment-timestamp">${formattedDate}</span>
        </div>
        
        <div class="comment-content">
            <div class="comment-text">${escapeHtml(comment.comment)}</div>
        </div>
        
        <div class="comment-actions">
            <button class="comment-like-btn ${userLiked ? 'liked' : ''}" 
                    title="${userLiked ? 'Unlike' : 'Like'}">
                Like
            </button>
            ${likes > 0 ? `<span class="comment-like-count">${likes} ${likes === 1 ? 'like' : 'likes'}</span>` : ''}
        </div>
    `;
    
    // Add event listener for comment like
    const likeBtn = commentEl.querySelector('.comment-like-btn');
    likeBtn.addEventListener('click', () => handleCommentLike(commentEl));
    
    return commentEl;
}
// FIXED: Update handleCommentLike to use correct selector
async function handleCommentLike(commentElement) {
    const commentId = commentElement.dataset.commentId;
    const articleId = commentElement.closest('.article-interactions').dataset.articleId;
    const likeBtn = commentElement.querySelector('.comment-like-btn');
    
    if (likeBtn.disabled) return;
    
    likeBtn.disabled = true;
    likeBtn.style.opacity = '0.6';
    
    try {
        const response = await fetch('/api/comment-like', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comment_id: commentId,
                article_id: articleId
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Update button state
        const isLiked = result.user_liked;
        const newLikeCount = result.likes || 0;
        
        if (isLiked) {
            likeBtn.classList.add('liked');
            likeBtn.textContent = 'Unlike';
        } else {
            likeBtn.classList.remove('liked');
            likeBtn.textContent = 'Like';
        }
        
        // Update like count display
        const actions = commentElement.querySelector('.comment-actions');
        let likeCountEl = actions.querySelector('.comment-like-count');
        
        if (newLikeCount > 0) {
            if (!likeCountEl) {
                likeCountEl = document.createElement('span');
                likeCountEl.className = 'comment-like-count';
                actions.appendChild(likeCountEl);
            }
            likeCountEl.textContent = `${newLikeCount} ${newLikeCount === 1 ? 'like' : 'likes'}`;
        } else if (likeCountEl) {
            likeCountEl.remove();
        }
        
    } catch (error) {
        console.error('Comment like error:', error);
    } finally {
        likeBtn.disabled = false;
        likeBtn.style.opacity = '';
    }
}
// Helper function to escape HTML and prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// UPDATED: Create comment element with voting buttons
function createCommentElement(comment) {
    const commentEl = document.createElement('div');
    commentEl.className = 'comment text-start mb-1';
    commentEl.dataset.commentId = comment.id;
    
    // Calculate likes count
    const likes = comment.likes || 0;
    const userLiked = comment.userLiked || false;
    
    // Handle timestamp
    let formattedDate = 'Just now';
    if (comment.timestamp) {
        try {
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
        <div class="comment-header">
            <div class="comment-meta">
                <span class="comment-nickname">${escapeHtml(comment.nickname || 'Anonymous')}</span>
                <small class="comment-timestamp">${formattedDate}</small>
            </div>
        </div>
        
        <div class="comment-content">
            <div class="comment-text">${escapeHtml(comment.comment)}</div>
        </div>
        
        <div class="comment-actions">
            <button class="like-btn ${userLiked ? 'liked' : ''}" 
                    title="${userLiked ? 'Unlike' : 'Like'} this comment">
                <span class="heart-icon">${userLiked ? '❤️' : '🤍'}</span>
                <span class="like-count">${likes > 0 ? likes : ''}</span>
            </button>
        </div>
    `;
    
    // Add event listener for heart like
    const likeBtn = commentEl.querySelector('.like-btn');
    likeBtn.addEventListener('click', () => handleLike(commentEl));
    
    return commentEl;
}

async function handleLike(commentElement) {
    const commentId = commentElement.dataset.commentId;
    const articleId = commentElement.closest('.article-comments').dataset.articleId;
    const likeBtn = commentElement.querySelector('.like-btn');
    const heartIcon = likeBtn.querySelector('.heart-icon');
    const likeCount = likeBtn.querySelector('.like-count');
    
    // Prevent double-clicking
    if (likeBtn.disabled) return;
    
    // Show loading state
    likeBtn.disabled = true;
    likeBtn.style.opacity = '0.6';
    
    try {
        const response = await fetch('/api/comment-like', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comment_id: commentId,
                article_id: articleId
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Update UI with new like state
        const isLiked = result.user_liked;
        const newLikeCount = result.likes || 0;
        
        // Update heart icon
        heartIcon.textContent = isLiked ? '❤️' : '🤍';
        
        // Update like count
        likeCount.textContent = newLikeCount > 0 ? newLikeCount : '';
        
        // Update button state
        if (isLiked) {
            likeBtn.classList.add('liked');
            likeBtn.title = 'Unlike this comment';
        } else {
            likeBtn.classList.remove('liked');
            likeBtn.title = 'Like this comment';
        }
        
        // Re-sort comments after a short delay (optional)
        setTimeout(() => {
            const container = commentElement.closest('.article-comments');
            if (container) {
                loadComments(articleId, container);
            }
        }, 500);
        
    } catch (error) {
        console.error('Like error:', error);
        // Show error feedback
        likeBtn.style.background = 'rgba(255, 0, 0, 0.1)';
        setTimeout(() => {
            likeBtn.style.background = '';
        }, 1000);
        
    } finally {
        // Remove loading state
        likeBtn.disabled = false;
        likeBtn.style.opacity = '';
    }
}
// Updated: Inject Instagram-style CSS
function injectVotingStyles() {
    // This function name stays the same but now injects Instagram styles
    if (document.getElementById('instagram-styles')) return;
    
    // The CSS is now in the separate CSS file
    // This function is kept for compatibility but doesn't inject styles
    console.log('Instagram-style CSS should be loaded from external file');
}

// FIXED: Updated setupCommentForms to use correct selectors
function setupCommentForms() {
    document.querySelectorAll('.article-interactions').forEach(container => {
        const articleId = container.dataset.articleId;
        const likeBtn = container.querySelector('.like-btn');
        const commentBtn = container.querySelector('.comment-btn');
        const shareBtn = container.querySelector('.share-btn');
        const commentsContainer = container.querySelector('.comments-container');
        const form = container.querySelector('.comment-form');
        const likeCountEl = container.querySelector('.like-count');

        // Load initial like count
        if (likeCountEl) {
            loadLikeCount(articleId, likeCountEl);
        }

        // Setup like button
        if (likeBtn) {
            likeBtn.addEventListener('click', function() {
                handleArticleLike(articleId, likeBtn, likeCountEl);
            });
        }

        // Setup comment toggle button
        if (commentBtn && commentsContainer) {
            commentBtn.addEventListener('click', function() {
                const isVisible = commentsContainer.style.display !== 'none';
                
                if (isVisible) {
                    // Hide comments
                    commentsContainer.style.display = 'none';
                    commentBtn.classList.remove('active');
                } else {
                    // Show comments and load them
                    commentsContainer.style.display = 'block';
                    commentBtn.classList.add('active');
                    loadComments(articleId, container);
                }
            });
        }

        // Setup share button
        if (shareBtn) {
            shareBtn.addEventListener('click', function() {
                handleArticleShare(articleId, shareBtn);
            });
        }

        // Setup form submission
        if (form) {
            const newForm = form.cloneNode(true);
            form.parentNode.replaceChild(newForm, form);
            
            newForm.addEventListener('submit', e => {
                e.preventDefault();

                const nickname = newForm.nickname.value.trim();
                const commentText = newForm.comment.value.trim();
                const submitBtn = newForm.querySelector('button[type="submit"]');

                if (!commentText) {
                    return;
                }

                submitBtn.disabled = true;
                submitBtn.textContent = 'Posting...';

                const payload = {
                    article_id: articleId,
                    comment_text: commentText
                };

                if (nickname) {
                    payload.nickname = nickname;
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
                })
                .finally(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Post';
                });
            });
        }
    });
}

// Add this JavaScript to your existing news.js file

// ===== FAQ SYSTEM =====

// Initialize FAQ when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFAQ();
});

function initializeFAQ() {
    const faqButton = document.getElementById('faqButton');
    const faqBox = document.getElementById('faqBox');
    const faqClose = document.getElementById('faqClose');

    if (!faqButton || !faqBox || !faqClose) {
        console.warn('FAQ elements not found in DOM');
        return;
    }

    // Toggle FAQ box visibility
    faqButton.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleFAQ();
    });

    // Close FAQ with X button
    faqClose.addEventListener('click', function() {
        closeFAQ();
    });

    // Close FAQ when clicking outside
    document.addEventListener('click', function(event) {
        if (!faqBox.contains(event.target) && !faqButton.contains(event.target)) {
            closeFAQ();
        }
    });

    // Prevent FAQ box clicks from closing it
    faqBox.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Setup question buttons and feedback
    setupFAQInteractions();

    // ESC key closes FAQ
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeFAQ();
        }
    });
}

function toggleFAQ() {
    const faqBox = document.getElementById('faqBox');
    const isVisible = faqBox.style.display === 'flex';
    
    if (isVisible) {
        closeFAQ();
    } else {
        openFAQ();
    }
}

function openFAQ() {
    const faqBox = document.getElementById('faqBox');
    faqBox.style.display = 'flex';
}

function closeFAQ() {
    const faqBox = document.getElementById('faqBox');
    faqBox.style.display = 'none';
    
    // Reset everything when closing
    resetFAQConversation();
}

// ===== FAQ INTERACTIONS =====

function setupFAQInteractions() {
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach((button, index) => {
        button.addEventListener('click', function() {
            const reply = this.getAttribute('data-reply');
            const questionText = this.textContent.trim();
            
            // Hide the clicked button immediately
            this.style.display = 'none';
            
            // Special handling for feedback button
            if (questionText.toLowerCase().includes('feedback')) {
                hideAllFAQButtons();
                showFeedbackSection();
                addFAQMessage('Please share your feedback below:', 'bot');
                return;
            }
            
            // Add user question and bot reply for other buttons
            addFAQMessage(questionText, 'user');
            
            setTimeout(() => {
                addFAQMessage(reply, 'bot');
                
                // After showing the answer, check if we should show reset option
                const remainingButtons = getRemainingButtons();
                if (remainingButtons.length > 0 && remainingButtons.length < 5) {
                    showResetOption();
                }
            }, 300);
        });
    });

    // Setup feedback functionality
    setupFeedbackSection();
}

function hideAllFAQButtons() {
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(button => {
        button.style.display = 'none';
    });
}

function getRemainingButtons() {
    const faqQuestions = document.querySelectorAll('.faq-question');
    return Array.from(faqQuestions).filter(button => button.style.display !== 'none');
}

function showResetOption() {
    const faqFooter = document.getElementById('faqFooter');
    
    // Check if reset button already exists
    if (document.getElementById('resetFAQ')) return;
    
    // Create reset button
    const resetButton = document.createElement('button');
    resetButton.id = 'resetFAQ';
    resetButton.className = 'faq-reset';
    resetButton.textContent = 'Ask Another Question';
    resetButton.style.cssText = `
        background: transparent;
        color: var(--source-date-color);
        border: 1px dashed var(--border-color);
        border-radius: 0;
        padding: 8px 15px;
        font-size: 0.8em;
        cursor: pointer;
        font-family: 'Times New Roman', Times, serif;
        font-style: italic;
        margin-top: 10px;
        width: 100%;
        transition: all 0.2s ease;
    `;
    
    resetButton.addEventListener('click', function() {
        resetFAQConversation();
    });
    
    resetButton.addEventListener('mouseover', function() {
        this.style.borderStyle = 'solid';
        this.style.color = 'var(--text-color)';
    });
    
    resetButton.addEventListener('mouseout', function() {
        this.style.borderStyle = 'dashed';
        this.style.color = 'var(--source-date-color)';
    });
    
    faqFooter.appendChild(resetButton);
}

function resetFAQConversation() {
    // Clear all messages except the initial one
    const faqMessages = document.getElementById('faqMessages');
    const initialMessage = faqMessages.querySelector('.faq-message.bot-message');
    faqMessages.innerHTML = '';
    if (initialMessage) {
        faqMessages.appendChild(initialMessage);
    }
    
    // Show all FAQ buttons again
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(button => {
        button.style.display = 'block';
    });
    
    // Hide feedback section
    const feedbackSection = document.getElementById('feedbackSection');
    if (feedbackSection) {
        feedbackSection.style.display = 'none';
        document.getElementById('feedbackInput').value = '';
        clearFeedbackStatus();
    }
    
    // Remove reset button
    const resetButton = document.getElementById('resetFAQ');
    if (resetButton) {
        resetButton.remove();
    }
}

function addFAQMessage(message, sender) {
    const faqMessages = document.getElementById('faqMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('faq-message');
    
    if (sender === 'bot') {
        messageDiv.classList.add('bot-message');
        messageDiv.innerHTML = `<div class="message-content"><strong>FAQ</strong><br>${escapeHtml(message)}</div>`;
    } else {
        messageDiv.classList.add('user-message');
        messageDiv.innerHTML = `<div class="message-content"><strong>You</strong><br>${escapeHtml(message)}</div>`;
    }
    
    faqMessages.appendChild(messageDiv);
    faqMessages.scrollTop = faqMessages.scrollHeight;
}

// ===== FEEDBACK FUNCTIONALITY =====

function setupFeedbackSection() {
    const feedbackSubmit = document.getElementById('feedbackSubmit');
    const feedbackCancel = document.getElementById('feedbackCancel');
    const feedbackInput = document.getElementById('feedbackInput');

    if (!feedbackSubmit || !feedbackCancel || !feedbackInput) {
        console.warn('Feedback elements not found in DOM');
        return;
    }

    // Submit feedback
    feedbackSubmit.addEventListener('click', function(e) {
        e.preventDefault();
        submitFeedback();
    });

    // Cancel feedback
    feedbackCancel.addEventListener('click', function(e) {
        e.preventDefault();
        hideFeedbackSection();
    });

    // Submit on Ctrl/Cmd + Enter
    feedbackInput.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            submitFeedback();
        }
    });

    // Auto-resize textarea
    feedbackInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

function showFeedbackSection() {
    const feedbackSection = document.getElementById('feedbackSection');
    const feedbackInput = document.getElementById('feedbackInput');
    
    // Hide all FAQ buttons
    hideAllFAQButtons();
    
    // Remove reset button if it exists
    const resetButton = document.getElementById('resetFAQ');
    if (resetButton) {
        resetButton.remove();
    }
    
    feedbackSection.style.display = 'block';
    
    // Focus on textarea after a short delay
    setTimeout(() => {
        feedbackInput.focus();
    }, 100);
}

function hideFeedbackSection() {
    const feedbackSection = document.getElementById('feedbackSection');
    const feedbackInput = document.getElementById('feedbackInput');
    
    feedbackSection.style.display = 'none';
    feedbackInput.value = '';
    feedbackInput.style.height = 'auto';
    clearFeedbackStatus();
    
    // Show all FAQ buttons again
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(button => {
        button.style.display = 'block';
    });
}

function submitFeedback() {
    const feedbackInput = document.getElementById('feedbackInput');
    const feedbackSubmit = document.getElementById('feedbackSubmit');
    
    if (!feedbackInput || !feedbackSubmit) {
        console.error('Feedback elements not found');
        return;
    }
    
    const feedback = feedbackInput.value.trim();

    // Validate input
    if (!feedback) {
        showFeedbackStatus('Please enter your feedback before submitting.', 'error');
        feedbackInput.focus();
        return;
    }

    if (feedback.length < 5) {
        showFeedbackStatus('Please provide more detailed feedback (at least 5 characters).', 'error');
        feedbackInput.focus();
        return;
    }

    // Show loading state
    feedbackSubmit.disabled = true;
    feedbackSubmit.textContent = 'Sending...';
    clearFeedbackStatus();

    // Prepare feedback data
    const feedbackData = {
        feedback: feedback,
        timestamp: new Date().toISOString(),
        source: 'faq',
        page: window.location.pathname
    };

    // Submit to Flask backend
    fetch('/api/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            return response.json().then(errorData => {
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }).catch(() => {
                throw new Error(`Server error: ${response.status}`);
            });
        }
        
        return response.json();
    })
    .then(data => {
        console.log('Success response:', data);
        
        // Your backend returns: {"message": "Feedback submitted successfully", "success": true}
        if (data.success === true || data.message) {
            handleFeedbackSuccess();
        } else {
            throw new Error('Unexpected response format');
        }
    })
    .catch(error => {
        console.error('Feedback error:', error);
        handleFeedbackError(error);
    })
    .finally(() => {
        // Reset submit button
        feedbackSubmit.disabled = false;
        feedbackSubmit.textContent = 'Send';
    });
}

function handleFeedbackSuccess() {
    // Show success message
    showFeedbackStatus('Thank you for your feedback!', 'success');
    
    // Add bot response to chat
    addFAQMessage('Thank you for your feedback. We truly appreciate your input and will review it carefully.', 'bot');
    
    // Auto-close FAQ after showing success message
    setTimeout(() => {
        closeFAQ();
    }, 2000); // Close after 2 seconds
}

function handleFeedbackError(error) {
    let errorMessage = 'Unable to send feedback. Please try again.';
    
    // Provide more specific error messages
    if (error.message.includes('429')) {
        errorMessage = 'Please wait a moment before sending another message.';
    } else if (error.message.includes('413')) {
        errorMessage = 'Your message is too long. Please shorten it.';
    } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        errorMessage = 'Connection issue. Please check your internet and try again.';
    }
    
    showFeedbackStatus(errorMessage, 'error');
}

function showFeedbackStatus(message, type) {
    // Remove existing status
    clearFeedbackStatus();
    
    const feedbackSection = document.getElementById('feedbackSection');
    const statusDiv = document.createElement('div');
    statusDiv.className = `feedback-status feedback-${type}`;
    statusDiv.textContent = message;
    statusDiv.id = 'feedbackStatusMessage';
    
    feedbackSection.appendChild(statusDiv);
}

function clearFeedbackStatus() {
    const existingStatus = document.getElementById('feedbackStatusMessage');
    if (existingStatus) {
        existingStatus.remove();
    }
}