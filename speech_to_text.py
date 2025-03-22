import os
import asyncio
from abc import ABC, abstractmethod
from deepgram import Deepgram
from deepgram.errors import DeepgramSetupError
from openai import OpenAI


class SpeechToTextService(ABC):
    """Base abstract class for speech-to-text services"""
    
    @abstractmethod
    async def transcribe_audio(self, audio_file):
        """Transcribe audio file to text"""
        pass
    
    @classmethod
    @abstractmethod
    def initialize(cls, api_key):
        """Initialize service with API key"""
        pass


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
            raise Exception(f"Failed to initialize Deepgram: {str(e)}")
    
    async def transcribe_audio(self, audio_file, language='en'):
        """Transcribe audio file using DeepGram"""
        with open(audio_file, 'rb') as audio:
            source = {'buffer': audio, 'mimetype': 'audio/wav'}
            options = {
                'punctuate': True,
                'language': language,
                'model': 'nova-2',
            }
            response = await self.client.transcription.prerecorded(source, options)
            return response['results']['channels'][0]['alternatives'][0]['transcript']


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
            raise Exception(f"Failed to initialize OpenAI: {str(e)}")
    
    async def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio file using OpenAI"""
        try:
            with open(audio_file, 'rb') as audio:
                # Use asyncio to run the synchronous API call in a thread pool
                loop = asyncio.get_event_loop()
                transcription = await loop.run_in_executor(
                    None,
                    lambda: self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language=language
                    )
                )
                return transcription.text
        except Exception as e:
            raise Exception(f"OpenAI transcription error: {str(e)}")


def create_service(service_type, api_key):
    """Factory function to create the appropriate speech-to-text service"""
    if service_type == "deepgram":
        return DeepgramService.initialize(api_key)
    elif service_type == "openai":
        return OpenAIService.initialize(api_key)
    else:
        raise ValueError(f"Unsupported service type: {service_type}") 