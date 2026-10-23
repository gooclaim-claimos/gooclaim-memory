# Build from the repository root: docker build -f server/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

# libpq for psycopg (upstream requirements pin bare `psycopg` with no libpq in
# the slim base → "no pq wrapper available"). psycopg[binary] bundles libpq.
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.2.8"

# GOOCLAIM DEVIATION: mem0 from THIS checkout, never PyPI (see requirements.txt).
COPY pyproject.toml README.md /opt/mem0-src/
COPY mem0 /opt/mem0-src/mem0
RUN pip install --no-cache-dir /opt/mem0-src

COPY server/ .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
