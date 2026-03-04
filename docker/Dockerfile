FROM node:20-bullseye as builder

WORKDIR /code
COPY workout-frontend/package*.json ./workout-frontend/
RUN cd workout-frontend && npm install --legacy-peer-deps

COPY workout-frontend/ ./workout-frontend/
RUN cd workout-frontend && npm run build

# ============ Production Stage ============
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Installiere Node für runtime (falls nötig)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Kopiere Python requirements
COPY docker/requirements.txt /code/
RUN pip install -r /code/requirements.txt

# Kopiere React build output vom builder stage
COPY --from=builder /code/workout-frontend/dist /code/static/workout/

# Kopiere alles andere
COPY . /code/

EXPOSE 80

CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]
