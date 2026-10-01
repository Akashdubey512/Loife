# ML Service Dockerfile for reServe AI
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY ml/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ml/ ./ml/
COPY cv/ ./cv/
COPY models/ ./models/

EXPOSE 8001

CMD ["python", "-m", "ml.service"]
