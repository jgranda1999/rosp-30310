#!/bin/bash

# Fix the Flask and Werkzeug versions in the backend
echo "Fixing backend dependencies..."
cd backend
pip install flask==2.0.1 werkzeug==2.0.1 --force-reinstall
pip install -r requirements.txt

# Clean up node_modules completely from root and frontend
echo "Cleaning up all node_modules directories..."
cd ..
rm -rf node_modules package-lock.json
cd frontend
rm -rf node_modules package-lock.json

# Clean npm cache
echo "Cleaning npm cache..."
npm cache clean --force

# Install root dependencies first
echo "Installing root dependencies..."
cd ..
npm install

# Reinstall frontend dependencies with specific versions
echo "Reinstalling frontend dependencies..."
cd frontend
# Install React 18 and compatible react-router-dom
npm install --save react@18.2.0 react-dom@18.2.0
npm install --save react-router-dom@6.20.0

# Install other dependencies
npm install

echo "Done. Now you can run the application with 'npm start' from the root directory." 