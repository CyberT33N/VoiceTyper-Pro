import os
import sys
import asyncio
from deepgram import Deepgram
from deepgram.errors import DeepgramSetupError

class DeepgramService:
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
                
                # Modified options for better language support
                options = {
                    'punctuate': True,
                    'model': 'nova-2',  # Using nova-2 for better language support
                }
                
                # Language mapping for Deepgram
                language_mapping = {
                    'en': 'en',
                    'de': 'de',
                    'fr': 'fr',
                    'es': 'es',
                    'it': 'it',
                    'ja': 'ja',
                    'ko': 'ko',
                    'pt': 'pt',
                    'ru': 'ru',
                    'nl': 'nl',
                    'auto': None  # auto will not set a language parameter
                }
                
                # Only set language if it's specified and not auto-detect
                if language and language != "auto" and language in language_mapping:
                    mapped_language = language_mapping.get(language)
                    if mapped_language:
                        options['language'] = mapped_language
                
                print(f"Calling Deepgram with options: {options}", file=sys.stderr)
                    
                response = await self.client.transcription.prerecorded(source, options)
                
                # Check if response has the expected structure
                if not response:
                    print(f"Empty response from Deepgram", file=sys.stderr)
                    raise Exception("Empty response from Deepgram")
                
                if 'results' not in response:
                    print(f"Invalid response structure: {response}", file=sys.stderr)
                    raise Exception(f"Invalid response from Deepgram: missing 'results'")
                
                # Accessing the transcript safely
                if 'channels' not in response['results'] or not response['results']['channels']:
                    print(f"No channels in response: {response}", file=sys.stderr)
                    raise Exception("No channels in Deepgram response")
                
                channel = response['results']['channels'][0]
                if 'alternatives' not in channel or not channel['alternatives']:
                    print(f"No alternatives in response: {response}", file=sys.stderr)
                    raise Exception("No alternatives in Deepgram response")
                
                if 'transcript' not in channel['alternatives'][0]:
                    print(f"No transcript in response: {response}", file=sys.stderr)
                    raise Exception("No transcript in Deepgram response")
                
                transcript = channel['alternatives'][0]['transcript']
                if not transcript:
                    return "No speech detected"
                
                return transcript
                
        except Exception as e:
            print(f"Deepgram transcription error: {str(e)}", file=sys.stderr)
            raise Exception(f"Deepgram transcription error: {str(e)}")
    
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
            "nl": "Nederlands",
            "ja": "日本語",
            "ko": "한국어",
            "pt": "Português",
            "ru": "Русский",
        } 