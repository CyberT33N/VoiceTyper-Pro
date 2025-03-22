# VoiceTyper Pro

A graphical interface for voice-to-text transcription using Python. This application allows you to convert speech to text in real-time and automatically types the transcribed text at your cursor position.

Alternative to Mac Whisper, Voice Access, and other voice typing tools.

## Features
- Real-time speech-to-text transcription
- Multiple speech recognition services (Deepgram and OpenAI)
- Automatic text insertion at cursor position
- Keyboard shortcut support (F2)
- Transcription logging
- User-friendly GUI interface

## Requirements
- Python 3.7 or higher
- Speech-to-text API key (Deepgram or OpenAI)
- Operating System: Windows, macOS, or Linux

## Setup Instructions

1. Install the required dependencies:

```bash
sudo apt-get install portaudio19-dev

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


## Usage
- Click the "Start Recording" button or press F2 to begin recording
- Click again or press F2 to stop recording
- The transcribed text will appear in the window and be typed at your cursor position
- All transcriptions are logged in transcribe.log
- Switch between Deepgram and OpenAI in the settings dialog

## Supported Services

### Deepgram
- High-quality speech recognition 
- Fast processing
- Multiple language support

### OpenAI (Whisper)
- State-of-the-art accuracy
- Wide language support
- Enhanced contextual understanding

## Support
If you find this tool helpful, you can support the development by:
- Buying me a coffee at https://ko-fi.com/perrypixel
- UPI to kevinp@apl

