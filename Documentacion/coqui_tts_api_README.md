# 🎙️ Coqui TTS API - Integración Local

Esta API permite convertir texto en voz usando **Coqui TTS** con salida en `.wav`, lista para integrarse con **n8n, Telegram o bots**.

---

## ✅ Características

- 📦 Basado en imagen Docker `synesthesiam/mozillatts`
- 🌐 Endpoint HTTP `POST /tts`
- 🔊 Soporta idioma **español (es_ES)** por defecto
- 📁 Guarda los archivos en `/data/output_*.wav`
- ⚡ Devuelve el archivo generado directamente

---

## 🧪 Ejemplo de uso

```bash
curl -X POST http://localhost:5002/tts -H "Content-Type: application/json" -d '{"text": "Hola, ¿en qué puedo ayudarte?"}' --output respuesta.wav
```


## 📥 Voces disponibles

- Español: `tts_models/es/mai/tacotron2-DDC`
- Inglés: `tts_models/en/ljspeech/tacotron2-DDC`

Puedes cambiar `--model_name` y `--vocoder_name` según el idioma o calidad deseada.

---

## 📁 Archivos generados

Los `.wav` se guardan en:

```
shared/tts/output_<uuid>.wav
```

## 📌 Recomendación

Ejecutar este contenedor **con CPU**, ya que Coqui TTS puede consumir GPU pero no lo necesita para pruebas básicas.

---

Últimos tips rápidos:
Puedes consultar voces disponibles con:
  tts --list_models

Si deseas convertir .wav a .mp3 para reducir tamaño:

Usa ffmpeg en el contenedor o desde n8n (Execute Command):

  ffmpeg -i output.wav -codec:a libmp3lame output.mp3

Si el servicio tarda en responder por primera vez, es normal (descarga de modelos).