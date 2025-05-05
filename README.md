# Magistrados Interactive

An immersive, virtual experience that allows users to interact with historical Spanish magistrates from colonial South America through a web interface.

## Project Overview

This project aims to create an interactive website where users can engage in live conversations with historical Spanish magistrates. Each magistrate's responses are generated using AI-driven, standardized voice synthesis, offering an authentic auditory experience that reflects their historical context.

## Features

- Interactive selection of historical magistrates from colonial South America
- Real-time conversation interface with text and voice input
- AI-generated responses with audio output
- Educational information about each magistrate's historical role and significance

## Project Structure

```
magistrados-interactive/
├── frontend/           # React.js frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── types/      # TypeScript type definitions
│   │   └── styles/     # CSS styles
│   └── public/         # Static assets
└── backend/            # Flask backend
    ├── audio/          # Generated audio files
    ├── app.py          # Flask application
    └── magistrado_agentes.py  # AI agent implementation
```

## Setup Instructions

### Prerequisites

- Node.js (v14+)
- Python (v3.7+)
- npm or yarn

### Installing Dependencies

1. **Install all dependencies at once:**
   ```bash
   npm run install:all
   ```

   Or manually:

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

3. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Running the Project

1. **Start everything at once (both frontend and backend):**
   ```bash
   npm start
   ```

   Or start each individually:

2. **Start the Frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Start the Backend:**
   ```bash
   cd backend
   python app.py
   ```

4. Access the application at `http://localhost:3000`

## Troubleshooting

### Frontend Issues

1. **"Missing script: start" Error**
   - Make sure you're in the correct directory. If running from the root directory, use `npm start` (which will run both frontend and backend).
   - If you want to run just the frontend, navigate to the frontend directory first: `cd frontend` then `npm start`.

2. **"Module not found" or Import Errors**
   - Run `npm install` in the frontend directory to ensure all dependencies are installed.
   - Check if the package.json includes all required dependencies.

### Backend Issues

1. **Flask Import Error**
   - If you see an error like `ImportError: cannot import name 'url_quote' from 'werkzeug.urls'`, this indicates a version mismatch.
   - Solution: Make sure you install the exact versions in requirements.txt.
   - Try: `pip install werkzeug==2.0.1 flask==2.0.1` if you continue having issues.

2. **Audio Directory Error**
   - The app will automatically create the 'audio' directory, but if there are permission issues:
   - Manually create the directory: `mkdir -p backend/audio`

3. **Missing Agents Module**
   - The backend is designed to work even without the specific agents module.
   - If the agents module is not available, the app will use mock responses.

4. **Sounddevice/PortAudio Error**
   - If you encounter an error related to sounddevice or PortAudio, such as:
     ```
     OSError: cannot load library 'libportaudio.so.2'
     ```
   - The backend has been simplified to work without these dependencies.
   - The audio generation will use simple numpy operations to create mock audio files.

## Technical Details

### Backend Implementation

The backend has been designed with fallback mechanisms to handle missing dependencies:

1. **Mock Audio Generation**: The backend uses NumPy to generate simple sine wave audio files without requiring specialized audio libraries.

2. **Mock Agent Implementation**: If the required agent modules are not available, the application uses a mock implementation that simulates the agent responses.

3. **Error Handling**: The API endpoints include comprehensive error handling to provide helpful error messages when something goes wrong.

### Frontend-Backend Communication

The frontend communicates with the backend through these API endpoints:

- `GET /api/magistrates`: Retrieves the list of available magistrates
- `POST /api/chat`: Sends user messages and receives magistrate responses with audio
- `GET /api/audio/<filename>`: Retrieves audio files for playback

### General Issues

1. **CORS Errors in Browser Console**
   - Make sure both frontend and backend are running.
   - Verify that the proxy in frontend/package.json is set to `"proxy": "http://localhost:5000"`.

2. **Audio Not Playing**
   - Check browser console for errors.
   - Ensure the audio files are being generated in the backend/audio directory.
   - The mock audio is just a simple sine wave to demonstrate functionality.

## Project Inspiration

This project is inspired by the movie Zama and aims to leverage digital media to bring historical figures to life, providing an engaging way to learn about the judicial and administrative roles of Spanish magistrates in colonial South America.

## Author

Jonathan Granda Acaro - ROSP-30310 - Introduction to Hispanic Literature and Culture 