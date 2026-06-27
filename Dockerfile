FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (smaller layer, saves ~1.5 GB vs default)
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
# Skip torch line already installed above
RUN grep -v "^torch" requirements.txt | pip install --no-cache-dir -r /dev/stdin

COPY . .

# Pre-download the model at build time so startup is fast
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='cardiffnlp/twitter-xlm-roberta-base-sentiment', device=-1)"

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
