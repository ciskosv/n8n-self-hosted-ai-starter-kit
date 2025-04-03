#!/bin/sh

echo "🔍 Indexando documentos al inicio..."
python indexer.py || echo "⚠ No se pudo indexar (puede ser normal si no hay archivos)"

echo "🚀 Iniciando API FastAPI para indexación dinámica..."
uvicorn api:app --host 0.0.0.0 --port 8000
