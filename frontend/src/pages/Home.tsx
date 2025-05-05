import React, { useState } from 'react';
import MagistrateSelector from '../components/MagistrateSelector';
import ChatInterface from '../components/ChatInterface';

interface Magistrate {
  id: string;
  name: string;
  title: string;
  description: string;
  period: string;
  imageUrl: string;
  background: string;
  talkingPoints: string;
}

const Home: React.FC = () => {
  const [selectedMagistrate, setSelectedMagistrate] = useState<Magistrate | null>(null);

  const handleMagistrateSelect = (magistrate: Magistrate) => {
    setSelectedMagistrate(magistrate);
  };

  return (
    <div className="home-container">
      {!selectedMagistrate ? (
        <MagistrateSelector onSelect={handleMagistrateSelect} />
      ) : (
        <>
          <button 
            className="back-button"
            onClick={() => setSelectedMagistrate(null)}
          >
            ← Volver a la Selección de Magistrados
          </button>
          <div className="magistrate-image-container" style={{ display: 'flex', justifyContent: 'center' }}>
            <img 
              src={selectedMagistrate.imageUrl}
              alt={selectedMagistrate.name}
              onError={(e) => {
                console.error(`Failed to load image for magistrate: ${selectedMagistrate.id}`);
                e.currentTarget.src = `https://via.placeholder.com/400x500?text=${selectedMagistrate.id.replace(/-/g, '+')}`;
              }}
            />
          </div>
          <br/>
          <h2>Conversación con {selectedMagistrate.name}</h2>
          <h3>{selectedMagistrate.title}</h3>
          <ChatInterface 
            magistrateName={selectedMagistrate.name}
            talkingPoints={selectedMagistrate.talkingPoints || ''} 
          />
        </>
      )}
    </div>
  );
};

export default Home;
