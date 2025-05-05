import React, { useEffect, useState } from 'react';
import { Magistrate } from '../types';

interface MagistrateSelectorProps {
  onSelect: (magistrate: Magistrate) => void;
}

const MagistrateSelector: React.FC<MagistrateSelectorProps> = ({ onSelect }) => {
  const [magistrates, setMagistrates] = useState<Magistrate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);

  useEffect(() => {
    const fetchMagistrates = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/magistrates');
        if (!response.ok) {
          throw new Error('Failed to fetch magistrates');
        }
        const data = await response.json();
        setMagistrates(data.magistrates || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching magistrates:', err);
        setError('Failed to load magistrates. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchMagistrates();
  }, []);

  if (loading) {
    return <div className="loading">Loading magistrates...</div>;
  }

  // Function to handle image loading errors
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>, magistrateId: string) => {
    console.error(`Failed to load image for magistrate: ${magistrateId}`);
    setImageErrors(prev => ({ ...prev, [magistrateId]: true }));
    e.currentTarget.src = `https://via.placeholder.com/400x500?text=${magistrateId.replace(/-/g, '+')}`;
  };

  // Chat button click handler - stops event propagation to prevent card click
  const handleChatClick = (
    e: React.MouseEvent<HTMLButtonElement>, 
    magistrate: Magistrate
  ) => {
    e.stopPropagation();
    onSelect(magistrate);
  };

  // Toggle citation display
  const toggleCitation = (
    e: React.MouseEvent<HTMLButtonElement>,
    magistrateId: string
  ) => {
    e.stopPropagation();
    setSelectedCitation(prev => prev === magistrateId ? null : magistrateId);
  };

  // Mock citations data - in a real app, this would come from the API
  const citations: Record<string, string[]> = {
    'gaspar-de-espinosa': [
      'Famous Americans. (n.d.). Gaspar de Espinosa. Retrieved from http://famousamericans.net/gaspardeespinosa/',
      'Ruiz, B. (n.d.). Gaspar de Espinosa. Panama History. Retrieved from http://bruceruiz.net/PanamaHistory/gaspar_de_espinosa.htm',
      'Oxford Research Encyclopedia. (n.d.). Gaspar de Espinosa. Retrieved from https://oxfordre.com/latinamericanhistory/display/10.1093/acrefore/9780199366439.001.0001/acrefore-9780199366439-e-1005'
    ],
    'hernando-de-santillán-y-figueroa': [
      'Royal Audiencia of Quito. (n.d.). Ecuador Stamps. Retrieved from https://www.ecuadorstamps.com/royal-audiencia-of-quito/',
      'Contreras, H. (2020). Establishing Colonial Rule in a Frontier Encomienda: Chile\'s Copiapó Valley under Francisco de Aguirre and His Kin, 1549–1580. Latin American Research Review, 55(4), 673-687. Retrieved from https://www.cambridge.org/core/journals/latin-american-research-review/article/establishing-colonial-rule-in-a-frontier-encomienda-chiles-copiapo-valley-under-francisco-de-aguirre-and-his-kin-15491580/D155526D98A3F8DE4766C82AAA79BFC0',
      'Owensby, B., & Ross, R. (2018). The One, the Many, the None, Rethinking the Republics of Spaniards and Indians in the Sixteenth-Century Spanish Indies. The Americas, 75(4), 725-747. Retrieved from https://www.cambridge.org/core/journals/americas/article/two-the-one-the-many-the-none-rethinking-the-republics-of-spaniards-and-indians-in-the-sixteenthcentury-spanish-indies/834427C28A38B1F5A679DAB669501F5E'
    ],
    'vasco-de-quiroga': [
      'Salerno, R. (2014). Vasco de Quiroga: Advocate of the Amerindians of New Spain. Retrieved from https://rptimes.com/rosarie-salerno/2014/09/vasco-de-quiroga-advocate-of-the-amerindians-of-new-spain/',
      'Archivo General de la Nación. (n.d.). Vasco de Quiroga: The First Bishop of Michoacán. Retrieved from https://artsandculture.google.com/story/vasco-de-quiroga-the-first-bishop-of-michoac%C3%A1n-archivo-general-de-la-nacion/XgXRXccqCmfDuQ',
      'Wikiwand. (n.d.). Vasco de Quiroga. Retrieved from https://www.wikiwand.com/en/articles/Vasco_de_quiroga'
    ],
    'antonio-porlier': [
      'Burkholder, M. A. (1976). Antonio A. de Porlier y Sopranis, 1st Marquis of Bajamar. Retrieved from https://www.jstor.org/stable/pdf/45418485.pdf',
      'Fisher, J. R. (1981). Bureaucracy and Business in the Spanish Empire, 1759-1804: Failure of a Bourbon Reform in Mexico and Peru. Retrieved from https://www.jstor.org/stable/2514246?seq=11',
      'Encyclopedia.com. (n.d.). Minister of Indies. Retrieved from https://www.encyclopedia.com/humanities/encyclopedias-almanacs-transcripts-and-maps/minister-indies'
    ]
  };

  return (
    <div className="magistrate-selector">
      <h2>Elija un Magistrado para Conversar</h2>
      {error && <div className="error-message">{error}</div>}
      <div className="magistrate-grid">
        {magistrates.map((magistrate) => (
          <div 
            key={magistrate.id} 
            className="magistrate-card"
          >
            <div className="magistrate-image">
              <img 
                src={magistrate.imageUrl}
                alt={magistrate.name}
                onError={(e) => handleImageError(e, magistrate.id)}
                className={imageErrors[magistrate.id] ? 'image-error' : ''}
              />
            </div>
            <div className="magistrate-card-content">
              <h3>{magistrate.name}</h3>
              <h4>{magistrate.title}</h4>
              <p>{magistrate.background}</p>
              {selectedCitation === magistrate.id && citations[magistrate.id] && (
                <div className="citations-container">
                  <h4>Fuentes Bibliográficas:</h4>
                  <ul className="citations-list">
                    {citations[magistrate.id].map((citation, index) => (
                      <li key={index}>{citation}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="magistrate-card-footer">
              <button 
                className="chat-button"
                onClick={(e) => handleChatClick(e, magistrate)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
                  <path d="M7 9h10v2H7zm0-3h10v2H7zm0 6h7v2H7z"/>
                </svg>
                Conversar
              </button>
              <button
                className={`citation-button ${selectedCitation === magistrate.id ? 'active' : ''}`}
                onClick={(e) => toggleCitation(e, magistrate.id)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
                  <path d="M7 10h2v7H7zm4-3h2v10h-2zm4 6h2v4h-2z"/>
                </svg>
                Fuentes
              </button>
              <span className="period">{magistrate.period}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MagistrateSelector;