"""
Audio Analysis Module for AXIS AI
Features: 148-154
"""

import numpy as np
import librosa
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AudioAnalysisResult:
    """Result of audio analysis."""
    duration: float
    tempo: float
    beats: List[float]
    chroma: List[float]
    mfcc: List[float]
    spectral_features: Dict[str, float]
    energy_features: Dict[str, float]
    rhythm_features: Dict[str, float]

class AudioAnalyzer:
    """
    Advanced audio analysis for music and voice processing.
    Features: 148-154
    """
    
    def __init__(self):
        self.sample_rate = 22050
        
    async def analyze_audio(self, audio_path: str) -> AudioAnalysisResult:
        """Perform comprehensive audio analysis."""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Basic features
            duration = len(y) / sr
            
            # Tempo and beat tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1).tolist()
            
            # MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfcc, axis=1).tolist()
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            spectral_features = {
                'centroid_mean': float(np.mean(spectral_centroids)),
                'rolloff_mean': float(np.mean(spectral_rolloff)),
                'bandwidth_mean': float(np.mean(spectral_bandwidth))
            }
            
            # Energy features
            rms = librosa.feature.rms(y=y)[0]
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            
            energy_features = {
                'rms_mean': float(np.mean(rms)),
                'zcr_mean': float(np.mean(zcr)),
                'energy': float(np.sum(y**2))
            }
            
            # Rhythm features
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            
            rhythm_features = {
                'onset_density': len(onset_times) / duration,
                'tempo_stability': self._calculate_tempo_stability(y, sr)
            }
            
            return AudioAnalysisResult(
                duration=duration,
                tempo=float(tempo),
                beats=beats.tolist(),
                chroma=chroma_mean,
                mfcc=mfcc_mean,
                spectral_features=spectral_features,
                energy_features=energy_features,
                rhythm_features=rhythm_features
            )
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            raise
    
    def _calculate_tempo_stability(self, y: np.ndarray, sr: int) -> float:
        """Calculate how stable the tempo is throughout the audio."""
        try:
            # Split audio into segments and calculate tempo for each
            segment_length = sr * 10  # 10 second segments
            tempos = []
            
            for i in range(0, len(y), segment_length):
                segment = y[i:i+segment_length]
                if len(segment) > sr:  # At least 1 second
                    tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
                    tempos.append(tempo)
            
            if len(tempos) < 2:
                return 1.0
            
            # Calculate coefficient of variation (lower = more stable)
            tempo_std = np.std(tempos)
            tempo_mean = np.mean(tempos)
            
            if tempo_mean == 0:
                return 0.0
            
            cv = tempo_std / tempo_mean
            stability = max(0.0, 1.0 - cv)  # Invert so higher = more stable
            
            return float(stability)
            
        except Exception as e:
            logger.error(f"Tempo stability calculation failed: {e}")
            return 0.5  # Default middle value

def get_audio_analyzer() -> AudioAnalyzer:
    """Factory function to create audio analyzer."""
    return AudioAnalyzer() 