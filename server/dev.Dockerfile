FROM python:3.12

WORKDIR /app

# Copy requirements first for better caching
COPY server/requirements.txt .
RUN pip install -r requirements.txt

# GOOCLAIM DEVIATION: mem0 is installed from THIS checkout, into site-packages,
# outside /app — compose bind-mounts server/ over /app, which hid an install
# under /app/packages and is why the compose command used to re-install mem0ai
# from PyPI (unpinned) on every start. The image now runs exactly the commit it
# was built from. Upstream also installed Poetry by piping a script from the
# internet; nothing here uses it.
WORKDIR /opt/mem0-src
COPY pyproject.toml README.md ./
COPY mem0 ./mem0
RUN pip install --no-cache-dir ".[graph]"

# Return to app directory and copy server code
WORKDIR /app
COPY server .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
