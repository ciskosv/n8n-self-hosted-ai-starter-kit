from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Cargamos un pipeline para análisis de texto clínico
# Puedes cambiar el modelo por otro más específico si lo deseas
nlp = pipeline("ner", model="emilyalsentzer/Bio_ClinicalBERT", grouped_entities=True)

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
def analyze_text(req: TextRequest):
    result = nlp(req.text)
    return {"entities": result}

@app.get("/health")
def health():
    return {"status": "ok"}
