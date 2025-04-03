# 📁 Archivo: tts_api.py
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import uuid
import os
import torch  # Importación explícita de Torch
from pathlib import Path

app = FastAPI()

# Configuración de directorios
AUDIO_DIR = "/data"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Configuración de modelos
MODEL_CONFIG = {
    "es": {
        "model": "tts_models/es/css10/vits",
        "vocoder": None  # Vits no necesita vocoder separado

        #"model":"tts_models/es/mai/tacotron2-DDC",
        #"vocoder":"vocoder_models/universal/libri-tts/fullband-melgan"
        #"vocoder":"vocoder_models/universal/libri-tts/wavegrad"
    },
    "en": {
        "model": "tts_models/en/ljspeech/tacotron2-DDC",
        "vocoder": "vocoder_models/en/ljspeech/hifigan_v2"  # Vocoder específico
    }
}

def check_torch():
    """Verifica que Torch esté instalado correctamente"""
    try:
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        return True
    except Exception as e:
        print(f"Error verificando Torch: {e}")
        return False

def model_exists(model_path: str) -> bool:
    """Verifica si un modelo está descargado"""
    return Path(os.path.expanduser(f"~/.local/share/tts/{model_path.replace('/', '--')}")).exists()

@app.on_event("startup")
async def startup():
    """Descarga modelos si no existen"""
    if not check_torch():
        raise RuntimeError("PyTorch no está funcionando correctamente")
    
    for lang, config in MODEL_CONFIG.items():
        if not model_exists(config["model"]):
            try:
                # Descarga usando el modelo
                subprocess.run([
                    "tts",
                    "--model_name", config["model"],
                    "--text", "test",
                    "--out_path", "/tmp/startup_test.wav"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error descargando modelo {config['model']}: {e}")

        if config["vocoder"] and not model_exists(config["vocoder"]):
            try:
                subprocess.run([
                    "tts",
                    "--vocoder_name", config["vocoder"],
                    "--text", "test",
                    "--out_path", "/tmp/startup_test_vocoder.wav"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error descargando vocoder {config['vocoder']}: {e}")

@app.post("/tts")
async def generate_tts(request: Request):
    data = await request.json()
    texto = data.get("text", "").strip()
    idioma = data.get("lang", "es")  # "es" por defecto

    if not texto:
        return JSONResponse(status_code=400, content={"error": "Falta el texto"})

    if idioma not in MODEL_CONFIG:
        return JSONResponse(status_code=400, content={"error": f"Idioma '{idioma}' no soportado"})

    config = MODEL_CONFIG[idioma]
    audio_id = str(uuid.uuid4())
    output_path = os.path.join(AUDIO_DIR, f"output_{audio_id}.wav")

    try:
        cmd = [
            "tts",
            "--text", texto,
            "--out_path", output_path,
            "--model_name", config["model"],
            "--use_cuda", "false"  # Fuerza CPU
        ]
        
        if config["vocoder"]:
            cmd.extend(["--vocoder_name", config["vocoder"]])
        
        subprocess.run(cmd, check=True)

        return FileResponse(output_path, media_type="audio/wav", filename=f"tts_{idioma}.wav")

    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": "Error en TTS", "details": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Error interno", "details": str(e)})

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "torch_version": torch.__version__,
        "models_loaded": list(MODEL_CONFIG.keys())
    }

@app.on_event("shutdown")
def cleanup():
    for file in os.listdir(AUDIO_DIR):
        if file.startswith("output_") and file.endswith(".wav"):
            os.remove(os.path.join(AUDIO_DIR, file))