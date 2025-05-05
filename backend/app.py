from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
import tempfile
import os
import numpy as np
import wave
import io
import random
import json
from pathlib import Path
import sys
import asyncio
from dotenv import load_dotenv
import sounddevice as sd
from magistrado_agentes import MagistrateVoiceAgent
from openai_voice_handler import OpenAIVoiceHandler

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv('OPENAI_API_KEY'):
    print("Warning: OPENAI_API_KEY not found in environment variables")
    print("Please set up your OpenAI API key in a .env file or environment variables")
    print("Example: OPENAI_API_KEY=your-key-here")

app = Flask(__name__)
CORS(app, origins=["https://jgranda1999.github.io", "http://localhost:3000"], supports_credentials=True)

# Create audio directory if it doesn't exist
AUDIO_DIR = Path(__file__).parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Create images directory for static files
IMAGES_DIR = Path(__file__).parent / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Configuration for different magistrates
MAGISTRATES = {
    "Gaspar de Espinosa": {
        "description": "Oidor (juez) de la Real Audiencia de Santo Domingo, gobernador interino de Santo Domingo, teniente gobernador de Panamá, explorador, conquistador",
        "language": "spanish",
        "persona": """
        Eres Gaspar de Espinosa, un abogado, explorador, conquistador y oidor (juez) de la Real Audiencia de Santo Domingo. 
        Desempeñaste un papel importante en la colonización española temprana de las Américas, particularmente en el Caribe y América Central.
        """,
        "imageUrl": "/images/Gaspar.jpeg",
        "background": """
        Gaspar de Espinosa (ca. 1483/84 – 1537) fue un abogado español, explorador, conquistador, oficial militar y administrador colonial que desempeñó un papel significativo 
        en la temprana colonización española de las Américas, particularmente en el Caribe y América Central. 
        Es especialmente notable por su servicio como oidor (juez) y gobernador interino en Santo Domingo y por su participación en la conquista de Panamá y Perú.
        """,
        "period": "Siglo XVI",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en Santo Domingo, la administración de justicia colonial, o mis experiencias como gobernador interino. 
        """, 
        "context_instructions":   """Tieneis que hablar en español del siglo XVI como un Dominicano. Eres Gaspar de Espinosa, un abogado, explorador, conquistador y oidor (juez) de la Real Audiencia de Santo Domingo. 
        Desempeñaste un papel importante en la colonización española temprana de las Américas, particularmente en el Caribe y América Central.
        Habla en español formal del siglo XVI, con autoridad y dignidad como corresponde a tu posición.
        Tienes que hablar en español del siglo XVI como un Dominicano. Usa palabras y frases del siglo XVI."""
    },
    "Hernando de Santillán y Figueroa": {
        "description": "Oidor (Lima, Chile), Teniente Gobernador (Chile), Presidente-Gobernador (Quito), Obispo electo",
        "language": "spanish",
        "persona": """
        Eres Hernando de Santillán y Figueroa, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales, derechos para indijenas y tu participación en la fundación de la Real Audiencia de Quito.
        """,
        "imageUrl": "/images/Hernando_Santillan.jpg",
        "background": """
        Hernando de Santillán y Figueroa (ca. 1519 – 1574/1575) fue un abogado español, administrador colonial y el primer presidente de la Real Audiencia de Quito, que fundó 
        en 1564 bajo órdenes del Rey Felipe II. 
        Su mandato y acciones tuvieron un profundo impacto en la gobernanza colonial temprana en lo que hoy es Ecuador.
        """,
        "period": "Siglo XVI",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en Quito, la fundación de la Real Audiencia, mis experiencias como gobernador interino, mis
         contribuciones intelectuales, o mi participación en la fundación de la Real Audiencia de Quito.
        """,
        "context_instructions": """Tienes que hablar en español del siglo XVI como un Ecuatoriano. Eres Hernando de Santillán y Figueroa, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales, derechos para indijenas y tu participación en la fundación de la Real Audiencia de Quito.
        Habla en español formal, mostrando tu preocupación por los derechos de los indígenas y tu conocimiento de la ley colonial.
        Tienes que hablar en español del siglo XVI como un Ecuatoriano. Usa palabras y frases del siglo XVI."""
    },
    "Vasco de Quiroga": {
        "description": "Oidor de la Segunda Audiencia de México, Primer Obispo de Michoacán.",
        "language": "spanish",
        "persona": """
        Eres Vasco de Quiroga, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales en medio de presiones coloniales.
        """,
        "imageUrl": "/images/Vasco_de_Quiroga.jpg",
        "background": """
        Vasco de Quiroga (ca. 1470/78 – 1565) fue un obispo español, abogado y administrador colonial que se convirtió en una figura destacada en la protección y cristianización 
        de los pueblos indígenas en el México colonial temprano. 
        Es especialmente reconocido por sus reformas humanitarias, la fundación de comunidades utópicas inspiradas en la Utopía de Tomás Moro, y su perdurable legado como el 
        primer obispo de Michoacán.
        """,
        "period": "Siglo XVI", 
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en México, mi trabajo como Obispo de Michoacán, o discutir la evangelización.
        """,
        "context_instructions": """Tienes que hablar en español del siglo XVIII como un Mexicano. Eres Vasco de Quiroga, un magistrado criollo y oidor (juez) en Lima durante el siglo XVIII. 
        Fuiste conocido por tus contribuciones intelectuales y apoyo a los derechos locales en medio de presiones coloniales.
        Habla en español con un tono pastoral y humanista, reflejando tu preocupación por los indígenas y tu visión utópica.
        Tienes que hablar en español del siglo XVIII como un Mexicano. Usa palabras y frases del siglo XVIII."""
    },
    "Antonio Porlier": {
        "description": "Fiscal del Consejo de Indias y de la Audiencia de Lima",
        "language": "spanish",
        "persona": """
        Eres Antonio Porlier, fiscal del Consejo de Indias y de la Audiencia de Lima en el siglo XVIII. 
        Desempeñaste un papel crucial asesorando al Rey Carlos III en reformas judiciales y administrativas.
        """,
        "imageUrl": "/images/antonio-porlier.jpg",
        "background": """
        Antonio Aniceto Porlier y Sopranis, primer Marqués de Bajamar (ca. 1722 – 1813) fue un distinguido jurista español, historiador y estadista ilustrado. 
        Nacido en San Cristóbal de la Laguna (Tenerife, Islas Canarias) el 16 de abril de 1722, se convirtió en una figura destacada en la administración del Imperio Español 
        durante finales del siglo XVIII y principios del XIX.
        """,
        "period": "Siglo XVIII",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como fiscal del Consejo de Indias, mis contribuciones a la reforma judicial, mis esfuerzos por promover la justicia y la 
        administración pública, o mis investigaciones históricas.
        """,
        "context_instructions": """Tienes que hablar en español del siglo XVIII como un Peruano. Eres Antonio Porlier, fiscal del Consejo de Indias y de la Audiencia de Lima en el siglo XVIII. 
        Desempeñaste un papel crucial asesorando al Rey Carlos III en reformas judiciales y administrativas.
        Habla en español ilustrado del siglo XVIII, mostrando tu erudición y conocimiento de las reformas borbónicas.
        Tienes que hablar en español del siglo XVIII como un Peruano. Usa palabras y frases del siglo XVIII."""
    }
}

# Serve static files
@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve image files"""
    try:
        print(f"Requested image: {filename}")
        
        # Handle spaces and special characters in filenames
        image_path = IMAGES_DIR / filename
        print(f"Looking for image at: {image_path}")
        
        if image_path.exists():
            print(f"Image found, serving: {image_path}")
            return send_file(str(image_path), mimetype='image/jpeg')
        else:
            print(f"Image not found, redirecting to placeholder")
            # Return a placeholder image or default image
            placeholder_name = filename.split('.')[0]
            placeholder_url = f"https://via.placeholder.com/400x500?text={placeholder_name.replace('-', '+').replace(' ', '+')}"
            print(f"Redirecting to: {placeholder_url}")
            return redirect(placeholder_url)
    except Exception as e:
        print(f"Error serving image: {e}")
        # Return a generic placeholder in case of errors
        return redirect("https://via.placeholder.com/400x500?text=Image+Error")

@app.route('/api/magistrates', methods=['GET'])
def get_magistrates():
    """Return the list of available magistrates"""
    return jsonify({
        "magistrates": [
            {
                "id": name.lower().replace(" ", "-"),
                "name": name,
                "title": info["description"],
                "description": info["description"],
                "period": info["period"],
                "imageUrl": info["imageUrl"],
                "background": info["background"],
                "talkingPoints": info["talkingPoints"]
            } for name, info in MAGISTRATES.items()
        ]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """This endpoint is kept for compatibility, but redirects to the voice chat mechanism"""
    return jsonify({
        "error": "Text chat is disabled. Please use voice chat instead.",
        "audioUrl": None
    }), 400

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """Serve an audio file"""
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "Audio file not found"}), 404
    
    # Determine mime type based on file extension
    if filename.lower().endswith('.mp3'):
        mimetype = 'audio/mpeg'
    else:
        mimetype = 'audio/wav'
    
    return send_file(str(file_path), mimetype=mimetype)

@app.route('/api/voice-chat', methods=['POST'])
def voice_chat():
    """Process a voice message and return an audio response"""
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({"error": "OpenAI API key not configured"}), 503
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
        
    magistrate_name = request.form.get('magistrate')
    if not magistrate_name:
        return jsonify({"error": "Magistrate name is required"}), 400
    
    # Get magistrate info
    magistrate_info = None
    for name, info in MAGISTRATES.items():
        if name.lower().replace(" ", "-") == magistrate_name.lower().replace(" ", "-"):
            magistrate_info = {**info, 'name': name}
            break
    
    if not magistrate_info:
        return jsonify({"error": f"Magistrate '{magistrate_name}' not found"}), 404
    
    try:
        # Get the audio file from the request
        audio_file = request.files['audio']
        content_type = audio_file.content_type
        print(f"Received audio file with content type: {content_type}")
        
        # Read the audio data
        audio_bytes = audio_file.read()
        print(f"Audio data size: {len(audio_bytes)} bytes")
        
        # Save the input audio for both debugging and processing
        debug_audio_path = AUDIO_DIR / f"debug_input_{random.randint(10000, 99999)}.wav"
        with open(debug_audio_path, 'wb') as f:
            f.write(audio_bytes)
        print(f"Saved debug input to {debug_audio_path}")
        
        # Convert audio bytes to numpy array
        try:
            # Use wave module to read the saved WAV file for consistent handling
            with wave.open(str(debug_audio_path), 'rb') as wf:
                # Print wave file info for debugging
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                print(f"WAV info: channels={channels}, sample_width={sample_width}, framerate={framerate}, frames={n_frames}")
                
                # Read all frames
                audio_data = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)
                
                # Ensure we have non-zero data
                if len(audio_data) == 0 or np.max(np.abs(audio_data)) < 10:
                    print("Warning: Audio data appears to be silent or corrupted")
        except Exception as e:
            print(f"Error processing audio data: {e}")
            return jsonify({"error": f"Error processing audio: {str(e)}"}), 400
        
        # Create voice handler for the magistrate
        print(f"Creating voice handler for magistrate: {magistrate_info['name']}")
        print(f"Magistrate info: {magistrate_info}")
        voice_handler = OpenAIVoiceHandler(magistrate_info)
        
        # Process the audio
        result = asyncio.run(voice_handler.process_audio(audio_data, framerate))
        
        if 'error' in result:
            return jsonify({"error": result['error']}), 500
            
        # Save the response audio
        response_filename = f"response_{random.randint(10000, 99999)}.wav"
        response_path = AUDIO_DIR / response_filename
        
        with wave.open(str(response_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(result['audio_data'].tobytes())
            
        return jsonify({
            "audioUrl": f"/api/audio/{response_filename}",
            "transcribedText": result['transcribed_text'],
            "responseText": result['response_text'],
            "text": result['response_text']  # For backward compatibility
        })
        
    except Exception as e:
        print(f"Error processing voice chat: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)