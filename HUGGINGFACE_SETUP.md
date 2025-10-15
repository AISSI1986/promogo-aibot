# Hugging Face API Setup Guide

## Getting Your Hugging Face Token

### Step 1: Create Hugging Face Account
1. Go to [huggingface.co](https://huggingface.co)
2. Click "Sign Up" and create your account
3. Verify your email address

### Step 2: Get Your API Token
1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Give it a name (e.g., "Promogo API Token")
4. Select "Read" permissions
5. Click "Generate a token"
6. Copy the token (it starts with `hf_...`)

### Step 3: Update Your Render Configuration

#### Option A: Update render.yaml (Recommended)
Replace `your_huggingface_token_here` in `render.yaml` with your actual token:

```yaml
envVars:
  - key: HUGGINGFACE_TOKEN
    value: hf_your_actual_token_here
```

#### Option B: Set in Render Dashboard
1. Go to your Render dashboard
2. Select your STT service
3. Go to "Environment" tab
4. Add new environment variable:
   - Key: `HUGGINGFACE_TOKEN`
   - Value: `hf_your_actual_token_here`
5. Repeat for TTS service

### Step 4: Deploy
1. Commit and push your changes:
   ```bash
   git add .
   git commit -m "Add Hugging Face API integration"
   git push origin kekeli
   ```

2. Redeploy your Blueprint in Render

## Supported Languages

### Text-to-Speech (TTS)
- English (en)
- French (fr)
- Spanish (es)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Hausa (ha)
- Ewe (ee)
- Twi (tw)

### Speech-to-Text (STT)
- All languages above
- Plus multilingual models for automatic language detection

## API Usage Limits

### Free Tier
- 1,000 requests per month
- Rate limit: 1 request per second
- Perfect for testing and small applications

### Pro Tier (if needed)
- $9/month
- 10,000 requests per month
- Higher rate limits
- Priority support

## Testing Your Setup

### Test TTS Service
```bash
curl -X POST "https://promogo-tts.onrender.com/synthesize/" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test", "language": "en"}'
```

### Test STT Service
```bash
curl -X POST "https://promogo-stt.onrender.com/transcribe" \
  -F "audio=@test_audio.wav" \
  -F "language=en"
```

## Troubleshooting

### Common Issues

1. **"Model is loading" error**
   - Wait 30-60 seconds and try again
   - Models need to be loaded on first use

2. **"API token not configured" error**
   - Check that HUGGINGFACE_TOKEN is set correctly
   - Verify the token starts with `hf_`

3. **Rate limit exceeded**
   - You've hit the free tier limit
   - Wait until next month or upgrade to Pro

4. **Audio file not found**
   - Check that audio files are being saved correctly
   - Verify file permissions

### Getting Help
- [Hugging Face Documentation](https://huggingface.co/docs/api-inference)
- [Hugging Face Community](https://huggingface.co/community)
- [Render Support](https://render.com/docs)

## Security Notes

- Never commit your Hugging Face token to Git
- Use environment variables for all sensitive data
- Rotate your tokens regularly
- Monitor your API usage
