FROM python:3.11-slim

WORKDIR /app
RUN apt-get update &&  apt-get install -y build-essential pkg-config libcairo2-dev libgirepository1.0-dev

COPY . /app
# COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt


ENV DATABASE_URL=sqlite:///./billing.db

EXPOSE 8000

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8001"]
