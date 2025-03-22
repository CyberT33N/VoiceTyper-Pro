import os
import sys
import asyncio
from openai import OpenAI

class OpenAIService:
    """OpenAI implementation of speech-to-text service"""
    
    def __init__(self, client, use_post_processing=False):
        self.client = client
        self.use_post_processing = use_post_processing
    
    @classmethod
    def initialize(cls, api_key, use_post_processing=False):
        """Initialize OpenAI client with API key"""
        try:
            client = OpenAI(api_key=api_key)
            return cls(client, use_post_processing)
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
                
                transcript = transcription.text
                
                # Apply post-processing if enabled
                if self.use_post_processing and transcript:
                    print("Applying GPT-4 post-processing...", file=sys.stderr)
                    processed_transcript = await self.post_process_with_gpt4(transcript, language)
                    return processed_transcript
                
                return transcript
        except Exception as e:
            print(f"OpenAI transcription error: {str(e)}", file=sys.stderr)
            raise Exception(f"OpenAI transcription error: {str(e)}")
    
    async def post_process_with_gpt4(self, transcript, language=None):
        """Post-process transcript with GPT-4 to improve quality"""
        try:
            loop = asyncio.get_event_loop()
            
            # Create a system prompt based on language
            system_prompt = self._get_system_prompt_for_language(language)
            
            print(f"Using system prompt: {system_prompt[:50]}...", file=sys.stderr)
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": transcript
                        }
                    ]
                )
            )
            
            processed_text = response.choices[0].message.content
            return processed_text
        except Exception as e:
            print(f"Post-processing error: {str(e)}", file=sys.stderr)
            print("Returning original transcript instead", file=sys.stderr)
            return transcript
    
    def _get_system_prompt_for_language(self, language):
        """Get appropriate system prompt based on language"""
        base_prompt = """
You are a helpful assistant specializing in improving speech-to-text transcriptions. 
Your task is to improve the transcribed text by:
1. Fixing any grammatical errors
2. Adding appropriate punctuation
3. Correcting obvious word misrecognitions
4. Maintaining the original meaning and intent
5. Preserving technical terms and proper nouns

Only return the corrected transcript without any explanations or additional text.
"""
        
        # Language-specific additions
        if language == "de":
            return base_prompt + """
For German text, pay special attention to:
- Correct use of German grammatical cases
- Proper noun capitalization
- Compound word formation
- Umlauts (ä, ö, ü) and ß
"""
        elif language == "fr":
            return base_prompt + """
For French text, pay special attention to:
- Gendered agreements
- Accents and diacritical marks
- Proper use of liaisons in writing
"""
        elif language == "es":
            return base_prompt + """
For Spanish text, pay special attention to:
- Accents and diacritical marks
- Gendered agreements
- Subjunctive verb forms
"""
        
        return base_prompt
    
    @staticmethod
    def get_supported_languages():
        """Return a dictionary of supported languages for UI selection"""
        return {
            "auto": "Auto-detect (Ignore language parameter)",
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