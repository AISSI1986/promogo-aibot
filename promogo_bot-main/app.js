// In your frontend app.js
const RASA_URL = process.env.REACT_APP_RASA_URL || 'http://localhost:5005';
const STT_URL = process.env.REACT_APP_STT_URL || 'http://localhost:5006';
const TTS_URL = process.env.REACT_APP_TTS_URL || 'http://localhost:5007';

// Chatbot communication
async function sendMessage(message) {
  const response = await fetch(`${RASA_URL}/webhooks/rest/webhook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender: 'user',
      message: { text: message }
    })
  });
  return response.json();
}

// Speech-to-Text
async function convertSpeechToText(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  
  const response = await fetch(`${STT_URL}/transcribe`, {
    method: 'POST',
    body: formData
  });
  return response.json();
}

// Text-to-Speech
async function convertTextToSpeech(text) {
  const response = await fetch(`${TTS_URL}/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  return response.blob();
}