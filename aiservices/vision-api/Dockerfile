FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git ffmpeg libgl1-mesa-glx build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Script de entrada
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
