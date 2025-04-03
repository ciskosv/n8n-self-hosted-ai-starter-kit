FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg git && \
    pip install git+https://github.com/openai/whisper.git flask

WORKDIR /app
COPY api.py .

CMD ["python", "api.py"]
