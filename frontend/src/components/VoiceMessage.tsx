import React, { useState, useRef } from 'react';
import { Button, Box, CircularProgress } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';

interface VoiceMessageProps {
    magistrateId: string;
    onMessageSent: () => void;
}

const VoiceMessage: React.FC<VoiceMessageProps> = ({ magistrateId, onMessageSent }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
                await sendVoiceMessage(audioBlob);
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Error accessing microphone. Please make sure you have granted microphone permissions.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            setIsRecording(false);
        }
    };

    const sendVoiceMessage = async (audioBlob: Blob) => {
        setIsProcessing(true);
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('magistrate', magistrateId);

            const response = await fetch('/api/voice-chat', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to send voice message');
            }

            const data = await response.json();
            
            // Play the response audio
            if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                await audio.play();
            }

            onMessageSent();
        } catch (error) {
            console.error('Error sending voice message:', error);
            alert('Error sending voice message. Please try again.');
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
                variant="contained"
                color={isRecording ? "error" : "primary"}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                startIcon={isRecording ? <StopIcon /> : <MicIcon />}
            >
                {isRecording ? 'Stop Recording' : 'Start Recording'}
            </Button>
            {isProcessing && <CircularProgress size={24} />}
        </Box>
    );
};

export default VoiceMessage; 