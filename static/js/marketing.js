// marketing.js - Enhanced Script Generator

document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const marketingForm = document.getElementById('marketingForm');
    const outputContainer = document.getElementById('outputContainer');
    const scriptOutput = document.getElementById('scriptOutput');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const copyBtn = document.getElementById('copyBtn');
    const editScriptBtn = document.getElementById('editScriptBtn');
    const showOptionsBtn = document.getElementById('showOptionsBtn');
    const voiceForm = document.getElementById('voiceForm');
    const generateVoiceBtn = document.getElementById('generateVoiceBtn');
    const templateSection = document.getElementById('templateSection');
    
    // Hide loading spinner initially
    loadingSpinner.style.display = 'none';
    
    // Hide output container initially
    outputContainer.style.display = 'none';
    
    // AI Suggestions Feature
    setupAISuggestions();
    
    // Preview Feature
    setupPreviewFeature();
    
    // Voice Options Toggle
    showOptionsBtn.addEventListener('click', function() {
        if (voiceForm.style.display === 'none' || !voiceForm.style.display) {
            voiceForm.style.display = 'block';
            showOptionsBtn.innerHTML = '<i class="fas fa-angle-up me-1"></i> Hide voice options';
        } else {
            voiceForm.style.display = 'none';
            showOptionsBtn.innerHTML = '<i class="fas fa-sliders me-1"></i> Show voice options';
        }
    });
    
    // Hide voice options by default
    voiceForm.style.display = 'none';
    
    // Form Submission
    marketingForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading spinner
        loadingSpinner.style.display = 'inline-block';
        
        // Get form data
        const formData = new FormData(marketingForm);
        
        // AJAX request to generate script
        fetch('/generate-marketing-script', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
            
            if (data.success) {
                // Display the script
                scriptOutput.innerHTML = formatScriptOutput(data.script);
                
                // Show output container
                outputContainer.style.display = 'block';
                
                // Populate hidden field for TTS
                document.getElementById('text-content').value = data.script;
                
                // Scroll to the output
                outputContainer.scrollIntoView({ behavior: 'smooth' });
                
                // Save to local history
                saveToScriptHistory(formData, data.script);
                
                // Add emotional tone analysis
                analyzeEmotionalTone(data.script);
            } else {
                // Show error
                scriptOutput.innerHTML = `<div class="alert alert-danger">${data.error || 'An error occurred while generating the script.'}</div>`;
                outputContainer.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingSpinner.style.display = 'none';
            scriptOutput.innerHTML = '<div class="alert alert-danger">An error occurred while generating the script. Please try again.</div>';
            outputContainer.style.display = 'block';
        });
    });
    
    // Copy button functionality
    copyBtn.addEventListener('click', function() {
        const scriptText = document.getElementById('text-content').value;
        navigator.clipboard.writeText(scriptText).then(() => {
            // Change button text temporarily
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        });
    });
    
    // Edit script functionality
    editScriptBtn.addEventListener('click', function() {
        const currentScript = document.getElementById('text-content').value;
        // Create editable area
        scriptOutput.innerHTML = `
            <div class="edit-mode-container">
                <textarea class="form-control" id="editScriptTextarea" rows="10">${currentScript}</textarea>
                <div class="d-flex justify-content-end mt-3">
                    <button class="btn btn-outline-secondary me-2" id="cancelEditBtn">Cancel</button>
                    <button class="btn btn-primary" id="saveEditBtn">Save Changes</button>
                </div>
            </div>
        `;
        
        // Add event listeners for the edit buttons
        document.getElementById('cancelEditBtn').addEventListener('click', function() {
            scriptOutput.innerHTML = formatScriptOutput(currentScript);
        });
        
        document.getElementById('saveEditBtn').addEventListener('click', function() {
            const newScript = document.getElementById('editScriptTextarea').value;
            document.getElementById('text-content').value = newScript;
            scriptOutput.innerHTML = formatScriptOutput(newScript);
            
            // Re-analyze the emotional tone
            analyzeEmotionalTone(newScript);
        });
    });
    
    // Script History feature
    setupScriptHistory();
    
    // A/B Testing Feature
    setupABTesting();
});

// Function to format the script output with styled paragraphs
function formatScriptOutput(script) {
    // Split into paragraphs and wrap in styled p tags
    const paragraphs = script.split('\n').filter(para => para.trim() !== '');
    return paragraphs.map(para => `<p class="script-paragraph">${para}</p>`).join('');
}

// Function to update voices based on selected language
function updateVoices() {
    const languageSelect = document.getElementById('language');
    const voiceSelect = document.getElementById('voice');
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

// Function to update speed value display
function updateSpeedValue() {
    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speedValue');
    speedValue.textContent = speedSlider.value;
}

// Function to update depth value display
function updateDepthValue() {
    const depthSlider = document.getElementById('depth');
    const depthValue = document.getElementById('depthValue');
    depthValue.textContent = depthSlider.value;
}

// Function to load template data
function loadTemplate(templateType) {
    // Template data
    const templates = {
        problem_solution: {
            productName: "Problem-Solution Template",
            targetAudience: "People struggling with [specific problem]",
            mainBenefit: "Solve [problem] quickly and effectively",
            keyFeatures: "Easy to use, Fast results, Ongoing support",
            callToAction: "Try it risk-free for 30 days",
            tone: "empathetic"
        },
        benefit_focused: {
            productName: "Benefit-Focused Template",
            targetAudience: "People looking to improve [specific area]",
            mainBenefit: "Transform your [area] with [key benefit]",
            keyFeatures: "Proven results, Expert-designed, Time-saving",
            callToAction: "Claim your [benefit] today",
            tone: "enthusiastic"
        }
    };
    
    // Get template data
    const template = templates[templateType];
    
    // Populate form fields
    document.getElementById('productName').value = template.productName;
    document.getElementById('targetAudience').value = template.targetAudience;
    document.getElementById('mainBenefit').value = template.mainBenefit;
    document.getElementById('keyFeatures').value = template.keyFeatures;
    document.getElementById('callToAction').value = template.callToAction;
    document.getElementById('tone').value = template.tone;
    
    // Scroll to form
    document.getElementById('marketingForm').scrollIntoView({ behavior: 'smooth' });
}

// ===== NEW FEATURE IMPLEMENTATIONS =====

// Function to analyze emotional tone
function analyzeEmotionalTone(script) {
    // Simple analysis based on keywords
    const toneAnalysis = {
        persuasive: 0,
        emotional: 0,
        urgent: 0,
        trustworthy: 0,
        engaging: 0
    };
    
    // Keywords associated with different tones
    const keywords = {
        persuasive: ['proven', 'guarantee', 'results', 'transform', 'solution'],
        emotional: ['feel', 'imagine', 'love', 'happy', 'worry', 'stress'],
        urgent: ['now', 'limited', 'today', 'before', 'hurry', 'quickly'],
        trustworthy: ['trusted', 'expert', 'research', 'study', 'proven', 'evidence'],
        engaging: ['you', 'your', 'imagine', 'consider', 'picture', 'what if']
    };
    
    // Count keywords
    const lowerScript = script.toLowerCase();
    
    for (const tone in keywords) {
        keywords[tone].forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            const matches = lowerScript.match(regex);
            if (matches) {
                toneAnalysis[tone] += matches.length;
            }
        });
    }
    
    // Normalize scores (0-100)
    const maxScore = Math.max(...Object.values(toneAnalysis));
    if (maxScore > 0) {
        for (const tone in toneAnalysis) {
            toneAnalysis[tone] = Math.round((toneAnalysis[tone] / maxScore) * 100);
        }
    }
    
    // Add tone analysis to the output
    let toneHTML = `
        <div class="tone-analysis mt-4">
            <h5><i class="fas fa-chart-bar me-2"></i>Script Tone Analysis</h5>
            <div class="tone-bars">
    `;
    
    for (const tone in toneAnalysis) {
        const score = toneAnalysis[tone];
        toneHTML += `
            <div class="tone-metric">
                <div class="d-flex justify-content-between">
                    <span class="tone-label text-capitalize">${tone}</span>
                    <span class="tone-score">${score}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar" role="progressbar" style="width: ${score}%" 
                        aria-valuenow="${score}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
            </div>
        `;
    }
    
    toneHTML += `
            </div>
            <div class="tone-tip mt-2">
                <small><i class="fas fa-info-circle me-1"></i>This analysis helps identify the emotional appeal of your script.</small>
            </div>
        </div>
    `;
    
    // Append to script output
    scriptOutput.innerHTML += toneHTML;
}

// Function to set up AI suggestions feature
function setupAISuggestions() {
    const fields = ['productName', 'targetAudience', 'mainBenefit', 'keyFeatures', 'callToAction'];
    
    fields.forEach(field => {
        const input = document.getElementById(field);
        const inputContainer = input.parentElement;
        
        // Add suggestion button next to the field
        const buttonHTML = `<button type="button" class="btn btn-sm btn-outline-secondary suggestion-btn" data-field="${field}">
            <i class="fas fa-lightbulb"></i> Suggest
        </button>`;
        
        // Create button container and inject after input
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'mt-2';
        buttonContainer.innerHTML = buttonHTML;
        inputContainer.appendChild(buttonContainer);
        
        // Add event listener to the button
        buttonContainer.querySelector('.suggestion-btn').addEventListener('click', function() {
            generateSuggestion(field);
        });
    });
}

// Function to generate field suggestions
function generateSuggestion(field) {
    const contentType = document.getElementById('contentType').value;
    
    // Sample suggestions based on content type and field
    const suggestions = {
        product_explainer: {
            productName: ["Smart Home Assistant", "Premium Learning Platform", "Health Tracking System"],
            targetAudience: ["Busy professionals seeking convenience", "Parents looking for educational tools", "Health-conscious individuals"],
            mainBenefit: ["Save 2 hours daily on household tasks", "Accelerate learning progress by 40%", "Track and improve health metrics effortlessly"],
            keyFeatures: ["Voice control, Smart scheduling, Personalization", "Interactive lessons, Progress tracking, Expert feedback", "Real-time monitoring, Data insights, Personalized recommendations"],
            callToAction: ["Experience the future of home management", "Start your learning journey today", "Begin your health transformation"]
        },
        lead_generation: {
            productName: ["Free Industry Report", "Expert Consultation Session", "Exclusive Webinar Series"],
            targetAudience: ["Business owners seeking growth strategies", "Professionals looking to upskill", "Decision makers in the healthcare industry"],
            mainBenefit: ["Gain insider knowledge on market trends", "Receive personalized advice from experts", "Learn cutting-edge strategies before competitors"],
            keyFeatures: ["Data-driven insights, Actionable strategies, Future predictions", "One-on-one guidance, Tailored advice, Implementation plan", "Live Q&A, Expert presentations, Resource toolkit"],
            callToAction: ["Download your free report now", "Book your complimentary consultation", "Reserve your spot while spaces last"]
        },
        sales_pitch: {
            productName: ["Premium Subscription Plan", "All-in-One Business Solution", "Professional Service Package"],
            targetAudience: ["Growing businesses looking to scale", "Teams struggling with workflow efficiency", "Companies wanting to increase revenue"],
            mainBenefit: ["Increase revenue by 30% within 90 days", "Reduce operational costs while improving productivity", "Attract and convert 50% more qualified leads"],
            keyFeatures: ["Advanced analytics, Priority support, Unlimited usage", "Streamlined workflows, Team collaboration, Automated reporting", "Customized strategy, Implementation support, Results monitoring"],
            callToAction: ["Upgrade to premium today", "Schedule a demo to see it in action", "Start your 14-day trial with no credit card required"]
        },
        testimonial_style: {
            productName: ["Client Success Story", "Transformation Journey", "Results Showcase"],
            targetAudience: ["Prospects facing similar challenges", "Decision-makers evaluating solutions", "Customers considering an upgrade"],
            mainBenefit: ["Achieved 3x ROI within the first quarter", "Completely transformed their business processes", "Solved their biggest challenge in just weeks"],
            keyFeatures: ["Easy implementation, Measurable results, Ongoing support", "Personalized approach, Quick adoption, Scalable solution", "Problem identification, Strategic solution, Continued optimization"],
            callToAction: ["Join hundreds of successful customers", "See how we can help you achieve similar results", "Book a case study presentation"]
        },
        educational: {
            productName: ["Knowledge Series", "Industry Guide", "Masterclass"],
            targetAudience: ["Professionals seeking to stay current", "Beginners looking to learn fundamentals", "Experts wanting to deepen their knowledge"],
            mainBenefit: ["Master essential skills in half the typical time", "Build a solid foundation of practical knowledge", "Discover advanced techniques used by industry leaders"],
            keyFeatures: ["Practical examples, Step-by-step guidance, Expert insights", "Foundational concepts, Hands-on exercises, Progress tracking", "Advanced strategies, Case studies, Implementation frameworks"],
            callToAction: ["Start learning today", "Access your first lesson free", "Join our community of learners"]
        }
    };
    
    // Get random suggestion based on content type and field
    const fieldSuggestions = suggestions[contentType][field];
    const randomSuggestion = fieldSuggestions[Math.floor(Math.random() * fieldSuggestions.length)];
    
    // Create suggestion dropdown
    const input = document.getElementById(field);
    const dropdown = document.createElement('div');
    dropdown.className = 'suggestion-dropdown';
    dropdown.innerHTML = `
        <div class="suggestion-header">
            <small><i class="fas fa-magic me-1"></i>AI Suggestions:</small>
            <button type="button" class="btn-close btn-sm" aria-label="Close"></button>
        </div>
        <div class="suggestion-body">
            ${randomSuggestion}
        </div>
        <div class="suggestion-footer">
            <button type="button" class="btn btn-sm btn-outline-primary use-suggestion-btn">Use This</button>
            <button type="button" class="btn btn-sm btn-link refresh-suggestion-btn">Refresh</button>
        </div>
    `;
    
    // Add to the DOM
    const existingDropdown = input.parentElement.querySelector('.suggestion-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }
    input.parentElement.appendChild(dropdown);
    
    // Add event listeners
    dropdown.querySelector('.btn-close').addEventListener('click', function() {
        dropdown.remove();
    });
    
    dropdown.querySelector('.use-suggestion-btn').addEventListener('click', function() {
        input.value = randomSuggestion;
        dropdown.remove();
    });
    
    dropdown.querySelector('.refresh-suggestion-btn').addEventListener('click', function() {
        generateSuggestion(field);
    });
}

// Function to set up script history feature
function setupScriptHistory() {
    // Create history button in the header
    const header = document.querySelector('.header');
    const historyButton = document.createElement('button');
    historyButton.className = 'btn btn-sm btn-outline-light history-btn';
    historyButton.innerHTML = '<i class="fas fa-history me-1"></i> Script History';
    header.appendChild(historyButton);
    
    // Add event listener
    historyButton.addEventListener('click', function() {
        showScriptHistory();
    });
}

// Function to save script to local history
function saveToScriptHistory(formData, script) {
    // Get current history from localStorage
    let history = JSON.parse(localStorage.getItem('marketingScriptHistory') || '[]');
    
    // Create new history entry
    const entry = {
        id: Date.now(),
        date: new Date().toISOString(),
        productName: formData.get('productName'),
        contentType: formData.get('contentType'),
        script: script,
        tone: formData.get('tone')
    };
    
    // Add to history (limit to 10 entries)
    history.unshift(entry);
    if (history.length > 10) {
        history = history.slice(0, 10);
    }
    
    // Save to localStorage
    localStorage.setItem('marketingScriptHistory', JSON.stringify(history));
}

// Function to display script history
function showScriptHistory() {
    // Get history from localStorage
    const history = JSON.parse(localStorage.getItem('marketingScriptHistory') || '[]');
    
    // Create modal for history
    const modalHTML = `
        <div class="modal fade" id="historyModal" tabindex="-1" aria-labelledby="historyModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="historyModalLabel">Script History</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${history.length === 0 ? 
                            '<p class="text-center text-muted">No script history found.</p>' : 
                            '<div class="list-group">' + 
                                history.map(entry => `
                                    <div class="list-group-item list-group-item-action" data-id="${entry.id}">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h5 class="mb-1">${entry.productName}</h5>
                                            <small>${new Date(entry.date).toLocaleDateString()}</small>
                                        </div>
                                        <p class="mb-1">Type: ${getContentTypeName(entry.contentType)}</p>
                                        <small>Tone: ${getToneName(entry.tone)}</small>
                                        <div class="mt-2">
                                            <button class="btn btn-sm btn-outline-primary load-history-btn" data-id="${entry.id}">
                                                Load Script
                                            </button>
                                        </div>
                                    </div>
                                `).join('') + 
                            '</div>'
                        }
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-danger" id="clearHistoryBtn">Clear History</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
    modal.show();
    
    // Add event listeners
    const loadButtons = document.querySelectorAll('.load-history-btn');
    loadButtons.forEach(button => {
        button.addEventListener('click', function() {
            const id = parseInt(this.getAttribute('data-id'));
            const entry = history.find(item => item.id === id);
            
            if (entry) {
                // Load script to output
                document.getElementById('scriptOutput').innerHTML = formatScriptOutput(entry.script);
                document.getElementById('text-content').value = entry.script;
                
                // Show output container
                document.getElementById('outputContainer').style.display = 'block';
                
                // Scroll to output
                document.getElementById('outputContainer').scrollIntoView({ behavior: 'smooth' });
                
                // Close modal
                modal.hide();
                
                // Re-analyze the emotional tone
                analyzeEmotionalTone(entry.script);
            }
        });
    });
    
    // Clear history button
    const clearButton = document.getElementById('clearHistoryBtn');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear your script history?')) {
                localStorage.removeItem('marketingScriptHistory');
                modal.hide();
            }
        });
    }
    
    // Clean up when modal is closed
    document.getElementById('historyModal').addEventListener('hidden.bs.modal', function() {
        modalContainer.remove();
    });
}

// Helper function to get content type display name
function getContentTypeName(contentType) {
    const contentTypes = {
        product_explainer: 'Product Explainer',
        lead_generation: 'Lead Generation',
        sales_pitch: 'Sales Pitch',
        testimonial_style: 'Customer Success Story',
        educational: 'Educational Marketing'
    };
    
    return contentTypes[contentType] || contentType;
}

// Helper function to get tone display name
function getToneName(tone) {
    const tones = {
        professional: 'Professional & Authoritative',
        conversational: 'Friendly & Conversational',
        enthusiastic: 'Enthusiastic & Energetic',
        empathetic: 'Empathetic & Understanding',
        humorous: 'Light & Humorous',
        urgent: 'Urgent & Compelling'
    };
    
    return tones[tone] || tone;
}

// Function to set up A/B testing feature
function setupABTesting() {
    // Add A/B testing button
    const generateBtn = document.getElementById('generateBtn');
    const abTestButton = document.createElement('button');
    abTestButton.type = 'button';
    abTestButton.className = 'btn btn-outline-primary btn-lg mt-3';
    abTestButton.innerHTML = '<i class="fas fa-code-branch me-2"></i>Generate A/B Variants';
    abTestButton.id = 'abTestButton';
    
    // Add to DOM after generate button
    generateBtn.parentNode.appendChild(abTestButton);
    
    // Add event listener
    abTestButton.addEventListener('click', function() {
        generateABVariants();
    });
}

// Function to generate A/B variants
function generateABVariants() {
    // Show loading spinner
    const loadingSpinner = document.getElementById('loadingSpinner').cloneNode(true);
    loadingSpinner.style.display = 'inline-block';
    document.getElementById('abTestButton').prepend(loadingSpinner);
    
    // Get form data
    const formData = new FormData(document.getElementById('marketingForm'));
    
    // Clone the form data for variant B (with different tone)
    const formDataB = new FormData();
    formData.forEach((value, key) => {
        formDataB.append(key, value);
    });
    
    // Change tone for variant B
    const currentTone = formData.get('tone');
    const tones = ['professional', 'conversational', 'enthusiastic', 'empathetic', 'humorous', 'urgent'];
    const availableTones = tones.filter(tone => tone !== currentTone);
    const randomTone = availableTones[Math.floor(Math.random() * availableTones.length)];
    formDataB.set('tone', randomTone);
    
    // AJAX requests for both variants
    Promise.all([
        fetch('/generate-marketing-script', {
            method: 'POST',
            body: formData
        }).then(response => response.json()),
        fetch('/generate-marketing-script', {
            method: 'POST',
            body: formDataB
        }).then(response => response.json())
    ])
    .then(([dataA, dataB]) => {
        // Hide loading spinner
        loadingSpinner.style.display = 'none';
        
        // Create A/B test container
        const abTestHTML = `
            <div class="ab-test-container mt-4">
                <h4 class="section-title">A/B Test Variants</h4>
                <p class="text-muted mb-3">Compare these two script variants to see which performs better.</p>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">Variant A: ${getToneName(currentTone)}</h5>
                                <button class="btn btn-sm btn-outline-primary select-variant-btn" data-variant="A">Select</button>
                            </div>
                            <div class="card-body variant-script">
                                ${formatScriptOutput(dataA.script)}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">Variant B: ${getToneName(randomTone)}</h5>
                                <button class="btn btn-sm btn-outline-primary select-variant-btn" data-variant="B">Select</button>
                            </div>
                            <div class="card-body variant-script">
                                ${formatScriptOutput(dataB.script)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3 text-center">
                    <button class="btn btn-outline-secondary close-ab-test-btn">
                        <i class="fas fa-times me-1"></i>Close A/B Test
                    </button>
                </div>
            </div>
        `;
        
        // Add to DOM
        const abTestContainer = document.createElement('div');
        abTestContainer.innerHTML = abTestHTML;
        document.querySelector('.card').appendChild(abTestContainer);
        
        // Store scripts
        abTestContainer.dataset.scriptA = dataA.script;
        abTestContainer.dataset.scriptB = dataB.script;
        
        // Add event listeners
        const selectButtons = abTestContainer.querySelectorAll('.select-variant-btn');
        selectButtons.forEach(button => {
            button.addEventListener('click', function() {
                const variant = this.getAttribute('data-variant');
                const script = variant === 'A' ? dataA.script : dataB.script;
                
                // Load selected script to output
                document.getElementById('scriptOutput').innerHTML = formatScriptOutput(script);
                document.getElementById('text-content').value = script;
                
                // Show output container
                document.getElementById('outputContainer').style.display = 'block';
                
                // Remove A/B test container
                abTestContainer.remove();
                
                // Scroll to output
                document.getElementById('outputContainer').scrollIntoView({ behavior: 'smooth' });
                
                // Re-analyze the emotional tone
                analyzeEmotionalTone(script);
            });
        });
        
        // Close button
        abTestContainer.querySelector('.close-ab-test-btn').addEventListener('click', function() {
            abTestContainer.remove();
        });
        
        // Scroll to A/B test
        abTestContainer.scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Error generating A/B variants:', error);
        loadingSpinner.style.display = 'none';
        alert('An error occurred while generating A/B variants. Please try again.');
    });
}

// Function to set up preview feature
function setupPreviewFeature() {
    // Add preview button
    const editScriptBtn = document.getElementById('editScriptBtn');
    const previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.className = 'btn btn-outline-secondary me-2';
    previewButton.innerHTML = '<i class="fas fa-eye me-1"></i>Preview';
    previewButton.id = 'previewButton';
    
    // Add to DOM before edit button
    editScriptBtn.parentNode.insertBefore(previewButton, editScriptBtn);
    
    // Add event listener
    previewButton.addEventListener('click', function() {
        showScriptPreview();
    });
}

// Function to show script preview
function showScriptPreview() {
    const script = document.getElementById('text-content').value;
    if (!script) {
        alert('Please generate a script first to preview');
        return;
    }
    
    // Create modal for preview
    const modalHTML = `
        <div class="modal fade" id="previewModal" tabindex="-1" aria-labelledby="previewModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="previewModalLabel">Script Preview</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="preview-container">
                            <!-- Mobile Frame -->
                            <div class="device-frame">
                                <div class="device-content">
                                    <div class="preview-video-container">
                                        <div class="preview-placeholder">
                                            <i class="fas fa-play-circle"></i>
                                        </div>
                                        <div class="preview-script-overlay">
                                            <div class="preview-script-text">
                                                ${formatScriptOutput(script)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="device-controls">
                                    <button class="btn btn-sm btn-dark rounded-circle">
                                        <i class="fas fa-home"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Preview Controls -->
                            <div class="preview-controls mt-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Background</label>
                                            <div class="btn-group w-100" role="group">
                                                <button type="button" class="btn btn-outline-secondary active" data-bg="gradient">Gradient</button>
                                                <button type="button" class="btn btn-outline-secondary" data-bg="solid">Solid</button>
                                                <button type="button" class="btn btn-outline-secondary" data-bg="dark">Dark</button>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Text Position</label>
                                            <div class="btn-group w-100" role="group">
                                                <button type="button" class="btn btn-outline-secondary active" data-position="center">Center</button>
                                                <button type="button" class="btn btn-outline-secondary" data-position="bottom">Bottom</button>
                                                <button type="button" class="btn btn-outline-secondary" data-position="caption">Caption</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row mt-2">
                                    <div class="col-12">
                                        <div class="form-check form-switch">
                                            <input class="form-check-input" type="checkbox" id="autoScrollSwitch" checked>
                                            <label class="form-check-label" for="autoScrollSwitch">Auto-scroll text</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-primary" id="exportPreviewBtn">
                            <i class="fas fa-download me-1"></i>Export Preview
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
    
    // Background buttons
    const bgButtons = document.querySelectorAll('[data-bg]');
    bgButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            bgButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Apply background
            const bgType = this.getAttribute('data-bg');
            const previewContainer = document.querySelector('.preview-video-container');
            
            // Remove existing classes
            previewContainer.classList.remove('bg-gradient', 'bg-solid', 'bg-dark');
            
            // Add new class
            previewContainer.classList.add('bg-' + bgType);
        });
    });
    
    // Position buttons
    const posButtons = document.querySelectorAll('[data-position]');
    posButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            posButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Apply position
            const position = this.getAttribute('data-position');
            const textOverlay = document.querySelector('.preview-script-overlay');
            
            // Remove existing classes
            textOverlay.classList.remove('position-center', 'position-bottom', 'position-caption');
            
            // Add new class
            textOverlay.classList.add('position-' + position);
        });
    });
    
    // Auto-scroll functionality
    const autoScrollSwitch = document.getElementById('autoScrollSwitch');
    let scrollInterval;
    
    function toggleAutoScroll() {
        const textContainer = document.querySelector('.preview-script-text');
        
        if (autoScrollSwitch.checked) {
            // Start auto-scroll
            let scrollPos = 0;
            const scrollHeight = textContainer.scrollHeight;
            const duration = 10000; // 10 seconds to scroll through entire script
            const scrollStep = scrollHeight / (duration / 50); // 50ms intervals
            
            scrollInterval = setInterval(() => {
                scrollPos += scrollStep;
                textContainer.scrollTop = scrollPos;
                
                // Reset when reaching bottom
                if (scrollPos >= scrollHeight) {
                    scrollPos = 0;
                }
            }, 50);
        } else {
            // Stop auto-scroll
            clearInterval(scrollInterval);
        }
    }
    
    autoScrollSwitch.addEventListener('change', toggleAutoScroll);
    
    // Start auto-scroll initially
    toggleAutoScroll();
    
    // Export preview functionality
    document.getElementById('exportPreviewBtn').addEventListener('click', function() {
        alert('Preview export feature would capture the current preview as an image/video.');
        // In a real implementation, this would use html2canvas or similar to capture the preview
    });
    
    // Clean up when modal is closed
    document.getElementById('previewModal').addEventListener('hidden.bs.modal', function() {
        clearInterval(scrollInterval);
        modalContainer.remove();
    });
}

// Add CSS for preview feature
function addPreviewCSS() {
    const style = document.createElement('style');
    style.textContent = `
        .device-frame {
            width: 280px;
            height: 500px;
            margin: 0 auto;
            border: 10px solid #333;
            border-radius: 24px;
            position: relative;
            overflow: hidden;
            background: #fff;
        }
        
        .device-content {
            width: 100%;
            height: calc(100% - 30px);
            overflow: hidden;
            position: relative;
        }
        
        .device-controls {
            height: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #222;
        }
        
        .preview-video-container {
            width: 100%;
            height: 100%;
            position: relative;
            background-image: linear-gradient(45deg, #6a11cb 0%, #2575fc 100%);
        }
        
        .preview-video-container.bg-solid {
            background-image: none;
            background-color: #3498db;
        }
        
        .preview-video-container.bg-dark {
            background-image: none;
            background-color: #222;
        }
        
        .preview-placeholder {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: rgba(255, 255, 255, 0.3);
            font-size: 48px;
        }
        
        .preview-script-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .preview-script-overlay.position-bottom {
            align-items: flex-end;
            padding-bottom: 40px;
        }
        
        .preview-script-overlay.position-caption {
            align-items: flex-end;
        }
        
        .preview-script-text {
            color: #fff;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
            max-height: 100%;
            overflow-y: auto;
            scrollbar-width: none;
        }
        
        .preview-script-text::-webkit-scrollbar {
            display: none;
        }
        
        .preview-script-overlay.position-caption .preview-script-text {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 10px;
            width: 100%;
            max-height: 40%;
        }
        
        .preview-controls {
            max-width: 400px;
            margin: 0 auto;
        }
    `;
    document.head.appendChild(style);
}

// Call to add CSS when page loads
document.addEventListener('DOMContentLoaded', function() {
    addPreviewCSS();
});

// Function to set up word counter feature
function setupWordCounter() {
    // Create word counter element
    const counterHTML = `
        <div class="word-counter">
            <span id="wordCount">0</span> words
            <span class="separator">|</span>
            ~<span id="speechTime">0</span> seconds
        </div>
    `;
    
    // Add to the page
    const scriptOutput = document.getElementById('scriptOutput');
    const counterElement = document.createElement('div');
    counterElement.className = 'word-counter-container';
    counterElement.innerHTML = counterHTML;
    scriptOutput.parentNode.insertBefore(counterElement, scriptOutput);
    
    // Hide initially
    counterElement.style.display = 'none';
    
    // Function to update word count
    function updateWordCount() {
        const script = document.getElementById('text-content').value;
        
        if (script) {
            // Count words
            const words = script.trim().split(/\s+/).length;
            document.getElementById('wordCount').textContent = words;
            
            // Estimate speech time (average speaking pace is about 150 words per minute)
            const seconds = Math.round(words / 2.5);
            document.getElementById('speechTime').textContent = seconds;
            
            // Show counter
            counterElement.style.display = 'block';
        } else {
            // Hide counter if no script
            counterElement.style.display = 'none';
        }
    }
    
    // Create MutationObserver to watch for script changes
    const observer = new MutationObserver(function(mutations) {
        updateWordCount();
    });
    
    // Start observing
    observer.observe(scriptOutput, { childList: true, subtree: true });
    
    // Also update when edit is saved
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'saveEditBtn') {
            setTimeout(updateWordCount, 100);
        }
    });
}

// Initialize word counter
document.addEventListener('DOMContentLoaded', function() {
    setupWordCounter();
});

// Add popular templates section
function addPopularTemplates() {
    const templateSection = document.getElementById('templateSection');
    
    // Get existing templates row
    const existingRow = templateSection.querySelector('.row');
    
    // Add more templates
    const newTemplates = `
        <div class="col-md-4 mb-3">
            <div class="card h-100" style="background-color: var(--soft-accent); cursor: pointer;" onclick="loadTemplate('story_arc')">
                <div class="card-body">
                    <h5 class="card-title">Story Arc</h5>
                    <p class="card-text">Use storytelling to engage viewers and create emotional connection.</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card h-100" style="background-color: var(--soft-accent); cursor: pointer;" onclick="loadTemplate('fomo')">
                <div class="card-body">
                    <h5 class="card-title">FOMO (Fear of Missing Out)</h5>
                    <p class="card-text">Create urgency and exclusivity to drive immediate action.</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card h-100" style="background-color: var(--soft-accent); cursor: pointer;" onclick="loadTemplate('tutorial')">
                <div class="card-body">
                    <h5 class="card-title">Quick Tutorial</h5>
                    <p class="card-text">Demonstrate how easy it is to use your product and get results.</p>
                </div>
            </div>
        </div>
    `;
    
    // Append to existing row
    existingRow.innerHTML += newTemplates;
    
    // Update loadTemplate function to handle new templates
    window.loadTemplate = function(templateType) {
        // Existing template data
        const templates = {
            problem_solution: {
                productName: "Problem-Solution Template",
                targetAudience: "People struggling with [specific problem]",
                mainBenefit: "Solve [problem] quickly and effectively",
                keyFeatures: "Easy to use, Fast results, Ongoing support",
                callToAction: "Try it risk-free for 30 days",
                tone: "empathetic"
            },
            benefit_focused: {
                productName: "Benefit-Focused Template",
                targetAudience: "People looking to improve [specific area]",
                mainBenefit: "Transform your [area] with [key benefit]",
                keyFeatures: "Proven results, Expert-designed, Time-saving",
                callToAction: "Claim your [benefit] today",
                tone: "enthusiastic"
            },
            // New templates
            story_arc: {
                productName: "Story-Arc Template",
                targetAudience: "People who relate to [specific situation]",
                mainBenefit: "Journey from [pain point] to [desired outcome]",
                keyFeatures: "Real success stories, Proven methodology, Step-by-step guidance",
                callToAction: "Start your journey today",
                tone: "conversational"
            },
            fomo: {
                productName: "Exclusive Offer Template",
                targetAudience: "People who want to stay ahead of the curve",
                mainBenefit: "Limited access to [exclusive benefit]",
                keyFeatures: "Limited availability, Exclusive bonuses, Early access",
                callToAction: "Secure your spot before it's gone",
                tone: "urgent"
            },
            tutorial: {
                productName: "Tutorial Template",
                targetAudience: "People wanting to learn [specific skill/process]",
                mainBenefit: "Master [skill] in just minutes",
                keyFeatures: "Step-by-step guidance, Visual demonstration, Practical application",
                callToAction: "Start using [product] now",
                tone: "professional"
            }
        };
        
        // Get template data
        const template = templates[templateType];
        
        // Populate form fields
        document.getElementById('productName').value = template.productName;
        document.getElementById('targetAudience').value = template.targetAudience;
        document.getElementById('mainBenefit').value = template.mainBenefit;
        document.getElementById('keyFeatures').value = template.keyFeatures;
        document.getElementById('callToAction').value = template.callToAction;
        document.getElementById('tone').value = template.tone;
        
        // Scroll to form
        document.getElementById('marketingForm').scrollIntoView({ behavior: 'smooth' });
    };
}

// Add categories for improved organization
function addScriptCategories() {
    const contentTypeSelect = document.getElementById('contentType');
    
    // Add category labels to options
    contentTypeSelect.innerHTML = `
        <optgroup label="Lead Generation">
            <option value="lead_generation">Lead Generation/Opt-in</option>
        </optgroup>
        <optgroup label="Product Marketing">
            <option value="product_explainer">Product Explainer/Demo</option>
            <option value="sales_pitch">Sales Pitch</option>
        </optgroup>
        <optgroup label="Storytelling">
            <option value="testimonial_style">Customer Success Story</option>
            <option value="case_study">Case Study</option>
        </optgroup>
        <optgroup label="Educational">
            <option value="educational">Educational Marketing</option>
            <option value="tutorial">Tutorial/How-To</option>
        </optgroup>
    `;
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', function() {
    addPopularTemplates();
    addScriptCategories();
});