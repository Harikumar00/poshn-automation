FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY requirements.txt .
RUN python -m pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium

COPY . .

# Secrets and environment-specific values must be supplied at runtime.
CMD ["pytest", "-q"]
