import os
import tempfile
import wave
import numpy as np
import sounddevice as sd
from openai import OpenAI
from typing import Optional, Dict, Any

class OpenAIVoiceHandler:
    def __init__(self, magistrate_info: Dict[str, Any]):
        """
        Initialize the OpenAI voice handler.
        
        Args:
            magistrate_info: Dictionary containing magistrate information
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.magistrate_info = magistrate_info
        self.sample_rate = 24000  # Default sample rate
        self.channels = 1
        
    def transcribe_audio(self, audio_data: np.ndarray, input_sample_rate: int = None) -> Optional[str]:
        """
        Transcribe audio data using OpenAI's Whisper model.
        
        Args:
            audio_data: numpy array containing the audio data
            input_sample_rate: sample rate of the input audio (Hz)
            
        Returns:
            str: Transcribed text or None if transcription failed
        """
        try:
            # Use the provided sample rate if available, otherwise use default
            sample_rate = input_sample_rate if input_sample_rate else self.sample_rate
            
            # Resample audio if the input sample rate is different from what OpenAI expects
            if input_sample_rate and input_sample_rate != self.sample_rate:
                # Try librosa first
                try:
                    from scipy import signal
                    
                    # Calculate the resampling ratio
                    ratio = self.sample_rate / input_sample_rate
                    
                    # Convert to float for processing
                    float_audio = audio_data.astype(np.float32) / 32768.0
                    
                    # Resample using scipy's resample function
                    resampled_length = int(len(float_audio) * ratio)
                    resampled_audio = signal.resample(float_audio, resampled_length)
                    
                    # Convert back to int16
                    audio_data = (resampled_audio * 32768).astype(np.int16)
                    sample_rate = self.sample_rate
                    print(f"Resampling with scipy complete. New audio length: {len(audio_data)}")
                
                # If all resampling fails, use original audio
                except Exception as e2:
                    print(f"Error during scipy resampling: {e2}. Using original audio.")
            
            # Save audio data to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                wav_path = temp_wav.name
                
                with wave.open(wav_path, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                # Transcribe using OpenAI's API
                with open(wav_path, 'rb') as audio_file:
                    try:
                        print("Transcribing with gpt-4o-transcribe")
                        print(f"Audio file: {wav_path}, Sample rate: {sample_rate}Hz")
                        
                        # Try with gpt-4o-transcribe for better quality
                        transcription = self.client.audio.transcriptions.create(
                            file=audio_file,
                            model="gpt-4o-transcribe",
                            language="es",
                            temperature=0.0
                        )
                    except Exception as e:
                        print(f"Error with gpt-4o-transcribe, falling back to whisper-1: {e}")
                        # If the gpt-4o-transcribe model isn't available, fall back to whisper-1
                        # Reopen the file since it was consumed in the previous attempt
                        audio_file.seek(0)
                        transcription = self.client.audio.transcriptions.create(
                            file=audio_file,
                            model="whisper-1",
                            language="es",
                            temperature=0.0  # Use 0 temperature for more deterministic results
                        )
                    
                # Clean up temporary file
                os.unlink(wav_path)
                
                # Print the transcription for debugging
                print(f"Raw transcription: {transcription.text}")
                
                return transcription.text
                
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
            
    def generate_response(self, transcribed_text: str) -> Optional[str]:
        """
        Generate a text response using the magistrate's persona.
        
        Args:
            transcribed_text: The transcribed user input
            
        Returns:
            str: Generated response text or None if generation failed
        """
        try:
            # Prepare the system message with the magistrate's persona
            system_message = self.magistrate_info.get('persona', '')
            if 'context_instructions' in self.magistrate_info:
                system_message += "\n" + self.magistrate_info['context_instructions']
                print(f"System message: {system_message}")
            
            # Generate response using chat completion
            response = self.client.chat.completions.create(
                model="gpt-4",  # or another appropriate model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": transcribed_text}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error during response generation: {e}")
            return None
            
    def synthesize_speech(self, text: str) -> Optional[np.ndarray]:
        """
        Convert text to speech using OpenAI's TTS model.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            numpy.ndarray: Audio data as a numpy array or None if synthesis failed
        """
        try:
            # Generate speech using OpenAI's API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input=text
            )
            
            # Save to temporary file and read as numpy array
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                temp_mp3.write(response.content)
                temp_mp3.flush()
                
                # Read the audio file
                import soundfile as sf
                audio_data, _ = sf.read(temp_mp3.name)
                
                # Convert to int16
                audio_data = (audio_data * 32767).astype(np.int16)
                
                # Clean up temporary file
                os.unlink(temp_mp3.name)
                
                return audio_data
                
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            return None
            
    async def process_audio(self, audio_data: np.ndarray, input_sample_rate: int = None) -> Dict[str, Any]:
        """
        Process audio through the complete pipeline: STT -> Response Generation -> TTS
        
        Args:
            audio_data: numpy array containing the audio data
            input_sample_rate: sample rate of the input audio (Hz)
            
        Returns:
            dict: Dictionary containing the results and any audio data
        """
        try:
            # Transcribe audio
            transcribed_text = self.transcribe_audio(audio_data, input_sample_rate)
            if not transcribed_text:
                return {'error': 'Failed to transcribe audio'}
                
            print(f"Transcribed text: {transcribed_text}")
            
            # Generate response
            response_text = self.generate_response(transcribed_text)
            if not response_text:
                return {'error': 'Failed to generate response'}
                
            print(f"Generated response: {response_text}")
            
            # Synthesize speech
            audio_response = self.synthesize_speech(response_text)
            if audio_response is None:
                return {'error': 'Failed to synthesize speech'}
                
            return {
                'transcribed_text': transcribed_text,
                'response_text': response_text,
                'audio_data': audio_response
            }
            
        except Exception as e:
            print(f"Error in audio processing pipeline: {e}")
            return {'error': str(e)} 