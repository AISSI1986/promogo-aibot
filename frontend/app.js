// Configuration
const apiEndpoints = {
  stt: "https://promogo-stt.onrender.com/transcribe",
  rasa: "https://promogo-rasa.onrender.com/webhooks/rest/webhook",
  tts: "https://promogo-tts.onrender.com/synthesize/"
};

// Global variables
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let currentLanguage = 'en';

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

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
  console.log('Promogo app initialized');
  
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
function addMessage(sender, text, isAudio = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  if (isAudio) {
    messageDiv.innerHTML = `
      <div class="message-content">
        <audio controls>
          <source src="${text}" type="audio/wav">
          Your browser does not support the audio element.
        </audio>
      </div>
    `;
  } else {
    messageDiv.innerHTML = `
      <div class="message-content">
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
  if (!message) return;
  
  // Add user message
  addMessage('user', message);
  textInput.value = '';
  
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
    
    // Add bot response
    if (data && data.length > 0) {
      data.forEach(msg => {
        addMessage('bot', msg.text);
      });
    } else {
      addMessage('bot', 'Sorry, I didn\'t understand that. Can you try again?');
    }
    
  } catch (error) {
    console.error('Error sending message:', error);
    typingDiv.remove();
    addMessage('bot', 'Sorry, there was an error connecting to the chatbot. Please try again.');
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
    addMessage('bot', 'Sorry, I couldn\'t access your microphone. Please check your permissions.');
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

// Process audio
async function processAudio(audioBlob) {
  try {
    // Convert speech to text
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('language', currentLanguage);
    
    const sttResponse = await fetch(apiEndpoints.stt, {
      method: 'POST',
      body: formData
    });
    
    if (!sttResponse.ok) {
      throw new Error(`STT API error: ${sttResponse.status}`);
    }
    
    const sttData = await sttResponse.json();
    const transcribedText = sttData.text || 'Could not transcribe audio';
    
    // Add transcribed message
    addMessage('user', `🎤 ${transcribedText}`);
    
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
    
    // Add bot response
    if (rasaData && rasaData.length > 0) {
      rasaData.forEach(msg => {
        addMessage('bot', msg.text);
      });
    } else {
      addMessage('bot', 'Sorry, I didn\'t understand that. Can you try again?');
    }
    
    recordingStatus.textContent = 'Ready to listen';
    
  } catch (error) {
    console.error('Error processing audio:', error);
    recordingStatus.textContent = 'Error processing audio';
    addMessage('bot', `Sorry, there was an error processing your audio: ${error.message}. Please try again.`);
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
  
  const response = await fetch(apiEndpoints.stt, {
    method: 'POST',
    body: formData
  });
  return response.json();
}

async function convertTextToSpeech(text) {
  const response = await fetch(apiEndpoints.tts, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  return response.blob();
}