FROM python:3.11-slim AS runtime

RUN groupadd -r app && useradd -r -g app -d /app app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY utils ./utils

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
	CMD sh -c 'python -c "import os, urllib.request; urllib.request.urlopen(\"http://localhost:\" + os.getenv(\"PORT\", \"8000\") + \"/health\")"' || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30"]
