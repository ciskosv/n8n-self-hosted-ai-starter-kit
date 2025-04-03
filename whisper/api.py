from flask import Flask, jsonify, request
import whisper
import os

app = Flask(__name__)
model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    file = request.files['audio']
    filepath = f"./audio/{file.filename}"
    file.save(filepath)
    result = model.transcribe(filepath, language="es")
    os.remove(filepath)
    return {"text": result["text"]}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
