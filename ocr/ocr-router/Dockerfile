FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 👇 Copiar solo requirements primero para caché
WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 👇 Ahora copiar el resto del código
COPY . .

EXPOSE 5020
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5020"]
