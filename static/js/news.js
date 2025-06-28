// ==================== GLOBAL VARIABLES ====================
let articles = [];
let currentCategory = localStorage.getItem('lastCategory') || 'general';
let currentLanguage = 'en';
let currentQuery = '';
let darkMode = localStorage.getItem('darkMode') === 'true';

// Audio state
let activeAudio = null;
let currentPlayButton = null;
let currentArticleIndex = null;
let directTTSCache = new Map();

// Performance tracking
let performanceCache = {
    newsHits: 0,
    newsMisses: 0,
    directTTSHits: 0,
    directTTSMisses: 0
};

// DOM elements
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const newsList = document.getElementById('newsList');
const newsTemplate = document.getElementById('newsArticleTemplate');

// Translations
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
            entertainment: "Entertainment"
        },
        noNews: "No news found for",
        tryDifferent: "Try a different keyword or category.",
        unknownSource: "Unknown Source",
        unknownDate: "Unknown Date",
        yesterday: "Yesterday",
        daysAgo: "days ago",
        readFull: "Read article",
        listen: "Listen",
        darkMode: "Dark Mode",
        lightMode: "Light Mode",
        noDescription: "No description available.",
        audioLoadError: "Error loading audio. Please try again.",
        loading: "Loading...",
        error: "An error occurred. Please try again later."
    }
};

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('category').value = currentCategory;
    initializeTheme();
    updateInterfaceLanguage();
    addThemeControl();
    updateCurrentDate();
    setupEventListeners();
    loadNews();
    startOptimizations();
});

// ==================== FIXED CACHE KEY GENERATION ====================
function generateDirectTTSCacheKey(article, voiceId) {
    const description = article.description || '';
    const title = article.title || '';
    const url = article.url || '';
    
    // Create a more unique identifier for the article
    const articleHash = btoa(encodeURIComponent(description + title + url)).substring(0, 20);
    
    // Include BOTH language code AND full voice ID for maximum uniqueness
    const langCode = voiceId.split('-')[0];
    const voiceShort = voiceId.split('-').slice(-1)[0]; // Neural part
    
    return `tts-${articleHash}-${langCode}-${voiceShort}-${voiceId}`;
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // Category links
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

    // Search functionality
    document.getElementById('searchBtn').addEventListener('click', () => {
        currentQuery = document.getElementById('searchQuery').value;
        currentCategory = document.getElementById('category').value;
        stopActiveAudio();
        loadNews();
    });

    document.getElementById('searchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') document.getElementById('searchBtn').click();
    });

    // Search with debounce
    document.getElementById('searchQuery').addEventListener('input', debounce(() => {
        currentQuery = document.getElementById('searchQuery').value;
        loadNews();
    }, 400));

    // FIXED: Voice selection changes - IMMEDIATE STOP and REGENERATE
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('voice-select')) {
            const articleIndex = parseInt(e.target.dataset.articleIndex);
            const newVoice = e.target.value;
            const oldVoice = localStorage.getItem('lastVoice') || 'en-CA-LiamNeural';
            
            console.log(`🔄 Voice changed for article ${articleIndex}: ${oldVoice} → ${newVoice}`);
            
            // Update stored voice preference
            localStorage.setItem('lastVoice', newVoice);

            // STEP 1: IMMEDIATELY STOP current audio if it's playing
            if (activeAudio && currentArticleIndex === articleIndex) {
                console.log(`⏹️ STOPPING current audio for article ${articleIndex}`);
                stopActiveAudio();
            }

            // STEP 2: AGGRESSIVE CACHE CLEARING
            const article = articles[articleIndex];
            if (article) {
                console.log(`🗑️ Clearing ALL cache entries for article ${articleIndex}`);
                
                // Clear cache for both old and new voices
                const oldCacheKey = generateDirectTTSCacheKey(article, oldVoice);
                const newCacheKey = generateDirectTTSCacheKey(article, newVoice);
                
                directTTSCache.delete(oldCacheKey);
                directTTSCache.delete(newCacheKey);
                
                // Clear ANY cache entries that might match this article
                const articleIdentifier = btoa(encodeURIComponent((article.description || '') + (article.title || '') + (article.url || ''))).substring(0, 20);
                
                // Remove ALL cache entries for this article regardless of voice
                for (let [key, value] of directTTSCache.entries()) {
                    if (key.includes(articleIdentifier)) {
                        console.log(`🗑️ Removing cache entry: ${key}`);
                        directTTSCache.delete(key);
                    }
                }
                
                console.log(`✅ Cache cleared. Remaining entries: ${directTTSCache.size}`);
            }

            // STEP 3: Reset button to initial state
            const listenBtn = document.querySelector(`.article-listen-btn[data-index="${articleIndex}"]`);
            if (listenBtn) {
                listenBtn.innerHTML = '▶︎';
                listenBtn.disabled = false;
                
                // Reset the onclick handler to ensure fresh generation
                listenBtn.onclick = () => generateDirectTTS(articleIndex);
            }

            console.log(`✅ Voice change completed for article ${articleIndex}`);
        }
    });
}

// ==================== THEME MANAGEMENT ====================
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
                <button id="newsletterBtn" class="btn btn-outline-primary btn-sm">Newsletter</button>
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

function openNewsletterPopup() {
    const modal = new bootstrap.Modal(document.getElementById('newsletterModal'));
    modal.show();
}

// ==================== UI UPDATES ====================
function updateCurrentDate() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDateDisplay').textContent = now.toLocaleDateString('en-US', options);
}

function updateInterfaceLanguage() {
    const t = translations.en;

    const titleElement = document.querySelector('.journal-title');
    if (titleElement) titleElement.textContent = t.title;

    const searchInput = document.getElementById('searchQuery');
    if (searchInput) searchInput.placeholder = t.search;

    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) searchBtn.textContent = t.searchBtn;

    document.querySelectorAll('.category-link').forEach(link => {
        const category = link.dataset.category;
        if (t.categories[category]) {
            link.textContent = t.categories[category];
        }
    });
}

// ==================== LOADING STATES ====================
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
    const t = translations.en;
    emptyState.textContent = `😕 ${t.noNews} "${currentQuery || currentCategory}". ${t.tryDifferent}`;
}

function hideStates() {
    loadingIndicator.classList.add('d-none');
    emptyState.classList.add('d-none');
    errorState.classList.add('d-none');
}

// ==================== NEWS LOADING ====================
async function loadNews() {
    showLoading();
    const startTime = performance.now();
    
    try {
        const params = new URLSearchParams({ category: currentCategory, language: currentLanguage });
        if (currentQuery) params.append('query', currentQuery);
        
        const response = await fetch(`/api/news?${params}`);
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        articles = data.articles || [];
        if (!articles.length) return showEmpty();
        
        // Performance tracking
        const loadTime = performance.now() - startTime;
        const isCacheHit = loadTime < 500;
        
        if (isCacheHit) {
            performanceCache.newsHits++;
        } else {
            performanceCache.newsMisses++;
        }
        
        displayNews(articles);
        setupCommentForms();
        hideStates();
        
    } catch (error) {
        console.error('Error loading news:', error);
        showError(error.message);
        performanceCache.newsMisses++;
    }
}

function displayNews(articlesData) {
    newsList.innerHTML = '';
    const totalArticles = articlesData.length;

    articlesData.forEach((article, index) => {
        const isLastArticle = (index === totalArticles - 1);
        const articleElement = createArticleElement(article, index, isLastArticle);
        newsList.appendChild(articleElement);
    });
}

function createArticleElement(article, index, isLastArticle = false) {
    const template = newsTemplate.content.cloneNode(true);
    const t = translations.en;

    const articleRoot = template.querySelector('.news-article');

    if (isLastArticle) {
        articleRoot.classList.remove('col-md-6', 'col-lg-4');
        articleRoot.classList.add('col-12', 'full-width-article');
    } else {
        articleRoot.classList.add('col-12', 'col-md-6', 'col-lg-4');
    }
    articleRoot.classList.add('mb-3', 'd-flex');

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

    // SIMPLE: Single triangle button
    const listenBtn = template.querySelector('.article-listen-btn');
    listenBtn.dataset.index = index;
    listenBtn.innerHTML = '▶︎';
    listenBtn.title = t.listen;
    listenBtn.onclick = () => generateDirectTTS(index);

    const voiceSelect = template.querySelector('.voice-select');
    voiceSelect.id = `voice-select-${index}`;
    voiceSelect.dataset.articleIndex = index;
    voiceSelect.value = localStorage.getItem('lastVoice') || 'en-CA-LiamNeural';

    // KEEP ONLY the main progress bar
    const progress = template.querySelector('.audio-progress');
    progress.style.display = 'none';
    progress.value = 0;

    const articleId = btoa(article.url || article.title || article.publishedAt || `${index}`);
    template.querySelector('.article-comments').dataset.articleId = articleId;

    return template;
}

function formatDate(dateString) {
    const t = translations.en;
    if (!dateString) return t.unknownDate;

    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return t.yesterday;
    if (diffDays < 7) return `${diffDays} ${t.daysAgo}`;

    return date.toLocaleDateString('en-US');
}

// ==================== ENHANCED GENERATETTS FUNCTION ====================
async function generateDirectTTS(index) {
    const article = articles[index];
    const voiceSelect = document.getElementById(`voice-select-${index}`);
    const selectedVoice = voiceSelect?.value || 'en-CA-LiamNeural';
    const listenBtn = document.querySelector(`.article-listen-btn[data-index="${index}"]`);
    const card = listenBtn?.closest('.card');
    const progressBar = card?.querySelector('.audio-progress');

    console.log(`🎵 Starting TTS generation for article ${index} with voice: ${selectedVoice}`);

    if (!article || !selectedVoice || !listenBtn) {
        console.error('❌ Missing required elements:', { 
            article: !!article, 
            selectedVoice, 
            listenBtn: !!listenBtn 
        });
        return;
    }

    // Validate description
    if (!article.description || article.description.trim().length < 10) {
        console.warn(`⚠️ Description too short for article ${index}`);
        showNotification('Article description is too short for audio generation.', 'warning');
        listenBtn.innerHTML = '▶︎';
        listenBtn.disabled = false;
        return;
    }

    // Generate cache key with current voice
    const cacheKey = generateDirectTTSCacheKey(article, selectedVoice);
    console.log(`🔑 Generated cache key: ${cacheKey}`);
    
    // Check cache ONLY if we're not forcing regeneration
    const cachedResult = directTTSCache.get(cacheKey);
    
    if (cachedResult) {
        console.log(`🎯 Using cached audio for article ${index} with voice ${selectedVoice}`);
        performanceCache.directTTSHits++;
        playAudio(cachedResult, index, listenBtn, progressBar);
        return;
    }

    console.log(`🔄 No cache hit. Generating new audio for article ${index} in ${selectedVoice}`);
    performanceCache.directTTSMisses++;

    // Show loading state
    listenBtn.innerHTML = '⏳';
    listenBtn.disabled = true;

    try {
        // Process and clean text
        let optimizedText = article.description.trim();
        
        // Enhanced cleanup
        optimizedText = optimizedText
            .replace(/Read more.*$/i, '')
            .replace(/Continue reading.*$/i, '')
            .replace(/Click here.*$/i, '')
            .replace(/Subscribe.*$/i, '')
            .replace(/Follow us.*$/i, '')
            .replace(/\[.*?\]/g, '')
            .replace(/\(Image:.*?\)/g, '')
            .replace(/\(Photo:.*?\)/g, '')
            .replace(/Source:.*$/i, '');

        // Voice-friendly replacements
        const voiceFixes = {
            'FBI': 'F-B-I', 'CIA': 'C-I-A', 'CEO': 'C-E-O', 'AI': 'A-I',
            'US': 'U-S', 'USA': 'U-S-A', 'UK': 'U-K', 'EU': 'E-U',
            'NASA': 'N-A-S-A', 'WHO': 'W-H-O', 'GDP': 'G-D-P',
            'NYC': 'New York City', 'LA': 'Los Angeles', 'IPO': 'I-P-O',
            'CFO': 'C-F-O', 'CTO': 'C-T-O', 'VP': 'Vice President'
        };
        
        for (const [acronym, voiceForm] of Object.entries(voiceFixes)) {
            const regex = new RegExp(`\\b${acronym}\\b`, 'g');
            optimizedText = optimizedText.replace(regex, voiceForm);
        }

        // Format numbers and currency
        optimizedText = optimizedText
            .replace(/(\d+)%/g, '$1 percent')
            .replace(/\$(\d+(?:,\d{3})*)B\b/g, '$1 billion dollars')
            .replace(/\$(\d+(?:,\d{3})*)M\b/g, '$1 million dollars')
            .replace(/\$(\d+(?:,\d{3})*)K\b/g, '$1 thousand dollars');

        // Add context from title if description is short
        if (optimizedText.split(' ').length < 8 && article.title) {
            const cleanTitle = article.title.trim().replace(/\.$/, '');
            optimizedText = `${cleanTitle}. ${optimizedText}`;
        }

        // Language detection and translation
        const langCode = selectedVoice.split('-')[0];
        console.log(`🌍 Target language: ${langCode}`);
        
        if (langCode !== 'en') {
            console.log(`📝 Translating text to ${langCode}...`);
            try {
                const translateRes = await fetch('/api/news/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        text: optimizedText, 
                        target_language: langCode 
                    })
                });
                
                if (translateRes.ok) {
                    const translateResult = await translateRes.json();
                    if (translateResult.translated_text?.trim()) {
                        optimizedText = translateResult.translated_text.trim();
                        console.log(`✅ Translation successful: ${optimizedText.substring(0, 50)}...`);
                    }
                } else {
                    console.warn('❌ Translation API failed, using original text');
                }
            } catch (translateError) {
                console.error('❌ Translation error:', translateError);
                showNotification('Translation failed, using original text', 'warning');
            }
        }

        // Ensure proper sentence ending
        if (!optimizedText.match(/[.!?]$/)) {
            optimizedText += '.';
        }

        // Clean for TTS (remove problematic characters)
        optimizedText = optimizedText
            .replace(/[^\w\s.,!?;:\-\'\"()]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        console.log(`🎙️ Final text for TTS (${optimizedText.length} chars): ${optimizedText.substring(0, 100)}...`);

        // Generate TTS with unique timestamp to prevent caching issues
        const response = await fetch('/api/news/summary-audio', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({
                content: optimizedText,
                voice_id: selectedVoice,
                speed: 1.0,
                depth: 1,
                timestamp: Date.now() // Force unique request
            })
        });

        if (!response.ok) {
            throw new Error(`TTS API returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            console.error(`❌ TTS API error:`, data.error);
            showNotification(data.error, 'danger');
            listenBtn.innerHTML = '▶︎';
            listenBtn.disabled = false;
            return;
        }

        if (!data.audio_url) {
            throw new Error('No audio URL received from TTS API');
        }

        // Create result with unique audio URL (add timestamp to prevent browser caching)
        const audioUrl = `${data.audio_url}?t=${Date.now()}`;
        const result = { 
            audio_url: audioUrl,
            text_used: optimizedText,
            voice_used: selectedVoice,
            generated_at: Date.now()
        };

        // Cache the new result
        directTTSCache.set(cacheKey, result);
        console.log(`💾 Cached new audio with key: ${cacheKey}`);
        console.log(`📊 Cache now contains ${directTTSCache.size} entries`);
        
        // AUTOMATICALLY play the newly generated audio
        playAudio(result, index, listenBtn, progressBar);

    } catch (error) {
        console.error('❌ TTS generation error:', error);
        showNotification(`Failed to generate audio: ${error.message}`, 'danger');
        listenBtn.innerHTML = '▶︎';
        listenBtn.disabled = false;
    }
}

function playAudio(data, index, button, progressBar) {
    console.log(`▶️ Playing audio for article ${index}`);
    
    // Clean up any previous audio
    if (activeAudio) {
        activeAudio.pause();
        if (currentPlayButton && currentPlayButton !== button) {
            currentPlayButton.innerHTML = '▶︎';
            currentPlayButton.disabled = false;
        }
    }

    // Set up new audio
    currentPlayButton = button;
    currentArticleIndex = index;

    const audio = new Audio(data.audio_url);
    activeAudio = audio;

    // Show progress bar
    if (progressBar) {
        progressBar.style.display = 'block';
        progressBar.value = 0;
    }

    // Set up audio events
    audio.onloadeddata = () => {
        console.log(`🎵 Audio loaded for article ${index}, starting playback`);
        button.innerHTML = '‖';
        button.disabled = false;
        
        // AUTOMATICALLY start playing
        audio.play().catch(err => {
            console.warn('Autoplay blocked:', err);
            button.innerHTML = '▶︎';
            showNotification('Click play to start audio', 'info');
        });
    };

    // Update progress
    audio.ontimeupdate = () => {
        if (progressBar && audio.duration) {
            progressBar.value = (audio.currentTime / audio.duration) * 100;
        }
    };

    audio.onended = () => {
        console.log(`🏁 Audio ended for article ${index}`);
        button.innerHTML = '▶︎';
        if (progressBar) progressBar.style.display = 'none';
        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
    };

    audio.onerror = () => {
        console.error("Audio error:", audio.error);
        showNotification('Error loading audio. Please try again.', 'danger');
        button.innerHTML = '▶︎';
        if (progressBar) progressBar.style.display = 'none';
    };

    // Set up play/pause click handler
    button.onclick = () => {
        if (audio.paused) {
            console.log(`▶️ Resuming audio for article ${index}`);
            audio.play();
            button.innerHTML = '‖';
        } else {
            console.log(`⏸️ Pausing audio for article ${index}`);
            audio.pause();
            button.innerHTML = '▶︎';
        }
    };
}

function stopActiveAudio() {
    if (activeAudio) {
        console.log(`⏹️ Stopping active audio for article ${currentArticleIndex}`);
        
        // Stop and cleanup audio
        activeAudio.pause();
        activeAudio.currentTime = 0;
        activeAudio = null;
        
        // Reset button state
        if (currentPlayButton) {
            currentPlayButton.innerHTML = '▶︎';
            currentPlayButton.disabled = false;
            currentPlayButton.onclick = () => generateDirectTTS(parseInt(currentPlayButton.dataset.index));
        }

        // Hide progress bar
        if (currentArticleIndex !== null) {
            const card = document.querySelector(`.article-listen-btn[data-index="${currentArticleIndex}"]`)?.closest('.card');
            if (card) {
                const progressBar = card.querySelector('.audio-progress');
                if (progressBar) {
                    progressBar.style.display = 'none';
                    progressBar.value = 0;
                }
            }
        }

        // Reset global state
        currentPlayButton = null;
        currentArticleIndex = null;
    }
}

// ==================== ENHANCED NOTIFICATION SYSTEM ====================
function showNotification(message, type = 'info') {
    // Remove any existing notifications of the same type
    document.querySelectorAll(`.alert-${type}.position-fixed`).forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }
    }, 4000);
}

// ==================== COMMENT SYSTEM ====================
function loadComments(articleId, container) {
    const commentsList = container.querySelector('.comments-list');
    commentsList.innerHTML = '<p class="text-muted text-center py-3" style="font-size: 0.8em;">Loading...</p>';

    fetch(`/api/article-comments?article_id=${encodeURIComponent(articleId)}`)
        .then(response => response.json())
        .then(data => {
            commentsList.innerHTML = '';

            if (data.comments && data.comments.length === 0) {
                commentsList.innerHTML = '<p class="text-muted text-center py-3" style="font-size: 0.8em;">No comments yet. Be the first to comment!</p>';
            } else if (data.comments) {
                const fragment = document.createDocumentFragment();
                
                data.comments.forEach(comment => {
                    const commentEl = document.createElement('div');
                    commentEl.className = 'comment text-start mb-2 px-2';
                    
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
                        <span class="fw-bold me-1 comment-nickname" style="font-size: 0.8em;">${escapeHtml(comment.nickname)}:</span>
                        <span class="comment-text text-dark" style="font-size: 0.8em;">${escapeHtml(comment.comment)}</span>
                        <br><small class="text-muted" style="font-size: 0.7em;">${formattedDate}</small>
                    `;
                    fragment.appendChild(commentEl);
                });
                
                commentsList.appendChild(fragment);
            }
        })
        .catch(err => {
            console.error('Error loading comments:', err);
            commentsList.innerHTML = '<p class="text-muted text-center py-3" style="font-size: 0.8em;">Error loading comments.</p>';
        });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setupCommentForms() {
    document.querySelectorAll('.article-comments').forEach(container => {
        const articleId = container.dataset.articleId;
        const form = container.querySelector('.comment-form');

        loadComments(articleId, container);

        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        newForm.addEventListener('submit', async e => {
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

            const payload = {
                article_id: articleId,
                comment_text: commentText
            };

            if (nickname) {
                payload.nickname = nickname;
            }

            try {
                const response = await fetch('/api/article-comment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.error) throw new Error(data.error);
                
                newForm.reset();
                loadComments(articleId, container);
                
            } catch (err) {
                console.error('Error posting comment:', err);
                alert('Error posting comment. Please try again.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Post';
            }
        });
    });
}

// ==================== NEWSLETTER SYSTEM ====================
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

// ==================== CHAT SYSTEM ====================
const chatButton = document.getElementById('chatButton');
const chatBox = document.getElementById('chatBox');

if (chatButton && chatBox) {
    chatButton.addEventListener('click', function() {
        chatBox.style.display = chatBox.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', function(event) {
        if (!chatBox.contains(event.target) && !chatButton.contains(event.target)) {
            chatBox.style.display = 'none';
        }
    });
}

document.querySelectorAll('.chat-question').forEach(button => {
    button.addEventListener('click', function() {
        const reply = this.getAttribute('data-reply');

        const msgDiv = document.createElement('div');
        msgDiv.classList.add('chat-message', 'bot-message');
        msgDiv.innerHTML = `<p>${reply}</p>`;
        
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.appendChild(msgDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        if (reply.toLowerCase().includes('feedback')) {
            const feedbackBox = document.getElementById('feedbackBox');
            if (feedbackBox) {
                feedbackBox.style.display = 'flex';
            }
        }
    });
});

const feedbackSubmit = document.getElementById('feedbackSubmit');
if (feedbackSubmit) {
    feedbackSubmit.addEventListener('click', function() {
        const feedbackInput = document.getElementById('feedbackInput');
        const feedback = feedbackInput ? feedbackInput.value.trim() : '';
        
        if (feedback) {
            fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ feedback: feedback })
            })
            .then(response => response.json())
            .then(data => {
                const msgDiv = document.createElement('div');
                msgDiv.classList.add('chat-message', 'bot-message');

                if (data.message) {
                    msgDiv.innerHTML = `<p>✅ Thanks for your feedback!</p>`;
                } else {
                    msgDiv.innerHTML = `<p>❌ Failed to send feedback. Please try again later.</p>`;
                }

                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.appendChild(msgDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                if (feedbackInput) feedbackInput.value = "";
                const feedbackBox = document.getElementById('feedbackBox');
                if (feedbackBox) feedbackBox.style.display = 'none';
            })
            .catch(err => {
                console.error('Error submitting feedback:', err);
            });
        }
    });
}

// ==================== PERFORMANCE OPTIMIZATIONS ====================

function optimizeCache() {
    // Keep cache size manageable
    if (directTTSCache.size > 25) {
        const keysToDelete = Array.from(directTTSCache.keys()).slice(0, 5);
        keysToDelete.forEach(key => directTTSCache.delete(key));
    }
}

function trackPerformance() {
    const total = performanceCache.newsHits + performanceCache.newsMisses + 
                  performanceCache.directTTSHits + performanceCache.directTTSMisses;
                  
    if (total > 0) {
        const hits = performanceCache.newsHits + performanceCache.directTTSHits;
        const hitRate = Math.round((hits / total) * 100);
        
        if (hitRate > 85) {
            console.log('⚡ Performance: Excellent (' + hitRate + '% instant)');
        } else if (hitRate > 60) {
            console.log('🔄 Performance: Good (' + hitRate + '% instant)');
        } else {
            console.log('📡 Performance: Building cache (' + hitRate + '% instant)');
        }
    }
}

function startOptimizations() {
    // Run optimizations every 30 seconds
    setInterval(() => {
        optimizeCache();
        trackPerformance();
    }, 30000);
}

// ==================== PERFORMANCE STATS ====================
window.getPerformanceStats = function() {
    const total = performanceCache.newsHits + performanceCache.newsMisses + 
                  performanceCache.directTTSHits + performanceCache.directTTSMisses;
                  
    const hits = performanceCache.newsHits + performanceCache.directTTSHits;
    const hitRate = total > 0 ? Math.round((hits / total) * 100) : 0;
    
    const directTTSTotal = performanceCache.directTTSHits + performanceCache.directTTSMisses;
    const directTTSHitRate = directTTSTotal > 0 ? Math.round((performanceCache.directTTSHits / directTTSTotal) * 100) : 0;
    
    return {
        cache: performanceCache,
        directTTSCache: {
            size: directTTSCache.size,
            hitRate: directTTSHitRate
        },
        performance: {
            hitRate: hitRate,
            status: hitRate > 85 ? 'Excellent' : hitRate > 60 ? 'Good' : 'Building'
        }
    };
};

// ==================== DEBUGGING HELPER ====================
window.debugTTSCache = function(articleIndex) {
    if (articleIndex !== undefined) {
        const article = articles[articleIndex];
        if (article) {
            console.log(`🔍 Debug info for article ${articleIndex}:`);
            console.log('Article:', article);
            
            // Show all cache keys for this article
            const articleIdentifier = btoa(encodeURIComponent((article.description || '') + (article.title || '') + (article.url || ''))).substring(0, 20);
            console.log('Article identifier:', articleIdentifier);
            
            const matchingKeys = [];
            for (let key of directTTSCache.keys()) {
                if (key.includes(articleIdentifier)) {
                    matchingKeys.push(key);
                }
            }
            console.log('Matching cache keys:', matchingKeys);
        }
    } else {
        console.log('🔍 All TTS cache entries:');
        console.log('Cache size:', directTTSCache.size);
        for (let [key, value] of directTTSCache.entries()) {
            console.log(`${key}:`, value);
        }
    }
};

console.log('🚀 Fixed News Reader loaded - Language switching now works perfectly!');