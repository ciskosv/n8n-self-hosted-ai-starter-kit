FROM python:3.10-slim

# Dependencias del sistema para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Dependencias Python
RUN pip install --no-cache-dir \
    fastapi==0.88.0 \
    uvicorn==0.20.0 \
    httpx==0.23.0 \
    python-multipart==0.0.6 \
    pymupdf==1.21.1 \
    pillow==9.3.0 \
    numpy==1.24.1 \
    opencv-python==4.5.4.60

EXPOSE 5020
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5020"]
