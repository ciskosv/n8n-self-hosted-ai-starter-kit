# Imagen base oficial de Paddle con Python preinstalado
FROM paddlepaddle/paddle:2.5.1

# Instalar dependencias del sistema necesarias para imágenes y PDF
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    wget \
    git \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    fastapi==0.88.0 \
    uvicorn==0.20.0 \
    python-multipart==0.0.6 \
    pdf2image==1.16.3 \
    paddleocr==2.6.1.3

# Exponer el puerto donde correrá la API
EXPOSE 5010

# Ejecutar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5010"]
