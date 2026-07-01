FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8767

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8767"]
