from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import os

app = FastAPI()

@app.post("/detect-edges")
async def detect_edges(file: UploadFile = File(...)):
    # Leer imagen como array de bytes
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse(status_code=400, content={"error": "Imagen inválida"})

    # Detectar bordes con Canny
    edges = cv2.Canny(img, 100, 200)

    # Guardar resultado en disco
    result_path = f"/data/edges_{file.filename}"
    cv2.imwrite(result_path, edges)

    return {"message": "Bordes detectados", "file": result_path}

@app.get("/health")
def health():
    return {"status": "ok"}
