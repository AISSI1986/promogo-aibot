this.apiEndpoints = {
  stt: process.env.REACT_APP_STT_URL || "http://localhost:5006/transcribe",
  rasa: process.env.REACT_APP_RASA_URL || "http://localhost:5005/webhooks/rest/webhook",
  tts: process.env.REACT_APP_TTS_URL || "http://localhost:5007/synthesize/",
}

// Chatbot communication
async function sendMessage(message) {
  const response = await fetch(`${this.apiEndpoints.rasa}/webhooks/rest/webhook`, {
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
  
  const response = await fetch(`${this.apiEndpoints.stt}/transcribe`, {
    method: 'POST',
    body: formData
  });
  return response.json();
}

// Text-to-Speech
async function convertTextToSpeech(text) {
  const response = await fetch(`${this.apiEndpoints.tts}/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  return response.blob();
}