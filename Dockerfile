FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 5001

# init-db is idempotent (CREATE TABLE IF NOT EXISTS), so it's safe on every start
CMD ["sh", "-c", "flask --app src.watches_app init-db && gunicorn --bind 0.0.0.0:5001 --workers 1 --threads 4 'src.watches_app:create_app()'"]
