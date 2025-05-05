#!/bin/bash

set -e  # Exit on error

echo "Starting fresh setup of Magistrados Interactive..."

# Setup backend
echo "Setting up backend..."
cd backend

# Install correct Flask and Werkzeug versions
pip install flask==2.0.1 werkzeug==2.0.1 --force-reinstall
pip install -r requirements.txt

# Create audio directory if it doesn't exist
mkdir -p audio

# Setup frontend
echo "Setting up frontend..."
cd ../frontend

# Remove all node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Create a new package.json with correct dependencies
cat > package.json << 'EOL'
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.11",
    "@types/react": "^18.0.26",
    "@types/react-dom": "^18.0.10",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.4",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:5000"
}
EOL

# Install dependencies
npm install

# Go back to project root
cd ..

echo "Creating a simplified root package.json..."
cat > package.json << 'EOL'
{
  "name": "magistrados-interactive",
  "version": "1.0.0",
  "description": "An immersive, virtual experience that allows users to interact with historical Spanish magistrates from colonial South America",
  "main": "index.js",
  "scripts": {
    "start": "concurrently \"npm run start:frontend\" \"npm run start:backend\"",
    "start:frontend": "cd frontend && npm start",
    "start:backend": "cd backend && python app.py",
    "install:all": "npm install && cd frontend && npm install"
  },
  "keywords": [
    "spanish",
    "magistrates",
    "interactive",
    "voice",
    "ai"
  ],
  "author": "Jonathan Granda Acaro",
  "license": "ISC",
  "dependencies": {
    "concurrently": "^8.2.0"
  }
}
EOL

# Install root dependencies
npm install

echo "Fresh setup completed!"
echo "You can now run the application with: npm start" 