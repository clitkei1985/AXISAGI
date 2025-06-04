"""
Voice Engine with Real-time Processing and Emotion Detection
Features: 138-141, 146, 147, 199
"""

import asyncio
import logging
import wave
import io
import threading
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import pyttsx3
import whisper
import librosa
from scipy import signal
import torch
import torch.nn.functional as F

from core.config import settings
from core.database import Session

logger = logging.getLogger(__name__)

class VoiceEngine:
    """
    Real-time voice processing engine with emotion detection and adaptive responses.
    Features: 138-141, 146, 147, 199
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Voice processing settings
        self.sample_rate = settings.audio.sample_rate
        self.latency_threshold = settings.audio.voice_latency_threshold
        self.max_audio_length = settings.audio.max_audio_length
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self._setup_tts()
        
        # Initialize Whisper for advanced speech recognition
        try:
            self.whisper_model = whisper.load_model(settings.audio.whisper_model, device=self.device)
            logger.info(f"Loaded Whisper model: {settings.audio.whisper_model} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
        
        # Real-time audio streaming
        self.is_listening = False
        self.is_speaking = False
        self.audio_buffer = []
        self.mic_stream = None
        self.speaker_stream = None
        
        # Voice characteristics and adaptation (Feature 199)
        self.voice_profiles = {}
        self.current_emotion = "neutral"
        self.adaptive_tone = True
        
        # Performance tracking
        self.stats = {
            'recognition_calls': 0,
            'synthesis_calls': 0,
            'total_latency': 0,
            'emotion_detections': 0,
            'voice_adaptations': 0
        }
        
        # Emotion detection setup
        self._setup_emotion_detection()
        
    def _setup_tts(self):
        """Configure text-to-speech engine."""
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
            
            # Set speech properties
            self.tts_engine.setProperty('rate', 180)  # Words per minute
            self.tts_engine.setProperty('volume', 0.8)
            
        except Exception as e:
            logger.error(f"TTS setup failed: {e}")
    
    def _setup_emotion_detection(self):
        """Setup emotion detection from voice features."""
        # Emotion feature extractors
        self.emotion_features = {
            'pitch_range': (80, 300),  # Hz
            'energy_threshold': 0.1,
            'zero_crossing_rate': 0.05,
            'spectral_centroid': 2000
        }
        
        # Emotion mappings for voice adaptation
        self.emotion_voice_mapping = {
            'happy': {'rate': 200, 'pitch': 1.2, 'volume': 0.9},
            'sad': {'rate': 150, 'pitch': 0.8, 'volume': 0.6},
            'angry': {'rate': 220, 'pitch': 1.1, 'volume': 1.0},
            'excited': {'rate': 240, 'pitch': 1.3, 'volume': 0.95},
            'calm': {'rate': 160, 'pitch': 0.9, 'volume': 0.7},
            'neutral': {'rate': 180, 'pitch': 1.0, 'volume': 0.8}
        }
    
    async def start_real_time_processing(self, callback=None) -> bool:
        """
        Start real-time voice processing with low latency.
        Feature: 147 (Voice latency < 300ms)
        """
        try:
            # Check audio devices
            devices = sd.query_devices()
            input_device = None
            output_device = None
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0 and input_device is None:
                    input_device = i
                if device['max_output_channels'] > 0 and output_device is None:
                    output_device = i
            
            if input_device is None or output_device is None:
                logger.error("No suitable audio devices found")
                return False
            
            # Configure low-latency streaming
            self.mic_stream = sd.InputStream(
                device=input_device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1024,  # Small buffer for low latency
                callback=self._audio_input_callback
            )
            
            self.speaker_stream = sd.OutputStream(
                device=output_device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1024
            )
            
            self.mic_stream.start()
            self.speaker_stream.start()
            self.is_listening = True
            
            logger.info("Real-time voice processing started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start real-time processing: {e}")
            return False
    
    def _audio_input_callback(self, indata, frames, time, status):
        """Low-latency audio input callback."""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        # Add to buffer for processing
        self.audio_buffer.extend(indata[:, 0])
        
        # Process when we have enough audio (≥1 second)
        if len(self.audio_buffer) >= self.sample_rate:
            audio_data = np.array(self.audio_buffer[:self.sample_rate])
            self.audio_buffer = self.audio_buffer[self.sample_rate:]
            
            # Process asynchronously to maintain low latency
            asyncio.create_task(self._process_audio_chunk(audio_data))
    
    async def _process_audio_chunk(self, audio_data: np.ndarray):
        """Process audio chunk for voice activity and emotion detection."""
        try:
            # Voice activity detection
            energy = np.sum(audio_data ** 2)
            if energy < self.emotion_features['energy_threshold']:
                return  # No significant audio
            
            # Extract emotion features
            emotion = await self._detect_emotion_from_audio(audio_data)
            
            if emotion != self.current_emotion:
                self.current_emotion = emotion
                if self.adaptive_tone:
                    await self._adapt_voice_tone(emotion)
                self.stats['emotion_detections'] += 1
                
        except Exception as e:
            logger.error(f"Audio chunk processing failed: {e}")
    
    async def _detect_emotion_from_audio(self, audio_data: np.ndarray) -> str:
        """
        Detect emotion from voice features.
        Feature: 146 (Emotion/tone detection in voice)
        """
        try:
            # Extract acoustic features
            features = {}
            
            # Pitch/fundamental frequency
            pitches, magnitudes = librosa.piptrack(
                y=audio_data, 
                sr=self.sample_rate,
                threshold=0.1
            )
            pitch_values = pitches[magnitudes > np.max(magnitudes) * 0.1]
            if len(pitch_values) > 0:
                features['pitch_mean'] = np.mean(pitch_values)
                features['pitch_std'] = np.std(pitch_values)
            else:
                features['pitch_mean'] = 0
                features['pitch_std'] = 0
            
            # Energy/loudness
            features['energy'] = np.sum(audio_data ** 2) / len(audio_data)
            
            # Zero crossing rate (voice quality indicator)
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            features['zcr_mean'] = np.mean(zcr)
            
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, 
                sr=self.sample_rate
            )[0]
            features['spectral_centroid_mean'] = np.mean(spectral_centroids)
            
            # Classify emotion based on features
            emotion = self._classify_emotion(features)
            return emotion
            
        except Exception as e:
            logger.error(f"Emotion detection failed: {e}")
            return "neutral"
    
    def _classify_emotion(self, features: Dict[str, float]) -> str:
        """Classify emotion based on extracted features."""
        # Simple rule-based classification (could be replaced with ML model)
        pitch_mean = features.get('pitch_mean', 0)
        energy = features.get('energy', 0)
        zcr_mean = features.get('zcr_mean', 0)
        spectral_centroid = features.get('spectral_centroid_mean', 0)
        
        # High energy, high pitch = excited/happy
        if energy > 0.05 and pitch_mean > 200:
            if zcr_mean > 0.1:
                return "excited"
            else:
                return "happy"
        
        # Low energy, low pitch = sad/calm
        elif energy < 0.02 and pitch_mean < 150:
            return "sad"
        
        # High energy, variable pitch = angry
        elif energy > 0.08 and features.get('pitch_std', 0) > 50:
            return "angry"
        
        # Moderate values = calm
        elif energy < 0.03 and pitch_mean < 180:
            return "calm"
        
        return "neutral"
    
    async def _adapt_voice_tone(self, emotion: str):
        """
        Adapt TTS voice tone based on detected emotion.
        Feature: 199 (Emotion-responsive voice tone adjustment)
        """
        if emotion not in self.emotion_voice_mapping:
            return
        
        try:
            voice_params = self.emotion_voice_mapping[emotion]
            
            # Adjust TTS parameters
            current_rate = self.tts_engine.getProperty('rate')
            current_volume = self.tts_engine.getProperty('volume')
            
            new_rate = int(current_rate * voice_params['rate'] / 180)
            new_volume = min(1.0, current_volume * voice_params['volume'] / 0.8)
            
            self.tts_engine.setProperty('rate', new_rate)
            self.tts_engine.setProperty('volume', new_volume)
            
            self.stats['voice_adaptations'] += 1
            logger.info(f"Adapted voice tone for emotion: {emotion}")
            
        except Exception as e:
            logger.error(f"Voice tone adaptation failed: {e}")
    
    async def recognize_speech(
        self, 
        audio_data: Optional[bytes] = None,
        use_whisper: bool = True,
        language: str = "en"
    ) -> Tuple[str, float]:
        """
        Convert speech to text with confidence scoring.
        Features: 138, 145
        """
        start_time = datetime.now()
        
        try:
            if audio_data is None:
                # Capture from microphone
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    logger.info("Listening for speech...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=5,
                        phrase_time_limit=self.max_audio_length
                    )
                    audio_data = audio.get_wav_data()
            
            # Use Whisper for high-quality recognition if available
            if use_whisper and self.whisper_model:
                text, confidence = await self._whisper_recognize(audio_data, language)
            else:
                # Fallback to Google Speech Recognition
                text, confidence = await self._google_recognize(audio_data)
            
            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.stats['total_latency'] += latency
            self.stats['recognition_calls'] += 1
            
            logger.info(f"Speech recognition: '{text}' (confidence: {confidence:.2f}, latency: {latency:.1f}ms)")
            
            # Check latency threshold
            if latency > self.latency_threshold:
                logger.warning(f"Speech recognition latency {latency:.1f}ms exceeds threshold {self.latency_threshold}ms")
            
            return text, confidence
            
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return "", 0.0
    
    async def _whisper_recognize(self, audio_data: bytes, language: str) -> Tuple[str, float]:
        """Use Whisper for speech recognition."""
        try:
            # Convert audio data to numpy array
            audio_io = io.BytesIO(audio_data)
            with wave.open(audio_io, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Resample to 16kHz if needed (Whisper requirement)
            if len(audio_array) > 0:
                if self.sample_rate != 16000:
                    audio_array = librosa.resample(
                        audio_array, 
                        orig_sr=self.sample_rate, 
                        target_sr=16000
                    )
                
                # Transcribe with Whisper
                result = self.whisper_model.transcribe(
                    audio_array,
                    language=language if language != "auto" else None,
                    fp16=self.device == 'cuda'
                )
                
                text = result["text"].strip()
                
                # Estimate confidence from Whisper's internal metrics
                # (Whisper doesn't provide direct confidence scores)
                confidence = min(0.95, max(0.1, 1.0 - (result.get("avg_logprob", -1.0) / -1.0)))
                
                return text, confidence
            
        except Exception as e:
            logger.error(f"Whisper recognition failed: {e}")
        
        return "", 0.0
    
    async def _google_recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Fallback Google Speech Recognition."""
        try:
            audio = sr.AudioData(audio_data, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio, show_all=False)
            return text, 0.8  # Assume moderate confidence
        except sr.UnknownValueError:
            return "", 0.0
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            return "", 0.0
    
    async def synthesize_speech(
        self, 
        text: str, 
        emotion: Optional[str] = None,
        save_file: Optional[str] = None,
        stream_output: bool = True
    ) -> Optional[bytes]:
        """
        Convert text to speech with emotional adaptation.
        Features: 139, 199
        """
        start_time = datetime.now()
        
        try:
            # Adapt voice for emotion if specified
            if emotion and emotion in self.emotion_voice_mapping:
                await self._adapt_voice_tone(emotion)
            
            # Generate speech
            if save_file:
                self.tts_engine.save_to_file(text, save_file)
                self.tts_engine.runAndWait()
                
                # Read generated file to return as bytes
                with open(save_file, 'rb') as f:
                    audio_data = f.read()
            else:
                # For streaming, we'll use a temporary file approach
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    self.tts_engine.save_to_file(text, tmp_file.name)
                    self.tts_engine.runAndWait()
                    
                    with open(tmp_file.name, 'rb') as f:
                        audio_data = f.read()
                    
                    # Clean up
                    import os
                    os.unlink(tmp_file.name)
            
            # Stream output if requested
            if stream_output and self.speaker_stream and self.speaker_stream.active:
                await self._stream_audio_output(audio_data)
            
            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.stats['synthesis_calls'] += 1
            
            logger.info(f"Speech synthesis completed: {len(text)} chars, {latency:.1f}ms")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return None
    
    async def _stream_audio_output(self, audio_data: bytes):
        """Stream audio output to speakers."""
        try:
            # Convert audio data to numpy array for streaming
            audio_io = io.BytesIO(audio_data)
            with wave.open(audio_io, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Stream to output
            chunk_size = 1024
            for i in range(0, len(audio_array), chunk_size):
                chunk = audio_array[i:i+chunk_size]
                if len(chunk) < chunk_size:
                    # Pad last chunk
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                self.speaker_stream.write(chunk.reshape(-1, 1))
                await asyncio.sleep(0.01)  # Small delay to prevent buffer overflow
                
        except Exception as e:
            logger.error(f"Audio streaming failed: {e}")
    
    def create_voice_profile(self, user_id: int, voice_characteristics: Dict[str, Any]):
        """
        Create personalized voice profile for user.
        Feature: 140 (Voice mic management)
        """
        self.voice_profiles[user_id] = {
            'characteristics': voice_characteristics,
            'created_at': datetime.now(),
            'adaptations': [],
            'preference_score': 0.5
        }
        
        logger.info(f"Created voice profile for user {user_id}")
    
    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice processing statistics."""
        avg_latency = (
            self.stats['total_latency'] / max(1, self.stats['recognition_calls'])
        )
        
        return {
            **self.stats,
            'average_latency_ms': avg_latency,
            'current_emotion': self.current_emotion,
            'adaptive_tone_enabled': self.adaptive_tone,
            'is_listening': self.is_listening,
            'is_speaking': self.is_speaking,
            'voice_profiles_count': len(self.voice_profiles),
            'whisper_available': self.whisper_model is not None,
            'audio_device_status': {
                'mic_active': self.mic_stream.active if self.mic_stream else False,
                'speaker_active': self.speaker_stream.active if self.speaker_stream else False
            }
        }
    
    async def stop_real_time_processing(self):
        """Stop real-time voice processing."""
        try:
            self.is_listening = False
            
            if self.mic_stream:
                self.mic_stream.stop()
                self.mic_stream.close()
            
            if self.speaker_stream:
                self.speaker_stream.stop()
                self.speaker_stream.close()
            
            logger.info("Real-time voice processing stopped")
            
        except Exception as e:
            logger.error(f"Error stopping voice processing: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            if hasattr(self, 'tts_engine'):
                self.tts_engine.stop()
        except:
            pass

def get_voice_engine(db: Session) -> VoiceEngine:
    """Factory function to create voice engine."""
    return VoiceEngine(db) 