FROM python:3.8-slim-buster

# Prevenir interferencia
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Dependencias del sistema y libssl1.1 aún disponible aquí
RUN apt-get update && \
    apt-get install -y \
    git \
    build-essential \
    wget \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libssl1.1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual limpio
RUN python -m venv $VIRTUAL_ENV

# Copiar requirements
COPY requirements.txt .

# Evitar conflictos con ABI de numpy y opencv
RUN pip install --upgrade pip && \
    pip install numpy==1.24.4 opencv-python-headless==4.8.1.78

# Instalar el resto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

RUN mkdir -p /app/temp_uploads

EXPOSE 5010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5010"]
