FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ffmpeg build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivo principal y requirements
COPY api.py .
COPY requirements.txt .

RUN pip install --no-cache-dir --extra-index-url https://pypi.org/simple -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5000"]
