import React, { useRef, useState } from 'react';

interface AudioPlayerProps {
  audioUrl: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play().catch(error => {
          console.error('Error playing audio:', error);
        });
      }
    }
  };

  const handlePlayStateChange = () => {
    if (audioRef.current) {
      setIsPlaying(!audioRef.current.paused);
    }
  };

  // Automatically handle file format based on extension
  const fileExtension = audioUrl.split('.').pop()?.toLowerCase();
  const audioType = fileExtension === 'mp3' ? 'audio/mpeg' : 'audio/wav';

  return (
    <div className="audio-player">
      <audio 
        ref={audioRef}
        src={audioUrl}
        onPlay={handlePlayStateChange}
        onPause={handlePlayStateChange}
        onEnded={handlePlayStateChange}
      />
      <button onClick={togglePlayback} className={isPlaying ? 'playing' : ''}>
        {isPlaying ? 'Pause' : 'Play'} 
        <span className="icon">{isPlaying ? '⏸' : '▶'}</span>
      </button>
    </div>
  );
};

export default AudioPlayer;