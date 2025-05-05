# Magistrados Interactive Backend

This is the backend server for the Magistrados Interactive application, which provides an interactive chat experience with historical magistrates using AI agents.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the backend directory with:
```
OPENAI_API_KEY=your_openai_api_key
```

## Running the Server

1. Make sure you're in the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Start the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5000` by default.

## API Endpoints

- `GET /api/magistrates` - Get list of available magistrates
- `POST /api/chat` - Send a chat message to a magistrate
- `GET /api/audio/<filename>` - Get audio response file
- `GET /images/<filename>` - Get magistrate images

## Features

- Text-to-speech and speech-to-text capabilities
- Historical persona simulation using AI agents
- Audio response generation
- Support for multiple historical magistrates

## Troubleshooting

If you encounter audio device issues:
1. Check your system's audio devices
2. Modify the `sd.default.device` settings in `app.py`
3. Ensure you have the correct audio drivers installed

For other issues, check the console output for error messages. 