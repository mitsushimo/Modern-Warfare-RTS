"""
Audio system and SoundManager for Age of Modernity.
Supports procedural generation of 16-bit PCM WAV sound effects
and runtime playback via pygame.mixer.
"""
import os
import math
import wave
import struct
import random
from typing import Dict, Optional
import pygame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(BASE_DIR, "assets", "sounds")


def _generate_wav_file(filename: str, samples: list, sample_rate: int = 44100):
    """Writes a list of normalized float samples (-1.0 to 1.0) into a 16-bit mono WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)        # Mono
        wav_file.setsampwidth(2)        # 16-bit (2 bytes)
        wav_file.setframerate(sample_rate)
        
        raw_bytes = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            int_val = int(clamped * 32767.0)
            raw_bytes.extend(struct.pack("<h", int_val))
            
        wav_file.writeframes(raw_bytes)


def create_gunfire_samples(sample_rate: int = 44100) -> list:
    """Generates a crisp infantry rifle gunshot."""
    duration = 0.14
    total_samples = int(sample_rate * duration)
    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 35.0)
        sine_crack = math.sin(2.0 * math.pi * 950.0 * (1.0 - t / duration) * t)
        noise = random.uniform(-1.0, 1.0)
        sample = (0.6 * noise + 0.4 * sine_crack) * envelope
        samples.append(sample * 0.85)
    return samples


def create_tank_cannon_samples(sample_rate: int = 44100) -> list:
    """Generates a punchy medium cannon blast (tank / destroyer)."""
    duration = 0.35
    total_samples = int(sample_rate * duration)
    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 12.0)
        freq = 45.0 + 135.0 * math.exp(-t * 22.0)
        sine_punch = math.sin(2.0 * math.pi * freq * t)
        noise = random.uniform(-1.0, 1.0) * math.exp(-t * 16.0)
        sample = (0.65 * sine_punch + 0.35 * noise) * envelope
        samples.append(sample * 0.9)
    return samples


def create_battleship_cannon_samples(sample_rate: int = 44100) -> list:
    """Generates a heavy battleship / artillery naval dreadnought boom."""
    duration = 0.65
    total_samples = int(sample_rate * duration)
    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 6.5)
        freq = 26.0 + 69.0 * math.exp(-t * 9.0)
        sub_sine = math.sin(2.0 * math.pi * freq * t)
        noise = random.uniform(-1.0, 1.0) * math.exp(-t * 8.0)
        rumble = 0.5 * math.sin(2.0 * math.pi * (freq * 0.5) * t)
        sample = (0.55 * sub_sine + 0.25 * rumble + 0.20 * noise) * envelope
        samples.append(sample * 0.95)
    return samples


def create_torpedo_samples(sample_rate: int = 44100) -> list:
    """Generates a pressurized launch whoosh followed by underwater thump."""
    duration = 0.42
    total_samples = int(sample_rate * duration)
    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        env = (t / 0.05) if t < 0.05 else math.exp(-(t - 0.05) * 8.0)
        freq = 220.0 + 350.0 * math.sin(math.pi * (t / duration))
        sweep = math.sin(2.0 * math.pi * freq * t)
        noise = random.uniform(-0.8, 0.8)
        sample = (0.5 * sweep + 0.5 * noise) * env
        samples.append(sample * 0.85)
    return samples



def ensure_default_sound_files(sound_dir: Optional[str] = None):
    """
    Ensures that default .wav sound files exist in the sound directory.
    If custom files already exist, they are preserved and NOT overwritten.
    """
    target_dir = sound_dir or SOUND_DIR
    os.makedirs(target_dir, exist_ok=True)

    sound_generators = {
        "gunfire.wav": create_gunfire_samples,
        "tank_cannon.wav": create_tank_cannon_samples,
        "battleship_cannon.wav": create_battleship_cannon_samples,
        "torpedo.wav": create_torpedo_samples,
    }

    for fname, generator_fn in sound_generators.items():
        filepath = os.path.join(target_dir, fname)
        if not os.path.exists(filepath):
            samples = generator_fn()
            _generate_wav_file(filepath, samples)


class SoundManager:
    """
    Manages loading and playback of game sound effects.
    Gracefully handles headless environments and missing audio hardware.
    """
    def __init__(self, sound_dir: Optional[str] = None):
        self.sound_dir = sound_dir or SOUND_DIR
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.enabled = False
        self._init_audio()

    def _init_audio(self):
        """Attempts to initialize pygame.mixer and loads sound files."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False
            return

        ensure_default_sound_files(self.sound_dir)
        self._load_sounds()

    def _load_sounds(self):
        """Loads available sound files from the sound directory."""
        if not self.enabled:
            return

        sound_keys = [
            ("gunfire", "gunfire.wav", 0.55),
            ("tank_cannon", "tank_cannon.wav", 0.70),
            ("battleship_cannon", "battleship_cannon.wav", 0.85),
            ("torpedo", "torpedo.wav", 0.65),
        ]

        for key, filename, volume in sound_keys:
            path = os.path.join(self.sound_dir, filename)
            ogg_path = os.path.join(self.sound_dir, f"{key}.ogg")
            chosen_path = ogg_path if os.path.exists(ogg_path) else path

            if os.path.exists(chosen_path):
                try:
                    snd = pygame.mixer.Sound(chosen_path)
                    snd.set_volume(volume)
                    self.sounds[key] = snd
                except Exception:
                    pass

    def play_sound(self, sound_key: str):
        """Plays the sound mapped to sound_key if loaded and audio is enabled."""
        if not self.enabled:
            return
        snd = self.sounds.get(sound_key)
        if snd:
            snd.play()

    def play_attack_sound(self, unit_type: str):
        """
        Determines the appropriate weapon sound for a given unit type and plays it.
        - Battleship, Cannon -> heavy battleship cannon
        - Tank, Destroyer -> medium tank cannon
        - Torpedo Boat -> torpedo
        - Foot Soldier, Engineer -> gunfire
        """
        if not unit_type:
            self.play_sound("gunfire")
            return

        if "Battleship" in unit_type or "Cannon" in unit_type:
            self.play_sound("battleship_cannon")
        elif "Tank" in unit_type or "Destroyer" in unit_type:
            self.play_sound("tank_cannon")
        elif "Torpedo" in unit_type:
            self.play_sound("torpedo")
        else:
            self.play_sound("gunfire")
