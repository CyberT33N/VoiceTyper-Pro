import customtkinter as ctk
import threading
from pynput import keyboard
import codecs
import time
import pyaudio
import wave
import os
# from playsound import playsound
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import asyncio
import pystray
import json
import sys
from speech_to_text import create_service, SpeechToTextService
from deepgram_service import DeepgramService
from openai_service import OpenAIService

# Set theme and color scheme - 2025 AI Gradient Dark Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Define the 2025 AI Gradient Dark Theme colors
GRADIENT_BG_DARK = "#0A0E17"
GRADIENT_BG_MEDIUM = "#121725"
GRADIENT_BG_LIGHT = "#1A2133"
ACCENT_PRIMARY = "#7E6AFE"
ACCENT_SECONDARY = "#36D7B7"
ACCENT_DANGER = "#FF5D68"
ACCENT_WARNING = "#FFC56D"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0B9D1"
GRADIENT_START = "#8A63FF"
GRADIENT_END = "#36D7B7"

# Debug-Flag zum Speichern der Audio-Dateien
DEBUG_KEEP_AUDIO = False
DEBUG_AUDIO_DIR = "tmp"

# Additional imports for clipboard functionality
import tkinter as tk

# Simple alternative to playsound
def play_sound(sound_file):
    try:
        # Open the sound file
        wf = wave.open(sound_file, 'rb')
        
        # Create PyAudio object
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        # Read data in chunks and play
        chunk_size = 1024
        data = wf.readframes(chunk_size)
        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)
            
        # Close everything
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print(f"Error playing sound: {str(e)}")

class SettingsDialog:
    def __init__(self, parent):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("450x600")
        self.dialog.transient(parent)
        self.dialog.resizable(True, True)
        self.dialog.minsize(400, 550)
        self.dialog.configure(fg_color=GRADIENT_BG_DARK)
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_x() + (parent.winfo_width() - 450) // 2,
            parent.winfo_y() + (parent.winfo_height() - 600) // 2
        ))
        
        # Wait for dialog to be visible before setting grab
        self.dialog.after(100, lambda: self.make_modal())
        
        # Erstelle Container-Frame mit Scrollbar
        self.container = ctk.CTkScrollableFrame(self.dialog, fg_color=GRADIENT_BG_MEDIUM, 
                                               scrollbar_button_color=ACCENT_PRIMARY,
                                               scrollbar_button_hover_color=ACCENT_SECONDARY)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load current settings
        with open('settings.json', 'r') as f:
            self.settings = json.load(f)
        
        # Service selection frame
        self.service_frame = ctk.CTkFrame(self.container, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.service_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.service_label = ctk.CTkLabel(
            self.service_frame, 
            text="Speech-to-Text Service:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.service_label.pack(anchor="w", pady=5, padx=10)
        
        # Radio buttons for service selection
        self.service_var = ctk.StringVar(value=self.settings.get('service', 'deepgram'))
        
        self.deepgram_radio = ctk.CTkRadioButton(
            self.service_frame,
            text="Deepgram",
            variable=self.service_var,
            value="deepgram",
            command=self.update_api_visibility,
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        self.deepgram_radio.pack(anchor="w", pady=5, padx=20)
        
        self.openai_radio = ctk.CTkRadioButton(
            self.service_frame,
            text="OpenAI",
            variable=self.service_var,
            value="openai",
            command=self.update_api_visibility,
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        self.openai_radio.pack(anchor="w", pady=5, padx=20)
        
        # Language selection frame
        self.language_frame = ctk.CTkFrame(self.container, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.language_frame.pack(fill="x", padx=10, pady=5)
        
        self.language_label = ctk.CTkLabel(
            self.language_frame, 
            text="Language:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.language_label.pack(anchor="w", pady=5, padx=10)
        
        # Get supported languages from service class
        self.languages = SpeechToTextService.get_supported_languages()
        
        # Create the dropdown for language selection
        self.language_var = ctk.StringVar(value=self.settings.get('language', 'auto'))
        
        # Get language display names
        language_display_names = list(self.languages.values())
        
        # Get current language name
        current_lang_code = self.language_var.get()
        current_lang_name = self.languages.get(current_lang_code, current_lang_code)
        
        self.language_menu = ctk.CTkOptionMenu(
            self.language_frame,
            values=language_display_names,
            variable=None,
            width=200,
            fg_color=GRADIENT_BG_MEDIUM,
            button_color=ACCENT_PRIMARY,
            button_hover_color=ACCENT_SECONDARY,
            dropdown_fg_color=GRADIENT_BG_MEDIUM,
            dropdown_hover_color=GRADIENT_BG_LIGHT,
            dropdown_text_color=TEXT_PRIMARY,
            text_color=TEXT_PRIMARY
        )
        self.language_menu.pack(pady=5, padx=10)
        self.language_menu.set(current_lang_name)
        
        # Handle language selection
        def on_language_change(selection):
            # Convert display name to code
            for code, name in self.languages.items():
                if name == selection:
                    self.language_var.set(code)
                    return
            self.language_var.set(selection)
        
        self.language_menu.configure(command=on_language_change)
        
        # OpenAI Post-Processing Frame
        self.post_processing_frame = ctk.CTkFrame(self.container, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.post_processing_frame.pack(fill="x", padx=10, pady=5)
        
        self.post_processing_label = ctk.CTkLabel(
            self.post_processing_frame,
            text="OpenAI GPT-4 Post-Processing:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.post_processing_label.pack(anchor="w", pady=5, padx=10)
        
        self.post_processing_info = ctk.CTkLabel(
            self.post_processing_frame,
            text="Improve transcription quality using GPT-4.\nMay add latency but increases accuracy.",
            font=ctk.CTkFont(size=12),
            wraplength=350,
            justify="left",
            text_color=TEXT_SECONDARY
        )
        self.post_processing_info.pack(anchor="w", pady=5, padx=10)
        
        self.post_processing_var = ctk.BooleanVar(value=self.settings.get('post_processing', False))
        
        self.post_processing_checkbox = ctk.CTkCheckBox(
            self.post_processing_frame,
            text="Enable GPT-4 Post-Processing",
            variable=self.post_processing_var,
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        self.post_processing_checkbox.pack(anchor="w", pady=5, padx=20)
        
        # Deepgram API Key input
        self.deepgram_frame = ctk.CTkFrame(self.container, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.deepgram_frame.pack(fill="x", padx=10, pady=5)
        
        self.deepgram_label = ctk.CTkLabel(
            self.deepgram_frame, 
            text="Deepgram API Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.deepgram_label.pack(anchor="w", pady=5, padx=10)
        
        self.deepgram_entry = ctk.CTkEntry(
            self.deepgram_frame,
            width=300,
            font=ctk.CTkFont(size=14),
            fg_color=GRADIENT_BG_MEDIUM,
            text_color=TEXT_PRIMARY,
            border_color=ACCENT_PRIMARY,
            placeholder_text_color=TEXT_SECONDARY
        )
        self.deepgram_entry.pack(pady=5, padx=10)
        self.deepgram_entry.insert(0, self.settings.get('api_key', ''))
        
        # OpenAI API Key input
        self.openai_frame = ctk.CTkFrame(self.container, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.openai_frame.pack(fill="x", padx=10, pady=5)
        
        self.openai_label = ctk.CTkLabel(
            self.openai_frame, 
            text="OpenAI API Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.openai_label.pack(anchor="w", pady=5, padx=10)
        
        self.openai_entry = ctk.CTkEntry(
            self.openai_frame,
            width=300,
            font=ctk.CTkFont(size=14),
            fg_color=GRADIENT_BG_MEDIUM,
            text_color=TEXT_PRIMARY,
            border_color=ACCENT_PRIMARY,
            placeholder_text_color=TEXT_SECONDARY
        )
        self.openai_entry.pack(pady=5, padx=10)
        self.openai_entry.insert(0, self.settings.get('openai_api_key', ''))
        
        # Status label for test results
        self.status_label = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=350,
            text_color=TEXT_PRIMARY
        )
        self.status_label.pack(pady=5)
        
        # Test button
        self.test_btn = ctk.CTkButton(
            self.container,
            text="Test Service",
            command=self.test_service,
            width=100,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            corner_radius=8
        )
        self.test_btn.pack(pady=5)
        
        # Save button - in einem Frame am unteren Rand
        self.button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        self.button_frame.pack(fill="x", side="bottom", pady=10)
        
        self.save_btn = ctk.CTkButton(
            self.button_frame,
            text="Save",
            command=self.save_settings,
            width=100,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            corner_radius=8
        )
        self.save_btn.pack(pady=5)
        
        # Set initial visibility based on selected service
        self.update_api_visibility()
    
    def test_service(self):
        """Test the selected service with current settings"""
        try:
            service_type = self.service_var.get()
            if service_type == "deepgram":
                api_key = self.deepgram_entry.get()
                post_processing = False
            else:
                api_key = self.openai_entry.get()
                post_processing = self.post_processing_var.get()
                
            language = self.language_var.get()
            
            # Validate input
            if not api_key:
                self.status_label.configure(text="Please enter an API key", text_color="red")
                return
                
            # Create service
            service = create_service(service_type, api_key, post_processing)
            
            self.status_label.configure(text=f"Testing {service_type.capitalize()}...", text_color="black")
            self.dialog.update()
            
            # Just do a quick test to see if service initializes properly
            post_process_text = " with GPT-4 post-processing" if post_processing and service_type == "openai" else ""
            self.status_label.configure(
                text=f"{service_type.capitalize()} service initialized successfully{post_process_text}",
                text_color="green"
            )
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
    
    def update_language_display(self):
        # Update the displayed value in the dropdown to show language name instead of code
        current_lang_code = self.language_var.get()
        # Get the language name for the current code
        current_lang_name = self.languages.get(current_lang_code, current_lang_code)
        # Set the displayed value to the language name
        self.language_menu.set(current_lang_name)
    
    def on_language_change(self, selection):
        # Convert the display name back to language code
        for code, name in self.languages.items():
            if name == selection:
                self.language_var.set(code)
                return
        
        # If we get here, assume selection is already a code
        self.language_var.set(selection)
    
    def update_api_visibility(self):
        service = self.service_var.get()
        if service == "deepgram":
            self.deepgram_frame.pack(fill="x", padx=10, pady=5)
            self.openai_frame.pack_forget()
            self.post_processing_frame.pack_forget()
        else:
            self.deepgram_frame.pack_forget()
            self.openai_frame.pack(fill="x", padx=10, pady=5)
            self.post_processing_frame.pack(fill="x", padx=10, pady=5)
        
    def save_settings(self):
        self.settings['service'] = self.service_var.get()
        self.settings['api_key'] = self.deepgram_entry.get()
        self.settings['openai_api_key'] = self.openai_entry.get()
        self.settings['language'] = self.language_var.get()
        self.settings['post_processing'] = self.post_processing_var.get()
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
        self.dialog.destroy()

    def make_modal(self):
        """Make the dialog modal after it's visible"""
        if self.dialog.winfo_exists() and self.dialog.winfo_viewable():
            self.dialog.grab_set()
        else:
            # Try again later
            self.dialog.after(100, self.make_modal)

class VoiceTyperApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Voice Typer Pro")
        self.root.geometry("400x250")
        self.root.minsize(400, 250)
        self.root.configure(fg_color=GRADIENT_BG_DARK)
        
        # Initialize variables
        self.is_recording = False
        self.file_ready_counter = 0
        self.stop_recording = False
        self.pykeyboard = keyboard.Controller()
        self.recording_animation_active = False
        self.service = None
        self.transcription_thread_started = False
        self.transcription_thread_running = True  # Flag to control the transcription thread loop
        
        # Ensure tmp directory exists if debug mode is enabled
        if DEBUG_KEEP_AUDIO:
            os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)
        
        # Try to load settings and initialize Speech-to-Text service
        try:
            self.load_settings()
        except ValueError as ve:
            # Show settings dialog immediately if API key is invalid
            self.setup_ui()  # Setup UI first
            self.show_api_key_error(str(ve))
        except Exception as e:
            self.setup_ui()
            self.show_error(f"Error: {str(e)}")
            
        # Initialize system tray
        self.setup_system_tray()
        
        # Track if log section is expanded
        self.log_expanded = False  # Start with log collapsed
        
        # Global keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
        
        self.setup_ui()
        
    def show_api_key_error(self, error_message="Invalid API Key detected"):
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("API Key Error")
        error_dialog.geometry("400x400")
        error_dialog.transient(self.root)
        error_dialog.resizable(False, False)
        error_dialog.configure(fg_color=GRADIENT_BG_DARK)
        
        # Center the dialog
        error_dialog.geometry("+%d+%d" % (
            self.root.winfo_x() + (self.root.winfo_width() - 400) // 2,
            self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        ))
        
        # Error message
        message = ctk.CTkLabel(
            error_dialog,
            text=f"{error_message}.\nPlease enter valid API keys to continue.",
            font=ctk.CTkFont(size=14),
            wraplength=350,
            text_color=ACCENT_DANGER
        )
        message.pack(pady=20)
        
        # Service selection
        service_frame = ctk.CTkFrame(error_dialog, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        service_frame.pack(fill="x", padx=20, pady=5)
        
        service_var = ctk.StringVar(value=self.settings.get('service', 'deepgram'))
        
        deepgram_radio = ctk.CTkRadioButton(
            service_frame,
            text="Deepgram",
            variable=service_var,
            value="deepgram",
            command=lambda: update_visibility(),
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        deepgram_radio.pack(anchor="w", pady=5, padx=10)
        
        openai_radio = ctk.CTkRadioButton(
            service_frame,
            text="OpenAI",
            variable=service_var,
            value="openai",
            command=lambda: update_visibility(),
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        openai_radio.pack(anchor="w", pady=5, padx=10)
        
        # Post-processing option (only for OpenAI)
        post_processing_frame = ctk.CTkFrame(error_dialog, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        post_processing_var = ctk.BooleanVar(value=self.settings.get('post_processing', False))
        
        post_processing_checkbox = ctk.CTkCheckBox(
            post_processing_frame,
            text="Enable GPT-4 Post-Processing",
            variable=post_processing_var,
            fg_color=ACCENT_PRIMARY,
            text_color=TEXT_PRIMARY,
            hover_color=ACCENT_SECONDARY
        )
        post_processing_checkbox.pack(anchor="w", pady=5, padx=10)
        
        # Language selection
        language_frame = ctk.CTkFrame(error_dialog, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        language_frame.pack(fill="x", padx=20, pady=5)
        
        language_label = ctk.CTkLabel(
            language_frame,
            text="Language:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        language_label.pack(anchor="w", pady=5, padx=10)
        
        # Get supported languages
        languages = SpeechToTextService.get_supported_languages()
        
        # Create dropdown for language selection
        language_var = ctk.StringVar(value=self.settings.get('language', 'auto'))
        
        # Get language display names
        language_display_names = list(languages.values())
        
        # Get current language name
        current_lang_code = language_var.get()
        current_lang_name = languages.get(current_lang_code, current_lang_code)
        
        language_menu = ctk.CTkOptionMenu(
            language_frame,
            values=language_display_names,
            variable=None,
            width=200,
            fg_color=GRADIENT_BG_MEDIUM,
            button_color=ACCENT_PRIMARY,
            button_hover_color=ACCENT_SECONDARY,
            dropdown_fg_color=GRADIENT_BG_MEDIUM,
            dropdown_hover_color=GRADIENT_BG_LIGHT,
            dropdown_text_color=TEXT_PRIMARY,
            text_color=TEXT_PRIMARY
        )
        language_menu.pack(pady=5)
        language_menu.set(current_lang_name)
        
        # Handle language selection
        def on_language_change(selection):
            # Convert display name to code
            for code, name in languages.items():
                if name == selection:
                    language_var.set(code)
                    return
            language_var.set(selection)
        
        language_menu.configure(command=on_language_change)
        
        # API Key input
        api_entry = ctk.CTkEntry(
            error_dialog,
            width=300,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter API key for selected service",
            fg_color=GRADIENT_BG_MEDIUM,
            text_color=TEXT_PRIMARY,
            border_color=ACCENT_PRIMARY
        )
        api_entry.pack(pady=10)
        
        if service_var.get() == "deepgram":
            api_entry.insert(0, self.settings.get('api_key', ''))
        else:
            api_entry.insert(0, self.settings.get('openai_api_key', ''))
        
        def update_api_entry(*args):
            api_entry.delete(0, 'end')
            if service_var.get() == "deepgram":
                api_entry.insert(0, self.settings.get('api_key', ''))
            else:
                api_entry.insert(0, self.settings.get('openai_api_key', ''))
        
        def update_visibility(*args):
            if service_var.get() == "deepgram":
                post_processing_frame.pack_forget()
            else:
                post_processing_frame.pack(fill="x", padx=20, pady=5)
            update_api_entry()
        
        # Initial visibility
        update_visibility()
        
        service_var.trace_add("write", update_api_entry)
        
        def save_and_retry():
            new_key = api_entry.get()
            selected_service = service_var.get()
            
            # Update settings
            if selected_service == "deepgram":
                self.settings['api_key'] = new_key
                self.settings['service'] = 'deepgram'
                self.settings['post_processing'] = False
            else:
                self.settings['openai_api_key'] = new_key
                self.settings['service'] = 'openai'
                self.settings['post_processing'] = post_processing_var.get()
                
            self.settings['language'] = language_var.get()
            
            # Save settings
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f)
                
            # Try to initialize service with new settings
            try:
                self.load_settings()
                error_dialog.destroy()
            except Exception as e:
                message.configure(text=f"Error: {str(e)}\nPlease check your API key and try again.")
                
        # Save button
        save_btn = ctk.CTkButton(
            error_dialog,
            text="Save & Retry",
            command=save_and_retry,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            corner_radius=8,
            height=35
        )
        save_btn.pack(pady=10)

    def show_error(self, error_message):
        """Display a simple error message dialog"""
        error_window = ctk.CTkToplevel(self.root)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.transient(self.root)
        error_window.resizable(False, False)
        error_window.configure(fg_color=GRADIENT_BG_DARK)
        
        # Center the window
        error_window.geometry("+%d+%d" % (
            self.root.winfo_x() + (self.root.winfo_width() - 400) // 2,
            self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        ))
        
        # Frame for content
        frame = ctk.CTkFrame(error_window, fg_color=GRADIENT_BG_MEDIUM, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Error message
        msg = ctk.CTkLabel(
            frame, 
            text=error_message,
            font=ctk.CTkFont(size=14),
            wraplength=350,
            text_color=ACCENT_DANGER
        )
        msg.pack(pady=20)
        
        # OK button
        ok_btn = ctk.CTkButton(
            frame,
            text="OK",
            command=error_window.destroy,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            corner_radius=8,
            width=100
        )
        ok_btn.pack(pady=10)
        
    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {'api_key': '', 'service': 'deepgram', 'openai_api_key': ''}
            
        service_type = self.settings.get('service', 'deepgram')
        api_key = self.settings.get('api_key' if service_type == 'deepgram' else 'openai_api_key', '')
        
        try:
            self.service = create_service(service_type, api_key)
        except ValueError as ve:
            raise ValueError(f"Invalid {service_type.capitalize()} API Key")
        except Exception as e:
            raise Exception(f"Failed to initialize {service_type.capitalize()}: {str(e)}")
        
    def setup_system_tray(self):
        # Create system tray icon
        self.icon_image = Image.new('RGB', (64, 64), color='blue')
        self.tray_icon = pystray.Icon(
            "Voice Typer",
            self.icon_image,
            menu=pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.quit_app)
            )
        )
        
    def setup_ui(self):
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self.root, fg_color=GRADIENT_BG_MEDIUM, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame with title and settings button
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.header_frame.pack(fill="x", pady=5, padx=5)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Voice Typer Pro",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.title_label.pack(side="left", padx=10, pady=5)
        
        # Service indicator
        service_type = self.settings.get('service', 'deepgram').capitalize()
        language_code = self.settings.get('language', 'auto')
        language_name = SpeechToTextService.get_supported_languages().get(language_code, language_code)
        
        self.service_label = ctk.CTkLabel(
            self.header_frame,
            text=f"({service_type} - {language_name})",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=TEXT_SECONDARY
        )
        self.service_label.pack(side="left", padx=5, pady=5)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.header_frame,
            text="⚙️",
            width=40,
            command=self.open_settings,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            corner_radius=8
        )
        self.settings_btn.pack(side="right", padx=10, pady=5)
        
        # Record button and indicator in one frame
        self.control_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.control_frame.pack(fill="x", pady=15)
        
        self.record_button = ctk.CTkButton(
            self.control_frame,
            text="Start Recording (F2)",
            command=self.toggle_recording,
            height=45,
            corner_radius=22,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_SECONDARY,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.record_button.pack(pady=5)
        
        self.recording_indicator = ctk.CTkProgressBar(
            self.control_frame,
            width=280,
            height=6,
            progress_color=ACCENT_SECONDARY,
            fg_color=GRADIENT_BG_LIGHT
        )
        self.recording_indicator.pack(pady=5)
        self.recording_indicator.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Ready to record...",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY
        )
        self.status_label.pack(pady=5)
        
        # Create a container frame for log section
        self.log_container = ctk.CTkFrame(self.main_frame, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.log_container.pack(fill="x", expand=False, padx=5, pady=5)
        
        # Log controls in container
        self.toggle_log_btn = ctk.CTkButton(
            self.log_container,
            text="▶ Show Log",
            command=self.toggle_log_section,
            width=100,
            height=28,
            fg_color=GRADIENT_BG_MEDIUM,
            hover_color=GRADIENT_BG_DARK,
            text_color=TEXT_PRIMARY,
            corner_radius=8
        )
        self.toggle_log_btn.pack(side="left", padx=5, pady=5)
        
        self.clear_log_btn = ctk.CTkButton(
            self.log_container,
            text="Clear",
            command=self.clear_logs,
            width=60,
            height=28,
            fg_color=ACCENT_DANGER,
            hover_color="#FF7B80",
            text_color=TEXT_PRIMARY,
            corner_radius=8
        )
        self.clear_log_btn.pack(side="right", padx=5, pady=5)
        
        # Log frame and content
        self.log_frame = ctk.CTkFrame(self.main_frame, fg_color=GRADIENT_BG_LIGHT, corner_radius=10)
        self.transcription_text = ctk.CTkTextbox(
            self.log_frame,
            height=200,
            font=ctk.CTkFont(size=12),
            fg_color=GRADIENT_BG_MEDIUM,
            text_color=TEXT_PRIMARY,
            border_width=0,
            corner_radius=8,
            scrollbar_button_color=ACCENT_PRIMARY,
            scrollbar_button_hover_color=ACCENT_SECONDARY
        )
        self.transcription_text.pack(fill="both", expand=True, pady=5, padx=5)
        
    def animate_recording(self):
        if self.recording_animation_active:
            current = self.recording_indicator.get()
            if current >= 1:
                self.recording_indicator.set(0)
            else:
                self.recording_indicator.set(current + 0.05)  # Smoother animation
            
            # Create gradient pulsing effect by cycling through gradient colors
            pulse_value = (current * 2) % 1.0  # Normalize to 0-1 range for smoother cycle
            r1, g1, b1 = int(GRADIENT_START[1:3], 16), int(GRADIENT_START[3:5], 16), int(GRADIENT_START[5:7], 16)
            r2, g2, b2 = int(GRADIENT_END[1:3], 16), int(GRADIENT_END[3:5], 16), int(GRADIENT_END[5:7], 16)
            
            # Interpolate between start and end colors
            r = int(r1 + (r2 - r1) * pulse_value)
            g = int(g1 + (g2 - g1) * pulse_value)
            b = int(b1 + (b2 - b1) * pulse_value)
            
            # Convert back to hex
            pulse_color = f"#{r:02x}{g:02x}{b:02x}"
            
            self.record_button.configure(fg_color=pulse_color)
            self.root.after(50, self.animate_recording)  # Faster updates
    
    def toggle_recording(self):
        if not hasattr(self, 'service'):
            self.show_api_key_error()
            return
            
        if not self.is_recording:
            # Start the transcription thread if it's not already started
            if not self.transcription_thread_started:
                self.start_transcription_thread()
                self.transcription_thread_started = True
                
            self.start_recording()
            # Start animation with pulsing effect
            self.recording_animation_active = True
            self.record_button.configure(
                fg_color=ACCENT_DANGER,
                text="■ Stop Recording (F2)"  # Square stop symbol
            )
            self.animate_recording()
        else:
            self.stop_recording = True
            # Stop animation
            self.recording_animation_active = False
            self.record_button.configure(
                fg_color=ACCENT_PRIMARY,
                text="● Start Recording (F2)"  # Circle record symbol
            )
            self.recording_indicator.set(0)
    
    def on_key_press(self, key):
        try:
            if key == keyboard.Key.f2:
                self.root.after(0, self.toggle_recording)
        except AttributeError:
            pass
    
    def on_key_release(self, key):
        pass
            
    def start_recording(self):
        threading.Thread(target=self.record_speech, daemon=True).start()
        
    def record_speech(self):
        self.is_recording = True
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 2
        fs = 44100
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=sample_format,
            channels=channels,
            rate=fs,
            frames_per_buffer=chunk,
            input=True
        )
        
        frames = []
        play_sound("assets/on.wav")
        
        while not self.stop_recording:
            data = stream.read(chunk)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        play_sound("assets/off.wav")
        
        # Save recording
        wf = wave.open(f"test{self.file_ready_counter+1}.wav", 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        self.stop_recording = False
        self.is_recording = False
        self.file_ready_counter += 1
        
        self.status_label.configure(text="Processing transcription...")
        
    async def transcribe_audio(self, audio_file):
        try:
            # Get language from settings, default to English
            language = self.settings.get('language', 'en')
            post_processing = self.settings.get('post_processing', False)
            
            # Log the transcription process
            service_type = self.settings.get('service', 'deepgram').capitalize()
            if service_type == "Openai" and post_processing:
                print(f"Starting transcription with {service_type} (GPT-4 post-processing enabled) for language: {language}")
            else:
                print(f"Starting transcription with {service_type} for language: {language}")
                
            transcript = await self.service.transcribe_audio(audio_file, language)
            
            # Log completion
            if service_type == "Openai" and post_processing:
                print(f"✓ Completed {service_type} transcription with GPT-4 post-processing")
                
            return transcript
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")
            
    def start_transcription_thread(self):
        self.transcription_thread_running = True  # Ensure flag is set to True when starting
        threading.Thread(target=self.transcribe_speech, daemon=True).start()
        
    def transcribe_speech(self):
        i = 1
        
        while self.transcription_thread_running:  # Use the flag to control the loop
            while self.file_ready_counter < i and self.transcription_thread_running:
                time.sleep(0.01)
                
            if not self.transcription_thread_running:  # Check if we should exit
                break
                
            audio_file = f"test{i}.wav"
            
            # Check if the file exists before trying to transcribe it
            if not os.path.exists(audio_file):
                i += 1
                continue
                
            try:
                transcript = asyncio.run(self.transcribe_audio(audio_file))
                
                # Update GUI
                self.transcription_text.insert('1.0', f"{datetime.now().strftime('%H:%M:%S')}: {transcript}\n\n")
                self.status_label.configure(text="Ready to record...")
                
                # Log transcription
                with codecs.open('transcribe.log', 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now()}: {transcript}\n")
                    
                # IMPROVED CLIPBOARD METHOD: Save previous clipboard content, then restore after pasting
                try:
                    # Save current clipboard content
                    try:
                        previous_clipboard = self.root.clipboard_get()
                    except:
                        previous_clipboard = ""  # Empty if no content or error
                    
                    # Copy transcribed text to clipboard
                    self.root.clipboard_clear()
                    self.root.clipboard_append(transcript)
                    
                    # Brief pause to ensure clipboard is set
                    time.sleep(0.2)
                    
                    # Simulate Ctrl+V to paste
                    with self.pykeyboard.pressed(keyboard.Key.ctrl):
                        self.pykeyboard.press('v')
                        self.pykeyboard.release('v')
                    
                    # Brief pause before restoring clipboard
                    time.sleep(0.2)
                    
                    # Restore previous clipboard content
                    self.root.clipboard_clear()
                    self.root.clipboard_append(previous_clipboard)
                    
                except Exception as e:
                    print(f"Error with clipboard operation: {str(e)}")
                
                # Entweder Datei löschen oder in tmp-Ordner verschieben
                if DEBUG_KEEP_AUDIO:
                    # Verschiebe die Audiodatei in den tmp-Ordner mit Zeitstempel
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_filename = f"{DEBUG_AUDIO_DIR}/audio_{timestamp}_{i}.wav"
                    os.rename(audio_file, new_filename)
                    print(f"Saved audio file to {new_filename}")
                else:
                    # Datei löschen (Standardverhalten)
                    os.remove(audio_file)
                
                i += 1
                
            except Exception as e:
                error_msg = str(e)
                print(f"Transcription error: {error_msg}", file=sys.stderr)
                
                # Make sure the error message is visible in the UI
                self.status_label.configure(
                    text=f"Error: {error_msg[:50]}..." if len(error_msg) > 50 else f"Error: {error_msg}",
                    text_color="red"
                )
                
                # Also log the error to the transcription text area
                self.transcription_text.insert('1.0', f"{datetime.now().strftime('%H:%M:%S')}: ❌ Error: {error_msg}\n\n")
                
                # Try to remove the audio file if not in debug mode
                try:
                    if not DEBUG_KEEP_AUDIO:
                        os.remove(audio_file)
                    else:
                        # Move to tmp with error indicator
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{DEBUG_AUDIO_DIR}/error_{timestamp}_{i}.wav"
                        os.rename(audio_file, new_filename)
                        print(f"Saved error audio file to {new_filename}")
                except:
                    pass
                    
                i += 1

    def __del__(self):
        # Stop the transcription thread
        self.transcription_thread_running = False
        
        # Clean up keyboard listener
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()

    def animate_window_resize(self, target_height, current_height=None, step=0):
        """Animate the window resizing for a smoother transition"""
        if current_height is None:
            current_height = self.root.winfo_height()
            
        # Calculate the total steps based on the difference
        total_steps = 10
        height_diff = target_height - current_height
        
        # Don't animate if there's no change needed
        if height_diff == 0:
            return
            
        # Calculate the height for this step
        progress = step / total_steps
        # Use easing function for smoother animation (ease in/out)
        if progress < 0.5:
            # Ease in (slow → fast)
            ease = 2 * progress * progress
        else:
            # Ease out (fast → slow)
            ease = 1 - pow(-2 * progress + 2, 2) / 2
            
        new_height = int(current_height + height_diff * ease)
        
        # Update the window size
        self.root.geometry(f"{self.root.winfo_width()}x{new_height}")
        
        # Continue animation if not complete
        if step < total_steps:
            self.root.after(15, lambda: self.animate_window_resize(target_height, current_height, step + 1))

    def toggle_log_section(self):
        if not self.log_expanded:
            # Expand log section
            self.log_expanded = True
            
            # Change button text to collapse
            self.toggle_log_btn.configure(
                text="▼ Hide Log",
                fg_color=GRADIENT_BG_MEDIUM,
                hover_color=GRADIENT_BG_DARK,
                text_color=TEXT_PRIMARY
            )
            
            # Show log frame
            self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Get current height
            current_height = self.root.winfo_height()
            # Target height with log expanded
            target_height = current_height + 200
            
            # Animate the window resize
            self.animate_window_resize(target_height, current_height)
            
        else:
            # Collapse log section
            self.log_expanded = False
            
            # Change button text to expand
            self.toggle_log_btn.configure(
                text="▶ Show Log",
                fg_color=GRADIENT_BG_MEDIUM,
                hover_color=GRADIENT_BG_DARK,
                text_color=TEXT_PRIMARY
            )
            
            # Get current height
            current_height = self.root.winfo_height()
            # Target height with log collapsed
            target_height = current_height - 200
            
            # Animate the window resize (decrease)
            self.animate_window_resize(target_height, current_height)
            
            # Hide log frame (do this after animation completes)
            def hide_log_frame():
                if not self.log_expanded:  # Double-check to avoid race conditions
                    self.log_frame.pack_forget()
            
            # Delay hiding the log frame until after animation
            self.root.after(300, hide_log_frame)
            
    def clear_logs(self):
        self.transcription_text.delete('1.0', 'end')
        # Also clear the log file
        with open('transcribe.log', 'w', encoding='utf-8') as f:
            f.write('')
            
    def minimize_to_tray(self):
        self.root.withdraw()  # Hide the window
        if not self.tray_icon.visible:
            # Start system tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
    def show_window(self):
        self.tray_icon.stop()
        self.root.after(0, self.root.deiconify)
        
    def quit_app(self):
        # Stop the transcription thread
        self.transcription_thread_running = False
        
        self.tray_icon.stop()
        self.root.quit()

    def open_settings(self):
        """Open the settings dialog"""
        # Create settings dialog
        settings_dialog = SettingsDialog(self.root)
        
        # Monitor when dialog is closed
        def on_dialog_close():
            if not settings_dialog.dialog.winfo_exists():
                # Re-enable main window
                self.root.focus_force()
                
                # Reload settings and update UI
                try:
                    old_service = self.settings.get('service', 'deepgram')
                    old_language = self.settings.get('language', 'auto')
                    old_post_processing = self.settings.get('post_processing', False)
                    
                    # Reload settings from file
                    with open('settings.json', 'r') as f:
                        self.settings = json.load(f)
                    
                    # Check if service or language changed
                    new_service = self.settings.get('service', 'deepgram')
                    new_language = self.settings.get('language', 'auto')
                    new_post_processing = self.settings.get('post_processing', False)
                    
                    if (old_service != new_service or 
                        old_language != new_language or 
                        old_post_processing != new_post_processing):
                        
                        # Update service with new settings
                        try:
                            self.load_settings()
                            
                            # Update service indicator
                            service_type = self.settings.get('service', 'deepgram').capitalize()
                            post_process_text = " + GPT-4" if new_post_processing and new_service == "openai" else ""
                            language_code = self.settings.get('language', 'auto')
                            language_name = SpeechToTextService.get_supported_languages().get(language_code, language_code)
                            
                            self.service_label.configure(text=f"({service_type}{post_process_text} - {language_name})")
                            
                            # Show success message
                            self.status_label.configure(
                                text=f"Settings updated successfully", 
                                text_color=ACCENT_SECONDARY
                            )
                        except Exception as e:
                            self.status_label.configure(
                                text=f"Error updating settings: {str(e)}", 
                                text_color=ACCENT_DANGER
                            )
                except Exception as e:
                    # Error reading settings
                    self.status_label.configure(
                        text=f"Error loading settings: {str(e)}", 
                        text_color=ACCENT_DANGER
                    )
                
                # Stop checking
                return
            
            # Continue checking while dialog exists
            self.root.after(100, on_dialog_close)
            
        # Start monitoring dialog
        self.root.after(100, on_dialog_close)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceTyperApp()
    app.run() 