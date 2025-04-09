FROM python:3.13-slim

RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

COPY dependencies.txt ./
RUN pip install --no-cache-dir -r dependencies.txt

RUN python -m nltk.downloader punkt

RUN mkdir -p /app/cache

VOLUME ["/app/cache"]

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
