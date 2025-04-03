#!/bin/bash

# Ruta donde TTS almacena los modelos (¡DEBE coincidir con el volumen en docker-compose.yml!)
TTS_HOME="/root/.local/share/tts"

# Modelos y vocoders requeridos (ajusta según tus necesidades)
REQUIRED_MODELS=(
    "tts_models/es/css10/vits"             # Modelo todo-en-uno para español (no necesita vocoder)
    "tts_models/en/ljspeech/tacotron2-DDC" # Modelo inglés (requiere vocoder)
)

REQUIRED_VOCODERS=(
    "vocoder_models/en/ljspeech/hifigan_v2"          # Vocoder específico para inglés
    "vocoder_models/universal/libri-tts/fullband-melgan" # Vocoder universal alternativo
)

# Crear directorio si no existe
mkdir -p "$TTS_HOME"

# Función para descargar solo si no existe
download_if_needed() {
    local type=$1  # "model" o "vocoder"
    local name=$2
    local dir_name="${name//\//--}"  # Convierte tts_models/es/vits → tts_models--es--vits
    
    if [ ! -d "$TTS_HOME/$dir_name" ]; then
        echo "Descargando $type: $name..."
        if [ "$type" == "model" ]; then
            tts --download_model "$name"
        else
            tts --download_vocoder "$name"
        fi
    else
        echo "$type ya existe: $name"
    fi
}

# Descargar modelos
for model in "${REQUIRED_MODELS[@]}"; do
    download_if_needed "model" "$model"
done

# Descargar vocoders (solo si son necesarios)
for vocoder in "${REQUIRED_VOCODERS[@]}"; do
    download_if_needed "vocoder" "$vocoder"
done

# Iniciar la API
echo "Iniciando servicio TTS..."
uvicorn tts_api:app --host 0.0.0.0 --port 5002