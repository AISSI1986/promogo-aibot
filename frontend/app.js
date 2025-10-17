// Configuration - Updated for GhanaNLP Integration
const apiEndpoints = {
  ghananlp: "https://promogo-ghananlp.onrender.com", // GhanaNLP service
  rasa: "https://promogo-rasa.onrender.com/webhooks/rest/webhook",
  // Legacy endpoints (will be removed)
  stt: "https://promogo-stt.onrender.com/transcribe",
  tts: "https://promogo-tts.onrender.com/synthesize/"
};

// Global variables
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let currentLanguage = 'en';

// Language configuration
const languageConfig = {
    'en': { name: 'English', flag: '🇬🇧', code: 'en' },
    'ha': { name: 'Hausa', flag: '🇳🇬', code: 'ha' },
    'tw': { name: 'Twi', flag: '🇬🇭', code: 'tw' },
    'ee': { name: 'Eʋegbe', flag: '🇬🇭', code: 'ee' },
    'ga': { name: 'Ga', flag: '🇬🇭', code: 'ga' },
    'dagbani': { name: 'Dagbani', flag: '🇬🇭', code: 'dagbani' }
};

// DOM elements
const startChatButton = document.getElementById('startChatButton');
const welcomeOverlay = document.getElementById('welcomeOverlay');
const messagesContainer = document.getElementById('messagesContainer');
const recordButton = document.getElementById('recordButton');
const textInput = document.getElementById('textInput');
const sendButton = document.getElementById('sendButton');
const toggleInputBtn = document.getElementById('toggleInputBtn');
const textInputContainer = document.getElementById('textInputContainer');
const recordingStatus = document.getElementById('recordingStatus');
const recordingWaves = document.getElementById('recordingWaves');

// Language selector elements
const selectedLanguage = document.getElementById('selectedLanguage');
const languageDropdown = document.getElementById('languageDropdown');
const languageSelector = document.querySelector('.language-selector');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
  console.log('Promogo app initialized');
  
  // Initialize language selector
  initializeLanguageSelector();
  
  // Event listeners
  if (startChatButton) {
    startChatButton.addEventListener('click', startConversation);
  }
  
  if (recordButton) {
    recordButton.addEventListener('click', toggleRecording);
  }
  
  if (sendButton) {
    sendButton.addEventListener('click', sendTextMessage);
  }
  
  if (textInput) {
    textInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        sendTextMessage();
      }
    });
  }
  
  if (toggleInputBtn) {
    toggleInputBtn.addEventListener('click', toggleInputMode);
  }
  
  // Language selector
  setupLanguageSelector();
  
  // Theme toggle
  setupThemeToggle();
});

// Start conversation - hide welcome overlay
function startConversation() {
  console.log('Starting conversation...');
  if (welcomeOverlay) {
    welcomeOverlay.style.display = 'none';
  }
  
  // Add welcome message
  addMessage('bot', 'Hello! I\'m your Promogo assistant. How can I help you today?');
}

// Add message to chat
function addMessage(sender, text, isAudio = false, language = null) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  if (isAudio) {
    messageDiv.innerHTML = `
      <div class="message-content">
        <audio controls class="audio-player">
          <source src="${text}" type="audio/wav">
          Your browser does not support the audio element.
        </audio>
      </div>
    `;
  } else {
    const languageInfo = language ? `<div class="message-language">${languageConfig[language]?.name || language}</div>` : '';
    messageDiv.innerHTML = `
      <div class="message-content">
        ${languageInfo}
        <span class="message-text">${text}</span>
      </div>
    `;
  }
  
  if (messagesContainer) {
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

// Send text message
async function sendTextMessage() {
  const message = textInput.value.trim();
  if (!message) {
    // Show validation feedback
    textInput.style.borderColor = 'var(--error)';
    textInput.placeholder = 'Please enter a message...';
    setTimeout(() => {
      textInput.style.borderColor = '';
      textInput.placeholder = 'Type a message...';
    }, 2000);
    return;
  }
  
    // Add user message with language info
    addMessage('user', message, false, currentLanguage);
  textInput.value = '';
  
  // Disable send button and show loading state
  sendButton.disabled = true;
  sendButton.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" class="loading-spinner">
      <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.416" stroke-dashoffset="31.416">
        <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
        <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
      </circle>
    </svg>
  `;
  
  // Show typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message bot-message typing';
  typingDiv.innerHTML = '<div class="message-content"><span class="typing-indicator">Bot is typing...</span></div>';
  messagesContainer.appendChild(typingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  try {
    // Send to chatbot
    const response = await fetch(apiEndpoints.rasa, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender: 'user',
        message: message
      })
    });
    
    const data = await response.json();
    
    // Remove typing indicator
    typingDiv.remove();
    
    // Add bot response and convert to speech
    if (data && data.length > 0) {
      data.forEach(msg => {
        addMessage('bot', msg.text, false, currentLanguage);
        // Convert bot response to speech
        textToSpeech(msg.text, currentLanguage);
      });
    } else {
      const fallbackMessage = 'Sorry, I didn\'t understand that. Can you try again?';
      addMessage('bot', fallbackMessage, false, currentLanguage);
      // Convert fallback message to speech
      textToSpeech(fallbackMessage, currentLanguage);
    }
    
  } catch (error) {
    console.error('Error sending message:', error);
    typingDiv.remove();
    addMessage('bot', 'Sorry, there was an error connecting to the chatbot. Please try again.', false, currentLanguage);
  } finally {
    // Restore send button
    sendButton.disabled = false;
    sendButton.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18.3333 1.66667L9.16667 10.8333" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M18.3333 1.66667L12.5 18.3333L9.16667 10.8333L1.66667 7.5L18.3333 1.66667Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
  }
}

// Toggle recording
async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
}

// Start recording
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    
    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      await processAudio(audioBlob);
      stream.getTracks().forEach(track => track.stop());
    };
    
    mediaRecorder.start();
    isRecording = true;
    
    // Update UI
    recordButton.classList.add('recording');
    recordingWaves.style.display = 'flex';
    recordingStatus.textContent = 'Recording... Click to stop';
    
  } catch (error) {
    console.error('Error starting recording:', error);
    addMessage('bot', 'Sorry, I couldn\'t access your microphone. Please check your permissions.', false, currentLanguage);
  }
}

// Stop recording
function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    
    // Update UI
    recordButton.classList.remove('recording');
    recordingWaves.style.display = 'none';
    recordingStatus.textContent = 'Processing audio...';
  }
}

// Convert text to speech
async function textToSpeech(text, language = currentLanguage) {
  try {
    const response = await fetch(apiEndpoints.tts, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        language: language
      })
    });
    
    if (!response.ok) {
      throw new Error(`TTS API error: ${response.status}`);
    }
    
    // Get audio blob from response
    const audioBlob = await response.blob();
    
    // Create audio element and play
    const audio = new Audio();
    audio.src = URL.createObjectURL(audioBlob);
    audio.play();
    
    return true;
  } catch (error) {
    console.error('Error with text-to-speech:', error);
    return false;
  }
}

// Process audio
async function processAudio(audioBlob) {
  try {
    // Convert speech to text
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('language', currentLanguage);
    
    const sttResponse = await fetch(`${apiEndpoints.ghananlp}/transcribe`, {
      method: 'POST',
      body: formData
    });
    
    if (!sttResponse.ok) {
      throw new Error(`GhanaNLP STT API error: ${sttResponse.status}`);
    }
    
    const sttData = await sttResponse.json();
    const transcribedText = sttData.text || 'Could not transcribe audio';
    
    // Add transcribed message with language info
    addMessage('user', `🎤 ${transcribedText}`, false, currentLanguage);
    
    // Send to chatbot
    const rasaResponse = await fetch(apiEndpoints.rasa, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sender: 'user',
        message: transcribedText
      })
    });
    
    if (!rasaResponse.ok) {
      throw new Error(`Chatbot API error: ${rasaResponse.status}`);
    }
    
    const rasaData = await rasaResponse.json();
    
    // Add bot response and convert to speech
    if (rasaData && rasaData.length > 0) {
      rasaData.forEach(msg => {
        addMessage('bot', msg.text, false, currentLanguage);
        // Convert bot response to speech
        textToSpeech(msg.text, currentLanguage);
      });
    } else {
      const fallbackMessage = 'Sorry, I didn\'t understand that. Can you try again?';
      addMessage('bot', fallbackMessage, false, currentLanguage);
      // Convert fallback message to speech
      textToSpeech(fallbackMessage, currentLanguage);
    }
    
    recordingStatus.textContent = 'Ready to listen';
    
  } catch (error) {
    console.error('Error processing audio:', error);
    recordingStatus.textContent = 'Error processing audio';
    addMessage('bot', `Sorry, there was an error processing your audio: ${error.message}. Please try again.`, false, currentLanguage);
  }
}

// Toggle input mode
function toggleInputMode() {
  if (textInputContainer.classList.contains('hidden')) {
    textInputContainer.classList.remove('hidden');
    recordButton.style.display = 'none';
  } else {
    textInputContainer.classList.add('hidden');
    recordButton.style.display = 'flex';
  }
}

// Setup language selector
function setupLanguageSelector() {
  const selectedLanguage = document.getElementById('selectedLanguage');
  const languageDropdown = document.getElementById('languageDropdown');
  const languageOptions = document.querySelectorAll('.language-option');
  
  if (selectedLanguage && languageDropdown) {
    selectedLanguage.addEventListener('click', () => {
      languageDropdown.classList.toggle('show');
    });
    
    languageOptions.forEach(option => {
      option.addEventListener('click', () => {
        const value = option.dataset.value;
        const flag = option.querySelector('.flag').textContent;
        const name = option.querySelector('.language-name').textContent;
        
        // Update selected language
        selectedLanguage.querySelector('.flag').textContent = flag;
        selectedLanguage.querySelector('.language-name').textContent = name;
        
        // Update current language
        currentLanguage = value;
        
        // Remove selected class from all options
        languageOptions.forEach(opt => opt.classList.remove('selected'));
        // Add selected class to clicked option
        option.classList.add('selected');
        
        // Hide dropdown
        languageDropdown.classList.remove('show');
      });
    });
  }
}

// Setup theme toggle
function setupThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
    }
  }
}

// Utility functions for API calls (kept for compatibility)
async function sendMessage(message) {
  const response = await fetch(apiEndpoints.rasa, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender: 'user',
      message: message
    })
  });
  return response.json();
}

async function convertSpeechToText(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  
  const response = await fetch(`${apiEndpoints.ghananlp}/transcribe`, {
    method: 'POST',
    body: formData
  });
  return response.json();
}

async function convertTextToSpeech(text) {
  const response = await fetch(`${apiEndpoints.ghananlp}/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      text: text,
      language: currentLanguage 
    })
  });
  return response.blob();
}

// Language Selector Functions
function initializeLanguageSelector() {
  if (!selectedLanguage || !languageDropdown || !languageSelector) {
    console.warn('Language selector elements not found');
    return;
  }

  // Set initial language
  updateSelectedLanguage(currentLanguage);

  // Add click event to selected language
  selectedLanguage.addEventListener('click', toggleLanguageDropdown);

  // Add click events to language options
  const languageOptions = languageDropdown.querySelectorAll('.language-option');
  languageOptions.forEach(option => {
    option.addEventListener('click', function() {
      const languageCode = this.getAttribute('data-value');
      selectLanguage(languageCode);
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(event) {
    if (!languageSelector.contains(event.target)) {
      closeLanguageDropdown();
    }
  });
}

function toggleLanguageDropdown() {
  if (languageSelector.classList.contains('open')) {
    closeLanguageDropdown();
  } else {
    openLanguageDropdown();
  }
}

function openLanguageDropdown() {
  languageSelector.classList.add('open');
  languageDropdown.style.display = 'block';
}

function closeLanguageDropdown() {
  languageSelector.classList.remove('open');
  languageDropdown.style.display = 'none';
}

function selectLanguage(languageCode) {
  if (languageConfig[languageCode]) {
    currentLanguage = languageCode;
    updateSelectedLanguage(languageCode);
    updateLanguageOptions(languageCode);
    closeLanguageDropdown();
    
    // Update recording status text based on language
    updateRecordingStatusText();
    
    console.log(`Language changed to: ${languageConfig[languageCode].name}`);
  }
}

function updateSelectedLanguage(languageCode) {
  const config = languageConfig[languageCode];
  if (config && selectedLanguage) {
    const flagElement = selectedLanguage.querySelector('.flag');
    const nameElement = selectedLanguage.querySelector('.language-name');
    
    if (flagElement) flagElement.textContent = config.flag;
    if (nameElement) nameElement.textContent = config.name;
  }
}

function updateLanguageOptions(selectedLanguageCode) {
  const languageOptions = languageDropdown.querySelectorAll('.language-option');
  languageOptions.forEach(option => {
    const languageCode = option.getAttribute('data-value');
    if (languageCode === selectedLanguageCode) {
      option.classList.add('selected');
    } else {
      option.classList.remove('selected');
    }
  });
}

function updateRecordingStatusText() {
  const statusText = recordingStatus.querySelector('.status-text');
  if (statusText) {
    const statusMessages = {
      'en': 'Ready to listen',
      'ha': 'Shirye don sauraro',
      'tw': 'Ase sɛ wote',
      'ee': 'Kpe ɖe nàte ŋu',
      'ga': 'Kpe ɖe nàte ŋu',
      'dagbani': 'Shirya ni a wum'
    };
    statusText.textContent = statusMessages[currentLanguage] || statusMessages['en'];
  }
}