#!/bin/bash
# Start Voice Typer Pro im Debug-Modus

# Stellt sicher, dass der tmp-Ordner existiert
mkdir -p tmp

# Aktiviere die virtuelle Umgebung, falls sie existiert
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Starte die App
python main.py

# Deaktiviere die virtuelle Umgebung
if [ -d "venv" ]; then
    deactivate
fi 