// translations.js - Language translations for RealTalk

const translations = {
    en: {
        // Header
        appTitle: "REALTALK",
        appSubtitle: "AI VOICE GENERATION PLATFORM",
        marketingTitle: "MARKETING SCRIPT GENERATOR",
        marketingSubtitle: "CREATE PERSUASIVE SCRIPTS FOR LEAD GENERATION AND PRODUCT MARKETING",
        
        // Navigation
        homeLink: "Home",
        marketingGenerator: "Marketing Generator",
        ssmlEditor: "SSML Editor",
        
        // Main Form
        textTab: "TEXT",
        fileUploadTab: "FILE UPLOAD",
        textPlaceholder: "Type or paste your text here...",
        dragDropText: "Drag and drop your file here or",
        browseFiles: "Browse Files",
        supportedFormats: "Supported formats: .txt (Max 10MB)",
        
        // Voice Selection
        voiceSelection: "VOICE SELECTION",
        language: "LANGUAGE",
        voice: "VOICE",
        titleOptional: "TITLE (OPTIONAL)",
        titlePlaceholder: "Custom name for your audio file",
        titleHelp: "This will be used as the filename when downloading.",
        
        // Voice Parameters
        voiceParameters: "VOICE PARAMETERS",
        speed: "SPEED",
        voiceDepth: "VOICE DEPTH",
        speedLabels: {
            slow: "0.5x",
            normal: "1.0x",
            fast: "2.0x"
        },
        depthLabels: {
            normal: "1",
            medium: "3",
            deep: "5"
        },
        speedInfo: "Values below 0.8 or above 1.2 create more dramatic effects",
        depthInfo: "Higher values add more bass and depth to the voice",
        
        // About Parameters
        aboutParameters: "ABOUT VOICE PARAMETERS",
        speedDescription: "Adjust how fast or slow the voice speaks. Extreme values (0.5 or 2.0) create very noticeable effects.",
        depthDescription: "Adjust the bass and tone of the voice. Higher values (4-5) create a significantly deeper, more resonant voice.",
        
        // Buttons
        generateButton: "GENERATE REALTALK VOICE",
        viewHistory: "VIEW HISTORY",
        shortsGenerator: "SHORTS GENERATOR",
        aiScriptGenerator: "AI SCRIPT GENERATOR",
        marketingScripts: "MARKETING SCRIPTS",
        mediaDownloader: "MEDIA DOWNLOADER",
        generateScript: "GENERATE MARKETING SCRIPT",
        generateVoice: "GENERATE VOICE",
        copy: "COPY",
        editScript: "EDIT SCRIPT",
        
        // Feature Badges
        new: "NEW",
        pro: "PRO",
        
        // Marketing Generator
        contentDetails: "CONTENT DETAILS",
        contentType: "CONTENT TYPE",
        contentTypes: {
            productExplainer: "Product Explainer/Demo",
            leadGeneration: "Lead Generation/Opt-in",
            salesPitch: "Sales Pitch",
            testimonialStyle: "Customer Success Story",
            educational: "Educational Marketing"
        },
        productName: "PRODUCT/SERVICE NAME",
        productPlaceholder: "Premium Coffee Subscription",
        targetAudience: "TARGET AUDIENCE",
        audiencePlaceholder: "Coffee enthusiasts looking for convenience",
        primaryBenefit: "PRIMARY BENEFIT",
        benefitPlaceholder: "Fresh, ethically sourced coffee delivered weekly",
        benefitTip: "Focus on the main benefit that solves your audience's problem",
        keyFeatures: "KEY FEATURES (UP TO 3, SEPARATED BY COMMAS)",
        featuresPlaceholder: "Customized roasts, Free shipping, Flexible scheduling",
        callToAction: "CALL TO ACTION",
        ctaPlaceholder: "Sign up for a free trial box",
        scriptLength: "SCRIPT LENGTH",
        lengthOptions: {
            short: {
                label: "SHORT",
                duration: "30-60 seconds"
            },
            medium: {
                label: "MEDIUM",
                duration: "1-2 minutes"
            },
            long: {
                label: "LONG",
                duration: "2-3 minutes"
            }
        },
        toneOfVoice: "TONE OF VOICE",
        toneOptions: {
            professional: "Professional & Authoritative",
            conversational: "Friendly & Conversational",
            enthusiastic: "Enthusiastic & Energetic",
            empathetic: "Empathetic & Understanding",
            humorous: "Light & Humorous",
            urgent: "Urgent & Compelling"
        },
        additionalInfo: "ADDITIONAL INFORMATION (OPTIONAL)",
        additionalInfoPlaceholder: "Any specific offers, pricing details, or additional context",
        marketingTip: "Marketing scripts work best when they focus on benefits, not just features. For lead generation, consider what value you're offering in exchange for contact information.",
        
        // Output
        generatedScript: "GENERATED SCRIPT",
        showVoiceOptions: "SHOW VOICE OPTIONS",
        
        // Templates
        scriptTemplates: "SCRIPT TEMPLATES",
        templateDescription: "Choose a template as a starting point for your marketing scripts:",
        templateTypes: {
            problemSolution: {
                title: "PROBLEM-SOLUTION",
                description: "Identify a pain point, then present your product as the ideal solution."
            },
            benefitFocused: {
                title: "BENEFIT-FOCUSED",
                description: "Highlight the key benefits and transformation your product offers."
            }
        },
        
        // Footer
        footerText: "Create natural-sounding voice content with our advanced AI voice generation technology.",
        copyright: "© 2025 RealTalk. All rights reserved.",
        marketingFooterText: "Create persuasive marketing scripts and voice content with our advanced AI technology."
    },
    
    fr: {
        // Header
        appTitle: "REALTALK",
        appSubtitle: "PLATEFORME DE GÉNÉRATION VOCALE IA",
        marketingTitle: "GÉNÉRATEUR DE SCRIPTS MARKETING",
        marketingSubtitle: "CRÉEZ DES SCRIPTS PERSUASIFS POUR LA GÉNÉRATION DE LEADS ET LE MARKETING PRODUIT",
        
        // Navigation
        homeLink: "Accueil",
        marketingGenerator: "Générateur Marketing",
        ssmlEditor: "Éditeur SSML",
        
        // Main Form
        textTab: "TEXTE",
        fileUploadTab: "UPLOAD DE FICHIER",
        textPlaceholder: "Tapez ou collez votre texte ici...",
        dragDropText: "Glissez-déposez votre fichier ici ou",
        browseFiles: "Parcourir les fichiers",
        supportedFormats: "Formats supportés: .txt (Max 10MB)",
        
        // Voice Selection
        voiceSelection: "SÉLECTION DE LA VOIX",
        language: "LANGUE",
        voice: "VOIX",
        titleOptional: "TITRE (OPTIONNEL)",
        titlePlaceholder: "Nom personnalisé pour votre fichier audio",
        titleHelp: "Sera utilisé comme nom de fichier lors du téléchargement.",
        
        // Voice Parameters
        voiceParameters: "PARAMÈTRES DE LA VOIX",
        speed: "VITESSE",
        voiceDepth: "PROFONDEUR DE LA VOIX",
        speedLabels: {
            slow: "0.5x",
            normal: "1.0x",
            fast: "2.0x"
        },
        depthLabels: {
            normal: "1",
            medium: "3",
            deep: "5"
        },
        speedInfo: "Les valeurs inférieures à 0.8 ou supérieures à 1.2 créent des effets plus dramatiques",
        depthInfo: "Les valeurs plus élevées ajoutent plus de basses et de profondeur à la voix",
        
        // About Parameters
        aboutParameters: "À PROPOS DES PARAMÈTRES VOCAUX",
        speedDescription: "Ajustez la vitesse de parole de la voix. Les valeurs extrêmes (0.5 ou 2.0) créent des effets très perceptibles.",
        depthDescription: "Ajustez les basses et le ton de la voix. Les valeurs plus élevées (4-5) créent une voix significativement plus profonde et résonante.",
        
        // Buttons
        generateButton: "GÉNÉRER LA VOIX REALTALK",
        viewHistory: "VOIR L'HISTORIQUE",
        shortsGenerator: "GÉNÉRATEUR DE SHORTS",
        aiScriptGenerator: "GÉNÉRATEUR DE SCRIPT IA",
        marketingScripts: "SCRIPTS MARKETING",
        mediaDownloader: "TÉLÉCHARGEUR MÉDIA",
        generateScript: "GÉNÉRER LE SCRIPT MARKETING",
        generateVoice: "GÉNÉRER LA VOIX",
        copy: "COPIER",
        editScript: "MODIFIER LE SCRIPT",
        
        // Feature Badges
        new: "NOUVEAU",
        pro: "PRO",
        
        // Marketing Generator
        contentDetails: "DÉTAILS DU CONTENU",
        contentType: "TYPE DE CONTENU",
        contentTypes: {
            productExplainer: "Explicateur/Démo Produit",
            leadGeneration: "Génération de Leads",
            salesPitch: "Pitch de Vente",
            testimonialStyle: "Histoire de Succès Client",
            educational: "Marketing Éducatif"
        },
        productName: "NOM DU PRODUIT/SERVICE",
        productPlaceholder: "Abonnement Café Premium",
        targetAudience: "AUDIENCE CIBLE",
        audiencePlaceholder: "Amateurs de café cherchant la commodité",
        primaryBenefit: "BÉNÉFICE PRINCIPAL",
        benefitPlaceholder: "Café frais, d'origine éthique, livré chaque semaine",
        benefitTip: "Concentrez-vous sur le principal bénéfice qui résout le problème de votre audience",
        keyFeatures: "CARACTÉRISTIQUES CLÉS (JUSQU'À 3, SÉPARÉES PAR DES VIRGULES)",
        featuresPlaceholder: "Torréfactions personnalisées, Livraison gratuite, Planification flexible",
        callToAction: "APPEL À L'ACTION",
        ctaPlaceholder: "Inscrivez-vous pour une boîte d'essai gratuite",
        scriptLength: "LONGUEUR DU SCRIPT",
        lengthOptions: {
            short: {
                label: "COURT",
                duration: "30-60 secondes"
            },
            medium: {
                label: "MOYEN",
                duration: "1-2 minutes"
            },
            long: {
                label: "LONG",
                duration: "2-3 minutes"
            }
        },
        toneOfVoice: "TON DE LA VOIX",
        toneOptions: {
            professional: "Professionnel & Autoritaire",
            conversational: "Amical & Conversationnel",
            enthusiastic: "Enthousiaste & Énergique",
            empathetic: "Empathique & Compréhensif",
            humorous: "Léger & Humoristique",
            urgent: "Urgent & Convaincant"
        },
        additionalInfo: "INFORMATIONS SUPPLÉMENTAIRES (OPTIONNEL)",
        additionalInfoPlaceholder: "Offres spécifiques, détails des prix, ou contexte supplémentaire",
        marketingTip: "Les scripts marketing fonctionnent mieux lorsqu'ils se concentrent sur les bénéfices, pas seulement les caractéristiques. Pour la génération de leads, considérez quelle valeur vous offrez en échange des informations de contact.",
        
        // Output
        generatedScript: "SCRIPT GÉNÉRÉ",
        showVoiceOptions: "AFFICHER LES OPTIONS VOCALES",
        
        // Templates
        scriptTemplates: "MODÈLES DE SCRIPTS",
        templateDescription: "Choisissez un modèle comme point de départ pour vos scripts marketing:",
        templateTypes: {
            problemSolution: {
                title: "PROBLÈME-SOLUTION",
                description: "Identifiez un point de douleur, puis présentez votre produit comme la solution idéale."
            },
            benefitFocused: {
                title: "AXÉS SUR LES BÉNÉFICES",
                description: "Mettez en évidence les avantages clés et la transformation qu'offre votre produit."
            }
        },
        
        // Footer
        footerText: "Créez du contenu vocal au son naturel avec notre technologie avancée de génération vocale IA.",
        copyright: "© 2025 RealTalk. Tous droits réservés.",
        marketingFooterText: "Créez des scripts marketing persuasifs et du contenu vocal avec notre technologie IA avancée."
    },
    
    es: {
        // Header
        appTitle: "REALTALK",
        appSubtitle: "PLATAFORMA DE GENERACIÓN DE VOZ IA",
        marketingTitle: "GENERADOR DE SCRIPTS DE MARKETING",
        marketingSubtitle: "CREA SCRIPTS PERSUASIVOS PARA GENERACIÓN DE LEADS Y MARKETING DE PRODUCTOS",
        
        // Navigation
        homeLink: "Inicio",
        marketingGenerator: "Generador de Marketing",
        ssmlEditor: "Editor SSML",
        
        // Main Form
        textTab: "TEXTO",
        fileUploadTab: "SUBIR ARCHIVO",
        textPlaceholder: "Escribe o pega tu texto aquí...",
        dragDropText: "Arrastra y suelta tu archivo aquí o",
        browseFiles: "Explorar archivos",
        supportedFormats: "Formatos soportados: .txt (Máx 10MB)",
        
        // Voice Selection
        voiceSelection: "SELECCIÓN DE VOZ",
        language: "IDIOMA",
        voice: "VOZ",
        titleOptional: "TÍTULO (OPCIONAL)",
        titlePlaceholder: "Nombre personalizado para tu archivo de audio",
        titleHelp: "Se usará como nombre del archivo al descargar.",
        
        // Voice Parameters
        voiceParameters: "PARÁMETROS DE VOZ",
        speed: "VELOCIDAD",
        voiceDepth: "PROFUNDIDAD DE VOZ",
        speedLabels: {
            slow: "0.5x",
            normal: "1.0x",
            fast: "2.0x"
        },
        depthLabels: {
            normal: "1",
            medium: "3",
            deep: "5"
        },
        speedInfo: "Valores por debajo de 0.8 o arriba de 1.2 crean efectos más dramáticos",
        depthInfo: "Valores más altos añaden más graves y profundidad a la voz",
        
        // About Parameters
        aboutParameters: "SOBRE PARÁMETROS DE VOZ",
        speedDescription: "Ajusta qué tan rápido o lento habla la voz. Valores extremos (0.5 o 2.0) crean efectos muy notables.",
        depthDescription: "Ajusta los graves y el tono de la voz. Valores más altos (4-5) crean una voz significativamente más profunda y resonante.",
        
        // Buttons
        generateButton: "GENERAR VOZ REALTALK",
        viewHistory: "VER HISTORIAL",
        shortsGenerator: "GENERADOR DE SHORTS",
        aiScriptGenerator: "GENERADOR DE SCRIPT IA",
        marketingScripts: "SCRIPTS DE MARKETING",
        mediaDownloader: "DESCARGADOR DE MEDIOS",
        generateScript: "GENERAR SCRIPT DE MARKETING",
        generateVoice: "GENERAR VOZ",
        copy: "COPIAR",
        editScript: "EDITAR SCRIPT",
        
        // Feature Badges
        new: "NUEVO",
        pro: "PRO",
        
        // Marketing Generator
        contentDetails: "DETALLES DEL CONTENIDO",
        contentType: "TIPO DE CONTENIDO",
        contentTypes: {
            productExplainer: "Explicador/Demo de Producto",
            leadGeneration: "Generación de Leads",
            salesPitch: "Presentación de Ventas",
            testimonialStyle: "Historia de Éxito del Cliente",
            educational: "Marketing Educativo"
        },
        productName: "NOMBRE DEL PRODUCTO/SERVICIO",
        productPlaceholder: "Suscripción de Café Premium",
        targetAudience: "AUDIENCIA OBJETIVO",
        audiencePlaceholder: "Entusiastas del café que buscan comodidad",
        primaryBenefit: "BENEFICIO PRINCIPAL",
        benefitPlaceholder: "Café fresco, de origen ético, entregado semanalmente",
        benefitTip: "Enfócate en el beneficio principal que resuelve el problema de tu audiencia",
        keyFeatures: "CARACTERÍSTICAS CLAVE (HASTA 3, SEPARADAS POR COMAS)",
        featuresPlaceholder: "Tuestes personalizados, Envío gratis, Horarios flexibles",
        callToAction: "LLAMADO A LA ACCIÓN",
        ctaPlaceholder: "Regístrate para una caja de prueba gratis",
        scriptLength: "LONGITUD DEL SCRIPT",
        lengthOptions: {
            short: {
                label: "CORTO",
                duration: "30-60 segundos"
            },
            medium: {
                label: "MEDIO",
                duration: "1-2 minutos"
            },
            long: {
                label: "LARGO",
                duration: "2-3 minutos"
            }
        },
        toneOfVoice: "TONO DE VOZ",
        toneOptions: {
            professional: "Profesional & Autoritario",
            conversational: "Amigable & Conversacional",
            enthusiastic: "Entusiasta & Enérgico",
            empathetic: "Empático & Comprensivo",
            humorous: "Ligero & Humorístico",
            urgent: "Urgente & Convincente"
        },
        additionalInfo: "INFORMACIÓN ADICIONAL (OPCIONAL)",
        additionalInfoPlaceholder: "Ofertas específicas, detalles de precios, o contexto adicional",
        marketingTip: "Los scripts de marketing funcionan mejor cuando se enfocan en beneficios, no solo características. Para generación de leads, considera qué valor ofreces a cambio de información de contacto.",
        
        // Output
        generatedScript: "SCRIPT GENERADO",
        showVoiceOptions: "MOSTRAR OPCIONES DE VOZ",
        
        // Templates
        scriptTemplates: "PLANTILLAS DE SCRIPTS",
        templateDescription: "Elige una plantilla como punto de partida para tus scripts de marketing:",
        templateTypes: {
            problemSolution: {
                title: "PROBLEMA-SOLUCIÓN",
                description: "Identifica un punto de dolor, luego presenta tu producto como la solución ideal."
            },
            benefitFocused: {
                title: "ENFOCADO EN BENEFICIOS",
                description: "Resalta los beneficios clave y la transformación que ofrece tu producto."
            }
        },
        
        // Footer
        footerText: "Crea contenido de voz con sonido natural con nuestra tecnología avanzada de generación de voz IA.",
        copyright: "© 2025 RealTalk. Todos los derechos reservados.",
        marketingFooterText: "Crea scripts de marketing persuasivos y contenido de voz con nuestra tecnología IA avanzada."
    }
};

// Function to get translated text
function t(key, params = {}) {
    const currentLang = getCurrentLanguage();
    const keys = key.split('.');
    let value = translations[currentLang];
    
    for (const k of keys) {
        if (value && typeof value === 'object') {
            value = value[k];
        } else {
            return key; // Return the key if translation not found
        }
    }
    
    // Replace parameters in string
    if (typeof value === 'string' && Object.keys(params).length > 0) {
        Object.keys(params).forEach(param => {
            value = value.replace(`{{${param}}}`, params[param]);
        });
    }
    
    return value;
}

// Function to get current language from localStorage or default to English
function getCurrentLanguage() {
    return localStorage.getItem('preferredLanguage') || 'en';
}

// Function to set language
function setLanguage(lang) {
    localStorage.setItem('preferredLanguage', lang);
    updatePageLanguage();
}

// Function to update all text on the page
function updatePageLanguage() {
    const elementsToTranslate = document.querySelectorAll('[data-i18n]');
    
    elementsToTranslate.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translatedText = t(key);
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.getAttribute('placeholder') !== null) {
                element.placeholder = translatedText;
            } else {
                element.value = translatedText;
            }
        } else {
            element.textContent = translatedText;
        }
    });
    
    // Update select options
    const selectsToTranslate = document.querySelectorAll('select[data-i18n-options]');
    selectsToTranslate.forEach(select => {
        const optionsKey = select.getAttribute('data-i18n-options');
        const options = t(optionsKey);
        
        if (options && typeof options === 'object') {
            Array.from(select.options).forEach(option => {
                const value = option.value;
                if (options[value]) {
                    option.textContent = options[value];
                }
            });
        }
    });
}