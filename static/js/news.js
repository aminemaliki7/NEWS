// Global variables
let currentArticles = [];
let articleModal;
let currentArticleData = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing news page');
    
    // Find DOM Elements
    const categorySelect = document.getElementById('category');
    const languageSelect = document.getElementById('language');
    const searchInput = document.getElementById('searchQuery');
    const searchBtn = document.getElementById('searchBtn');
    const newsList = document.getElementById('newsList');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const emptyState = document.getElementById('emptyState');
    const errorState = document.getElementById('errorState');
    const generateVoiceBtn = document.getElementById('generateVoiceBtn');

    // Content tabs
    const fullContentBtn = document.getElementById('fullContentBtn');
    const summaryBtn = document.getElementById('summaryBtn');
    const voiceOptimizedBtn = document.getElementById('voiceOptimizedBtn');
    const fullContent = document.getElementById('fullContent');
    const summaryContent = document.getElementById('summaryContent');
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    const contentWordCount = document.getElementById('contentWordCount');
    
    // Check if elements exist and log results
    console.log('DOM Elements found:', {
        categorySelect: !!categorySelect,
        searchBtn: !!searchBtn,
        fullContentBtn: !!fullContentBtn,
        articleModal: !!document.getElementById('articleModal')
    });
    
    // Initialize Bootstrap modal
    try {
        if (typeof bootstrap !== 'undefined' && document.getElementById('articleModal')) {
            articleModal = new bootstrap.Modal(document.getElementById('articleModal'));
            console.log('Modal initialized successfully');
        } else {
            console.error('Bootstrap or modal element not found');
        }
    } catch (error) {
        console.error('Error initializing modal:', error);
    }
    
    // Add event listeners
    if (searchBtn) {
        searchBtn.addEventListener('click', fetchNews);
        console.log('Search button listener added');
    }
    
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                fetchNews();
            }
        });
    }
    
    // Voice parameters
    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speedValue');
    if (speedSlider && speedValue) {
        speedSlider.addEventListener('input', function() {
            speedValue.textContent = this.value;
        });
    }
    
    const depthSlider = document.getElementById('depth');
    const depthValue = document.getElementById('depthValue');
    if (depthSlider && depthValue) {
        depthSlider.addEventListener('input', function() {
            depthValue.textContent = this.value;
        });
    }
    
    // Voice language change handler
    const voiceLanguageSelect = document.getElementById('voiceLanguage');
    const voiceIdSelect = document.getElementById('voiceId');
    
    if (voiceLanguageSelect && voiceIdSelect) {
        voiceLanguageSelect.addEventListener('change', function() {
            updateVoiceOptions(this.value);
        });
        
        // Initialize voice options
        if (voiceLanguageSelect.options.length > 0) {
            updateVoiceOptions(voiceLanguageSelect.value);
        }
        console.log('Voice language handlers initialized');
    }
    
    // Generate voice button handler
    if (generateVoiceBtn) {
        generateVoiceBtn.addEventListener('click', function() {
            console.log('Generate voice button clicked');
            generateVoice();
        });
    }
    
    // Content tab switchers
    if (fullContentBtn && summaryBtn && voiceOptimizedBtn) {
        fullContentBtn.addEventListener('click', function() {
            switchContentTab('full');
        });
        
        summaryBtn.addEventListener('click', function() {
            switchContentTab('summary');
        });
        
        voiceOptimizedBtn.addEventListener('click', function() {
            switchContentTab('voice-optimized');
        });
        console.log('Content tab listeners added');
    }
    
    // Fetch news on initial load
    console.log('Fetching initial news');
    fetchNews();
});

// Update available voices based on selected language
function updateVoiceOptions(selectedLanguage) {
    const voiceIdSelect = document.getElementById('voiceId');
    if (!voiceIdSelect) return;
    
    // Hide options that don't match the selected language
    Array.from(voiceIdSelect.options).forEach(option => {
        const optionLanguage = option.getAttribute('data-language');
        option.style.display = optionLanguage === selectedLanguage ? '' : 'none';
    });
    
    // Select the first available option for the language
    const firstMatchingOption = Array.from(voiceIdSelect.options).find(
        option => option.getAttribute('data-language') === selectedLanguage
    );
    
    if (firstMatchingOption) {
        firstMatchingOption.selected = true;
    }
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

// Show error message
function showError(message) {
    const errorState = document.getElementById('errorState');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const emptyState = document.getElementById('emptyState');
    
    if (errorState) {
        errorState.textContent = message || 'An error occurred while fetching news. Please try again later.';
        errorState.classList.remove('d-none');
    }
    
    if (loadingIndicator) {
        loadingIndicator.classList.add('d-none');
    }
    
    if (emptyState) {
        emptyState.classList.add('d-none');
    }
}

// Hide error message
function hideError() {
    const errorState = document.getElementById('errorState');
    if (errorState) {
        errorState.classList.add('d-none');
    }
}

// Fetch news articles
async function fetchNews() {
    console.log('Fetching news articles');
    
    const categorySelect = document.getElementById('category');
    const languageSelect = document.getElementById('language');
    const searchInput = document.getElementById('searchQuery');
    const newsList = document.getElementById('newsList');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const emptyState = document.getElementById('emptyState');
    
    if (!categorySelect || !languageSelect || !newsList) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Show loading state
    if (loadingIndicator) loadingIndicator.classList.remove('d-none');
    if (emptyState) emptyState.classList.add('d-none');
    if (newsList) newsList.innerHTML = '';
    hideError();
    
    // Get search parameters
    const category = categorySelect.value;
    const language = languageSelect.value;
    const query = searchInput ? searchInput.value.trim() : '';
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            category: category,
            language: language
        });
        
        if (query) {
            params.append('query', query);
        }
        
        console.log('Fetching with params:', params.toString());
        
        // Fetch news from API
        const response = await fetch(`/api/news?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Check for API errors
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Store articles and display them
        currentArticles = data.articles || [];
        displayArticles(currentArticles);
        
    } catch (error) {
        console.error('Error fetching news:', error);
        showError(error.message);
    } finally {
        if (loadingIndicator) loadingIndicator.classList.add('d-none');
    }
}

// Display news articles
function displayArticles(articles) {
    console.log('Displaying articles:', articles.length);
    
    const newsList = document.getElementById('newsList');
    const emptyState = document.getElementById('emptyState');
    
    if (!newsList) {
        console.error('News list element not found');
        return;
    }
    
    // Clear the list
    newsList.innerHTML = '';
    
    // Check if there are articles to display
    if (!articles || articles.length === 0) {
        if (emptyState) {
            emptyState.classList.remove('d-none');
            emptyState.textContent = 'No articles found. Try different search criteria.';
        }
        return;
    }
    
    // Hide empty state
    if (emptyState) {
        emptyState.classList.add('d-none');
    }
    
    // Get the article template
    const template = document.getElementById('newsArticleTemplate');
    if (!template) {
        console.error('Article template not found');
        return;
    }
    
    // Create article elements from template
    articles.forEach((article, index) => {
        // Clone template
        const articleElement = document.importNode(template.content, true);
        
        // Populate with article data
        articleElement.querySelector('.article-title').textContent = article.title;
        articleElement.querySelector('.source-name').textContent = article.source.name;
        articleElement.querySelector('.publish-date').textContent = formatDate(article.publishedAt);
        articleElement.querySelector('.article-description').textContent = article.description;
        
        // Set image (with fallback)
        const imageElement = articleElement.querySelector('.article-image');
        imageElement.src = article.image || '/static/images/news-placeholder.jpg';
        imageElement.alt = article.title;
        
        // Set read article link
        const readLink = articleElement.querySelector('.article-read-btn');
        readLink.href = article.url;
        
        // Set convert to voice action
        const convertBtn = articleElement.querySelector('.article-voice-btn');
        convertBtn.dataset.index = index;
        
        // We're using onclick in the HTML now, but add this as a backup
        convertBtn.addEventListener('click', function() {
            console.log('Convert button clicked for article:', index);
            openArticleModal(index);
        });
        
        // Add to news list
        newsList.appendChild(articleElement);
    });
    
    console.log('Articles displayed successfully');
}

// Count words in text
function countWords(text) {
    return text.split(/\s+/).filter(Boolean).length;
}

// Switch between content tabs
function switchContentTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    const fullContentBtn = document.getElementById('fullContentBtn');
    const summaryBtn = document.getElementById('summaryBtn');
    const voiceOptimizedBtn = document.getElementById('voiceOptimizedBtn');
    const fullContent = document.getElementById('fullContent');
    const summaryContent = document.getElementById('summaryContent');
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    
    if (!fullContentBtn || !summaryBtn || !voiceOptimizedBtn || 
        !fullContent || !summaryContent || !voiceOptimizedContent) {
        console.error('Tab elements not found');
        return;
    }
    
    // Reset all buttons and content containers
    [fullContentBtn, summaryBtn, voiceOptimizedBtn].forEach(btn => {
        btn.classList.remove('active');
    });
    
    [fullContent, summaryContent, voiceOptimizedContent].forEach(container => {
        container.classList.add('d-none');
    });
    
    // Activate the selected tab
    switch (tabName) {
        case 'full':
            fullContentBtn.classList.add('active');
            fullContent.classList.remove('d-none');
            break;
        case 'summary':
            summaryBtn.classList.add('active');
            summaryContent.classList.remove('d-none');
            
            // Generate summary if needed
            if (summaryContent.querySelector('.content-placeholder')) {
                generateSummary();
            }
            break;
        case 'voice-optimized':
            voiceOptimizedBtn.classList.add('active');
            voiceOptimizedContent.classList.remove('d-none');
            
            // Generate voice-optimized content if needed
            if (voiceOptimizedContent.querySelector('.content-placeholder')) {
                generateVoiceOptimized();
            }
            break;
    }
    
    // Update word count
    updateWordCount();
}

// Update word count display
function updateWordCount() {
    const fullContent = document.getElementById('fullContent');
    const summaryContent = document.getElementById('summaryContent');
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    const contentWordCount = document.getElementById('contentWordCount');
    
    if (!fullContent || !summaryContent || !voiceOptimizedContent || !contentWordCount) {
        return;
    }
    
    // Get the active content container
    let activeContent;
    if (!fullContent.classList.contains('d-none')) {
        activeContent = fullContent;
    } else if (!summaryContent.classList.contains('d-none')) {
        activeContent = summaryContent;
    } else {
        activeContent = voiceOptimizedContent;
    }
    
    // Get text and count words
    const text = activeContent.textContent || '';
    const count = countWords(text);
    
    // Update the display
    contentWordCount.textContent = count;
}

// Generate article summary
async function generateSummary() {
    console.log('Generating article summary');
    
    const summaryContent = document.getElementById('summaryContent');
    
    if (!summaryContent) {
        console.error('Summary content element not found');
        return;
    }
    
    if (!currentArticleData || !currentArticleData.content) {
        summaryContent.innerHTML = '<div class="alert alert-warning">Unable to generate summary. Content not available.</div>';
        return;
    }
    
    try {
        // Show loading state
        summaryContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Generating summary...</span>
                </div>
                <p class="mt-2">Generating summary...</p>
            </div>
        `;
        
        // Call API to generate summary
        const response = await fetch('/api/news/summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: currentArticleData.content,
                title: currentArticleData.title
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Summary generated:', data);
        
        // Display summary
        if (data.summary) {
            summaryContent.innerHTML = data.summary.split('\n').map(para => `<p>${para}</p>`).join('');
            updateWordCount();
        } else {
            throw new Error('No summary returned from the server');
        }
        
    } catch (error) {
        console.error('Error generating summary:', error);
        summaryContent.innerHTML = `
            <div class="alert alert-danger">
                Failed to generate summary: ${error.message}
            </div>
        `;
    }
}

// Generate voice-optimized content
async function generateVoiceOptimized() {
    console.log('Generating voice-optimized content');
    
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    
    if (!voiceOptimizedContent) {
        console.error('Voice optimized content element not found');
        return;
    }
    
    if (!currentArticleData || !currentArticleData.content) {
        voiceOptimizedContent.innerHTML = '<div class="alert alert-warning">Unable to generate voice-optimized content. Content not available.</div>';
        return;
    }
    
    try {
        // Show loading state
        voiceOptimizedContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Optimizing for voice...</span>
                </div>
                <p class="mt-2">Optimizing content for voice narration...</p>
            </div>
        `;
        
        // Call API to generate voice-optimized content
        const response = await fetch('/api/news/voice-optimize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: currentArticleData.content,
                title: currentArticleData.title
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Voice-optimized content generated:', data);
        
        // Display voice-optimized content
        if (data.optimized_content) {
            voiceOptimizedContent.innerHTML = data.optimized_content.split('\n').map(para => `<p>${para}</p>`).join('');
            updateWordCount();
        } else {
            throw new Error('No optimized content returned from the server');
        }
        
    } catch (error) {
        console.error('Error generating voice-optimized content:', error);
        voiceOptimizedContent.innerHTML = `
            <div class="alert alert-danger">
                Failed to optimize content: ${error.message}
            </div>
        `;
    }
}

// Manual show modal function as fallback
function showModal(modalElement) {
    console.log('Manual showModal called');
    if (!modalElement) return false;
    
    try {
        // Try using Bootstrap's modal if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const bsModal = new bootstrap.Modal(modalElement);
            bsModal.show();
            console.log('Modal shown via Bootstrap');
            return true;
        }
    } catch (error) {
        console.warn('Failed to show modal with Bootstrap:', error);
        // Continue to manual fallback
    }
    
    // Manual fallback
    try {
        modalElement.classList.add('show');
        modalElement.style.display = 'block';
        document.body.classList.add('modal-open');
        
        // Create backdrop
        let backdrop = document.querySelector('.modal-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.classList.add('modal-backdrop', 'fade', 'show');
            document.body.appendChild(backdrop);
        }
        
        console.log('Modal shown manually');
        return true;
    } catch (error) {
        console.error('Failed to show modal manually:', error);
        return false;
    }
}

// Open article modal
function openArticleModal(articleIndex) {
    console.log('Opening article modal for index:', articleIndex);
    
    // Extract the correct article index if it's a string
    if (typeof articleIndex === 'string') {
        articleIndex = parseInt(articleIndex, 10);
    }
    
    const article = currentArticles[articleIndex];
    if (!article) {
        console.error('Article not found for index:', articleIndex);
        return;
    }
    
    console.log('Found article:', article.title);
    
    const fullContent = document.getElementById('fullContent');
    const summaryContent = document.getElementById('summaryContent');
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    const modalArticleTitle = document.getElementById('modalArticleTitle');
    const modalArticleSource = document.getElementById('modalArticleSource');
    const outputTitle = document.getElementById('outputTitle');
    const modalElement = document.getElementById('articleModal');
    
    if (!fullContent || !summaryContent || !voiceOptimizedContent || 
        !modalArticleTitle || !modalArticleSource || !outputTitle || !modalElement) {
        console.error('Modal elements not found');
        alert('Error: Modal elements not found');
        return;
    }
    
    // Reset modal state
    fullContent.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading article content...</span>
            </div>
            <p class="mt-2">Loading article content...</p>
        </div>
    `;
    summaryContent.innerHTML = '<div class="content-placeholder">Generating summary...</div>';
    voiceOptimizedContent.innerHTML = '<div class="content-placeholder">Optimizing for voice...</div>';
    
    // Set article info in modal
    modalArticleTitle.textContent = article.title;
    modalArticleSource.textContent = `${article.source.name} • ${formatDate(article.publishedAt)}`;
    
    // Prefill output title with article title
    outputTitle.value = article.title;
    
    // Reset to full content tab
    switchContentTab('full');
    
    // Show the modal - try various approaches
    console.log('Attempting to show modal');
    
    let modalOpened = false;
    
    // Try using articleModal variable if initialized
    if (articleModal) {
        try {
            articleModal.show();
            modalOpened = true;
            console.log('Modal shown with articleModal variable');
        } catch (error) {
            console.error('Error showing modal with articleModal:', error);
        }
    }
    
    // If not opened yet, try reinitializing Bootstrap
    if (!modalOpened && typeof bootstrap !== 'undefined') {
        try {
            const newModal = new bootstrap.Modal(modalElement);
            newModal.show();
            articleModal = newModal; // Update the global reference
            modalOpened = true;
            console.log('Modal shown with new Bootstrap Modal');
        } catch (error) {
            console.error('Error showing modal with new Bootstrap Modal:', error);
        }
    }
    
    // As a last resort, use manual method
    if (!modalOpened) {
        modalOpened = showModal(modalElement);
    }
    
    if (!modalOpened) {
        console.error('All methods to show modal failed');
        alert('Error: Could not open article modal. Check console for details.');
        return;
    }
    
    // Fetch article content
    fetchArticleContent(article);
}

// Fetch article content
async function fetchArticleContent(article) {
    console.log('Fetching content for article:', article.title);
    
    const fullContent = document.getElementById('fullContent');
    
    if (!fullContent) {
        console.error('Full content element not found');
        return;
    }
    
    try {
        // Show loading state
        fullContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading article content...</span>
                </div>
                <p class="mt-2">Loading article content...</p>
            </div>
        `;
        
        // Fetch article content
        const response = await fetch(`/api/news/content?url=${encodeURIComponent(article.url)}`);
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Article content received:', data);
        
        // Check for API errors
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Check if content is empty or contains an extraction error
        if (!data.content || data.content.trim() === '' || data.extraction_error) {
            throw new Error(data.extraction_error || 'No content available');
        }
        
        // Store current article data
        currentArticleData = {
            title: article.title,
            url: article.url,
            source: article.source,
            publishedAt: article.publishedAt,
            content: data.content
        };
        
        // Display article content
        fullContent.innerHTML = data.content.split('\n').map(para => para.trim() ? `<p>${para}</p>` : '').join('');
        updateWordCount();
        
    } catch (error) {
        console.error('Error fetching article content:', error);
        
        // Provide a more user-friendly error message with options
        fullContent.innerHTML = `
            <div class="alert alert-warning">
                <h5>Unable to extract article content</h5>
                <p>${error.message}</p>
                <p>Some websites prevent automatic content extraction. You have these options:</p>
                <ul>
                    <li>Visit the <a href="${article.url}" target="_blank" rel="noopener">original article</a> and copy the text manually</li>
                    <li>Try another article from the results list</li>
                    <li>Enter custom text below to convert to voice</li>
                </ul>
                
                <div class="mt-3">
                    <textarea id="customContent" class="form-control" rows="6" 
                        placeholder="Paste or type the article content here..."></textarea>
                    <button id="useCustomContent" class="btn btn-primary mt-2">
                        Use This Content
                    </button>
                </div>
            </div>
        `;
        
        // Add event listener for the custom content button
        const useCustomContentBtn = document.getElementById('useCustomContent');
        const customContentTextarea = document.getElementById('customContent');
        
        if (useCustomContentBtn && customContentTextarea) {
            useCustomContentBtn.addEventListener('click', function() {
                const content = customContentTextarea.value.trim();
                if (content) {
                    // Store the custom content
                    currentArticleData = {
                        title: article.title,
                        url: article.url,
                        source: article.source,
                        publishedAt: article.publishedAt,
                        content: content
                    };
                    
                    // Display the content
                    fullContent.innerHTML = content.split('\n').map(para => para.trim() ? `<p>${para}</p>` : '').join('');
                    updateWordCount();
                }
            });
        }
    }
}

// Generate voice from article
function generateVoice() {
    console.log('Generating voice from article');
    
    const fullContent = document.getElementById('fullContent');
    const summaryContent = document.getElementById('summaryContent');
    const voiceOptimizedContent = document.getElementById('voiceOptimizedContent');
    const modalArticleTitle = document.getElementById('modalArticleTitle');
    const outputTitle = document.getElementById('outputTitle');
    const voiceId = document.getElementById('voiceId');
    const speed = document.getElementById('speed');
    const depth = document.getElementById('depth');
    const articleModal = document.getElementById('articleModal');
    
    if (!fullContent || !summaryContent || !voiceOptimizedContent || 
        !modalArticleTitle || !outputTitle || !voiceId || !speed || !depth) {
        console.error('Form elements not found');
        alert('Error: Form elements not found');
        return;
    }
    
    // Get active content
    let contentToUse;
    
    if (!fullContent.classList.contains('d-none')) {
        contentToUse = fullContent.textContent;
    } else if (!summaryContent.classList.contains('d-none')) {
        contentToUse = summaryContent.textContent;
    } else {
        contentToUse = voiceOptimizedContent.textContent;
    }
    
    // Get modal values
    const articleTitle = modalArticleTitle.textContent;
    const finalOutputTitle = outputTitle.value || articleTitle;
    const finalVoiceId = voiceId.value;
    const finalSpeed = speed.value;
    const finalDepth = depth.value;
    
    // Check if content is available
    if (!contentToUse || contentToUse.trim() === '') {
        alert('No content available to convert to voice. Please try again.');
        return;
    }
    
    console.log('Form data:', {
        title: finalOutputTitle,
        voiceId: finalVoiceId,
        speed: finalSpeed,
        depth: finalDepth,
        contentLength: contentToUse.length
    });
    
    // Create form for submission
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/upload';
    form.style.display = 'none';
    
    // Add form fields
    const addFormField = (name, value) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        form.appendChild(input);
    };
    
    // Add all necessary form fields
    addFormField('text-content', contentToUse);
    addFormField('voice', finalVoiceId);
    addFormField('speed', finalSpeed);
    addFormField('depth', finalDepth);
    addFormField('title', finalOutputTitle);
    addFormField('input-method', 'text');
    
    // Add form to document and submit
    document.body.appendChild(form);
    
    console.log('Submitting form for voice generation');
    form.submit();
    
    // Hide modal using Bootstrap if available
    try {
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const bsModal = bootstrap.Modal.getInstance(articleModal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    } catch (error) {
        console.warn('Error hiding modal with Bootstrap:', error);
        // Try manual hiding
        if (articleModal) {
            articleModal.classList.remove('show');
            articleModal.style.display = 'none';
            document.body.classList.remove('modal-open');
            
            // Remove backdrop
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
    }
}
// YouTube script generator
const youtubeScriptBtn = document.getElementById('youtubeScriptBtn');
const generateYouTubeScriptBtn = document.getElementById('generateYouTubeScriptBtn');
const youtubeWordLimit = document.getElementById('youtubeWordLimit');

if (youtubeScriptBtn) {
    youtubeScriptBtn.addEventListener('click', function() {
        switchContentTab('youtube-script');
    });
}

if (generateYouTubeScriptBtn) {
    generateYouTubeScriptBtn.addEventListener('click', generateYouTubeScript);
}

if (youtubeWordLimit) {
    youtubeWordLimit.addEventListener('input', updateYouTubeWordLimitDisplay);
}