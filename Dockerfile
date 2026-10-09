# Pinned base image - never use :latest
FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first so Docker can cache the dependency layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the rest of the source code (.env is excluded by .dockerignore)
COPY . .

# Run as a non-root user; make sure it can write the media folder and database
RUN useradd -m appuser \
    && mkdir -p /app/media \
    && chown -R appuser:appuser /app
USER appuser

# Uploaded files (avatars) survive container restarts
VOLUME ["/app/media"]

EXPOSE 8000

# Applies database migrations, then runs the CMD below
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
