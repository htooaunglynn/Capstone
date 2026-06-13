FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

USER app

EXPOSE 8000

CMD ["gunicorn", "capstone.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
