
FROM python:3.12-slim

WORKDIR /app

# System dependencies for pdfplumber and psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency file
COPY pyproject.toml .

# Install all Python packages
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy all project files
COPY . .

# Create uploads folder
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
