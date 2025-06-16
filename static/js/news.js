// Global variables
let articles = [];
let currentCategory = localStorage.getItem('lastCategory') || 'general';
let currentLanguage = localStorage.getItem('lastLanguage') || 'en';
let currentQuery = '';
let siteLanguage = localStorage.getItem('siteLanguage') || 'en';
let darkMode = localStorage.getItem('darkMode') === 'true';

// Audio state
let activeAudio = null;
let currentPlayButton = null;
let currentArticleIndex = null;
let audioCache = new Map(); // Cache for faster audio loading
// Removed: isReadingAll, readAllQueue, readAllButton, resolveModalPromise

// DOM elements
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');
const newsList = document.getElementById('newsList');
const newsTemplate = document.getElementById('newsArticleTemplate');

// Language translations
const translations = {
    en: {
        title: "📰 News Reader",
        search: "Search news...",
        searchBtn: "Search",
        categories: {
            general: "General",
            business: "Business",
            technology: "Technology",
            sports: "Sports",
            health: "Health",
            entertainment: "Entertainment"
        },
        // Removed: readAll, stopReading, readingProgress, of
        noNews: "No news found for",
        tryDifferent: "Try a different keyword or category.",
        unknownSource: "Unknown Source",
        unknownDate: "Unknown Date",
        yesterday: "Yesterday",
        daysAgo: "days ago",
        readFull: "Read Full Article",
        listen: "Listen", // Kept for potential aria-label or other UI element if needed
        selectVoice: "Select Voice",
        darkMode: "Dark Mode",
        lightMode: "Light Mode",
        language: "Language",
        noDescription: "No description available.",
        noText: "This article does not contain any usable text.",
        audioFailed: "Failed to generate audio.",
        audioError: "An error occurred during voice generation.",
        audioLoadError: "Error loading audio. Please try again.",
        loading: "Loading...",
        error: "An error occurred. Please try again later."
        // Removed: readNextArticlePrompt, continueReadingTitle, yes, no
    },
    fr: {
        title: "📰 Lecteur d'Actualités",
        search: "Rechercher des actualités...",
        searchBtn: "Rechercher",
        categories: {
            general: "Général",
            business: "Affaires",
            technology: "Technologie",
            sports: "Sports",
            health: "Santé",
            entertainment: "Divertissement"
        },
        // Removed: readAll, stopReading, readingProgress, of
        noNews: "Aucune actualité trouvée pour",
        tryDifferent: "Essayez un autre mot-clé ou catégorie.",
        unknownSource: "Source Inconnue",
        unknownDate: "Date Inconnue",
        yesterday: "Hier",
        daysAgo: "jours passés",
        readFull: "Lire l'Article Complet",
        listen: "Écouter",
        selectVoice: "Sélectionner la Voix",
        darkMode: "Mode Sombre",
        lightMode: "Mode Clair",
        language: "Langue",
        noDescription: "Aucune description disponible.",
        noText: "Cet article ne contient aucun texte utilisable.",
        audioFailed: "Échec de génération audio.",
        audioError: "Une erreur s'est produite lors de la génération vocale.",
        audioLoadError: "Erreur de chargement audio. Veuillez réessayer.",
        loading: "Chargement...",
        error: "Une erreur s'est produite. Veuillez réessayer plus tard."
        // Removed: readNextArticlePrompt, continueReadingTitle, yes, no
    },
    es: {
        title: "📰 Lector de Noticias",
        search: "Buscar noticias...",
        searchBtn: "Buscar",
        categories: {
            general: "General",
            business: "Negocios",
            technology: "Tecnología",
            sports: "Deportes",
            health: "Salud",
            entertainment: "Entretenimiento"
        },
        // Removed: readAll, stopReading, readingProgress, of
        noNews: "No se encontraron noticias para",
        tryDifferent: "Prueba con otra palabra clave o categoría.",
        unknownSource: "Fuente Desconocida",
        unknownDate: "Fecha Desconocida",
        yesterday: "Ayer",
        daysAgo: "días atrás",
        readFull: "Leer Artículo Completo",
        listen: "Escuchar",
        selectVoice: "Seleccionar Voz",
        darkMode: "Modo Oscuro",
        lightMode: "Modo Claro",
        language: "Idioma",
        noDescription: "No hay descripción disponible.",
        noText: "Este artículo no contiene texto utilizable.",
        audioFailed: "Error al generar audio.",
        audioError: "Ocurrió un error durante la generación de voz.",
        audioLoadError: "Error cargando audio. Por favor intenta de nuevo.",
        loading: "Cargando...",
        error: "Ocurrió un error. Por favor intenta más tarde."
        // Removed: readNextArticlePrompt, continueReadingTitle, yes, no
    },
    ar: {
        title: "📰 قارئ الأخبار",
        search: "البحث في الأخبار...",
        searchBtn: "بحث",
        categories: {
            general: "عام",
            business: "أعمال",
            technology: "تكنولوجيا",
            sports: "رياضة",
            health: "صحة",
            entertainment: "ترفيه"
        },
        // Removed: readAll, stopReading, readingProgress, of
        noNews: "لم يتم العثور على أخبار لـ",
        tryDifferent: "جرب كلمة مفتاحية أو فئة مختلفة.",
        unknownSource: "مصدر غير معروف",
        unknownDate: "تاريخ غير معروف",
        yesterday: "أمس",
        daysAgo: "أيام مضت",
        readFull: "قراءة المقال كاملاً",
        listen: "استمع",
        selectVoice: "اختر الصوت",
        darkMode: "الوضع المظلم",
        lightMode: "الوضع المضيء",
        language: "اللغة",
        noDescription: "لا يوجد وصف متاح.",
        noText: "هذا المقال لا يحتوي على نص قابل للاستخدام.",
        audioFailed: "فشل في توليد الصوت.",
        audioError: "حدث خطأ أثناء توليد الصوت.",
        audioLoadError: "خطأ في تحميل الصوت. يرجى المحاولة مرة أخرى.",
        loading: "جاري التحميل...",
        error: "حدث خطأ. يرجى المحاولة مرة أخرى لاحقاً."
        // Removed: readNextArticlePrompt, continueReadingTitle, yes, no
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Apply saved preferences
    document.getElementById('language').value = currentLanguage;
    document.getElementById('category').value = currentCategory;

    // Initialize theme and language
    initializeTheme();
    initializeLanguage();
    addThemeAndLanguageControls();

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
        currentLanguage = document.getElementById('language').value;
        localStorage.setItem('lastLanguage', currentLanguage);
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
    const locale = siteLanguage === 'ar' ? 'ar-EG' : siteLanguage === 'es' ? 'es-ES' : siteLanguage === 'fr' ? 'fr-FR' : 'en-US';
    document.getElementById('currentDateDisplay').textContent = now.toLocaleDateString(locale, options);
}

// Theme and Language Functions
function initializeTheme() {
    if (darkMode) {
        document.body.classList.add('dark-mode');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        document.documentElement.setAttribute('data-bs-theme', 'light');
    }
}

function initializeLanguage() {
    updateInterfaceLanguage();
    if (siteLanguage === 'ar') {
        document.body.classList.add('rtl');
        document.dir = 'rtl';
    } else {
        document.body.classList.remove('rtl');
        document.dir = 'ltr';
    }
}

function addThemeAndLanguageControls() {
    // Add controls to the top navigation area
    const header = document.querySelector('.container-fluid') || document.body;
    const controlsHTML = `
        <div class="theme-language-controls d-flex align-items-center gap-3 mb-3">
            <div class="theme-toggle">
                <button id="themeToggle" class="btn btn-outline-secondary btn-sm">
                    <span class="theme-icon">${darkMode ? '☀️' : '🌙'}</span>
                    <span class="theme-text">${translations[siteLanguage][darkMode ? 'lightMode' : 'darkMode']}</span>
                </button>
            </div>
            <div class="language-selector">
                <select id="siteLanguageSelect" class="form-select form-select-sm">
                    <option value="en" ${siteLanguage === 'en' ? 'selected' : ''}>🇺🇸 English</option>
                    <option value="fr" ${siteLanguage === 'fr' ? 'selected' : ''}>🇫🇷 Français</option>
                    <option value="es" ${siteLanguage === 'es' ? 'selected' : ''}>🇪🇸 Español</option>
                    <option value="ar" ${siteLanguage === 'ar' ? 'selected' : ''}>🇸🇦 العربية</option>
                </select>
            </div>
        </div>
    `;

    if (header.firstChild) {
        header.insertAdjacentHTML('afterbegin', controlsHTML);
    } else {
        header.innerHTML = controlsHTML + header.innerHTML;
    }

    // Add event listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('siteLanguageSelect').addEventListener('change', changeSiteLanguage);
}

function toggleTheme() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode.toString());
    initializeTheme();

    const themeButton = document.getElementById('themeToggle');
    const themeIcon = themeButton.querySelector('.theme-icon');
    const themeText = themeButton.querySelector('.theme-text');

    themeIcon.textContent = darkMode ? '☀️' : '🌙';
    themeText.textContent = translations[siteLanguage][darkMode ? 'lightMode' : 'darkMode'];
}

function changeSiteLanguage(e) {
    siteLanguage = e.target.value;
    localStorage.setItem('siteLanguage', siteLanguage);
    initializeLanguage();
    updateCurrentDate();

    // Update theme toggle text
    const themeText = document.querySelector('.theme-text');
    if (themeText) {
        themeText.textContent = translations[siteLanguage][darkMode ? 'lightMode' : 'darkMode'];
    }
}

function updateInterfaceLanguage() {
    const t = translations[siteLanguage];

    // Update title
    const titleElement = document.querySelector('h1, .title');
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

    // Update language label
    const languageLabel = document.querySelector('label[for="language"]');
    if (languageLabel) languageLabel.textContent = t.language + ':';
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
    const t = translations[siteLanguage];
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
        const params = new URLSearchParams({ category: currentCategory, language: currentLanguage });
        if (currentQuery) params.append('query', currentQuery);
        const response = await fetch(`/api/news?${params}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        articles = data.articles || [];
        if (!articles.length) return showEmpty();
        displayNews(articles);
        hideStates();
    } catch (error) {
        console.error('Error loading news:', error);
        showError(error.message);
    }
}

function displayNews(articlesData) {
    newsList.innerHTML = '';
    // Removed: "Read All Articles" button and its container logic
    // Removed: readAllBtn and its event listener

    articlesData.forEach((article, index) => {
        const articleElement = createArticleElement(article, index);
        newsList.appendChild(articleElement);
    });
}

function createArticleElement(article, index) {
    const template = newsTemplate.content.cloneNode(true);
    const t = translations[siteLanguage];

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
    readBtn.textContent = t.readFull;

    const listenBtn = template.querySelector('.article-listen-btn');
    listenBtn.dataset.index = index;
    // Only use the play emoji for the initial state
    listenBtn.innerHTML = '▶︎';
    listenBtn.onclick = () => listenToSummary(index);

    const voiceSelect = template.querySelector('.voice-select');
    voiceSelect.id = `voice-select-${index}`;
    voiceSelect.dataset.articleIndex = index;

    // Add voice select label
    const voiceLabel = template.querySelector('.voice-label');
    if (voiceLabel) voiceLabel.textContent = t.selectVoice + ':';

    const progress = template.querySelector('.audio-progress');
    progress.style.display = 'none';
    progress.value = 0;

    return template;
}

function stopActiveAudio() {
    if (activeAudio) {
        activeAudio.pause();
        activeAudio.currentTime = 0;
        if (currentPlayButton) {
            // Reset to play emoji
            currentPlayButton.innerHTML = '▶︎';
            currentPlayButton.disabled = false;
        }

        // Hide loading and progress for current article
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
    // Removed: stopReadAll() call if isReadingAll
}

document.addEventListener('change', function(e) {
    if (e.target.classList.contains('voice-select')) {
        const articleIndex = parseInt(e.target.dataset.articleIndex);
        const newVoice = e.target.value;
        localStorage.setItem('lastVoice', newVoice);

        console.log(`Voice changed for article ${articleIndex}: ${newVoice}`);

        // Clear cache for this article when voice changes
        const cacheKey = `${articleIndex}-${newVoice}`;
        audioCache.delete(cacheKey);

        // Check if this is the currently active article (playing or paused)
        if (currentArticleIndex === articleIndex) {
            console.log('Voice changed for active article, regenerating immediately...');

            // Remember if it was playing
            const wasPlaying = activeAudio && !activeAudio.paused;

            // Stop current audio
            stopActiveAudio();

            // Regenerate audio with new voice immediately
            // No delay needed for better UX
            listenToSummary(articleIndex, wasPlaying);
        }
    }
});

function formatDate(dateString) {
    const t = translations[siteLanguage];
    if (!dateString) return t.unknownDate;

    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return t.yesterday;
    if (diffDays < 7) return `${diffDays} ${t.daysAgo}`;

    const locale = siteLanguage === 'ar' ? 'ar-EG' : siteLanguage === 'es' ? 'es-ES' : siteLanguage === 'fr' ? 'fr-FR' : 'en-US';
    return date.toLocaleDateString(locale);
}

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
            listenBtn.innerHTML = '‖'; // Pause emoji
        } else {
            activeAudio.pause();
            listenBtn.innerHTML = '▶︎'; // Play emoji
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

    // Generate new audio
    stopActiveAudio();
    currentArticleIndex = index;

    loadingUI.classList.remove('d-none');
    progressBar.style.display = 'block';
    progressBar.value = 0;
    listenBtn.disabled = true;
    listenBtn.innerHTML = '⏳'; // Loading emoji

    card.scrollIntoView({ behavior: 'smooth', block: 'center' });

    const langCode = selectedVoice.split('-')[0];
    const rawText = article.content || article.description || article.full_content || article.title || '';

    if (!rawText.trim()) {
        alert(t.noText);
        resetAudioUI(listenBtn, loadingUI, progressBar);
        return;
    }

    try {
        // Optimize content if needed
        if (!article.voiceOptimizedContent || article.voiceOptimizedContent.length < 30) {
            const res = await fetch('/api/news/voice-optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: rawText, title: article.title })
            });
            const result = await res.json();
            article.voiceOptimizedContent = result.optimized_content?.trim() || rawText;
        }

        let summaryText = article.voiceOptimizedContent;

        // Translate if needed
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
            // Cache the audio URL for faster future access
            audioCache.set(cacheKey, result.audio_url);

            // Limit cache size to prevent memory issues
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

// Function to play audio and handle end-of-audio logic
function playAudio(audioUrl, index, listenBtn, loadingUI, progressBar, autoPlay = true) {
    activeAudio = new Audio(audioUrl);
    currentPlayButton = listenBtn;
    currentArticleIndex = index;
    const t = translations[siteLanguage];

    // Setup audio events
    activeAudio.onloadeddata = () => {
        loadingUI.classList.add('d-none');
        listenBtn.disabled = false;

        if (autoPlay) {
            activeAudio.play();
            listenBtn.innerHTML = '‖'; // Pause emoji
        } else {
            listenBtn.innerHTML = '▶︎'; // Play emoji
        }
    };

    activeAudio.ontimeupdate = () => {
        if (progressBar && activeAudio.duration) {
            progressBar.value = (activeAudio.currentTime / activeAudio.duration) * 100;
        }
    };

    activeAudio.onended = () => {
        resetAudioUI(listenBtn, loadingUI, progressBar);

        // Normal single article mode - audio ends and stops
        activeAudio = null;
        currentPlayButton = null;
        currentArticleIndex = null;
    };

    activeAudio.onerror = () => {
        alert(t.audioLoadError);
        resetAudioUI(listenBtn, loadingUI, progressBar);
    };
}

// Function to reset audio UI elements
function resetAudioUI(listenBtn, loadingUI, progressBar) {
    if (loadingUI) loadingUI.classList.add('d-none');
    if (progressBar) progressBar.style.display = 'none';
    if (listenBtn) {
        listenBtn.disabled = false;
        // Reset to play emoji
        listenBtn.innerHTML = '▶︎';
    }
}

// Removed: showCustomConfirm function (as it's tied to Read All auto-advance)
// Removed: All Read All Articles Functions (toggleReadAll, startReadAll, stopReadAll, etc.)

function highlightCurrentArticle(index) {
    // This function was primarily for "Read All" highlighting.
    // Keeping it as a generic utility, but it won't be called automatically now.
    // If you plan to introduce other highlighting features, keep it.
    // If not, it can also be removed. For now, it's harmless.
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