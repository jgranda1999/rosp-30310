FROM python:3.10

# Install system dependencies including audio libraries
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libsndfile1-dev \
    ffmpeg \
    libasound2-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Configure the container to run as a server
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]