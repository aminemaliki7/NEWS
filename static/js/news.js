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
let activeAudioJobId = null; // This might become less relevant if all audio is direct

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

window.articles = articles;
