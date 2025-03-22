# VoiceTyper Pro

A graphical interface for voice-to-text transcription using Python. This application allows you to convert speech to text in real-time and automatically types the transcribed text at your cursor position.

Alternative to Mac Whisper, Voice Access, and other voice typing tools.

![VoiceTyper Pro](https://github.com/perrypixel/VoiceTyper-Pro/raw/main/assets/app_icon.ico)

## 🔥 Features
- Real-time speech-to-text transcription
- Multiple speech recognition services (Deepgram and OpenAI)
- GPT-4o post-processing for improved transcript quality
- Multiple language support with easy language selection
- Automatic text insertion at cursor position
- Keyboard shortcut support (F2)
- Modern customized UI with dark mode
- Transcription logging with expandable log view
- System tray integration for minimized operation
- Sound feedback for recording start/stop
- User-friendly settings dialog

## 🛠️ Requirements
- Python 3.7 or higher (3.9 recommended)
- Speech-to-text API key (Deepgram or OpenAI)
- Operating System: Windows, macOS, or Linux
- PortAudio (for PyAudio)

## 🚀 Setup Instructions

1. Install the required dependencies:

```bash
sudo apt-get install portaudio19-dev xdotool

cd C:\Projects\utils\ai\voice
git clone https://github.com/perrypixel/VoiceTyper-Pro.git
cd VoiceTyper-Pro

pyenv install 3.9
pyenv local 3.9

python3 -m venv venv

# Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

2. Run the application:

```bash
python main.py
```
3. Add your API key in the settings dialog:
   - For Deepgram API, get one at https://deepgram.com
   - For OpenAI API, get one at https://platform.openai.com

4. Enjoy!


## 🎯 Usage
- Click the "Start Recording" button or press F2 to begin recording
- Click again or press F2 to stop recording
- The transcribed text will appear in the window and be typed at your cursor position
- Transcriptions are automatically logged and viewable in the expandable log section
- Customize settings by clicking the gear icon:
  - Switch between Deepgram and OpenAI services
  - Select your preferred language
  - Toggle GPT-4o post-processing (for OpenAI service)
  - Test your API key directly from the settings dialog
- Minimize to system tray for unobtrusive operation

## 🧠 Advanced Features

### GPT-4o Post-Processing
When using the OpenAI service, you can enable GPT-4o post-processing to significantly improve the quality of transcriptions:
- Fixes grammatical errors
- Adds appropriate punctuation
- Corrects word misrecognitions
- Maintains the original meaning and intent
- Preserves technical terms and proper nouns
- Language-specific enhancements for German, French, and Spanish

### System Tray Integration
- Application can be minimized to system tray
- Continue recording and transcribing even when minimized
- Quick access to show/hide the application or quit

### Customizable UI
- Modern dark theme with AI gradient color scheme
- Expandable/collapsible log view
- Smooth animations for better user experience
- Sound feedback for recording status changes

## 🌐 Supported Services

### Deepgram
- High-quality speech recognition 
- Fast processing
- Multiple language support
- Uses the nova-2 model for improved accuracy

### OpenAI (Whisper)
- State-of-the-art accuracy
- Wide language support (15+ languages)
- Enhanced contextual understanding
- Optional GPT-4o post-processing

## 🗣️ Supported Languages

The application supports many languages including:
- English
- German (Deutsch)
- French (Français)
- Spanish (Español)
- Italian (Italiano)
- Japanese (日本語)
- Chinese (中文)
- Russian (Русский)
- Portuguese (Português)
- Korean (한국어)
- Arabic (العربية)
- Dutch (Nederlands)
- Swedish (Svenska)
- Polish (Polski)

You can also use Auto-detect mode to let the service determine the language automatically.

## 💪 Support
If you find this tool helpful, you can support the development by:
- Buying me a coffee at https://ko-fi.com/perrypixel
- UPI to kevinp@apl

## 🙏 Contributors
- https://github.com/perrypixel
- https://github.com/CyberT33N

