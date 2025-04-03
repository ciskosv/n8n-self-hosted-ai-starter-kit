FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Directorios necesarios
RUN mkdir -p /usr/share/tesseract-ocr/tessdata/ /app/temp_uploads

# Descargar modelos de Tesseract necesarios
RUN wget -nc -O /usr/share/tesseract-ocr/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata && \
    wget -nc -O /usr/share/tesseract-ocr/tessdata/spa.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata && \
    wget -nc -O /usr/share/tesseract-ocr/tessdata/spa_old.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/spa_old.traineddata

# Variables de entorno para Tesseract
ENV PYTHONUNBUFFERED=1
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata/

WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5003
CMD ["uvicorn", "ocr-api:app", "--host", "0.0.0.0", "--port", "5003"]
