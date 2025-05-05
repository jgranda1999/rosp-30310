import asyncio
import numpy as np
import sounddevice as sd
import os
import tempfile
import wave
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
    VoicePipelineConfig,
    OpenAIVoiceModelProvider,
    STTModelSettings,
    TTSModelSettings,
)
from magistrado_agentes import MagistrateVoiceAgent
from openai import OpenAI

# Initialize OpenAI client for direct transcription debugging
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class VoiceMessageHandler:
    def __init__(self, magistrate_info=None):
        """
        Initialize the voice message handler.
        
        Args:
            magistrate_info: Dictionary containing magistrate information.
                If None, uses a default magistrate.
        """
        # Use a default magistrate if none is provided
        if magistrate_info is None:
            magistrate_info = {
                "name": "Gaspar de Espinosa",
                "description": "Oidor de la Real Audiencia de Santo Domingo",
                "period": "16th Century",
                "background": "Abogado, explorador, conquistador y oidor de la Real Audiencia de Santo Domingo.",
                "talkingPoints": "Experiencias en la administración de justicia colonial, exploración y conquista.",
                "language_settings": {
                    "language": "es",
                    "voice_language": "es"
                }
            }
        
        # Ensure language settings are present
        if "language_settings" not in magistrate_info:
            magistrate_info["language_settings"] = {
                "language": "es",
                "voice_language": "es"
            }
            
        print(f"Creating voice handler for {magistrate_info['name']}")
        self.voice_agent = MagistrateVoiceAgent(magistrate_info)
        
    async def process_voice_message(self, audio_data: np.ndarray) -> bytes:
        """
        Process a voice message through the pipeline
        
        Args:
            audio_data: numpy array containing the audio data
            
        Returns:
            bytes: The processed audio response
        """
        try:
            # Debug: First try to transcribe the input directly to see what we're receiving
            if audio_data is not None and len(audio_data) > 0:
                try:
                    # Save a temporary WAV file for direct transcription testing
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        wav_path = temp_wav.name
                        
                        # Write PCM data to WAV file
                        with wave.open(wav_path, 'wb') as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2)  # 16-bit
                            wf.setframerate(24000)
                            wf.writeframes(audio_data.tobytes())
                    
                    # Direct transcription for debugging
                    print(f"DEBUG: Direct transcription of input audio")
                    with open(wav_path, 'rb') as audio_file:
                        transcription = client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-1",
                            language="es"
                        )
                        print(f"DEBUG: Direct input transcription: '{transcription.text}'")
                    
                    # Clean up
                    os.unlink(wav_path)
                except Exception as e:
                    print(f"DEBUG: Error during direct transcription: {e}")
            
            # Process the audio using the voice agent
            print(f"Processing audio of length {len(audio_data) if audio_data is not None else 'None'}")
            result = await self.voice_agent.process_audio(audio_data.tobytes())
            
            # Check for errors in the result
            if 'error' in result:
                print(f"Error in voice processing: {result['error']}")
                return None
            
            # Get the audio data from the result
            if result['audio_data'] is not None:
                # Validate audio quality
                if np.abs(result['audio_data']).max() < 500:
                    print("WARNING: Response audio has very low amplitude")
                    # Normalize if very quiet but not silent
                    if np.abs(result['audio_data']).max() > 0:
                        scale_factor = min(32767 / np.abs(result['audio_data']).max() * 0.8, 5)
                        result['audio_data'] = (result['audio_data'].astype(np.float32) * scale_factor).astype(np.int16)
                        print(f"Audio normalized - new max amplitude: {np.abs(result['audio_data']).max()}")
                
                return result['audio_data'].tobytes()
            
            print("No audio data in result")
            return None
            
        except Exception as e:
            print(f"Error in voice message processing: {e}")
            return None

    @staticmethod
    def create_audio_player():
        """Create and return a sounddevice audio player"""
        return sd.OutputStream(
            samplerate=24000,
            channels=1,
            dtype=np.int16
        )

    @staticmethod
    def play_audio(player, audio_data):
        """Play audio data through the given player"""
        if audio_data is not None:
            try:
                player.write(audio_data)
            except Exception as e:
                print(f"Error playing audio: {e}") 