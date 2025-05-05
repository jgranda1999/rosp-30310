import asyncio
import numpy as np
import random
from typing import Optional, Dict, Any, List, Callable
import os
import openai
import json
from gtts import gTTS
import speech_recognition as sr
import io
import wave
import tempfile
import sounddevice as sd
import time

from openai import OpenAI
from agents import (
    Agent,
    function_tool,
    set_tracing_disabled,
)
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# Mock implementation of sounddevice
class MockSoundDevice:
    """Mock implementation for sounddevice to avoid dependency issues."""
    default = type('obj', (object,), {
        'device': (None, 1),
        'samplerate': 24000,
        'channels': 1,
        'dtype': 'int16'
    })
    
    class OutputStream:
        def __init__(self):
            self.callback = None
        
        def start(self):
            print("[Mock] Audio player started")
        
        def stop(self):
            print("[Mock] Audio player stopped")
        
        def write(self, data):
            print(f"[Mock] Audio data written: {len(data)} samples")
    
    @staticmethod
    def rec(frames, samplerate=None, channels=None, dtype=None):
        """Record audio (mock)"""
        print(f"[Mock] Recording {frames} frames of audio")
        return np.zeros((frames, 1), dtype=np.int16)
    
    @staticmethod
    def stop():
        """Stop recording (mock)"""
        print("[Mock] Recording stopped")

# Use our mock implementation
sd = MockSoundDevice()

client = OpenAI()

# Configure audio device
sd.default.device = (None, 1)   # (input_device, output_device)
sd.default.samplerate = 24000
sd.default.channels = 1
sd.default.dtype = 'int16'
SAMPLE_RATE = 24000

@function_tool
def get_historical_context(period: str) -> str:
    """Get historical context for a given period."""
    contexts = {
        "16th Century": "Era de la colonización española en las Américas, establecimiento de los virreinatos y audiencias.",
        "17th Century": "Período de consolidación colonial, desarrollo de sistemas administrativos y judiciales.",
        "18th Century": "Período de las Reformas Borbónicas, modernización de la administración colonial."
    }
    return contexts.get(period, "Contexto histórico no disponible para este período.")

def create_voice_pipeline(magistrate_info: Dict[str, Any]) -> VoicePipeline:
    """Create a voice pipeline for a magistrate agent."""
    agent = create_magistrate_agent(magistrate_info)
    return VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(agent)
            )

class MagistrateVoiceAgent:
    def __init__(self, magistrate_info: Dict[str, Any]):
        self.agent = Agent(
            name=magistrate_info['name'],
            handoff_description=f"{magistrate_info['name']}, {magistrate_info['description']}",
            instructions=prompt_with_handoff_instructions(
                f"""Eres {magistrate_info['name']}, {magistrate_info['description']}.
                
                Trasfondo histórico: {magistrate_info['background']}
                Período: {magistrate_info['period']}
                
                Instrucciones específicas:
                1. Habla en español formal de tu época ({magistrate_info['period']})
                2. Mantén la dignidad y autoridad propias de tu cargo
                3. Utiliza referencias históricas de tu período
                4. Responde basándote en tu experiencia como magistrado
                5. Mantén el estilo lingüístico de tu época
                
                Puntos de conversación principales:
                {magistrate_info['talkingPoints']}
                """
            ),
            model="gpt-4-turbo-preview",
            tools=[get_historical_context]
        )
        
        self.pipeline = VoicePipeline(
            workflow=SingleAgentVoiceWorkflow(self.agent)
        )

    async def collect_audio_stream(self, result) -> np.ndarray:
        """Collect and concatenate all audio data from the stream."""
        audio_chunks = []
        
        async for event in result.stream():
            if event.type == "voice_stream_event_audio" and event.data is not None:
                audio_chunks.append(event.data)
                # Add a small delay to ensure we get the complete stream
                await asyncio.sleep(0.01)
        
        # Concatenate all audio chunks
        if audio_chunks:
            return np.concatenate(audio_chunks)
        return np.zeros(SAMPLE_RATE, dtype=np.int16)  # 1 second of silence if no audio

    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Process audio input and return audio response."""
        try:
            # Convert audio data to numpy array
            buffer = np.frombuffer(audio_data, dtype=np.int16)
            audio_input = AudioInput(buffer=buffer)

            # Run through pipeline
            result = await self.pipeline.run(audio_input)
            
            # Collect complete audio stream
            audio_data = await self.collect_audio_stream(result)
            
            return {
                'audio_data': audio_data
            }
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return {
                'audio_data': np.zeros(SAMPLE_RATE, dtype=np.int16)  # Empty audio
            }

    async def process_text(self, text: str) -> Dict[str, Any]:
        """Process text input and return audio response."""
        try:
            # Create silent audio for text-only input
            buffer = np.zeros(SAMPLE_RATE, dtype=np.int16)  # 1 second of silence
            audio_input = AudioInput(buffer=buffer)

            # Run through pipeline
            result = await self.pipeline.run(audio_input)
            
            # Collect complete audio stream
            audio_data = await self.collect_audio_stream(result)
            
            return {
                'audio_data': audio_data
            }
            
        except Exception as e:
            print(f"Error processing text: {e}")
            return {
                'audio_data': np.zeros(SAMPLE_RATE, dtype=np.int16)  # Empty audio
            }

# Example usage in a standalone context
async def main():
    # Example magistrate info
    magistrate_info = {
        "name": "Gaspar de Espinosa",
        "description": "Oidor de la Real Audiencia de Santo Domingo",
        "period": "16th Century",
        "background": "Abogado, explorador, conquistador y oidor de la Real Audiencia de Santo Domingo.",
        "talkingPoints": "Experiencias en la administración de justicia colonial, exploración y conquista."
    }
    
    # Create voice agent
    voice_agent = MagistrateVoiceAgent(magistrate_info)
    
    # Example recording and playback loop
    while True:
        input("Presiona Enter para comenzar a hablar...")
        print("Grabando... presiona Enter nuevamente para detener.")
        
        # Record audio
        recording = sd.rec(int(SAMPLE_RATE * 30),  # max 30s
                         samplerate=SAMPLE_RATE,
                         channels=1,
                         dtype='int16')
        
        input()  # Wait for Enter to stop recording
        sd.stop()
        
        print("Procesando tu mensaje...")
        result = await voice_agent.process_audio(recording.tobytes())
        
        if result['audio_data'] is not None:
            # Play the response
            player = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype=np.int16)
            player.start()
            player.write(result['audio_data'])
            # Add a small delay to ensure complete playback
            await asyncio.sleep(len(result['audio_data']) / SAMPLE_RATE + 0.5)
            player.stop()

# Enable for standalone testing
if __name__ == "__main__":
    set_tracing_disabled(True)
    asyncio.run(main()) 