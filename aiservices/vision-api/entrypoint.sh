#!/bin/bash

echo "🚀 Iniciando Vision API..."
echo "📁 Ruta de trabajo: $(pwd)"

# Crear carpeta de datos si no existe
mkdir -p /data

# Lanzar la API
exec uvicorn vision_api:app --host 0.0.0.0 --port 5004
