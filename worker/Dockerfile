FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Reutilizamos el requirements.txt único
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código del Worker
COPY ./worker /app

CMD ["python", "worker.py"]
