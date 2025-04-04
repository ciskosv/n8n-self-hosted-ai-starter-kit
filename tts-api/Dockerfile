FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Configuración básica
ENV TZ=America/El_Salvador
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Configura Python 3.10 como predeterminado
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Configura el caché de modelos
RUN mkdir -p /app/model_cache && chmod 777 /app/model_cache
ENV XDG_CACHE_HOME=/app/model_cache

# Instala Torch con CUDA 12.1
RUN pip install --no-cache-dir \
    torch==2.1.2+cu121 \
    torchaudio==2.1.2+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Instala TTS y dependencias (incluyendo uvicorn)
RUN pip install --no-cache-dir \
    git+https://github.com/coqui-ai/TTS@v0.22.0#egg=TTS \
    git+https://github.com/ciskosv/fastapi_response_standard.git@v1.0.0 \
    numpy==1.22.0 \
    opencv-python-headless==4.8.1.78 \
    fastapi \
    uvicorn \
    python-multipart

# Descarga el modelo XTTS v2
#RUN python3 -c "\
#import os;\
#from TTS.utils.manage import ModelManager;\
#os.environ['COQUI_TOS_AGREED'] = '1';\
#os.environ['TTS_VERBOSE'] = '1';\
#print('=== Descargando modelo ===');\
#manager = ModelManager();\
#manager.download_model('tts_models/multilingual/multi-dataset/xtts_v2');\
#print('=== Modelo descargado ===');\
#"

WORKDIR /app
COPY . .

EXPOSE 5002

# Ejecuta uvicorn especificando el módulo python explícitamente
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]