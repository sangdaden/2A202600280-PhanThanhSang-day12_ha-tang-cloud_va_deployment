FROM python:3.11-slim

WORKDIR /app

COPY 05-scaling-reliability/production/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY 05-scaling-reliability/production/app.py /app/app.py
COPY 05-scaling-reliability/production/utils /app/utils

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
