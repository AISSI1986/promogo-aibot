document.addEventListener("DOMContentLoaded", () => {
    window.chatWidget = new ChatApp()
    window.chatWidget.init()
})

class ChatApp {
    constructor() {
        // État de l'application
        this.isRecording = false
        this.isDemoMode = false
        this.currentLanguage = "en" // Anglais par défaut
        this.mediaRecorder = null
        this.audioChunks = []
        this.isHelpOpen = false
        this.isDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches
        this.isTextInputVisible = false // État pour la visibilité de l'input texte
        this.ttsAvailable = true // Indicateur pour savoir si le TTS est disponible, true par défaut
        this.currentAudio = null; // Pour suivre l'audio en cours de lecture
        this.isProcessing = false; // Nouvel état pour le traitement
        this.isIframeVisible = false // Nouvel état pour l'iframe

        // Configuration des APIs
        this.apiEndpoints = {
            stt: "https://stt-promogo.souciance.com/transcribe",
            rasa: "https://rasa-promogo.souciance.com/webhooks/rest/webhook",
            tts: "https://tts-promogo.souciance.com/synthesize/",
        }

        // Messages de bienvenue dans chaque langue
        this.welcomeMessages = {
            ha: {
                greeting: "Barka da zuwa! Me zan iya taimaka maka yau?",
                translation: "Bienvenue ! Comment puis-je vous aider aujourd'hui ?",
            },
            ee: {
                greeting: "Woezɔ! Aleke mate ŋu akpe ɖe ŋuwò egbe?",
                translation: "Bienvenue ! Comment puis-je vous aider aujourd'hui ?",
            },
            tw: {
                greeting: "Akwaaba! Ɛdeɛn na mɛtumi ayɛ ama wo ɛnnɛ?",
                translation: "Bienvenue ! Comment puis-je vous aider aujourd'hui ?",
            },
            ga: {
                greeting: "Obaa ojogbaŋŋ! Mɛni manyɛ matsu mahã bo ŋmɛnɛ?",
                translation: "Bienvenue ! Comment puis-je vous aider aujourd'hui ?",
            },
            en: {
                greeting: "Welcome! How can I help you today?",
                translation: "Welcome! How can I help you today?",
            },
        }

        // Messages système dans chaque langue
        this.systemMessages = {
            ha: {
                ready: "A shirye don sauraro",
                recording: "Ana yin rikodin...",
                processing: "Ina tunani...",
                error: "Yi haƙuri, an sami kuskure",
                micError: "Kuskure: Ba za a iya samun damar microphone ba",
                languageChanged: "An canza harshe zuwa",
                demoMode: "An kunna yanayin demo",
                ttsError: "Kuskure: Ba za a iya samun damar TTS ba. Za a ci gaba ba tare da sauti ba.",
            },
            ee: {
                ready: "Wòe nà ɖe asi",
                recording: "Wòe nà ɖe asi...",
                processing: "Mele nububu me...",
                error: "Kafukafu, wòe nà ɖe asi",
                micError: "Kafukafu: Wòe nà ɖe asi",
                languageChanged: "Wòe nà ɖe asi",
                demoMode: "Wòe nà ɖe asi",
                ttsError: "Kafukafu: TTS mele. Za a ci gaba ba tare da sauti ba.",
            },
            tw: {
                ready: "Yɛ aseɛ",
                recording: "Yɛ aseɛ...",
                processing: "Medwendwen ho...",
                error: "Yɛ aseɛ",
                micError: "Yɛ aseɛ",
                languageChanged: "Yɛ aseɛ",
                demoMode: "Yɛ aseɛ",
                ttsError: "Yɛ aseɛ: TTS mele. Za a ci gaba ba tare da sauti ba.",
            },
            ga: {
                ready: "Yɛ aseɛ",
                recording: "Yɛ aseɛ...",
                processing: "Miisusumɔ he...",
                error: "Yɛ aseɛ",
                micError: "Yɛ aseɛ",
                languageChanged: "Yɛ aseɛ",
                demoMode: "Yɛ aseɛ",
                ttsError: "Yɛ aseɛ: TTS mele. Za a ci gaba ba tare da sauti ba.",
            },
            en: {
                ready: "Ready to listen",
                recording: "Recording...",
                processing: "Thinking...",
                error: "Sorry, an error occurred",
                micError: "Error: Could not access microphone",
                languageChanged: "Language changed to",
                demoMode: "Demo mode toggled",
                ttsError: "Error: Text-to-speech service unavailable. Continuing without audio.",
            },
        }

        // Réponses de démo pour le mode test
        this.demoResponses = {
            ha: [
                "Sannu! Ina kwana? Ina fatan kana lafiya.",
                "Na gode da tambayarka. Zan iya taimaka maka.",
                "Barka da zuwa. Me zan iya yi maka?",
                "Na fahimci. Zan iya ba da ƙarin bayani game da wannan.",
            ],
            ee: [
                "Woezɔ! Wòe nà? Mekafɔ be nàlé nyuie.",
                "Akpe ɖe wò nyabiabiawo ŋu. Mate ŋu akpe ɖe ŋuwò.",
                "Woezɔ ɖe mía gbɔ. Nuka mate ŋu awɔ na wò?",
                "Mese egɔme. Mate ŋu ana nyatakakawo tso eŋu.",
            ],
            tw: [
                "Maakyé! Wo ho te sɛn? Mewɔ anidasoɔ sɛ wo ho ye.",
                "Meda wo ase wɔ wo nsɛmmisa no ho. Mɛtumi aboa wo.",
                "Akwaaba. Dɛn na mɛtumi ayɛ ama wo?",
                "Mate aseɛ. Mɛtumi ama wo nsɛm pii afa yei ho.",
            ],
            ga: [
                "Mii! Afi oo? Miishɛɛlɛ akɛ oyeo jogbaŋŋ.",
                "Oyiwala dɔŋŋ wɔ osɛɛmɔ lɛ hewɔ. Manyɛ maye bo nine.",
                "Obaa ojogbaŋŋ. Mɛni manyɛ matsu mahã bo?",
                "Minuɛ. Manyɛ makɛ saji krokomɛi aha bo yɛ enɛ hewɔ.",
            ],
            en: [
                "Hello! How are you? I hope you're doing well.",
                "Thank you for your question. I can help you with that.",
                "Welcome. What can I do for you?",
                "I understand. I can provide more information about that.",
            ],
        }
        this.sessionId = `promogo-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
        this.welcomeMessagePlayed = false
        this.hasUserInteracted = false
        this.ttsErrorMessageDisplayed = false // Pour afficher le message d'erreur TTS une seule fois
    }

    async init() {
        this.initElements()
        this.setupEventListeners()
        this.applyTheme()
        this.updateStatusText()
        this.resetLanguageOptionListeners()
        this.updateInputVisibility()
        this.setupWelcomeScreen()
    }

    initElements() {
        this.messagesContainer = document.getElementById("messagesContainer")
        this.textInputContainer = document.getElementById("textInputContainer")
        this.textInput = document.getElementById("textInput")
        this.sendButton = document.getElementById("sendButton")
        this.recordButton = document.getElementById("recordButton")
        this.recordingStatus = document.getElementById("recordingStatus")
        this.recordingWaves = document.getElementById("recordingWaves")
        this.toggleInputBtn = document.getElementById("toggleInputBtn")
        this.selectedLanguage = document.getElementById("selectedLanguage")
        this.languageDropdown = document.getElementById("languageDropdown")
        this.languageOptions = document.querySelectorAll(".language-option")
        this.helpButton = document.getElementById("helpButton")
        this.helpPanel = document.getElementById("helpPanel")
        this.closeHelpButton = document.getElementById("closeHelpButton")
        this.demoButton = document.getElementById("demoButton")
        this.themeToggle = document.getElementById("themeToggle")
        this.welcomeOverlay = document.getElementById("welcomeOverlay")
        this.startChatButton = document.getElementById("startChatButton")

        // Créer et ajouter l'iframe container
        this.iframeContainer = document.createElement("div")
        this.iframeContainer.id = "iframeContainer"
        this.iframeContainer.className = "iframe-container hidden"
        this.iframeContainer.innerHTML = `
            <div class="iframe-header">
                <button class="iframe-close-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            <iframe id="contentIframe" title="Content"></iframe>
        `
        document.body.appendChild(this.iframeContainer)

        // Ajouter le gestionnaire d'événements pour le bouton de fermeture
        const closeBtn = this.iframeContainer.querySelector(".iframe-close-btn")
        closeBtn.addEventListener("click", () => this.closeIframe())
    }

    setupWelcomeScreen() {
        if (this.welcomeOverlay && this.startChatButton) {
            this.startChatButton.addEventListener("click", () => {
                this.hasUserInteracted = true
                this.welcomeOverlay.classList.add("fade-out")
                setTimeout(() => {
                    if (this.welcomeOverlay) {
                        this.welcomeOverlay.remove()
                    }
                    if (!this.welcomeMessagePlayed) {
                        this.playWelcomeMessage()
                    }
                }, 300)
            })
        } else {
            this.hasUserInteracted = true
            if (!this.welcomeMessagePlayed) {
                this.playWelcomeMessage()
            }
        }
    }

    playWelcomeMessage() {
        if (this.welcomeMessagePlayed) return;
        const welcomeMsg = this.welcomeMessages[this.currentLanguage];

        // Créer un message de processing
        const processingId = this.addMessage(this.systemMessages[this.currentLanguage].processing, "bot", true);

        this.welcomeMessagePlayed = true;

        if (this.hasUserInteracted && !this.isDemoMode && this.ttsAvailable) {
            this.sendToTTS(welcomeMsg.greeting)
                .then(async (audioBlob) => {
                    if (audioBlob.size > 0) {
                        const messageId = await this.addMessage("", "bot");
                        this.removeMessage(processingId);
                        await this.playAudioResponseWithText(audioBlob, welcomeMsg.greeting, messageId);
                    }
                })
                .catch((error) => {
                    console.error("Erreur TTS lors du message de bienvenue:", error);
                    this.removeMessage(processingId);
                    this.addMessage(welcomeMsg.greeting, "bot");
                    if (!this.ttsErrorMessageDisplayed) {
                        this.addMessage(this.systemMessages[this.currentLanguage].ttsError, "bot");
                        this.ttsErrorMessageDisplayed = true;
                    }
                });
        } else {
            this.removeMessage(processingId);
            this.addMessage(welcomeMsg.greeting, "bot");
        }
    }

    setupEventListeners() {
        this.textInput.addEventListener("keypress", (e) => {
            if (this.isProcessing) {
                e.preventDefault();
                return;
            }
            if (e.key === "Enter" && this.textInput.value.trim() !== "") this.handleTextInput();
        });

        this.sendButton.addEventListener("click", (e) => {
            if (this.isProcessing) {
                e.preventDefault();
                return;
            }
            if (this.textInput.value.trim() !== "") this.handleTextInput();
        });

        this.recordButton.addEventListener("click", (e) => {
            if (this.isProcessing) {
                e.preventDefault();
                return;
            }
            this.toggleRecording();
        });

        if (this.toggleInputBtn) {
            this.toggleInputBtn.addEventListener("click", (e) => {
                if (this.isProcessing) {
                    e.preventDefault();
                    return;
                }
                this.toggleTextInputVisibility();
            });
        }

        this.selectedLanguage.addEventListener("click", (e) => {
            if (this.isProcessing) {
                e.preventDefault();
                return;
            }
            this.toggleLanguageDropdown();
        });

        document.querySelectorAll(".language-option").forEach((option) => {
            option.addEventListener("click", (e) => {
                if (this.isProcessing) {
                    e.preventDefault();
                    return;
                }
                const langValue = option.getAttribute("data-value");
                this.changeLanguage(langValue);
                this.toggleLanguageDropdown(false);
            });
        });

        document.addEventListener("click", (e) => {
            if (
                !e.target.closest(".language-selector") &&
                this.languageDropdown &&
                this.languageDropdown.style.display !== "none"
            ) {
                this.toggleLanguageDropdown(false)
            }
        })
        this.helpButton.addEventListener("click", () => this.toggleHelpPanel())
        this.closeHelpButton.addEventListener("click", () => this.toggleHelpPanel(false))
        this.demoButton.addEventListener("click", () => this.toggleDemoMode())
        this.themeToggle.addEventListener("click", () => this.toggleTheme())
        document.addEventListener("keydown", (e) => {
            if (e.code === "Space" && document.activeElement !== this.textInput && !this.isTextInputVisible) {
                e.preventDefault()
                this.toggleRecording()
            }
            if (e.key === "?" && !e.shiftKey) {
                e.preventDefault()
                this.toggleHelpPanel()
            }
            if (e.key === "t" && !e.ctrlKey && !e.metaKey && document.activeElement !== this.textInput) {
                e.preventDefault()
                this.toggleTheme()
            }
            if (e.key === "k" && !e.ctrlKey && !e.metaKey && document.activeElement !== this.textInput) {
                e.preventDefault()
                this.toggleTextInputVisibility()
            }
            if (e.key === "Escape") {
                if (this.isHelpOpen) this.toggleHelpPanel(false)
                if (this.languageDropdown && this.languageDropdown.style.display !== "none") this.toggleLanguageDropdown(false)
            }
        })
    }

    toggleTextInputVisibility() {
        this.isTextInputVisible = !this.isTextInputVisible
        this.updateInputVisibility()
    }

    updateInputVisibility() {
        if (this.isTextInputVisible) {
            this.textInputContainer.classList.remove("hidden")
            this.recordButton.classList.add("hidden")
            if (this.toggleInputBtn) this.toggleInputBtn.classList.add("active")
            this.textInput.focus()
        } else {
            this.textInputContainer.classList.add("hidden")
            this.recordButton.classList.remove("hidden")
            if (this.toggleInputBtn) this.toggleInputBtn.classList.remove("active")
        }
    }

    resetLanguageOptionListeners() {
        document.querySelectorAll(".language-option").forEach((option) => {
            const newOption = option.cloneNode(true)
            option.parentNode.replaceChild(newOption, option)
            newOption.addEventListener("click", () => {
                const langValue = newOption.getAttribute("data-value")
                this.changeLanguage(langValue)
                this.toggleLanguageDropdown(false)
            })
        })
        this.languageOptions = document.querySelectorAll(".language-option")
    }

    toggleLanguageDropdown(show = null) {
        if (this.isProcessing) return; // Ne pas permettre l'ouverture pendant le traitement
        const languageSelector = this.selectedLanguage.parentElement;
        if (!languageSelector) return;
        if (show === null) languageSelector.classList.toggle("open");
        else if (show) languageSelector.classList.add("open");
        else languageSelector.classList.remove("open");
        if (this.languageDropdown)
            this.languageDropdown.style.display = languageSelector.classList.contains("open") ? "block" : "none";
    }

    toggleHelpPanel(show = null) {
        if (show === null) this.isHelpOpen = !this.isHelpOpen
        else this.isHelpOpen = show
        if (this.helpPanel) {
            if (this.isHelpOpen) this.helpPanel.classList.add("open")
            else this.helpPanel.classList.remove("open")
        }
    }

    toggleDemoMode() {
        this.isDemoMode = !this.isDemoMode
        if (this.demoButton) {
            this.demoButton.classList.toggle("active", this.isDemoMode)
            this.demoButton.textContent = this.isDemoMode ? "Disable demo mode" : "Enable demo mode"
        }
        const message = this.isDemoMode
            ? this.systemMessages[this.currentLanguage].demoMode
            : "Demo mode disabled. Using real API endpoints for communication."
        this.addMessage(message, "bot")
    }

    toggleTheme() {
        this.isDarkMode = !this.isDarkMode
        this.applyTheme()
    }

    applyTheme() {
        if (this.isDarkMode) document.documentElement.classList.add("dark")
        else document.documentElement.classList.remove("dark")
    }

    async changeLanguage(langCode) {
        if (this.isProcessing) return; // Ne pas permettre le changement pendant le traitement
        this.currentLanguage = langCode;
        const selectedOption = Array.from(this.languageOptions).find(
            (option) => option.getAttribute("data-value") === langCode,
        );
        if (selectedOption) {
            const flag = selectedOption.querySelector(".flag").textContent;
            const name = selectedOption.querySelector(".language-name").textContent;
            this.selectedLanguage.querySelector(".flag").textContent = flag;
            this.selectedLanguage.querySelector(".language-name").textContent = name;
            this.languageOptions.forEach((option) =>
                option.classList.toggle("selected", option.getAttribute("data-value") === langCode),
            );

            const langChangedMsg = `${this.systemMessages[this.currentLanguage].languageChanged} ${name}`;

            // Créer un message de processing
            const processingId = this.addMessage(this.systemMessages[this.currentLanguage].processing, "bot", true);

            if (this.hasUserInteracted && !this.isDemoMode && this.ttsAvailable) {
                try {
                    const audioBlob = await this.sendToTTS(langChangedMsg);
                    if (audioBlob.size > 0) {
                        const messageId = await this.addMessage("", "bot");
                        this.removeMessage(processingId);
                        await this.playAudioResponseWithText(audioBlob, langChangedMsg, messageId);
                    }
                } catch (error) {
                    console.error("TTS error for language change:", error);
                    this.removeMessage(processingId);
                    this.addMessage(langChangedMsg, "bot");
                    if (!this.ttsErrorMessageDisplayed) {
                        this.addMessage(this.systemMessages[this.currentLanguage].ttsError, "bot");
                        this.ttsErrorMessageDisplayed = true;
                    }
                }
            } else {
                this.removeMessage(processingId);
                this.addMessage(langChangedMsg, "bot");
            }
        }
        this.updateStatusText();
    }

    updateStatusText() {
        const statusText = this.isRecording
            ? this.systemMessages[this.currentLanguage].recording
            : this.systemMessages[this.currentLanguage].ready
        if (this.recordingStatus) this.recordingStatus.textContent = statusText
    }

    async toggleRecording() {
        if (this.isProcessing) return;
        if (!this.hasUserInteracted) console.warn("User interaction required to start recording and play audio.");

        if (!this.isRecording) {
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                this.currentAudio = null;
                const playingButton = this.messagesContainer.querySelector(".play-button.playing");
                if (playingButton) playingButton.classList.remove("playing");
            }
            await this.startRecording();
        } else {
            await this.stopRecording();
        }
    }

    async startRecording() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.addMessage(this.systemMessages[this.currentLanguage].micError + " (MediaDevices API not supported)", "bot")
            return
        }
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const supportedTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/ogg", "audio/wav"]
            const mimeType = supportedTypes.find((type) => MediaRecorder.isTypeSupported(type)) || ""
            this.mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
            this.audioChunks = []
            this.mediaRecorder.ondataavailable = (event) => this.audioChunks.push(event.data)
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: mimeType || "audio/webm" })
                if (this.isDemoMode) {
                    const randomText = this.getRandomUserQuery()
                    this.addMessage(randomText, "user")
                    this.simulateResponse()
                } else {
                    await this.processAudio(audioBlob)
                }
            }
            this.mediaRecorder.start()
            this.isRecording = true
            this.recordButton.classList.add("recording")
            document.body.classList.add("recording")
            this.updateStatusText()
        } catch (error) {
            console.error("Erreur lors de l'accès au microphone:", error)
            this.addMessage(this.systemMessages[this.currentLanguage].micError, "bot")
        }
    }

    async stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop()
            this.isRecording = false
            this.recordButton.classList.remove("recording")
            document.body.classList.remove("recording")
            this.updateStatusText()
            if (this.mediaRecorder.stream) this.mediaRecorder.stream.getTracks().forEach((track) => track.stop())
        }
    }

    handleTextInput() {
        if (this.isProcessing) return;
        const text = this.textInput.value.trim();
        if (text === "") return;

        // Activer l'état de traitement avant de commencer
        this.isProcessing = true;
        this.updateControlsState();

        this.addMessage(text, "user");
        this.textInput.value = "";
        if (this.isDemoMode) this.simulateResponse();
        else this.processText(text);
    }

    async processText(text) {
        const processingId = this.addMessage(this.systemMessages[this.currentLanguage].processing, "bot", true);
        try {
            const rasaResult = await this.sendToRasa(text);
            this.removeMessage(processingId);
            const rasaResponse = rasaResult.text;
            const redirectURL = rasaResult.redirectUrl;
            const buttons = rasaResult.buttons || [];
            if (redirectURL) this.openInIframe(redirectURL);

            const messageId = await this.addMessage("", "bot", false, buttons);

            if (this.hasUserInteracted && !this.isDemoMode && this.ttsAvailable) {
                try {
                    const audioResponse = await this.sendToTTS(rasaResponse);
                    if (audioResponse.size > 0) {
                        await this.playAudioResponseWithText(audioResponse, rasaResponse, messageId);
                    }
                } catch (error) {
                    console.error("TTS Error in processText:", error);
                    if (!this.ttsErrorMessageDisplayed) {
                        this.addMessage(this.systemMessages[this.currentLanguage].ttsError, "bot");
                        this.ttsErrorMessageDisplayed = true;
                    }
                    this.updateMessageText(messageId, rasaResponse);
                }
            } else {
                this.updateMessageText(messageId, rasaResponse);
            }
        } catch (error) {
            console.error("Erreur lors du traitement du texte:", error);
            this.removeMessage(processingId);
            this.addMessage(this.systemMessages[this.currentLanguage].error, "bot");
        } finally {
            this.isProcessing = false;
            this.updateControlsState();
        }
    }

    async processAudio(audioBlob) {
        const processingId = this.addMessage(this.systemMessages[this.currentLanguage].processing, "bot", true);
        try {
            const transcription = await this.sendToSTT(audioBlob);
            this.removeMessage(processingId);
            this.addMessage(transcription, "user");
            const rasaResult = await this.sendToRasa(transcription);
            const rasaResponse = rasaResult.text;
            const redirectURL = rasaResult.redirectUrl;
            const buttons = rasaResult.buttons || [];
            if (redirectURL) this.openInIframe(redirectURL);

            const messageId = await this.addMessage("", "bot", false, buttons);

            if (this.hasUserInteracted && !this.isDemoMode && this.ttsAvailable) {
                try {
                    const audioResponse = await this.sendToTTS(rasaResponse);
                    if (audioResponse.size > 0) {
                        await this.playAudioResponseWithText(audioResponse, rasaResponse, messageId);
                    }
                } catch (error) {
                    console.error("TTS Error in processAudio:", error);
                    if (!this.ttsErrorMessageDisplayed) {
                        this.addMessage(this.systemMessages[this.currentLanguage].ttsError, "bot");
                        this.ttsErrorMessageDisplayed = true;
                    }
                    this.updateMessageText(messageId, rasaResponse);
                }
            } else {
                this.updateMessageText(messageId, rasaResponse);
            }
        } catch (error) {
            console.error("Erreur lors du traitement audio:", error);
            this.removeMessage(processingId);
            this.addMessage(this.systemMessages[this.currentLanguage].error, "bot");
        } finally {
            this.isProcessing = false;
            this.updateControlsState();
        }
    }

    simulateResponse() {
        const processingId = this.addMessage(this.systemMessages[this.currentLanguage].processing, "bot", true)
        setTimeout(() => {
            this.removeMessage(processingId)
            const response = this.getRandomBotResponse()
            this.addMessage(response, "bot")
            if (this.hasUserInteracted) this.simulateAudioPlayback()
        }, 1500)
    }

    simulateAudioPlayback() {
        if (!this.hasUserInteracted) return
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()
        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)
        oscillator.type = "sine"
        oscillator.frequency.setValueAtTime(440, audioContext.currentTime)
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)
        oscillator.start()
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 1)
        oscillator.stop(audioContext.currentTime + 1)
    }

    getRandomUserQuery() {
        const queries = ["Hello", "Help me", "What time is it?", "Thanks"]
        return queries[Math.floor(Math.random() * queries.length)]
    }

    getRandomBotResponse() {
        const responses = this.demoResponses[this.currentLanguage]
        return responses[Math.floor(Math.random() * responses.length)]
    }

    async sendToSTT(audioBlob) {
        if (this.isDemoMode) return this.getRandomUserQuery()
        if (this.apiEndpoints.stt === "VOTRE_API_STT") {
            console.warn("STT API not configured.")
            return this.getRandomUserQuery()
        }
        const formData = new FormData()
        formData.append("audio", audioBlob, "audio.webm")
        formData.append("language", this.currentLanguage)
        try {
            const response = await fetch(this.apiEndpoints.stt, { method: "POST", body: formData })
            if (!response.ok) throw new Error(`STT Error: ${response.statusText}`)
            const data = await response.json()
            return data.transcription
        } catch (error) {
            console.error("STT Error:", error)
            return this.getRandomUserQuery()
        }
    }

    async sendToRasa(text) {
        if (this.isDemoMode) return { text: this.getRandomBotResponse(), redirectUrl: null, buttons: [] }
        if (this.apiEndpoints.rasa === "VOTRE_API_RASA") {
            console.warn("Rasa API not configured.")
            return { text: this.getRandomBotResponse(), redirectUrl: null, buttons: [] }
        }
        const payload = {
            sender: this.sessionId,
            message: text,
            metadata: { language: this.currentLanguage },
        }
        try {
            const response = await fetch(this.apiEndpoints.rasa, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
            if (!response.ok) throw new Error(`Rasa Error: ${response.statusText} - ${await response.text()}`)

            const rawRasaResponse = await response.json()
            let customPayload

            if (Array.isArray(rawRasaResponse) && rawRasaResponse.length > 0) {
                customPayload = rawRasaResponse[0].custom || rawRasaResponse[0]
            } else if (rawRasaResponse && typeof rawRasaResponse === "object") {
                customPayload = rawRasaResponse.custom || rawRasaResponse
            } else {
                console.error("Unexpected Rasa response format:", rawRasaResponse)
                return { text: this.systemMessages[this.currentLanguage].error, redirectUrl: null, buttons: [] }
            }

            if (
                !customPayload ||
                typeof customPayload !== "object" ||
                !("response" in customPayload || "text" in customPayload)
            ) {
                console.error(
                    "Could not extract valid custom payload from Rasa response. Extracted:",
                    customPayload,
                    "Original Rasa response:",
                    rawRasaResponse,
                )
                let fallbackText = this.systemMessages[this.currentLanguage].error
                if (Array.isArray(rawRasaResponse) && rawRasaResponse.length > 0 && rawRasaResponse[0].text) {
                    fallbackText = rawRasaResponse[0].text
                } else if (rawRasaResponse && rawRasaResponse.text) {
                    fallbackText = rawRasaResponse.text
                }
                return { text: fallbackText, redirectUrl: null, buttons: [] }
            }

            const textResponse = customPayload.response || customPayload.text || ""
            const buttons = (customPayload.buttons || []).map((btn) => ({
                title: btn.title,
                payload: btn.payload,
                type: btn.type,
                useIframe: btn.useIframe !== false, // Nouveau paramètre pour contrôler l'utilisation de l'iframe
            }))
            const redirectUrl = customPayload.redirect_url || null

            return { text: textResponse, redirectUrl, buttons }
        } catch (error) {
            console.error("Rasa Error:", error)
            return { text: this.systemMessages[this.currentLanguage].error, redirectUrl: null, buttons: [] }
        }
    }

    async sendToTTS(text) {
        if (!this.ttsAvailable || this.isDemoMode || !text.trim()) {
            return new Blob([], { type: "audio/wav" })
        }

        if (this.apiEndpoints.tts === "VOTRE_API_TTS") {
            console.warn("TTS API not configured.")
            return new Blob([], { type: "audio/wav" })
        }

        try {
            const ttsUrl = this.apiEndpoints.tts
            const response = await fetch(ttsUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, language: this.currentLanguage }),
            })

            if (!response.ok) {
                throw new Error(`TTS Error: ${response.statusText} (${response.status})`)
            }
            return await response.blob()
        } catch (error) {
            console.error("TTS Error in sendToTTS:", error)
            this.ttsAvailable = false // Marquer le TTS comme indisponible
            // Ne pas ajouter de message ici, le faire dans le code appelant pour éviter les doublons
            throw error // Renvoyer l'erreur pour que le code appelant puisse la gérer
        }
    }

    playAudioResponse(audioBlob) {
        return new Promise((resolve, reject) => {
            if (!this.hasUserInteracted || audioBlob.size === 0) {
                if (audioBlob.size === 0) console.warn("TTS returned empty audio blob.");
                resolve();
                return;
            }
            if (this.isDemoMode) {
                this.simulateAudioPlayback();
                resolve();
                return;
            }

            // Arrêter l'audio en cours s'il y en a un
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                const playingButton = this.messagesContainer.querySelector(".play-button.playing");
                if (playingButton) playingButton.classList.remove("playing");
            }

            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            this.currentAudio = audio;

            audio.addEventListener("play", () => {
                const lastBotMessage = this.messagesContainer.querySelector(".message.bot:last-child .play-button");
                if (lastBotMessage) lastBotMessage.classList.add("playing");
            });

            audio.addEventListener("ended", () => {
                const lastBotMessage = this.messagesContainer.querySelector(".message.bot:last-child .play-button");
                if (lastBotMessage) lastBotMessage.classList.remove("playing");
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                resolve();
            });

            audio.addEventListener("error", (e) => {
                console.error("Error playing audio:", e);
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                reject(e);
            });

            audio.play().catch((e) => {
                console.error("Audio play failed:", e);
                reject(e);
            });
        });
    }

    async playAudioResponseWithText(audioBlob, fullText, messageId) {
        return new Promise((resolve, reject) => {
            if (!this.hasUserInteracted || audioBlob.size === 0) {
                if (audioBlob.size === 0) console.warn("TTS returned empty audio blob.");
                this.updateMessageText(messageId, fullText);
                resolve();
                return;
            }

            // Arrêter l'audio en cours s'il y en a un
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
                const playingButton = this.messagesContainer.querySelector(".play-button.playing");
                if (playingButton) playingButton.classList.remove("playing");
            }

            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            this.currentAudio = audio;

            // Ajouter la classe processing au message en attendant que l'audio commence
            const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
            if (messageElement) {
                messageElement.classList.add("processing");
            }

            // Mettre à jour le texte progressivement pendant la lecture
            audio.addEventListener("timeupdate", () => {
                const progress = audio.currentTime / audio.duration;
                const targetChars = Math.floor(fullText.length * progress);
                const textToShow = fullText.substring(0, targetChars);
                this.updateMessageText(messageId, textToShow);
            });

            audio.addEventListener("play", () => {
                // Retirer la classe processing une fois que l'audio commence
                if (messageElement) {
                    messageElement.classList.remove("processing");
                }
                const playButton = this.messagesContainer.querySelector(".message.bot:last-child .play-button");
                if (playButton) playButton.classList.add("playing");
            });

            audio.addEventListener("ended", () => {
                this.updateMessageText(messageId, fullText);
                const playButton = this.messagesContainer.querySelector(".message.bot:last-child .play-button");
                if (playButton) playButton.classList.remove("playing");
                if (messageElement) {
                    messageElement.classList.remove("processing");
                }
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                resolve();
            });

            audio.addEventListener("error", (e) => {
                this.updateMessageText(messageId, fullText);
                if (messageElement) {
                    messageElement.classList.remove("processing");
                }
                console.error("Error playing audio:", e);
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                reject(e);
            });

            // Commencer la lecture
            audio.play().catch((e) => {
                this.updateMessageText(messageId, fullText);
                if (messageElement) {
                    messageElement.classList.remove("processing");
                }
                console.error("Audio play failed:", e);
                reject(e);
            });
        });
    }

    updateMessageText(messageId, text) {
        const messageElement = document.querySelector(`.message[data-id="${messageId}"] p`);
        if (messageElement) {
            messageElement.textContent = text;
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    addMessage(text, sender, isProcessing = false, buttons = []) {
        const messageId = Date.now().toString()
        const now = new Date()
        const timeString = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        const messageElement = document.createElement("div")
        messageElement.classList.add("message", sender)
        messageElement.dataset.id = messageId
        if (isProcessing) messageElement.classList.add("processing")

        const avatarSrc = sender === "bot" ? "assets/icons/bot-avatar.svg" : "assets/icons/mic.svg"

        let btnHtml = ""
        if (sender === "bot" && buttons && buttons.length > 0 && !isProcessing) {
            btnHtml = `<div class="bot-buttons">${buttons
                .map(
                    (b) =>
                        `<button class="bot-btn" data-type="${b.type}" data-payload="${b.payload}" data-use-iframe="${b.useIframe !== false}" title="${b.title}">${b.title}</button>`,
                )
                .join("")}</div>`
        }

        messageElement.innerHTML = `
      <div class="message-avatar">
        <img src="${avatarSrc}" alt="${sender === "bot" ? "Assistant" : "You"}" class="avatar-img">
      </div>
      <div class="message-content">
        <div class="message-bubble">
          <p>${text}</p>
          ${btnHtml}
        </div>
        <div class="message-actions">
          ${sender === "bot" && !isProcessing
                ? `
            <button class="play-button" aria-label="Listen">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3.71V12.29C3 12.7654 3.5346 13.0777 3.94281 12.8236L11.0572 8.53365C11.4436 8.29057 11.4436 7.70943 11.0572 7.46635L3.94281 3.17636C3.5346 2.92233 3 3.23464 3 3.71Z" fill="currentColor"/>
              </svg>
            </button>`
                : ""
            }
          <span class="message-time">${timeString}</span>
        </div>
      </div>`

        this.messagesContainer.appendChild(messageElement)
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight

        if (sender === "bot" && !isProcessing) {
            const playButton = messageElement.querySelector(".play-button")
            if (playButton) {
                if (!this.ttsAvailable) {
                    playButton.classList.add("disabled")
                    playButton.title = this.systemMessages[this.currentLanguage].ttsError
                }

                playButton.addEventListener("click", async () => {
                    if (playButton.classList.contains("disabled")) return

                    const messageText = messageElement.querySelector("p").textContent
                    if (this.isDemoMode) {
                        if (this.hasUserInteracted) this.simulateAudioPlayback()
                        playButton.classList.add("playing")
                        setTimeout(() => playButton.classList.remove("playing"), 2000)
                    } else {
                        if (this.hasUserInteracted) {
                            if (this.ttsAvailable) {
                                try {
                                    const audioResponse = await this.sendToTTS(messageText)
                                    if (audioResponse.size > 0) {
                                        this.playAudioResponse(audioResponse)
                                    }
                                } catch (error) {
                                    console.error("TTS Error on play button click:", error)
                                    playButton.classList.add("disabled")
                                    playButton.title = this.systemMessages[this.currentLanguage].ttsError
                                    if (!this.ttsErrorMessageDisplayed) {
                                        this.addMessage(this.systemMessages[this.currentLanguage].ttsError, "bot")
                                        this.ttsErrorMessageDisplayed = true
                                    }
                                }
                            }
                        } else {
                            console.warn("User interaction needed to play audio.")
                        }
                    }
                })
            }
        }

        if (sender === "bot" && buttons && buttons.length > 0 && !isProcessing) {
            messageElement.querySelectorAll(".bot-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    const type = btn.dataset.type
                    const payload = btn.dataset.payload
                    const useIframe = btn.dataset.useIframe !== "false"

                    if (type === "phone") {
                        window.location.href = payload
                    } else if (type === "email") {
                        window.location.href = payload
                    } else if (type === "url") {
                        this.openInIframe(payload)
                    } else if (type === "postback") {
                        this.addMessage(btn.title, "user")
                        this.processText(payload)
                    } else {
                        if (payload && payload.startsWith("tel:")) {
                            window.location.href = payload
                        } else if (payload && payload.startsWith("mailto:")) {
                            window.location.href = payload
                        } else if (payload && (payload.startsWith("http:") || payload.startsWith("https:"))) {
                            this.openInIframe(payload)
                        } else {
                            console.warn(`Unhandled button type: '${type}' with payload: '${payload}'`)
                        }
                    }
                })
            })
        }
        return messageId
    }

    removeMessage(messageId) {
        const message = this.messagesContainer.querySelector(`.message[data-id="${messageId}"]`)
        if (message) message.remove()
    }

    configureAPIEndpoints(endpoints) {
        if (endpoints.stt) this.apiEndpoints.stt = endpoints.stt
        if (endpoints.rasa) this.apiEndpoints.rasa = endpoints.rasa
        if (endpoints.tts) this.apiEndpoints.tts = endpoints.tts
        console.log("API endpoints configured:", this.apiEndpoints)
        if (
            this.apiEndpoints.stt !== "VOTRE_API_STT" &&
            this.apiEndpoints.rasa !== "VOTRE_API_RASA" &&
            this.apiEndpoints.tts !== "VOTRE_API_TTS"
        ) {
            this.isDemoMode = false
            if (this.demoButton) {
                this.demoButton.classList.remove("active")
                this.demoButton.textContent = "Enable demo mode"
            }
            // Réinitialiser ttsAvailable car les endpoints ont peut-être changé
            this.ttsAvailable = true
            this.ttsErrorMessageDisplayed = false
        }
    }

    updateControlsState() {
        // Désactiver/activer le bouton d'enregistrement
        if (this.recordButton) {
            this.recordButton.disabled = this.isProcessing;
            this.recordButton.style.pointerEvents = this.isProcessing ? 'none' : 'auto';
            this.recordButton.classList.toggle('disabled', this.isProcessing);
        }

        // Désactiver/activer le champ texte et le bouton d'envoi
        if (this.textInput) {
            this.textInput.disabled = this.isProcessing;
            this.textInput.style.pointerEvents = this.isProcessing ? 'none' : 'auto';
            this.textInput.classList.toggle('disabled', this.isProcessing);
        }
        if (this.sendButton) {
            this.sendButton.disabled = this.isProcessing;
            this.sendButton.style.pointerEvents = this.isProcessing ? 'none' : 'auto';
            this.sendButton.classList.toggle('disabled', this.isProcessing);
        }

        // Désactiver/activer le bouton de basculement du mode texte
        if (this.toggleInputBtn) {
            this.toggleInputBtn.disabled = this.isProcessing;
            this.toggleInputBtn.style.pointerEvents = this.isProcessing ? 'none' : 'auto';
            this.toggleInputBtn.classList.toggle('disabled', this.isProcessing);
        }

        // Désactiver/activer le sélecteur de langue
        if (this.selectedLanguage) {
            this.selectedLanguage.style.pointerEvents = this.isProcessing ? 'none' : 'auto';
            this.selectedLanguage.classList.toggle('disabled', this.isProcessing);
            // Si le menu est ouvert pendant le traitement, le fermer
            if (this.isProcessing) {
                this.toggleLanguageDropdown(false);
            }
        }
    }

    // Nouvelle méthode pour ouvrir l'iframe
    openInIframe(url) {
        const iframe = document.getElementById("contentIframe")
        iframe.src = url
        this.iframeContainer.classList.remove("hidden")
        this.isIframeVisible = true
    }

    // Nouvelle méthode pour fermer l'iframe
    closeIframe() {
        const iframe = document.getElementById("contentIframe")
        iframe.src = ""
        this.iframeContainer.classList.add("hidden")
        this.isIframeVisible = false
    }
}
