FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Installiere Node und npm
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Kopiere Python requirements
COPY docker/requirements.txt /code/
RUN pip install -r /code/requirements.txt

# Kopiere alles
COPY . /code/

EXPOSE 80

CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]
