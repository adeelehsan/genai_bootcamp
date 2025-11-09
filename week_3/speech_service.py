"""
Speech Service - Handles speech-to-text and text-to-speech

This module provides:
- Speech-to-text using OpenAI Whisper API
- Text-to-speech using ElevenLabs API
"""

import io
import tempfile
from typing import Optional
from openai import OpenAI
from elevenlabs import ElevenLabs
from elevenlabs import VoiceSettings


class SpeechService:
    """
    Service for handling speech-to-text and text-to-speech operations.

    Features:
    - Transcribe audio using OpenAI Whisper
    - Generate speech using ElevenLabs
    - Support for multiple voices
    """

    def __init__(
        self,
        openai_api_key: str,
        elevenlabs_api_key: Optional[str] = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel voice
    ):
        """
        Initialize the speech service.

        Args:
            openai_api_key: OpenAI API key for Whisper transcription
            elevenlabs_api_key: ElevenLabs API key for TTS
            voice_id: ElevenLabs voice ID (default: Rachel)
        """
        if not openai_api_key:
            raise ValueError("OpenAI API key is required for speech-to-text")

        self.openai_client = OpenAI(api_key=openai_api_key)
        self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key) if elevenlabs_api_key else None
        self.voice_id = voice_id

    def transcribe_audio(self, audio_bytes: bytes, file_format: str = "wav") -> Optional[str]:
        """
        Transcribe audio to text using OpenAI Whisper.

        Args:
            audio_bytes: Audio data as bytes
            file_format: Audio file format (default: "wav")

        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio.flush()

                # Open the file and transcribe
                with open(temp_audio.name, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )

                return transcript

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None

    def generate_speech(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Optional[bytes]:
        """
        Generate speech from text using ElevenLabs.

        Args:
            text: Text to convert to speech
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity boost (0.0-1.0)

        Returns:
            Audio data as bytes or None if generation fails
        """
        if not self.elevenlabs_client:
            print("ElevenLabs API key not configured")
            return None

        try:
            # Generate audio using ElevenLabs
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost
                )
            )

            # Collect audio bytes
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk

            return audio_bytes

        except Exception as e:
            print(f"Error generating speech: {e}")
            return None

    def get_available_voices(self) -> list:
        """
        Get list of available ElevenLabs voices.

        Returns:
            List of voice dictionaries with 'voice_id' and 'name'
        """
        if not self.elevenlabs_client:
            return []

        try:
            voices = self.elevenlabs_client.voices.get_all()
            return [
                {"voice_id": voice.voice_id, "name": voice.name}
                for voice in voices.voices
            ]
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
