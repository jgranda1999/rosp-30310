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

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv('OPENAI_API_KEY'):
    print("Warning: OPENAI_API_KEY not found in environment variables")
    print("Please set up your OpenAI API key in a .env file or environment variables")
    print("Example: OPENAI_API_KEY=your-key-here")

app = Flask(__name__)
CORS(app)

# Create audio directory if it doesn't exist
AUDIO_DIR = Path(__file__).parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# Create images directory for static files
IMAGES_DIR = Path(__file__).parent / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Try to import agents if available, otherwise use mock agents
try:
    from magistrado_agentes import agent, spanish_agent
    HAS_AGENTS = True
except ImportError:
    print("Error: 'magistrado_agentes' module not found. Please ensure it is installed.")
    HAS_AGENTS = False
    agent = None
    spanish_agent = None

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
        "period": "16th Century",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en Santo Domingo, la administración de justicia colonial, o mis experiencias como gobernador interino. 
        """
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
        "period": "16th Century",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en Quito, la fundación de la Real Audiencia, mis experiencias como gobernador interino, mis
         contribuciones intelectuales, o mi participación en la fundación de la Real Audiencia de Quito.
        """
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
        "period": "16th Century", 
        "talkingPoints": """
        Podríamos conversar sobre mi rol como oidor en México, mi trabajo como Obispo de Michoacán, o discutir la evangelización.
        """
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
        "period": "18th Century",
        "talkingPoints": """
        Podríamos conversar sobre mi rol como fiscal del Consejo de Indias, mis contribuciones a la reforma judicial, mis esfuerzos por promover la justicia y la 
        administración pública, o mis investigaciones históricas.
        """
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
    """Process a chat message and return an audio response"""
    if not os.getenv('OPENAI_API_KEY'):
        return jsonify({"error": "OpenAI API key not configured"}), 503
    
    data = request.json
    message = data.get('message', '')
    magistrate_name = data.get('magistrate', '')
    
    if not message or not magistrate_name:
        return jsonify({"error": "Message and magistrate are required"}), 400
    
    # Get magistrate info
    magistrate_info = None
    for name, info in MAGISTRATES.items():
        if name.lower().replace(" ", "-") == magistrate_name.lower().replace(" ", "-"):
            magistrate_info = {**info, 'name': name}
            break
    
    if not magistrate_info:
        return jsonify({"error": f"Magistrate '{magistrate_name}' not found"}), 404
    
    try:
        # Create voice agent for the magistrate
        voice_agent = MagistrateVoiceAgent(magistrate_info)
        
        # Process the text message
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(voice_agent.process_text(message))
        loop.close()
        
        if result['audio_data'] is not None:
            # Save the audio response
            audio_filename = f"response_{random.randint(10000, 99999)}.wav"
            file_path = AUDIO_DIR / audio_filename
            
            with wave.open(str(file_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(result['audio_data'].tobytes())
            
            return jsonify({
                "audioUrl": f"/api/audio/{audio_filename}"
            })
        else:
            raise Exception("No audio response generated")
            
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "Failed to generate response",
            "details": str(e)
        }), 500

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

def generate_mock_response(magistrate_name, message):
    """Generate a mock response for testing purposes"""
    responses = [
        f"Como magistrado en la América del Sur colonial, encuentro tu consulta sobre '{message}' bastante intrigante.",
        f"En mi época como juez en la Audiencia, habríamos abordado '{message}' con cuidadosa deliberación.",
        f"La administración colonial bajo la Corona Española vería '{message}' con particular interés.",
        f"Según las prácticas legales de mi época, '{message}' estaría sujeto a las Leyes de Indias."
    ]
    return random.choice(responses)

def generate_audio_file(text):
    """Generate realistic speech audio for the given text using gTTS"""
    try:
        # Use Google Text-to-Speech to generate Spanish voice
        tts = gTTS(text=text, lang='es', slow=False)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            temp_mp3_path = temp_mp3.name
            # Save the TTS output as MP3
            tts.save(temp_mp3_path)
            print(f"Generated TTS audio saved to {temp_mp3_path}")
            
            # We need to convert MP3 to WAV for compatibility
            # This would normally use ffmpeg but we'll use a simpler approach for now
            # Read the MP3 data into memory
            with open(temp_mp3_path, 'rb') as mp3_file:
                mp3_data = mp3_file.read()
        
        # Create output filename
        filename = f"response_{random.randint(10000, 99999)}.mp3"
        file_path = AUDIO_DIR / filename
        
        # Save the MP3 file directly (modern browsers can play MP3)
        with open(file_path, 'wb') as out_file:
            out_file.write(mp3_data)
            
        # Remove the temporary file
        os.unlink(temp_mp3_path)
        
        return filename
        
    except Exception as e:
        print(f"Error generating TTS: {e}")
        # Fallback to synthetic audio if TTS fails
        return generate_synthetic_audio(text)

def generate_synthetic_audio(text):
    """Fallback function to generate a simple synthetic audio if TTS fails"""
    # Create a simple sine wave with amplitude modulation
    sample_rate = 16000  # Hz
    duration = min(len(text) * 0.1, 10)  # Roughly 0.1 seconds per character, max 10 seconds
    frequency = 440  # Hz (A4 note)
    
    # Create time base
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a simple amplitude modulation to make it sound more like speech
    char_count = len(text)
    modulation_freq = 3  # Hz
    modulation = np.sin(2 * np.pi * modulation_freq * t) * 0.3 + 0.7
    
    # Generate sine wave with modulation
    audio_data = np.sin(2 * np.pi * frequency * t) * 32767 * 0.3 * modulation
    
    # Add some variance to make it sound more like speech
    for i, char in enumerate(text):
        if i >= len(t):
            break
        idx = int(i * len(t) / char_count)
        if idx < len(audio_data):
            # Add a slight variation based on the character
            var = (ord(char) % 10) / 10
            audio_data[idx:idx+100] *= (1.0 + var)
    
    # Convert to int16
    audio_data = audio_data.astype(np.int16)
    
    # Add short pauses at beginning and end
    pause_samples = int(0.2 * sample_rate)
    pause = np.zeros(pause_samples, dtype=np.int16)
    audio_data = np.concatenate([pause, audio_data, pause])
    
    # Save to a WAV file
    filename = f"response_{random.randint(10000, 99999)}.wav"
    file_path = AUDIO_DIR / filename
    
    with wave.open(str(file_path), 'wb') as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 2 bytes for int16
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    return filename

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
        audio_data = audio_file.read()

        # Create voice agent for the magistrate
        voice_agent = MagistrateVoiceAgent(magistrate_info)
        
        # Process the audio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(voice_agent.process_audio(audio_data))
        loop.close()
        
        if result['audio_data'] is not None:
            # Save the output audio
            audio_filename = f"response_{random.randint(10000, 99999)}.wav"
            file_path = AUDIO_DIR / audio_filename
            
            with wave.open(str(file_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(result['audio_data'].tobytes())
            
            return jsonify({
                "audioUrl": f"/api/audio/{audio_filename}"
            })
        else:
            raise Exception("No audio data generated")

    except Exception as e:
        print(f"Error in voice chat endpoint: {e}")
        return jsonify({
            "error": "Failed to process voice message",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)