FROM python:3.13-slim

WORKDIR /app

COPY r.txt .

RUN pip install -r r.txt

COPY . .

EXPOSE 8000

ENTRYPOINT [ "gunicorn", "backend.wsgi:application", "--chdir", "backend", "--bind", "0.0.0.0:8000" ]