import os
import sys
import asyncio
import re # Import re for regex substitutions
from openai import OpenAI

class OpenAIService:
    """OpenAI implementation of speech-to-text service"""
    
    def __init__(self, client, use_post_processing=False):
        self.client = client
        self.use_post_processing = use_post_processing
        # Define German word replacements as a class attribute
        self.german_word_replacements = {
            "v-test": "Vitest",
            "v-tests": "Vitest",
            "package jason": "package.json",
            "achse": ".exe",
            "echse": ".exe",
            "gyra": "Jira",
            "effektor": "Refactor",
            "pulverquest": "Pull Request",
            "konsole locks": "console.log",
            "juju-id": "UUID",
            "loks": "Logs",
            "locken": "loggen",
            "commentline": "Command Line"
        }
    
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
                
                print(f"🎤 Calling OpenAI Whisper with params: {params}", file=sys.stderr)
                
                transcription = await loop.run_in_executor(
                    None,
                    lambda: self.client.audio.transcriptions.create(**params)
                )
                
                transcript = transcription.text
                # Log the full initial transcript
                print(f"📝 Initial transcription: '{transcript}'", file=sys.stderr)
                
                # Apply post-processing if enabled
                if self.use_post_processing and transcript:
                    print(f"⏳ Applying GPT-4 post-processing to improve quality... (language={language})", file=sys.stderr)
                    print(f"📊 DEBUG: Post-processing is enabled = {self.use_post_processing}", file=sys.stderr)
                    processed_transcript = await self.post_process_with_gpt4(transcript, language)
                    print(f"🏁 FINAL RESULT: '{processed_transcript}'", file=sys.stderr)
                    return processed_transcript
                else:
                    print(f"⚠️ No post-processing applied! use_post_processing={self.use_post_processing}", file=sys.stderr)
                
                return transcript
        except Exception as e:
            print(f"❌ OpenAI transcription error: {str(e)}", file=sys.stderr)
            raise Exception(f"OpenAI transcription error: {str(e)}")
    
    async def post_process_with_gpt4(self, transcript, language=None):
        """Post-process transcript with GPT-4 to improve quality"""
        try:
            loop = asyncio.get_event_loop()
            
            # Log language parameter
            print(f"🚩 DEBUG: post_process_with_gpt4 called with language='{language}'", file=sys.stderr)
            
            # Create a system prompt based on language
            system_prompt = self._get_system_prompt_for_language(language)
            
            print(f"🧠 Starting GPT-4 post-processing for transcript...", file=sys.stderr)
            print(f"Original transcript: '{transcript}'", file=sys.stderr)
            
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
            print(f"✅ GPT-4 post-processing complete", file=sys.stderr)
            print(f"🧠 Text after GPT-4: '{processed_text}'", file=sys.stderr)
            
            # Check if the GPT-4 processed text contains V-Test (debug)
            if re.search(r"v[-\s]tests?", processed_text, re.IGNORECASE):
                print(f"✓✓✓ DEBUG: Found 'V-Test' or variant in GPT-4 processed text!", file=sys.stderr)
            else:
                print(f"❌❌❌ DEBUG: 'V-Test' pattern NOT found in GPT-4 processed text!", file=sys.stderr)
            
            # Apply explicit German word replacements if language is German
            final_text = processed_text
            if language == "de":
                print(f"⚙️ Applying explicit German word replacements... (language confirmed as 'de')", file=sys.stderr)
                final_text = self._apply_german_word_replacements(processed_text)
                
                # Check if there was any difference
                if final_text != processed_text:
                    print(f"✓ Replacements applied successfully", file=sys.stderr)
                else:
                    print(f"⚠️ No replacements were applied", file=sys.stderr)
                    
                print(f"🔧 Text after explicit replacements: '{final_text}'", file=sys.stderr)
                
                # Final check for V-Test (debug)
                if re.search(r"v[-\s]tests?", final_text, re.IGNORECASE):
                    print(f"❌❌❌ ERROR: 'V-Test' pattern STILL in final text!", file=sys.stderr)
                else:
                    print(f"✓✓✓ SUCCESS: 'V-Test' pattern properly replaced in final text!", file=sys.stderr)
            else:
                print(f"⚠️ WARNING: Language is '{language}', not 'de'. German replacements NOT applied!", file=sys.stderr)
            
            # Log the full processed text
            print(f"Improved transcript: '{final_text}'", file=sys.stderr)
            return final_text # Return the text after explicit replacements
        except Exception as e:
            print(f"❌ Post-processing error: {str(e)}", file=sys.stderr)
            print(f"❓ Error occurred at: {e.__traceback__.tb_lineno}", file=sys.stderr)
            print("⚠️ Returning original transcript instead", file=sys.stderr)
            return transcript
    
    def _get_system_prompt_for_language(self, language):
        """Get appropriate system prompt based on language"""
        base_prompt = """
You are a helpful assistant specializing in improving speech-to-text transcriptions. 
Your task is to improve the transcribed text by:
1. Fixing any grammatical errors
2. Adding appropriate punctuation
3. Correcting obvious word misrecognitions (where possible)
4. Maintaining the original meaning and intent
5. Preserving technical terms and proper nouns

Only return the corrected transcript without any explanations or additional text.
"""
        
        # Specific German word replacements dictionary is now a class attribute (self.german_word_replacements)
        # We still include instructions in the prompt as a hint for GPT-4
        # german_word_replacements = { ... } # Removed from here

        # Language-specific additions
        if language == "de":
            # Construct the specific correction instructions as hints for GPT-4
            correction_instructions = "\\nAdditionally, try to correct the following common misrecognitions in German technical context (case-insensitive matching):\\n"
            # Use the class attribute here
            for wrong, correct in self.german_word_replacements.items(): 
                # Make case-insensitivity explicit in the instruction to GPT-4
                correction_instructions += f"- If you see '{wrong}' (case-insensitive), try to correct it to '{correct}'.\\\\n"

            return base_prompt + "\\nFor German text, pay special attention to:\\n- Correct use of German grammatical cases\\n- Proper noun capitalization\\n- Compound word formation\\n- Umlauts (ä, ö, ü) and ß\\n" + correction_instructions
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
    
    def _apply_german_word_replacements(self, text):
        """Apply explicit, case-insensitive word replacements for German text."""
        if not text:
            return text
        
        print(f"🔍 DEBUG: Starting word replacements on text: '{text}'", file=sys.stderr)
        corrected_text = text
        replacement_occurred = False
        
        # Use the class attribute for general replacements
        for wrong, correct in self.german_word_replacements.items():
            # Escape any regex special characters in the 'wrong' string
            escaped_wrong = re.escape(wrong)
            
            # Create patterns with flexibility
            patterns_to_try = []
            
            # Standard pattern with word boundaries
            patterns_to_try.append(r'\b' + escaped_wrong + r'\b')
            
            # Add plural form if not already ending with 's'
            if not wrong.endswith('s'):
                patterns_to_try.append(r'\b' + escaped_wrong + r's\b')
            
            # Add flexibility for hyphens if present
            if '-' in wrong:
                # Replace hyphen with optional hyphen or space pattern
                flexible_pattern = escaped_wrong.replace('\\-', '[-\\s]')
                patterns_to_try.append(r'\b' + flexible_pattern + r'\b')
                # And plural version if needed
                if not wrong.endswith('s'):
                    patterns_to_try.append(r'\b' + flexible_pattern + r's\b')
            
            # Try each pattern
            for pattern in patterns_to_try:
                try:
                    # Check if this pattern has any matches
                    if re.search(pattern, corrected_text, flags=re.IGNORECASE):
                        # Store before replacement for comparison
                        before_replacement = corrected_text
                        
                        # Apply the replacement
                        corrected_text = re.sub(pattern, correct, corrected_text, flags=re.IGNORECASE)
                        
                        # Debug: show exactly what changed, but only if something actually changed
                        if before_replacement != corrected_text:
                            print(f"✓ Replaced: '{wrong}' → '{correct}'", file=sys.stderr)
                            replacement_occurred = True
                except re.error as e:
                    print(f"⚠️ Regex error for pattern '{wrong}': {e}", file=sys.stderr)
        
        # Log summary of replacements
        if replacement_occurred:
            print(f"✅ Completed word replacements", file=sys.stderr)
        else:
            print(f"ℹ️ No word replacements needed", file=sys.stderr)
            
        return corrected_text
    
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