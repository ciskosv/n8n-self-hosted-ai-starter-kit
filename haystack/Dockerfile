FROM python:3.10-slim

# 🛠️ Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    git curl ffmpeg libsndfile1 build-essential && \
    rm -rf /var/lib/apt/lists/*

# 🐍 Instala versiones compatibles verificadas (actualizado 2024-06-20)
RUN pip install --no-cache-dir \
    haystack-ai==2.1.0 \
    qdrant-haystack==2.0.1 \
    sentence-transformers==2.2.2 \
    transformers==4.34.1 \
    accelerate==0.23.0 \
    huggingface_hub==0.17.3 \
    fastapi==0.95.2 \
    uvicorn==0.22.0 \
    python-docx==0.8.11 \
    python-multipart==0.0.6 \
    pydantic==1.10.10 \
    qdrant-client==1.6.4 \
    pypdf==3.9.1


# 📁 Configuración del entorno
WORKDIR /app
COPY . .

# Variables de entorno para Haystack
ENV QDRANT_HOST=qdrant
ENV QDRANT_PORT=6333
ENV EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV OLLAMA_HOST=ollama:11434

# ✅ Permisos de ejecución
RUN chmod +x ./entrypoint.sh

# 🚀 Punto de entrada
ENTRYPOINT ["./entrypoint.sh"]