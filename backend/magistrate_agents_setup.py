import asyncio
import random
import numpy as np
import sounddevice as sd
from typing import Dict, Any

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

@function_tool
def get_historical_context(period: str) -> str:
    """Get historical context for a given period."""
    contexts = {
        "16th Century": "Era of Spanish colonization in the Americas, establishment of the viceroyalties.",
        "17th Century": "Period of colonial consolidation, development of administrative systems.",
        "18th Century": "Bourbon Reforms period, modernization of colonial administration."
    }
    return contexts.get(period, "Historical context not available for this period.")

def create_magistrate_agent(magistrate_info: Dict[str, Any]) -> Agent:
    """Create a magistrate agent with the given information."""
    return Agent(
        name=magistrate_info['name'],
        handoff_description=f"A {magistrate_info['period']} Spanish colonial magistrate.",
        instructions=prompt_with_handoff_instructions(
            f"""You are {magistrate_info['name']}, a historical magistrate from {magistrate_info['period']}.
            Background: {magistrate_info['background']}
            
            Speak in formal Spanish appropriate for your era.
            Be authoritative but polite in your responses.
            Draw from your historical context and experience.
            """
        ),
        model="gpt-4-turbo-preview",
        tools=[get_historical_context]
    )

def create_voice_pipeline(magistrate_info: Dict[str, Any]) -> VoicePipeline:
    """Create a voice pipeline for a magistrate agent."""
    agent = create_magistrate_agent(magistrate_info)
    return VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(agent),
        tts_voice='onyx'  # Male Spanish voice
    )

async def process_voice_input(pipeline: VoicePipeline, audio_data: bytes) -> Dict[str, Any]:
    """Process voice input through the pipeline."""
    # Convert audio data to numpy array
    buffer = np.frombuffer(audio_data, dtype=np.int16)
    audio_input = AudioInput(buffer=buffer)

    # Run through pipeline
    result = await pipeline.run(audio_input)
    
    response = {
        'transcription': None,
        'response_text': None,
        'audio_data': None
    }

    # Create audio player
    player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
    player.start()

    # Process streaming results
    async for event in result.stream():
        if event.type == "voice_stream_event_transcription":
            response['transcription'] = event.text
        elif event.type == "voice_stream_event_audio":
            response['audio_data'] = event.data
            response['response_text'] = event.text
            # Play audio in real-time
            player.write(event.data)

    player.stop()
    return response

# Disable tracing for cleaner output
set_tracing_disabled(True) 