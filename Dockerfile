FROM python:3.11-slim
WORKDIR /app
COPY LMT_Server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY LMT_Server /app/LMT_Server
COPY LMT_Script /app/LMT_Script
COPY config /app/config
WORKDIR /app/LMT_Server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main:app"]
