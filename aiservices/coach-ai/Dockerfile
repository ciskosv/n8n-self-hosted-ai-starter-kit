FROM python:3.10-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    git curl && rm -rf /var/lib/apt/lists/*

# Crea carpeta de trabajo
WORKDIR /app

# Requisitos Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Script de entrada (opcional si usas uvicorn directamente)
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
