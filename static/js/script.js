// Core JavaScript for RealTalk - Minimal version

document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const textInput = document.getElementById('text-content');
    const fileInput = document.getElementById('script');
    const inputMethodField = document.getElementById('input-method');
    const speedSlider = document.getElementById('speed');
    const depthSlider = document.getElementById('depth');
    const speedValue = document.getElementById('speedValue');
    const depthValue = document.getElementById('depthValue');
    const languageSelect = document.getElementById('language');
    const voiceSelect = document.getElementById('voice');
    const fileUploadArea = document.querySelector('.file-upload-area');
    
    // Track input method changes
    const textTab = document.getElementById('text-tab');
    const fileTab = document.getElementById('file-tab');
    
    if (textTab && fileTab) {
        textTab.addEventListener('click', function() {
            if (inputMethodField) inputMethodField.value = 'text';
            showActiveTab('text');
        });
        
        fileTab.addEventListener('click', function() {
            if (inputMethodField) inputMethodField.value = 'file';
            showActiveTab('file');
        });
    }
    
    // Tab switching functionality
    function showActiveTab(tabType) {
        const allTabs = document.querySelectorAll('.tab-pane');
        const allNavLinks = document.querySelectorAll('.nav-link');
        
        allTabs.forEach(tab => {
            tab.classList.remove('show', 'active');
        });
        
        allNavLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        if (tabType === 'text') {
            document.getElementById('text-input').classList.add('show', 'active');
            document.getElementById('text-tab').classList.add('active');
        } else if (tabType === 'file') {
            document.getElementById('file-input').classList.add('show', 'active');
            document.getElementById('file-tab').classList.add('active');
        }
    }
    
    // Initialize voices on page load
    updateVoices();
    
    // File upload handling with drag and drop
    if (fileUploadArea && fileInput) {
        // Display selected filename
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                displaySelectedFile(this.files[0]);
            }
        });
        
        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            fileUploadArea.classList.add('highlight');
        }
        
        function unhighlight() {
            fileUploadArea.classList.remove('highlight');
        }
        
        fileUploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files && files.length) {
                fileInput.files = files;
                displaySelectedFile(files[0]);
            }
        }
        
        function displaySelectedFile(file) {
            const fileName = file.name;
            const fileSize = (file.size / 1024).toFixed(2) + ' KB';
            
            // Update UI to show selected file
            fileUploadArea.innerHTML = `
                <div class="selected-file">
                    <span class="file-name">${fileName}</span>
                    <span class="file-size">(${fileSize})</span>
                    <button type="button" class="btn-close btn-sm ms-2" aria-label="Remove file"></button>
                </div>
            `;
            
            // Add event listener to remove button
            fileUploadArea.querySelector('.btn-close').addEventListener('click', function(e) {
                e.preventDefault();
                fileInput.value = '';
                resetFileUploadArea();
            });
        }
        
        function resetFileUploadArea() {
            fileUploadArea.innerHTML = `
                <p class="mb-2">Drag and drop your file here or</p>
                <label for="script" class="btn btn-outline-primary">
                    Browse Files
                    <input type="file" class="d-none" id="script" name="script" accept=".txt">
                </label>
                <p class="small text-muted mt-2">Supported formats: .txt (Max 10MB)</p>
            `;
        }
    }
    
    // Save preferences to localStorage
    function saveUserPreferences() {
        if (!languageSelect || !voiceSelect || !speedSlider || !depthSlider) return;
        
        const preferences = {
            lastUsedVoice: voiceSelect.value,
            lastUsedLanguage: languageSelect.value,
            lastUsedSpeed: speedSlider.value,
            lastUsedDepth: depthSlider.value
        };
        
        localStorage.setItem('realtalkPreferences', JSON.stringify(preferences));
    }
    
    // Load preferences from localStorage
    function loadUserPreferences() {
        const savedPreferences = localStorage.getItem('realtalkPreferences');
        
        if (savedPreferences) {
            const preferences = JSON.parse(savedPreferences);
            
            // Set language
            if (preferences.lastUsedLanguage && languageSelect) {
                languageSelect.value = preferences.lastUsedLanguage;
                updateVoices();
            }
            
            // Set voice
            if (preferences.lastUsedVoice && voiceSelect) {
                voiceSelect.value = preferences.lastUsedVoice;
            }
            
            // Set speed
            if (preferences.lastUsedSpeed && speedSlider) {
                speedSlider.value = preferences.lastUsedSpeed;
                updateSpeedValue();
            }
            
            // Set depth
            if (preferences.lastUsedDepth && depthSlider) {
                depthSlider.value = preferences.lastUsedDepth;
                updateDepthValue();
            }
        }
    }
    
    // Load preferences on page load
    loadUserPreferences();
    
    // Save preferences when values change
    [languageSelect, voiceSelect, speedSlider, depthSlider].forEach(element => {
        if (element) {
            element.addEventListener('change', saveUserPreferences);
            element.addEventListener('input', saveUserPreferences);
        }
    });
    
    // Auto-save text input as draft
    let saveTimeout;
    if (textInput) {
        textInput.addEventListener('input', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                localStorage.setItem('realtalkDraft', this.value);
            }, 1000);
        });
        
        // Load draft on page load
        const savedDraft = localStorage.getItem('realtalkDraft');
        if (savedDraft && !textInput.value) {
            textInput.value = savedDraft;
        }
    }
    
    // Character limit warning
    if (textInput) {
        const characterLimit = 5000;
        
        textInput.addEventListener('input', function() {
            const currentLength = this.value.length;
            if (currentLength > characterLimit) {
                showCharacterLimitWarning(currentLength, characterLimit);
            } else {
                clearCharacterLimitWarning();
            }
        });
    }
    
    function showCharacterLimitWarning(current, limit) {
        let warning = document.getElementById('characterWarning');
        
        if (!warning) {
            warning = document.createElement('div');
            warning.id = 'characterWarning';
            warning.style.position = 'fixed';
            warning.style.bottom = '20px';
            warning.style.left = '50%';
            warning.style.transform = 'translateX(-50%)';
            warning.style.padding = '8px 16px';
            warning.style.fontSize = '12px';
            warning.style.backgroundColor = '#000';
            warning.style.color = '#fff';
            warning.style.border = '1px solid #000';
            warning.style.zIndex = '1001';
            
            document.body.appendChild(warning);
        }
        
        warning.innerHTML = `Character limit exceeded: ${current}/${limit}`;
        warning.style.display = 'block';
    }
    
    function clearCharacterLimitWarning() {
        const warning = document.getElementById('characterWarning');
        if (warning) {
            warning.style.display = 'none';
        }
    }
});

// Global functions accessible from HTML
function updateVoices() {
    const languageSelect = document.getElementById('language');
    const voiceSelect = document.getElementById('voice');
    
    if (!languageSelect || !voiceSelect) return;
    
    const selectedLanguage = languageSelect.value;
    
    // Hide all options first
    Array.from(voiceSelect.options).forEach(option => {
        const optionLanguage = option.getAttribute('data-language');
        option.style.display = optionLanguage === selectedLanguage ? '' : 'none';
    });
    
    // Select the first visible option
    const firstVisibleOption = Array.from(voiceSelect.options).find(option => 
        option.getAttribute('data-language') === selectedLanguage
    );
    
    if (firstVisibleOption) {
        firstVisibleOption.selected = true;
    }
}

function updateSpeedValue() {
    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speedValue');
    
    if (speedSlider && speedValue) {
        speedValue.textContent = speedSlider.value;
    }
}

function updateDepthValue() {
    const depthSlider = document.getElementById('depth');
    const depthValue = document.getElementById('depthValue');
    
    if (depthSlider && depthValue) {
        depthValue.textContent = depthSlider.value;
    }
}
// Add this to your script.js or create a new language-switcher.js

// Language switcher functionality
class LanguageSwitcher {
    constructor() {
        this.currentLanguage = this.getCurrentLanguage();
        this.init();
    }

    init() {
        // Set initial language
        this.setLanguage(this.currentLanguage);
        
        // Set up language selector
        const selector = document.getElementById('languageSelector');
        if (selector) {
            selector.value = this.currentLanguage;
            selector.addEventListener('change', (e) => {
                this.changeLanguage(e.target.value);
            });
        }
        
        // Update page content
        this.updatePageContent();
    }

    getCurrentLanguage() {
        // Check localStorage first
        let lang = localStorage.getItem('userLanguage');
        
        // If not set, detect browser language
        if (!lang) {
            const browserLang = navigator.language || navigator.userLanguage;
            if (browserLang.startsWith('fr')) lang = 'fr';
            else if (browserLang.startsWith('es')) lang = 'es';
            else lang = 'en';
        }
        
        return lang;
    }

    changeLanguage(newLang) {
        if (newLang === this.currentLanguage) return;
        
        this.currentLanguage = newLang;
        localStorage.setItem('userLanguage', newLang);
        
        // Save to server if user is logged in
        this.saveToServer(newLang);
        
        // Update UI
        this.updatePageContent();
        
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: newLang }
        }));
    }

    saveToServer(language) {
        fetch('/set_language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ language })
        })
        .catch(error => console.error('Error saving language preference:', error));
    }

    updatePageContent() {
        // Update all translatable elements
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.hasAttribute('placeholder')) {
                    element.placeholder = translation;
                }
            } else {
                element.textContent = translation;
            }
        });
        
        // Update select options
        document.querySelectorAll('select[data-i18n-options]').forEach(select => {
            this.updateSelectOptions(select);
        });
    }

    getTranslation(key) {
        if (!translations[this.currentLanguage]) return key;
        
        const keys = key.split('.');
        let value = translations[this.currentLanguage];
        
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                return key;
            }
        }
        
        return value || key;
    }

    updateSelectOptions(selectElement) {
        const optionsKey = selectElement.getAttribute('data-i18n-options');
        const options = this.getTranslation(optionsKey);
        
        if (options && typeof options === 'object') {
            Array.from(selectElement.options).forEach(option => {
                if (options[option.value]) {
                    option.textContent = options[option.value];
                }
            });
        }
    }
}

// Initialize language switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const languageSwitcher = new LanguageSwitcher();
    
    // Make it globally accessible
    window.languageSwitcher = languageSwitcher;
});