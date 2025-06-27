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
let audioCache = new Map();

// Performance tracking
let performanceCache = {
    newsHits: 0,
    newsMisses: 0,
    contentHits: 0,
    contentMisses: 0,
    audioHits: 0,
    audioMisses: 0
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
        noText: "This article does not contain any usable text.",
        audioFailed: "Failed to generate audio.",
        audioError: "An error occurred during voice generation.",
        audioLoadError: "Error loading audio. Please try again.",
        loading: "Loading...",
        error: "An error occurred. Please try again later."
    }
};

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

    // Optimized search with faster debounce
    document.getElementById('searchQuery').addEventListener('input', debounce(() => {
        currentQuery = document.getElementById('searchQuery').value;
        loadNews();
    }, 400));

    // Voice selection changes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('voice-select')) {
            const articleIndex = parseInt(e.target.dataset.articleIndex);
            const newVoice = e.target.value;
            localStorage.setItem('lastVoice', newVoice);

            // Immediate cache invalidation
            const cacheKey = `${articleIndex}-${newVoice}`;
            audioCache.delete(cacheKey);

            // Instant regeneration if currently playing
            if (currentArticleIndex === articleIndex) {
                const wasPlaying = activeAudio && !activeAudio.paused;
                stopActiveAudio();
                if (wasPlaying) {
                    listenToSummary(articleIndex, true);
                }
            }
        }
    });
}

function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
    };
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

// ==================== OPTIMIZED NEWS LOADING ====================
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
        
        // Preload content for better performance
        preloadContent();
        
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

// ==================== OPTIMIZED AUDIO GENERATION ====================
async function listenToSummary(index, autoPlay = true) {
    const article = articles[index];
    const voiceSelect = document.getElementById(`voice-select-${index}`);
    const selectedVoice = voiceSelect?.value;
    const listenBtn = document.querySelector(`.article-listen-btn[data-index="${index}"]`);
    const card = listenBtn.closest('.card');
    const loadingUI = card.querySelector('.audio-loading');
    const progressBar = card.querySelector('.audio-progress');
    const t = translations.en;

    if (!article || !selectedVoice || !listenBtn) return;

    // Stop other audio
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

    // Check cache first for instant playback
    const cacheKey = `${index}-${selectedVoice}`;
    const cachedAudioUrl = audioCache.get(cacheKey);

    if (cachedAudioUrl) {
        performanceCache.audioHits++;
        playAudio(cachedAudioUrl, index, listenBtn, loadingUI, progressBar, autoPlay);
        return;
    }

    performanceCache.audioMisses++;
    stopActiveAudio();
    currentArticleIndex = index;

    loadingUI.classList.remove('d-none');
    progressBar.style.display = 'block';
    progressBar.value = 0;
    listenBtn.disabled = true;
    listenBtn.innerHTML = '⏳';

    const langCode = selectedVoice.split('-')[0];

    try {
        // Get full content efficiently
        const contentResult = await getFullContent(article);
        article.full_content = contentResult;

        const rawText = article.full_content || article.content || article.description || article.title || '';
        if (!rawText.trim()) {
            alert(t.noText);
            resetAudioUI(listenBtn, loadingUI, progressBar);
            return;
        }

        // Smart optimization - only if not cached
        let summaryText;
        if (article.voiceOptimizedContent && article.voiceOptimizedContent.length > 30) {
            summaryText = article.voiceOptimizedContent;
        } else {
            const res = await fetch('/api/news/voice-optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: rawText, title: article.title })
            });
            const result = await res.json();
            article.voiceOptimizedContent = result.optimized_content?.trim() || rawText;
            summaryText = article.voiceOptimizedContent;
        }

        // Translate if needed
        if (langCode !== 'en') {
            const translateRes = await fetch('/api/news/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: summaryText, target_language: langCode })
            });
            const translateResult = await translateRes.json();
            if (translateResult.translated_text?.trim()) {
                summaryText = translateResult.translated_text.trim();
            }
        }

        // Generate TTS
        const ttsRes = await fetch('/api/news/summary-audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: summaryText,
                title: article.title,
                voice_id: selectedVoice,
                speed: 1.0,
                depth: 1
            })
        });

        const result = await ttsRes.json();

        if (result.audio_url) {
            // Cache immediately for next time
            audioCache.set(cacheKey, result.audio_url);

            // Keep cache manageable
            if (audioCache.size > 25) {
                const firstKey = audioCache.keys().next().value;
                audioCache.delete(firstKey);
            }

            playAudio(result.audio_url, index, listenBtn, loadingUI, progressBar, autoPlay);
        } else {
            alert(t.audioFailed);
            resetAudioUI(listenBtn, loadingUI, progressBar);
        }

    } catch (err) {
        console.error('Audio generation error:', err);
        alert(t.audioError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
    }
}

async function getFullContent(article) {
    // Return immediately if already have good content
    if (article.full_content && article.full_content.length > 500) {
        performanceCache.contentHits++;
        return article.full_content;
    }

    try {
        const startTime = performance.now();
        const res = await fetch(`/api/news/content?url=${encodeURIComponent(article.url)}`);
        const result = await res.json();
        const loadTime = performance.now() - startTime;

        if (result.content && result.content.length > 500) {
            if (loadTime < 300) performanceCache.contentHits++;
            else performanceCache.contentMisses++;
            return result.content;
        } else {
            performanceCache.contentMisses++;
            return article.description || article.title || '';
        }
    } catch (err) {
        performanceCache.contentMisses++;
        return article.description || article.title || '';
    }
}

function playAudio(audioUrl, index, listenBtn, loadingUI, progressBar, autoPlay = true) {
    const t = translations.en;

    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        resetAudioUI(currentPlayButton, null, null);
    }

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

    currentPlayButton = listenBtn;
    currentArticleIndex = index;

    loadingUI.classList.add('d-none');
    listenBtn.disabled = false;

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
            });

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

function stopActiveAudio() {
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        if (currentPlayButton) {
            currentPlayButton.innerHTML = '▶︎ ';
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

function resetAudioUI(listenBtn, loadingUI, progressBar) {
    if (loadingUI) loadingUI.classList.add('d-none');
    if (progressBar) progressBar.style.display = 'none';
    if (listenBtn) {
        listenBtn.disabled = false;
        listenBtn.innerHTML = '▶︎ ';
    }
}

// ==================== OPTIMIZED COMMENT SYSTEM ====================
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
                // Batch DOM updates for better performance
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
                
                // Single DOM update
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

        // Load comments immediately
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

            // Immediate UI feedback
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
                
                // Immediate form reset
                newForm.reset();
                
                // Instant reload of comments
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

// Preload content for better performance
function preloadContent() {
    articles.slice(0, 3).forEach(article => {
        if (!article.full_content) {
            getFullContent(article);
        }
    });
}

// Smart cache management
function optimizeCache() {
    if (audioCache.size > 20) {
        const keysToDelete = Array.from(audioCache.keys()).slice(0, 5);
        keysToDelete.forEach(key => audioCache.delete(key));
    }
}

// Performance monitoring
function trackPerformance() {
    const total = performanceCache.newsHits + performanceCache.newsMisses + 
                  performanceCache.contentHits + performanceCache.contentMisses + 
                  performanceCache.audioHits + performanceCache.audioMisses;
                  
    if (total > 0) {
        const hits = performanceCache.newsHits + performanceCache.contentHits + performanceCache.audioHits;
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

// Start optimization routines
function startOptimizations() {
    // Run optimizations periodically
    setInterval(() => {
        optimizeCache();
        trackPerformance();
        preloadContent();
    }, 30000); // Every 30 seconds
}

// ==================== PERFORMANCE STATS ====================
window.getPerformanceStats = function() {
    const total = performanceCache.newsHits + performanceCache.newsMisses + 
                  performanceCache.contentHits + performanceCache.contentMisses + 
                  performanceCache.audioHits + performanceCache.audioMisses;
                  
    const hits = performanceCache.newsHits + performanceCache.contentHits + performanceCache.audioHits;
    const hitRate = total > 0 ? Math.round((hits / total) * 100) : 0;
    
    return {
        cache: performanceCache,
        audioCache: {
            size: audioCache.size,
            keys: Array.from(audioCache.keys()).slice(0, 5)
        },
        performance: {
            hitRate: hitRate,
            status: hitRate > 85 ? 'Excellent' : hitRate > 60 ? 'Good' : 'Building'
        }
    };
};

console.log('Optimized News Reader loaded - Performance focused!');