import sys
import os
import subprocess
import random
import time
from pathlib import Path

# Global flags for dependencies
PYTTSX_AVAILABLE = False
SPEECH_REC_AVAILABLE = False
PYAUDIO_AVAILABLE = False
SOUNDDEVICE_AVAILABLE = False

# Try loading speech synthesis (TTS)
try:
    import pyttsx3
    PYTTSX_AVAILABLE = True
except ImportError:
    pass

# Try loading speech recognition (STT) dependencies
try:
    import speech_recognition as sr
    
    # Check PyAudio
    try:
        import pyaudio
        PYAUDIO_AVAILABLE = True
    except ImportError:
        pass
        
    # Check Sounddevice fallback dependencies
    try:
        import sounddevice as sd
        import numpy as np
        import wave
        import tempfile
        SOUNDDEVICE_AVAILABLE = True
    except ImportError:
        pass
        
    if PYAUDIO_AVAILABLE or SOUNDDEVICE_AVAILABLE:
        SPEECH_REC_AVAILABLE = True
except ImportError:
    pass

class VoiceEngine:
    def __init__(self):
        self.enabled = False
        self.use_fallback = not PYTTSX_AVAILABLE
        self.engine = None
        
        # Configure stdout encoding to UTF-8
        if sys.platform.startswith('win'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
                
        if PYTTSX_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                # Set speaking rate (words per minute)
                self.engine.setProperty('rate', 170)
                # Adjust volume (0.0 to 1.0)
                self.engine.setProperty('volume', 0.9)
                
                # Try setting a female voice if available
                voices = self.engine.getProperty('voices')
                if len(voices) > 1:
                    self.engine.setProperty('voice', voices[1].id) # Index 1 is often female (Zira)
                elif len(voices) > 0:
                    self.engine.setProperty('voice', voices[0].id)
                self.enabled = True
            except Exception as e:
                self.use_fallback = True

    def speak(self, text, wait=True):
        """Speaks the text. Falls back to PowerShell if pyttsx3 is not available."""
        if not text:
            return
            
        clean_text = text.replace("[bold]", "").replace("[/bold]", "").replace("[cyan]", "").replace("[/cyan]", "").replace("[green]", "").replace("[/green]", "")
        
        if PYTTSX_AVAILABLE and not self.use_fallback and self.engine:
            try:
                self.engine.say(clean_text)
                if wait:
                    self.engine.runAndWait()
                return
            except Exception:
                self.use_fallback = True
                
        # Windows PowerShell TTS Fallback (Zero dependencies, offline)
        if sys.platform.startswith('win'):
            try:
                # Escape single quotes for PowerShell syntax
                escaped = clean_text.replace("'", "''")
                ps_script = (
                    f"Add-Type -AssemblyName System.Speech; "
                    f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$synth.Speak('{escaped}')"
                )
                
                # Run PowerShell command asynchronously if wait=False, else synchronously
                if wait:
                    subprocess.run(["powershell", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["powershell", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass # Fail silently if speech synthesizer is completely broken

class VoiceListener:
    def __init__(self):
        self.enabled = SPEECH_REC_AVAILABLE
        self.use_pyaudio = PYAUDIO_AVAILABLE
        self.recognizer = None
        self.microphone = None
        
        if SPEECH_REC_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 4000
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                
                if self.use_pyaudio:
                    self.microphone = sr.Microphone()
            except Exception:
                self.enabled = False

    def listen(self, console_status_callback=None):
        """
        Listens to the microphone and returns transcribed text.
        If microphone/packages are unavailable, prompts for console text input as a fallback.
        Supports both standard PyAudio microphone and Sounddevice recording fallbacks.
        """
        if not self.enabled:
            # Graceful keyboard fallback
            if console_status_callback:
                console_status_callback("Voice Fallback Mode (No Mic/Dependencies detected). Type command below.")
            try:
                user_input = input("\n⌨️  Enter voice command: ")
                return user_input.strip().lower()
            except (KeyboardInterrupt, EOFError):
                return "exit"

        if self.use_pyaudio:
            # Standard PyAudio microphone listening
            try:
                with self.microphone as source:
                    if console_status_callback:
                        console_status_callback("Calibrating background noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    
                    if console_status_callback:
                        console_status_callback("🎤 Listening... Speak now!")
                    
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    
                    if console_status_callback:
                        console_status_callback("🧠 Transcribing speech...")
                        
                    text = self.recognizer.recognize_google(audio)
                    return text.strip().lower()
                    
            except sr.WaitTimeoutError:
                if console_status_callback:
                    console_status_callback("⚠️ Listening timed out. No speech detected.")
                return ""
            except sr.UnknownValueError:
                if console_status_callback:
                    console_status_callback("⚠️ Could not understand audio.")
                return ""
            except sr.RequestError as e:
                if console_status_callback:
                    console_status_callback(f"⚠️ Speech Recognition service error: {str(e)}")
                return ""
            except Exception as e:
                if console_status_callback:
                    console_status_callback(f"⚠️ Microphone error: {str(e)}")
                return ""
        else:
            # Sounddevice fallback listening (doesn't require PyAudio build tools!)
            try:
                import sounddevice as sd
                import wave
                import tempfile
                
                fs = 16000
                duration = 4.0
                
                if console_status_callback:
                    console_status_callback("🎤 Listening (4s)... Speak now!")
                
                # Record blockingly
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                
                # Show countdown in status
                for remaining in range(4, 0, -1):
                    if console_status_callback:
                        console_status_callback(f"🎤 Listening... {remaining}s remaining")
                    time.sleep(1)
                    
                sd.wait() # Ensure audio is fully buffered
                
                if console_status_callback:
                    console_status_callback("🧠 Transcribing speech...")
                    
                # Save as a temporary wav file
                temp_dir = Path(tempfile.gettempdir())
                temp_wav = temp_dir / "yuki_voice_sd.wav"
                
                with wave.open(str(temp_wav), 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2) # 16-bit
                    wf.setframerate(fs)
                    wf.writeframes(recording.tobytes())
                    
                # Load WAV into speech_recognizer
                with sr.AudioFile(str(temp_wav)) as source:
                    audio = self.recognizer.record(source)
                    
                # Clean up temporary WAV
                try:
                    temp_wav.unlink()
                except Exception:
                    pass
                    
                text = self.recognizer.recognize_google(audio)
                return text.strip().lower()
                
            except sr.UnknownValueError:
                if console_status_callback:
                    console_status_callback("⚠️ Could not understand audio.")
                return ""
            except sr.RequestError as e:
                if console_status_callback:
                    console_status_callback(f"⚠️ Speech Recognition service error: {str(e)}")
                return ""
            except Exception as e:
                if console_status_callback:
                    console_status_callback(f"⚠️ sounddevice driver error: {str(e)}")
                return ""

def get_programmer_joke():
    """Returns a random programmer joke."""
    jokes = [
        "Why do programmers wear glasses? Because they cannot C sharp!",
        "There are 10 kinds of people in this world: Those who understand binary, and those who do not.",
        "How many programmers does it take to change a light bulb? None, that is a hardware problem!",
        "What is a programmer's favorite place to hang out? Foo bar!",
        "Why did the programmer quit his job? Because he did not get arrays!",
        "A SQL query goes into a bar, walks up to two tables and asks: Can I join you?",
        "Why do Java programmers have to wear glasses? Because they do not C#!"
    ]
    return random.choice(jokes)
