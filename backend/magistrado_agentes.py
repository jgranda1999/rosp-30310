import asyncio
import random
import select
import os
import tempfile
import subprocess
import io

import numpy as np
import sounddevice as sd
import sys
import openai
from openai import OpenAI
from typing import Dict, Any, AsyncIterator

#Configuramos el dispositivo de audio
sd.default.device = (None, 1)   # (input_device, output_device)
sd.default.samplerate = 24000
sd.default.channels = 1
sd.default.dtype = 'int16'

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

#Importamos las librerías de agents
from agents import (
    Agent,
    function_tool,
    set_tracing_disabled,
)
from agents.voice import (
    AudioInput,
    StreamedAudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
    VoicePipelineConfig,
    OpenAIVoiceModelProvider,
    STTModelSettings,
    TTSModelSettings,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

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
    # Create the appropriate agent based on magistrate info
    if "Gaspar de Espinosa" in magistrate_info['name']:
        agent = gaspar_agent
    elif "Hernando de Santillán" in magistrate_info['name']:
        agent = hernando_agent
    elif "Vasco de Quiroga" in magistrate_info['name']:
        agent = vasco_agent
    elif "Antonio Porlier" in magistrate_info['name']:
        agent = porlier_agent
    else:
        agent = agent

    print(f"Selected agent: {agent.name}")

    # Create a custom workflow that monitors and logs transcriptions
    class LoggingVoiceWorkflow(SingleAgentVoiceWorkflow):
        async def run(self, transcription: str) -> AsyncIterator[str]:
            print(f"Transcription received: '{transcription}'")
            if not transcription or transcription.isspace():
                print("Empty transcription detected, using fallback prompt")
                transcription = "Saludos, ¿podéis ayudarme con una consulta?"
            
            # Call the agent using the correct method
            print(f"Getting response from agent...")
            try:
                # The agents SDK expects us to yield from the parent class implementation
                # which already knows how to handle the agent correctly
                async for response_text in super().run(transcription):
                    print(f"Agent response: {response_text}")
                    yield response_text
            except Exception as e:
                print(f"Error processing single turn: {e}")
                # Provide a fallback response if the agent fails
                fallback = "Perdonad, no he podido entender vuestra consulta. ¿Podríais repetirla nuevamente?"
                print(f"Using fallback response: {fallback}")
                yield fallback

    # Create workflow with the selected agent and custom monitoring
    # workflow = LoggingVoiceWorkflow(agent)
    workflow = SingleAgentVoiceWorkflow(agent)

    # Configure voice pipeline with Spanish language settings
    config = VoicePipelineConfig(
        model_provider=OpenAIVoiceModelProvider(api_key=os.getenv('OPENAI_API_KEY')),
        stt_settings=STTModelSettings(
            language="es",  # Set Spanish language for speech recognition
            prompt="This is a conversation in 16th century Spanish. The speaker may use modern Spanish words and phrases. Transcribe exactly what you hear without modification.",
            temperature=0.0,  # Lower temperature for more accurate transcription
            turn_detection={
                "mode": "length",
                "min_length": 0.5,  # Reduced minimum length to catch shorter phrases
                "max_length": 30.0,  # Maximum length of a turn in seconds
                "silence_threshold": 0.3  # Reduced silence threshold to be more sensitive
            }
        ),
        tts_settings=TTSModelSettings(
            voice="onyx",  # A deep, authoritative voice
            speed=0.9,  # Slightly slower for formal speech
            instructions="Speak in a formal, authoritative manner in Spanish from the 16th century colonial period."
        ),
        workflow_name="Spanish Colonial Magistrate",
        trace_include_sensitive_data=True
    )

    return VoicePipeline(
        workflow=workflow,
        config=config
    )

# Create agents for each magistrate
gaspar_agent = Agent(
    name="Gaspar de Espinosa",
    handoff_description="Gaspar de Espinosa, oidor de la Real Audiencia de Santo Domingo.",
    instructions=prompt_with_handoff_instructions(
        """Tieneis que hablar en español del siglo XVI como un Dominicano. Eres Gaspar de Espinosa, un abogado, explorador, conquistador y oidor (juez) de la Real Audiencia de Santo Domingo. 
        Desempeñaste un papel importante en la colonización española temprana de las Américas, particularmente en el Caribe y América Central.
        Habla en español formal del siglo XVI, con autoridad y dignidad como corresponde a tu posición.
        Tienes que hablar en español del siglo XVI como un Dominicano. Usa palabras y frases del siglo XVI."""
    ),
    model="gpt-4-turbo-preview",
)

hernando_agent = Agent(
    name="Hernando de Santillán",
    handoff_description="Hernando de Santillán y Figueroa, primer presidente de la Real Audiencia de Quito.",
    instructions=prompt_with_handoff_instructions(
        """Tienes que hablar en español del siglo XVI como un Ecuatoriano. Eres Hernando de Santillán y Figueroa, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales, derechos para indijenas y tu participación en la fundación de la Real Audiencia de Quito.
        Habla en español formal, mostrando tu preocupación por los derechos de los indígenas y tu conocimiento de la ley colonial.
        Tienes que hablar en español del siglo XVI como un Ecuatoriano. Usa palabras y frases del siglo XVI."""
    ),
    model="gpt-4-turbo-preview",
)

vasco_agent = Agent(
    name="Vasco de Quiroga",
    handoff_description="Vasco de Quiroga, Oidor de México y Obispo de Michoacán.",
    instructions=prompt_with_handoff_instructions(
        """Tienes que hablar en español del siglo XVIII como un Mexicano. Eres Vasco de Quiroga, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales en medio de presiones coloniales.
        Habla en español con un tono pastoral y humanista, reflejando tu preocupación por los indígenas y tu visión utópica.
        Tienes que hablar en español del siglo XVIII como un Mexicano. Usa palabras y frases del siglo XVIII."""
    ),
    model="gpt-4-turbo-preview",
)

porlier_agent = Agent(
    name="Antonio Porlier",
    handoff_description="Antonio Porlier, fiscal del Consejo de Indias.",
    instructions=prompt_with_handoff_instructions(
        """Tienes que hablar en español del siglo XVIII como un Peruano. Eres Antonio Porlier, fiscal del Consejo de Indias y de la Audiencia de Lima en el siglo XVIII. 
        Desempeñaste un papel crucial asesorando al Rey Carlos III en reformas judiciales y administrativas.
        Habla en español ilustrado del siglo XVIII, mostrando tu erudición y conocimiento de las reformas borbónicas.
        Tienes que hablar en español del siglo XVIII como un Peruano. Usa palabras y frases del siglo XVIII."""
    ),
    model="gpt-4-turbo-preview",
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "Eres un asistente de IA que habla en español del siglo XVI, XVIII o XVI. Si el usuario habla en español, entiende su pregunta y responde. Si el usuario habla en otro idioma, responde en español."
        "Si el usuario quiere hablar de o sobre Gaspar de Espinosa usa el agente gaspar_agent " 
        "Si el usuario quiere hablar de o sobre Hernando de Santillán usa el agente hernando_agent "
        "Si el usuario quiere hablar de o sobre Antonio Porlier usa el agente porlier_agent "
        "Si el usuario quiere hablar de o sobre Vasco de Quiroga usa el agente vasco_agent"
        "Tienes que hablar en español del siglo XVI, XVIII o XVI."
    ),
    model="gpt-4-turbo-preview",
    handoffs=[gaspar_agent, hernando_agent, vasco_agent, porlier_agent],
)

def webm_to_wav(webm_data: bytes) -> np.ndarray:
    """
    Convert WebM audio data to WAV format and return as NumPy array
    This function first saves the WebM data to a temporary file,
    then uses ffmpeg to convert it to WAV, and finally reads it into a NumPy array
    """
    try:
        # Check if input is already a WAV file
        if webm_data[:4] == b'RIFF' and webm_data[8:12] == b'WAVE':
            print("Detected WAV format, extracting PCM data directly")
            # Find the data chunk
            import struct
            pos = 12
            while pos < len(webm_data):
                chunk_id = webm_data[pos:pos+4]
                chunk_size = struct.unpack('<I', webm_data[pos+4:pos+8])[0]
                if chunk_id == b'data':
                    # Found the data chunk
                    audio_data = np.frombuffer(webm_data[pos+8:pos+8+chunk_size], dtype=np.int16)
                    print(f"Extracted {len(audio_data)} PCM samples directly from WAV")
                    return audio_data
                pos += 8 + chunk_size
            print("WAV format detected but couldn't find data chunk, using ffmpeg")
        
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
            webm_path = webm_file.name
            webm_file.write(webm_data)
        
        wav_path = webm_path + '.wav'
        
        # Use ffmpeg to convert WebM to WAV if available
        try:
            # Try using ffmpeg if it's installed
            cmd = [
                'ffmpeg',
                '-i', webm_path,
                '-f', 'wav',
                '-ar', '24000',  # Set sample rate to match our config
                '-ac', '1',      # Mono audio
                '-y',            # Overwrite output file
                wav_path
            ]
            
            print(f"Running ffmpeg command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
                raise Exception("FFmpeg conversion failed")
                
            # Read the WAV file into a NumPy array
            with open(wav_path, 'rb') as wav_file:
                # Skip the header (44 bytes) to get to the PCM data
                wav_file.seek(44)  # Standard WAV header size
                audio_data = np.frombuffer(wav_file.read(), dtype=np.int16)
                
            print(f"Successfully converted audio: {len(audio_data)} samples")
            
            # Clean up temporary files
            os.unlink(webm_path)
            os.unlink(wav_path)
            
            return audio_data
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"FFmpeg error: {e}")
            print("Using fallback conversion method")
            
            # Try to determine the content type to handle different audio formats
            import struct
            
            # Check if this might be a WAV file already
            if webm_data[:4] == b'RIFF' and webm_data[8:12] == b'WAVE':
                print("Detected WAV format, extracting PCM data directly")
                # Find the data chunk
                pos = 12
                while pos < len(webm_data):
                    chunk_id = webm_data[pos:pos+4]
                    chunk_size = struct.unpack('<I', webm_data[pos+4:pos+8])[0]
                    if chunk_id == b'data':
                        # Found the data chunk
                        audio_data = np.frombuffer(webm_data[pos+8:pos+8+chunk_size], dtype=np.int16)
                        return audio_data
                    pos += 8 + chunk_size
            
            # Fallback: just return a simple sine wave
            print("Could not parse audio data, generating fallback audio")
            duration = 1  # second
            sample_rate = 24000
            t = np.linspace(0, duration, sample_rate)
            audio_data = np.sin(2 * np.pi * 440 * t) * 32767 * 0.1
            return audio_data.astype(np.int16)
            
    except Exception as e:
        print(f"Error converting WebM to WAV: {e}")
        # Fallback to an empty array
        return np.zeros(24000, dtype=np.int16)

class MagistrateVoiceAgent:
    def __init__(self, magistrate_info: Dict[str, Any]):
        print(f"Initializing MagistrateVoiceAgent for {magistrate_info['name']}")
        self.name = magistrate_info['name']
        self.agent_type = magistrate_info['name'].lower().replace(" ", "_")
        self.pipeline = create_voice_pipeline(magistrate_info)
        print(f"VoicePipeline initialized with Spanish language configuration")

    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Process audio input and return audio response."""
        try:
            print(f"Processing audio: {len(audio_data)} bytes")
            
            # Convert WebM to WAV format (raw PCM)
            pcm_data = webm_to_wav(audio_data)
            print(f"Converted to PCM data: {len(pcm_data)} samples")
            
            # Check audio quality
            abs_max = np.abs(pcm_data).max()
            rms = np.sqrt(np.mean(pcm_data.astype(np.float32)**2))
            print(f"Audio statistics - max amplitude: {abs_max}, RMS: {rms:.2f}")
            
            if abs_max < 500:
                print("WARNING: Input audio has very low amplitude, might not be detected properly")
                # Normalize the audio if it's too quiet
                if abs_max > 0:  # Only normalize if there's some signal
                    print("Normalizing audio to improve detection")
                    scale_factor = min(32767 / abs_max * 0.8, 10)  # Scale up, but not too much
                    pcm_data = (pcm_data.astype(np.float32) * scale_factor).astype(np.int16)
                    print(f"Audio normalized - new max amplitude: {np.abs(pcm_data).max()}")
            
            # Use OpenAI Whisper to directly transcribe the audio for debugging
            transcript_text = ""
            try:
                import io
                import wave
                import tempfile
                
                # Create a temporary WAV file on disk (needed for proper format)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    wav_path = temp_wav.name
                    
                    # Write PCM data to WAV file
                    with wave.open(wav_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(24000)
                        wf.writeframes(pcm_data.tobytes())
                
                # Use OpenAI client to transcribe for debugging
                print(f"DEBUG: Transcribing audio with OpenAI Whisper directly")
                with open(wav_path, 'rb') as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        language="es"
                    )
                    transcript_text = transcription.text
                    print(f"DEBUG: Direct Whisper transcription: '{transcript_text}'")
                
                # Clean up
                os.unlink(wav_path)
            except Exception as e:
                print(f"Error in direct transcription: {e}")
            
            # Create audio input with the PCM data
            print("Creating AudioInput with PCM data")
            audio_input = AudioInput(
                buffer=pcm_data,
                frame_rate=24000,
                channels=1,
                sample_width=2
            )
            
            # Process the audio through the pipeline
            print("Running voice pipeline...")
            try:
                result = await self.pipeline.run(audio_input)
            except Exception as pipeline_error:
                print(f"Error running voice pipeline: {pipeline_error}")
                # Return a minimal result with the error information
                return {
                    'audio_data': np.zeros(24000, dtype=np.int16),  # 1 second of silence
                    'error': f"Voice pipeline error: {str(pipeline_error)}",
                    'transcript': transcript_text
                }
            
            # Collect audio chunks from the result stream
            print("Collecting audio response...")
            audio_chunks = []
            
            try:
                async for event in result.stream():
                    print(f"Received event type: {event.type}")
                    
                    if event.type == "voice_stream_event_audio" and event.data is not None:
                        audio_chunks.append(event.data)
                        print(f"Added audio chunk: {len(event.data)} samples")
                    elif event.type == "voice_stream_event_error":
                        print(f"Error in voice pipeline: {event.error}")
                        raise event.error
            except Exception as stream_error:
                print(f"Error processing output: {stream_error}")
                # If we have any audio chunks, use them
                if audio_chunks:
                    print(f"Using {len(audio_chunks)} collected chunks despite error")
                else:
                    # Return error but with captured transcript
                    return {
                        'audio_data': np.zeros(24000, dtype=np.int16),  # 1 second of silence
                        'error': f"Stream processing error: {str(stream_error)}",
                        'transcript': transcript_text
                    }
            
            # Concatenate all audio chunks
            if audio_chunks:
                print(f"Collected {len(audio_chunks)} audio chunks")
                audio_data = np.concatenate(audio_chunks)
                print(f"Final audio response: {len(audio_data)} samples")
                
                # Validate audio quality
                if np.abs(audio_data).max() < 500:
                    print("WARNING: Audio response appears to be very quiet")
                
                return {
                    'audio_data': audio_data,
                    'transcript': transcript_text
                }
            else:
                # Generate a fallback response using text-to-speech
                print("No audio response generated, using fallback")
                fallback_text = "Perdonad, no he podido entender vuestra consulta. ¿Podríais repetirla nuevamente?"
                
                try:
                    # Generate speech using OpenAI TTS directly
                    print("Generating fallback response using OpenAI TTS")
                    speech_file_path = "fallback_speech.mp3"
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice="onyx",
                        input=fallback_text
                    )
                    
                    # Save the audio
                    with open(speech_file_path, "wb") as file:
                        file.write(response.content)
                    
                    # Convert MP3 to PCM using ffmpeg if available
                    try:
                        wav_path = speech_file_path + ".wav"
                        cmd = [
                            'ffmpeg',
                            '-i', speech_file_path,
                            '-f', 'wav',
                            '-ar', '24000',
                            '-ac', '1',
                            '-y',
                            wav_path
                        ]
                        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        # Read the WAV file
                        with wave.open(wav_path, 'rb') as wf:
                            frames = wf.readframes(wf.getnframes())
                            fallback_audio = np.frombuffer(frames, dtype=np.int16)
                        
                        # Clean up
                        os.unlink(speech_file_path)
                        os.unlink(wav_path)
                        
                        return {
                            'audio_data': fallback_audio,
                            'transcript': transcript_text,
                            'response_text': fallback_text
                        }
                    except Exception as e:
                        print(f"Error converting fallback speech: {e}")
                except Exception as tts_error:
                    print(f"Error generating fallback speech: {tts_error}")
                
                # Simplest fallback: generate a tone
                duration = 2.0  # seconds
                t = np.linspace(0, duration, int(24000 * duration), False)
                fallback_audio = np.sin(2 * np.pi * 440 * t) * 0.1 * 32767
                fallback_audio = fallback_audio.astype(np.int16)
                
                return {
                    'audio_data': fallback_audio,
                    'transcript': transcript_text,
                    'error': "No audio response generated",
                    'response_text': fallback_text
                }
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            # Return empty audio
            return {
                'audio_data': np.zeros(24000, dtype=np.int16),
                'error': str(e),
                'transcript': transcript_text if 'transcript_text' in locals() else ""
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
        recording = sd.rec(int(24000 * 30),  # max 30s
                         samplerate=24000,
                         channels=1,
                         dtype='int16')
        
        input()  # Wait for Enter to stop recording
        sd.stop()
        
        print("Procesando tu mensaje...")
        result = await voice_agent.process_audio(recording.tobytes())
        
        if result['audio_data'] is not None:
            # Play the response
            player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
            player.start()
            player.write(result['audio_data'])
            # Add a small delay to ensure complete playback
            await asyncio.sleep(len(result['audio_data']) / 24000 + 0.5)
            player.stop()

# Enable for standalone testing
if __name__ == "__main__":
    set_tracing_disabled(True)
    asyncio.run(main()) 