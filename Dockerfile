# ---------------------------------------------------------------------------
# Dockerfile — Production-ready RenovaSim AI image
# ---------------------------------------------------------------------------

FROM python:3.13-slim

WORKDIR /app

# Security: run as non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Own files as appuser
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Production: no --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]