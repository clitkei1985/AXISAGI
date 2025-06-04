import os
import numpy as np
import soundfile as sf
import librosa
import whisper
import pyaudio
import wave
from typing import Dict, List, Optional, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.whisper_model = whisper.load_model(settings.audio.whisper_model)
        self.sample_rate = settings.audio.sample_rate
        self.max_audio_length = settings.audio.max_audio_length
        self.voice_latency_threshold = settings.audio.voice_latency_threshold
        
        # Initialize PyAudio for real-time recording
        self.audio = pyaudio.PyAudio()
        
    def __del__(self):
        """Cleanup PyAudio on deletion."""
        if hasattr(self, 'audio'):
            self.audio.terminate()

    async def transcribe_file(
        self,
        file: BinaryIO,
        language: Optional[str] = None
    ) -> Dict:
        """Transcribe audio file using Whisper."""
        try:
            # Save temporary file
            temp_path = Path("uploads/audio/temp.wav")
            with open(temp_path, "wb") as f:
                f.write(file.read())
            
            # Load and preprocess audio
            audio = whisper.load_audio(str(temp_path))
            
            # Check duration
            if len(audio) / self.sample_rate > self.max_audio_length:
                raise ValueError(f"Audio length exceeds maximum of {self.max_audio_length} seconds")
            
            # Transcribe
            result = self.whisper_model.transcribe(
                audio,
                language=language,
                fp16=False
            )
            
            # Cleanup
            os.remove(temp_path)
            
            return {
                "text": result["text"],
                "segments": result["segments"],
                "language": result["language"]
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    async def start_recording(
        self,
        output_path: str,
        max_duration: int = 300  # 5 minutes
    ) -> None:
        """Start recording audio to file."""
        frames = []
        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        
        try:
            for _ in range(0, int(self.sample_rate / 1024 * max_duration)):
                data = stream.read(1024)
                frames.append(data)
                
        finally:
            stream.stop_stream()
            stream.close()
            
            # Save to file
            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paFloat32))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))

    async def process_audio_file(
        self,
        file_path: str,
        normalize: bool = True,
        remove_noise: bool = True
    ) -> str:
        """Process audio file with optional normalization and noise reduction."""
        try:
            # Load audio
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            
            if normalize:
                # Normalize audio
                audio = librosa.util.normalize(audio)
            
            if remove_noise:
                # Simple noise reduction using spectral gating
                S = librosa.stft(audio)
                mag = np.abs(S)
                phase = np.angle(S)
                
                # Estimate noise floor
                noise_floor = np.mean(np.sort(mag.flatten())[:int(len(mag.flatten())*0.1)])
                
                # Apply spectral gating
                mask = (mag > noise_floor * 2)
                mag_cleaned = mag * mask
                
                # Reconstruct signal
                S_cleaned = mag_cleaned * np.exp(1j * phase)
                audio = librosa.istft(S_cleaned)
            
            # Save processed file
            output_path = file_path.replace('.', '_processed.')
            sf.write(output_path, audio, self.sample_rate)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            raise

    async def detect_voice_activity(
        self,
        audio_data: np.ndarray,
        threshold: float = 0.01
    ) -> bool:
        """Detect voice activity in audio segment."""
        energy = librosa.feature.rms(y=audio_data)[0]
        return np.mean(energy) > threshold

    async def extract_audio_features(
        self,
        file_path: str
    ) -> Dict:
        """Extract audio features for analysis."""
        try:
            # Load audio
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            
            # Extract features
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)
            
            return {
                "mfcc": mfcc.mean(axis=1).tolist(),
                "chroma": chroma.mean(axis=1).tolist(),
                "spectral_centroid": float(spectral_centroid.mean()),
                "spectral_rolloff": float(spectral_rolloff.mean()),
                "zero_crossing_rate": float(zero_crossing_rate.mean()),
                "duration": float(len(audio) / sr)
            }
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            raise

# Singleton instance
_audio_processor = None

def get_audio_processor() -> AudioProcessor:
    """Get or create the AudioProcessor singleton instance."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor 