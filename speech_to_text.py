import os
import asyncio
import sys
from abc import ABC, abstractmethod
from deepgram import Deepgram
from deepgram.errors import DeepgramSetupError
from openai import OpenAI


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


class DeepgramService(SpeechToTextService):
    """DeepGram implementation of speech-to-text service"""
    
    def __init__(self, client):
        self.client = client
    
    @classmethod
    def initialize(cls, api_key):
        """Initialize DeepGram client with API key"""
        try:
            client = Deepgram(api_key)
            return cls(client)
        except DeepgramSetupError:
            raise ValueError("Invalid Deepgram API Key")
        except Exception as e:
            print(f"Deepgram init error: {str(e)}", file=sys.stderr)
            raise Exception(f"Failed to initialize Deepgram: {str(e)}")
    
    async def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio file using DeepGram"""
        try:
            with open(audio_file, 'rb') as audio:
                source = {'buffer': audio, 'mimetype': 'audio/wav'}
                options = {
                    'punctuate': True,
                    'model': 'nova-2',
                }
                
                # Only set language if it's specified and not auto-detect
                if language and language != "auto":
                    options['language'] = language
                    
                response = await self.client.transcription.prerecorded(source, options)
                return response['results']['channels'][0]['alternatives'][0]['transcript']
        except Exception as e:
            print(f"Deepgram transcription error: {str(e)}", file=sys.stderr)
            raise Exception(f"Deepgram transcription error: {str(e)}")


class OpenAIService(SpeechToTextService):
    """OpenAI implementation of speech-to-text service"""
    
    def __init__(self, client):
        self.client = client
    
    @classmethod
    def initialize(cls, api_key):
        """Initialize OpenAI client with API key"""
        try:
            client = OpenAI(api_key=api_key)
            return cls(client)
        except Exception as e:
            print(f"OpenAI init error: {str(e)}", file=sys.stderr)
            raise Exception(f"Failed to initialize OpenAI: {str(e)}")
    
    async def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio file using OpenAI"""
        try:
            with open(audio_file, 'rb') as audio:
                # Use asyncio to run the synchronous API call in a thread pool
                loop = asyncio.get_event_loop()
                
                # Prepare parameters for the API call
                params = {
                    "model": "whisper-1",
                    "file": audio,
                }
                
                # OpenAI doesn't support 'auto' - we just omit the language parameter
                # for auto-detection. For other languages, ensure we're sending valid codes
                if language and language != "auto":
                    # Make sure we're using a valid ISO-639-1 code
                    params["language"] = language
                
                print(f"Calling OpenAI with params: {params}", file=sys.stderr)
                
                transcription = await loop.run_in_executor(
                    None,
                    lambda: self.client.audio.transcriptions.create(**params)
                )
                return transcription.text
        except Exception as e:
            print(f"OpenAI transcription error: {str(e)}", file=sys.stderr)
            raise Exception(f"OpenAI transcription error: {str(e)}")


def create_service(service_type, api_key):
    """Factory function to create the appropriate speech-to-text service"""
    if service_type == "deepgram":
        return DeepgramService.initialize(api_key)
    elif service_type == "openai":
        return OpenAIService.initialize(api_key)
    else:
        raise ValueError(f"Unsupported service type: {service_type}") 