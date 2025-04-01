#!/bin/bash

# Ins richtige Verzeichnis wechseln
cd ~/Projects/ai/utils/voice/speech-to-text/VoiceTyper-Pro || exit

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Python-Skript starten
python main.py
