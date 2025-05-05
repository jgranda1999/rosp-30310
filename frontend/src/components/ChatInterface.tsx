import React, { useState, useRef, useEffect } from 'react';
import AudioPlayer from './AudioPlayer';
import { Message } from '../types';

interface ChatInterfaceProps {
  magistrateName: string;
  talkingPoints: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ magistrateName, talkingPoints = '' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to the bottom of the messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          magistrate: magistrateName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from magistrate');
      }

      const data = await response.json();
      
      const magistrateMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.text,
        sender: 'magistrate',
        audioUrl: data.audioUrl,
      };

      setMessages(prev => [...prev, magistrateMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'I apologize, but I am unable to respond at the moment. Please try again later.',
        sender: 'magistrate',
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const options = { mimeType: 'audio/webm' };
        const mediaRecorder = new MediaRecorder(stream, options);
        mediaRecorderRef.current = mediaRecorder;
        
        const audioChunks: BlobPart[] = [];
        
        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
          // Create a simpler text message for now since we're having audio issues
          setInput('Mensaje de prueba desde la interfaz de voz');
          handleSendMessage();
          
          // The code below is commented out until we resolve the audio issues
          /*
          // Create blob in webm format
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          
          // Create a FormData object to send the audio file
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          formData.append('magistrate', magistrateName);
          
          setIsLoading(true);
          
          try {
            const response = await fetch('/api/voice-chat', {
              method: 'POST',
              body: formData,
            });

            if (!response.ok) {
              throw new Error('Failed to process voice message');
            }

            const data = await response.json();
            
            // Add the transcribed user message
            const userMessage: Message = {
              id: Date.now().toString(),
              text: data.transcription,
              sender: 'user',
            };
            
            // Add the magistrate's response
            const magistrateMessage: Message = {
              id: (Date.now() + 1).toString(),
              text: data.text,
              sender: 'magistrate',
              audioUrl: data.audioUrl,
            };
            
            setMessages(prev => [...prev, userMessage, magistrateMessage]);
            
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
          */
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('No se pudo acceder al micrófono. Por favor, verifica los permisos.');
      }
    }
  };

  // Helper function to convert AudioBuffer to WAV format
  const convertToWav = async (audioBuffer: AudioBuffer): Promise<Blob> => {
    const numOfChannels = audioBuffer.numberOfChannels;
    const length = audioBuffer.length * numOfChannels * 2;
    const buffer = new ArrayBuffer(44 + length);
    const view = new DataView(buffer);
    
    // Write WAV header
    // "RIFF" identifier
    writeString(view, 0, 'RIFF');
    // File size
    view.setUint32(4, 36 + length, true);
    // "WAVE" identifier
    writeString(view, 8, 'WAVE');
    // "fmt " chunk identifier
    writeString(view, 12, 'fmt ');
    // Chunk length
    view.setUint32(16, 16, true);
    // Sample format (1 is PCM)
    view.setUint16(20, 1, true);
    // Number of channels
    view.setUint16(22, numOfChannels, true);
    // Sample rate
    view.setUint32(24, audioBuffer.sampleRate, true);
    // Byte rate
    view.setUint32(28, audioBuffer.sampleRate * numOfChannels * 2, true);
    // Block align
    view.setUint16(32, numOfChannels * 2, true);
    // Bits per sample
    view.setUint16(34, 16, true);
    // "data" chunk identifier
    writeString(view, 36, 'data');
    // Data chunk length
    view.setUint32(40, length, true);
    
    // Write audio data
    const offset = 44;
    const channelData = new Float32Array(audioBuffer.length);
    let pos = 0;
    
    for (let channel = 0; channel < numOfChannels; channel++) {
      audioBuffer.copyFromChannel(channelData, channel);
      for (let i = 0; i < channelData.length; i++) {
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
            <p>Pensando...</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={isRecording || isLoading}
        />
        <button 
          onClick={handleSendMessage}
          disabled={!input.trim() || isRecording || isLoading}
        >
          Send
        </button>
        <button 
          onClick={toggleRecording}
          className={isRecording ? 'recording' : ''}
          disabled={isLoading}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;