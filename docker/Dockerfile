FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY docker/requirements.txt /code/
RUN pip install -r /code/requirements.txt

EXPOSE 80

CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]
