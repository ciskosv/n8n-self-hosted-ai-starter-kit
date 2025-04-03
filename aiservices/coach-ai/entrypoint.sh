#!/bin/bash
echo "🔍 Iniciando classifier-api..."
uvicorn coach_api:app --host 0.0.0.0 --port 5009
