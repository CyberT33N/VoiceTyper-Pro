import os
from abc import ABC, abstractmethod
from deepgram_service import DeepgramService
from openai_service import OpenAIService


class SpeechToTextService(ABC):
    """Base abstract class for speech-to-text services"""
    
    @abstractmethod
    async def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio file to text"""
        pass
    
    @classmethod
    @abstractmethod
    def initialize(cls, api_key):
        """Initialize service with API key"""
        pass
    
    @staticmethod
    def get_supported_languages():
        """Return a dictionary of supported languages for UI selection"""
        return {
            "auto": "Auto-detect",
            "en": "English",
            "de": "Deutsch",
            "fr": "Français",
            "es": "Español",
            "it": "Italiano",
            "ja": "日本語",
            "zh": "中文",
            "ru": "Русский",
            "pt": "Português",
            "ko": "한국어",
            "ar": "العربية",
            "nl": "Nederlands",
            "sv": "Svenska",
            "pl": "Polski"
        }


def create_service(service_type, api_key, post_processing=False):
    """Factory function to create the appropriate speech-to-text service"""
    if service_type == "deepgram":
        return DeepgramService.initialize(api_key)
    elif service_type == "openai":
        return OpenAIService.initialize(api_key, post_processing)
    else:
        raise ValueError(f"Unsupported service type: {service_type}") 