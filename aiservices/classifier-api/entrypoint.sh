#!/bin/bash
echo "🔍 Iniciando classifier-api..."
uvicorn classifier_api:app --host 0.0.0.0 --port 5009
