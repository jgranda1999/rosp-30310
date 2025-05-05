import React, { useState, useRef, useEffect } from 'react';
import AudioPlayer from './AudioPlayer';
import { Message } from '../types';
import { API_URL } from '../config';


interface ChatInterfaceProps {
  magistrateName: string;
  talkingPoints: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ magistrateName, talkingPoints = '' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Auto-scroll to the bottom of the messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Initialize AudioContext
  useEffect(() => {
    // Only create a new AudioContext if needed
    if (!audioContextRef.current) {
      try {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      } catch (error) {
        console.error('Error creating AudioContext:', error);
      }
    }
    
    // Cleanup function
    return () => {
      // Check the state of the AudioContext before closing
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        try {
          audioContextRef.current.close().catch(err => {
            console.warn('Error closing AudioContext:', err);
          });
        } catch (error) {
          console.warn('Error while trying to close AudioContext:', error);
        }
      }
      // Reset the reference
      audioContextRef.current = null;
    };
  }, []);

  // Add initial greeting message
  useEffect(() => {
    // Format talking points to appear on separate lines if they exist
    const formattedMessage = talkingPoints 
      ? `Os saludo, yo soy ${magistrateName}. ¿Sobre qué asunto deseáis conversar el día de hoy, vuestra merced?\n\n${talkingPoints}`
      : `Os saludo, yo soy ${magistrateName}. ¿Sobre qué asunto deseáis conversar el día de hoy, vuestra merced?`;
      
    const greeting: Message = {
      id: 'greeting',
      text: formattedMessage,
      sender: 'magistrate',
    };
    setMessages([greeting]);
  }, [magistrateName, talkingPoints]);

  // Convert WebM to WAV for better compatibility
  const convertToWav = async (audioBlob: Blob): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      try {
        // Create a file reader to read the blob
        const fileReader = new FileReader();
        fileReader.onloadend = async () => {
          try {
            // Create ArrayBuffer from the file reader result
            const arrayBuffer = fileReader.result as ArrayBuffer;
            
            // Get or create an audio context to decode the audio
            let audioContext = audioContextRef.current;
            
            if (!audioContext || audioContext.state === 'closed') {
              console.log("Creating new AudioContext for conversion");
              audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
              audioContextRef.current = audioContext;
            } else if (audioContext.state === 'suspended') {
              console.log("Resuming suspended AudioContext");
              await audioContext.resume();
            }
            
            // Decode the audio data
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            // Create a WAV blob from the audio buffer
            const wavBlob = await createWavBlobFromAudioBuffer(audioBuffer);
            resolve(wavBlob);
          } catch (error) {
            console.error('Error converting to WAV:', error);
            resolve(audioBlob); // Fall back to original blob
          }
        };
        
        fileReader.onerror = () => {
          console.error('Error reading audio file');
          resolve(audioBlob); // Fall back to original blob
        };
        
        fileReader.readAsArrayBuffer(audioBlob);
      } catch (error) {
        console.error('Error in convertToWav:', error);
        resolve(audioBlob); // Fall back to original blob
      }
    });
  };

  // Create a WAV blob from an audio buffer
  const createWavBlobFromAudioBuffer = async (audioBuffer: AudioBuffer): Promise<Blob> => {
    const numOfChannels = audioBuffer.numberOfChannels;
    const length = audioBuffer.length * numOfChannels * 2;
    const buffer = new ArrayBuffer(44 + length);
    const view = new DataView(buffer);
    
    // WAV header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, numOfChannels, true);
    view.setUint32(24, audioBuffer.sampleRate, true);
    view.setUint32(28, audioBuffer.sampleRate * numOfChannels * 2, true);
    view.setUint16(32, numOfChannels * 2, true);
    view.setUint16(34, 16, true); // 16 bits per sample
    writeString(view, 36, 'data');
    view.setUint32(40, length, true);

    // Audio data
    const offset = 44;
    let pos = 0;
    
    for (let channel = 0; channel < numOfChannels; channel++) {
      const channelData = new Float32Array(audioBuffer.length);
      audioBuffer.copyFromChannel(channelData, channel);
      
      for (let i = 0; i < channelData.length; i++) {
        // Convert float to int16
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        view.setInt16(pos + offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
        pos += 2;
      }
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  };

  // Helper function to write strings to DataView
  const writeString = (view: DataView, offset: number, string: string): void => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  const MAX_RETRIES = 3;
  const RETRY_DELAY = 1000; // 1 second

  const sendAudioWithRetry = async (formData: FormData, retryCount = 0): Promise<any> => {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // Increase timeout to 60s

        const response = await fetch(`${API_URL}/api/voice-chat`, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json',
            },
            mode: 'cors',
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();

    } catch (error: any) {
        if (retryCount < MAX_RETRIES) {
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryCount + 1))); // Exponential backoff
            return sendAudioWithRetry(formData, retryCount + 1);
        }
        throw error;
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        // Request high-quality audio with specific constraints for better transcription
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 24000,  // Match backend sample rate
            sampleSize: 16,
            channelCount: 1     // Mono channel for better compatibility
          } 
        });
        
        // Try to use a more compatible format if available
        const mimeType = MediaRecorder.isTypeSupported('audio/wav') 
          ? 'audio/wav' 
          : (MediaRecorder.isTypeSupported('audio/webm;codecs=pcm') 
            ? 'audio/webm;codecs=pcm' 
            : 'audio/webm');
            
        console.log(`Using MIME type: ${mimeType}`);
        
        const options = { 
          mimeType,
          audioBitsPerSecond: 128000  // Higher bitrate for better quality
        };
        
        const mediaRecorder = new MediaRecorder(stream, options);
        mediaRecorderRef.current = mediaRecorder;
        
        const audioChunks: BlobPart[] = [];
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };
        
        mediaRecorder.onstop = async () => {
          // Stop the media stream tracks
          stream.getTracks().forEach(track => track.stop());
          
          // Add the user message first to provide immediate feedback
          const userMessage: Message = {
            id: Date.now().toString(),
            text: "Enviando mensaje de voz...", 
            sender: 'user',
          };
          setMessages(prev => [...prev, userMessage]);
          setIsLoading(true);
          
          try {
            // Create a blob from the audio chunks
            let audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            console.log(`Original audio type: ${mediaRecorder.mimeType}, size: ${audioBlob.size}`);
            
            // Try to convert to WAV for better compatibility
            if (mediaRecorder.mimeType.includes('webm')) {
              try {
                audioBlob = await convertToWav(audioBlob);
                console.log(`Converted to WAV, new size: ${audioBlob.size}`);
              } catch (error) {
                console.error('Error converting to WAV:', error);
              }
            }
            
            // Create a FormData object to send the audio file
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('magistrate', magistrateName);
            
            // Add these debug logs before the fetch call
            console.log('Request URL:', `${API_URL}/api/voice-chat`);
            console.log('FormData contents:', {
              audio: `Blob size: ${audioBlob.size}, type: ${audioBlob.type}`,
              magistrate: magistrateName
            });
            
            const data = await sendAudioWithRetry(formData);
            
            if (data.error) {
              console.warn(`Server warning: ${data.error}`);
            }
            
            // Update the user message with the transcription if available
            if (data.transcription) {
              const updatedMessages = messages.map(msg => 
                msg.id === userMessage.id 
                  ? { ...msg, text: data.transcription } 
                  : msg
              );
              setMessages(updatedMessages);
            }
            
            // Add the magistrate's response
            const magistrateMessage: Message = {
              id: (Date.now() + 1).toString(),
              text: data.text || "Respuesta del magistrado", // Use server text if available
              sender: 'magistrate',
              audioUrl: data.audioUrl,
            };
            
            setMessages(prev => {
              // Find and update the user message
              const updatedPrev = prev.map(msg => 
                msg.id === userMessage.id && data.transcription
                  ? { ...msg, text: data.transcription }
                  : msg
              );
              // Add the magistrate message
              return [...updatedPrev, magistrateMessage];
            });
            
          } catch (error) {
            console.error('Error processing voice message:', error);
            // Add error message
            const errorMessage: Message = {
              id: Date.now().toString(),
              text: 'Lo siento, hubo un error procesando tu mensaje de voz. Por favor, intenta nuevamente.',
              sender: 'magistrate',
            };
            setMessages(prev => [...prev, errorMessage]);
          } finally {
            setIsLoading(false);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('No se pudo acceder al micrófono. Por favor, verifica los permisos.');
      }
    }
  };

  // Clean up all audio resources when component unmounts
  useEffect(() => {
    return () => {
      // Stop any ongoing recording
      if (mediaRecorderRef.current && isRecording) {
        try {
          mediaRecorderRef.current.stop();
          if (mediaRecorderRef.current.stream) {
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
          }
        } catch (error) {
          console.warn('Error stopping media recorder during cleanup:', error);
        }
      }
      
      // We already handle AudioContext cleanup in another useEffect
    };
  }, [isRecording]);

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`message ${message.sender}`}
          >
            <p>{message.text}</p>
            {message.audioUrl && (
              <AudioPlayer audioUrl={message.audioUrl} />
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message magistrate loading">
            <p>Procesando mensaje de voz...</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <button 
          onClick={toggleRecording}
          className={isRecording ? 'recording' : ''}
          disabled={isLoading}
          style={{ 
            width: '100%', 
            padding: '15px',
            backgroundColor: isRecording ? '#e74c3c' : '#3498db',
            border: 'none',
            borderRadius: '5px',
            color: 'white',
            fontWeight: 'bold',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isRecording ? '⏹️ Detener Grabación' : '🎙️ Iniciar Grabación'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;