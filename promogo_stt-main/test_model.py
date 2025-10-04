# Load model directly
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

processor = AutoProcessor.from_pretrained("asr-africa/wav2vec2-xls-r-ewe-100-hours")
model = AutoModelForSpeechSeq2Seq.from_pretrained("asr-africa/wav2vec2-xls-r-ewe-100-hours")
