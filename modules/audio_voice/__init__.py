"""
Audio and Voice Processing Module for AXIS AI
Features: 138-154, 199
"""

from .voice_engine import VoiceEngine, get_voice_engine
from .audio_analyzer import AudioAnalyzer, get_audio_analyzer
from .speech_processor import SpeechProcessor, get_speech_processor

# Create a unified processor that combines all audio capabilities
class AudioProcessor:
    """Unified audio processor combining all audio capabilities."""
    
    def __init__(self):
        self.voice_engine = get_voice_engine()
        self.audio_analyzer = get_audio_analyzer() 
        self.speech_processor = get_speech_processor()
    
    async def process_audio_file(self, file_path: str):
        """Process an audio file with all available capabilities."""
        # Analyze audio structure
        analysis = await self.audio_analyzer.analyze_audio(file_path)
        
        # Transcribe speech if present
        transcription = await self.speech_processor.transcribe_file(file_path)
        
        return {
            'analysis': analysis,
            'transcription': transcription
        }

def get_audio_processor() -> AudioProcessor:
    """Factory function to create unified audio processor."""
    return AudioProcessor()

__all__ = [
    'VoiceEngine', 'get_voice_engine',
    'AudioAnalyzer', 'get_audio_analyzer',
    'SpeechProcessor', 'get_speech_processor',
    'AudioProcessor', 'get_audio_processor'
]
