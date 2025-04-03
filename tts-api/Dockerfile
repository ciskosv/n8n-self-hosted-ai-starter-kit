# Usa la imagen base con Python incluido
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# 1. Instala dependencias del sistema (incluyendo pip)
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    espeak \
    libsndfile1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Asegúrate de que pip esté actualizado
RUN python3 -m pip install --upgrade pip

# 3. Instala PyTorch con soporte CUDA 11.8
RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchaudio==2.0.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# 4. Instala TTS y FastAPI
RUN pip install --no-cache-dir \
    TTS==0.20.2 \
    fastapi==0.95.2 \
    uvicorn==0.22.0 \
    "python-multipart==0.0.6"

# Resto de tu configuración...
WORKDIR /app
COPY . .
RUN chmod +x init_tts.sh
EXPOSE 5002
CMD ["uvicorn", "tts_api:app", "--host", "0.0.0.0", "--port", "5002"]