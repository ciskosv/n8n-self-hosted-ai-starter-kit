#!/bin/bash

echo "📈 Iniciando Timeseries API..."
echo "📁 Ruta de trabajo: $(pwd)"

# Crear carpeta de datos si no existe
mkdir -p /data

# Lanzar la API
exec uvicorn timeseries_api:app --host 0.0.0.0 --port 5006
