# StaffConnect

Internal staff portal for **NovaTech Corporation**. Employees can register, keep a
profile (photo, display name, department, bio), and publish, read, edit and delete
company announcements. HR administers users and content through the Django Admin.

**Docker image:** https://hub.docker.com/r/<your-dockerhub-username>/staffconnect

## Features

- Registration, login, logout (POST only) and password reset by email
- Profile page with avatar (default placeholder when no photo) and Edit Profile
- Announcements: paginated list, detail by slug, create / edit / delete (owner only)
- Server-side validation of avatar uploads (type and size)
- Django Admin for HR (search, filters, date drill-down)
- Runs in Docker; all secrets come from environment variables

## Tech stack

Python 3.11 - Django 4.2 - SQLite (PostgreSQL via `DATABASE_URL`) - Pillow -
python-decouple - Docker

## Run locally (about 5 minutes)

```bash
git clone <repository-url>
cd staff-connect

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
# Generate a secret key and paste it into .env as SECRET_KEY=...
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 (site) and http://127.0.0.1:8000/admin/ (admin).
With the default `.env.example`, password-reset emails are printed in the terminal.

Run the tests:

```bash
python manage.py test
```

## Run with Docker

```bash
# 1. Build the image
docker build -t staffconnect:v1.0.0 .

# 2. Run it (secrets are passed at runtime, they are NOT in the image)
docker run --rm -p 8000:8000 --env-file .env -v staffconnect_media:/app/media staffconnect:v1.0.0
```

Open http://localhost:8000. The `-v staffconnect_media:/app/media` volume keeps uploaded
avatars when the container restarts. Migrations are applied automatically on start.

### Push to Docker Hub

```bash
docker login
docker tag staffconnect:v1.0.0 <your-dockerhub-username>/staffconnect:v1.0.0
docker push <your-dockerhub-username>/staffconnect:v1.0.0
```

Public registry URL: https://hub.docker.com/r/<your-dockerhub-username>/staffconnect

### Notes for the DevOps team (Kubernetes)

- Provide the variables below through a Kubernetes `Secret` / `ConfigMap`.
- Mount a persistent volume at `/app/media`.
- Set `DATABASE_URL` to use PostgreSQL (install a PostgreSQL driver such as
  `psycopg2-binary` in the image first).
- The container uses Django's development server, as required by the course brief.
  For real production traffic, put a production WSGI server (e.g. gunicorn) in front.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | yes | Django secret key. Keep it private. |
| `DEBUG` | no (default `False`) | `True` for development. Media files are only served by Django when `True`. |
| `ALLOWED_HOSTS` | no | Comma-separated hosts, default `localhost,127.0.0.1`. |
| `CSRF_TRUSTED_ORIGINS` | no | Comma-separated origins, e.g. `https://staff.novatech.example`. |
| `DATABASE_URL` | no | e.g. `postgres://user:pass@host:5432/db`. SQLite is used when empty. |
| `EMAIL_BACKEND` | no | Default prints emails to the console. Use `django.core.mail.backends.smtp.EmailBackend` for SMTP. |
| `EMAIL_HOST` | for SMTP | SMTP server, e.g. `smtp.gmail.com`. |
| `EMAIL_PORT` | for SMTP | Default `587`. |
| `EMAIL_USE_TLS` | no | Default `True`. |
| `EMAIL_HOST_USER` | for SMTP | SMTP username. |
| `EMAIL_HOST_PASSWORD` | for SMTP | SMTP password / app password. |
| `DEFAULT_FROM_EMAIL` | no | Sender address of password reset emails. |

## Project structure

```
staff-connect/
├── Dockerfile, docker-entrypoint.sh, .dockerignore
├── requirements.txt, .env.example, .gitignore
├── manage.py
├── config/      settings, root urls, wsgi
├── users/       Profile model, auth views, forms, validators, admin
├── posts/       Post model, class-based views, admin
├── templates/   base.html, home.html, 404.html, users/, posts/
├── static/      css/, img/
└── media/       user uploads (git-ignored)
```
