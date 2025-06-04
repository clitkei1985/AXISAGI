"""
Speech Processing Module for AXIS AI
Features: 138-141, 145
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import speech_recognition as sr
import whisper
import numpy as np
from core.config import settings
from .voice_engine import VoiceEngine

logger = logging.getLogger(__name__)

@dataclass
class SpeechResult:
    """Result of speech processing."""
    text: str
    confidence: float
    language: str
    processing_time: float

class SpeechProcessor:
    """
    Advanced speech processing with multiple recognition engines.
    Features: 138-141, 145
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize Whisper if available
        try:
            self.whisper_model = whisper.load_model(settings.audio.whisper_model)
            logger.info(f"Loaded Whisper model: {settings.audio.whisper_model}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
    
    async def process_speech(
        self, 
        audio_data: bytes, 
        language: str = "auto",
        use_whisper: bool = True
    ) -> SpeechResult:
        """Process speech audio and return transcription."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if use_whisper and self.whisper_model:
                text, confidence, detected_language = await self._whisper_process(audio_data, language)
            else:
                text, confidence, detected_language = await self._google_process(audio_data)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return SpeechResult(
                text=text,
                confidence=confidence,
                language=detected_language,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Speech processing failed: {e}")
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return SpeechResult(
                text="",
                confidence=0.0,
                language="unknown",
                processing_time=processing_time
            )
    
    async def _whisper_process(self, audio_data: bytes, language: str) -> Tuple[str, float, str]:
        """Process speech using Whisper."""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_array,
                language=language if language != "auto" else None
            )
            
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            # Estimate confidence from log probability
            confidence = min(0.95, max(0.1, 1.0 - abs(result.get("avg_logprob", -1.0))))
            
            return text, confidence, detected_language
            
        except Exception as e:
            logger.error(f"Whisper processing failed: {e}")
            raise
    
    async def _google_process(self, audio_data: bytes) -> Tuple[str, float, str]:
        """Process speech using Google Speech Recognition."""
        try:
            audio = sr.AudioData(audio_data, settings.audio.sample_rate, 2)
            text = self.recognizer.recognize_google(audio, show_all=False)
            return text, 0.8, "en"  # Assume English and moderate confidence
            
        except sr.UnknownValueError:
            return "", 0.0, "unknown"
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            raise
    
    async def transcribe_file(self, file_path: str, language: str = "auto") -> SpeechResult:
        """Transcribe audio from file."""
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            return await self.process_speech(audio_data, language)
            
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            raise
    
    async def real_time_transcribe(self, duration: int = 5) -> SpeechResult:
        """Real-time transcription from microphone."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info(f"Listening for {duration} seconds...")
                
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=duration)
                audio_data = audio.get_wav_data()
                
                return await self.process_speech(audio_data)
                
        except Exception as e:
            logger.error(f"Real-time transcription failed: {e}")
            raise

def get_speech_processor() -> SpeechProcessor:
    """Factory function to create speech processor."""
    return SpeechProcessor() 