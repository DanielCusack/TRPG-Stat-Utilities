# TRPG Stat Utilities

Django/FastAPI project for a service that offers various "fun" stats for various TRPGs (eventually) via a website or REST API

Current games included:
- FE9

## How it works

A single ASGI application (`combined_asgi.py`) mounts two things:

- **Django** at `/` — the server-rendered stat checker page
- **FastAPI** at `/api` — the JSON API

Game data lives in `db.sqlite3`, which is committed to the repository and baked
into the production image. It is **read-only in production**: the app only ever
reads at runtime, so data changes are made in development and shipped as part
of a deploy.

## Requirements

- Python 3.13
- [pipenv](https://pipenv.pypa.io/)
- Docker + Docker Compose (only needed for the container workflows)

## Development

Install dependencies:

```bash
pipenv install --dev
```

### Running the site

For the web page only, Django's dev server is the quickest option:

```bash
pipenv run python manage.py runserver
```

Then visit http://localhost:8000. Admin is available at http://localhost:8000/admin/.

> **Note:** `runserver` uses Django's URLconf and therefore does **not** serve
> the `/api` routes — they return 404. Use one of the options below if you need
> the API.

### Running the site *and* the API

To serve both, run the combined ASGI app the same way production does:

```bash
pipenv run uvicorn combined_asgi:application --reload
```

This serves the page at http://localhost:8000, the API under
http://localhost:8000/api, and interactive API docs at
http://localhost:8000/api/docs.

### Running in Docker

```bash
docker compose up
```

Serves http://localhost:8000 with the source bind-mounted and auto-reload
enabled. This uses development settings, so the database stays writable and
admin is available.

### Tests

```bash
pipenv run pytest
```

## Production deployment

The production stack runs the app behind nginx, which serves static files
directly and proxies everything else.

### 1. Create the environment file

```bash
cp .env.example .env
```

Generate a secret key and put it in `.env` as `DJANGO_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

> Use `token_urlsafe` rather than Django's `get_random_secret_key()`. The
> latter's alphabet includes `$`, which Docker Compose treats as variable
> interpolation and will silently mangle. If you must use a key containing
> `$`, escape each one as `$$`.

Also set `DJANGO_ALLOWED_HOSTS` to the hostnames/IPs the site is served on
(comma-separated). Compose will refuse to start if `.env` is missing.

### 2. Start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The site is then available on http://localhost (port 80). The same command
redeploys after any change.

### 3. Check it is healthy

```bash
curl http://localhost/api/health
```

### Logs and shutdown

```bash
docker compose -f docker-compose.prod.yml logs -f app
```

```bash
docker compose -f docker-compose.prod.yml down
```

### Adding TLS / a domain

`nginx/nginx.conf` has a single HTTP server block — add a TLS listener and set
`server_name` there. Then set `DJANGO_SECURE_SSL=1` in `.env` to enable
HTTPS redirects, HSTS and secure cookies. Leave it at `0` until TLS actually
terminates at the proxy, otherwise the redirect will loop.

## Updating game data

Production never writes to the database, so data and schema changes follow a
deploy rather than being edited live:

1. Make the change locally (scraper, admin, or `manage.py shell`) — this writes `db.sqlite3`.
2. If models changed, run `pipenv run python manage.py makemigrations` and `migrate`.
3. Run the tests.
4. Commit the updated `db.sqlite3` together with any migrations.
5. Redeploy: `docker compose -f docker-compose.prod.yml up -d --build`.

Do not run `migrate` against production — the database is opened read-only and
the image already ships a migrated copy.

## Settings

Settings are split into a package; pick one with `DJANGO_SETTINGS_MODULE`.

| | `mysite.settings.dev` (default) | `mysite.settings.prod` |
|---|---|---|
| `DEBUG` | `True` | `False` |
| Database | Read-write | Read-only (`mode=ro`) |
| Admin | Enabled | Not routed (404) |
| Static files | Served by WhiteNoise, unhashed | Built by `collectstatic`, served by nginx |
| Secret key | Hardcoded dev value | Required from environment |
| `django_extensions` | Installed | Not installed |

`manage.py`, `pytest` and the ASGI/WSGI entrypoints default to `dev`. The
Docker image sets `prod`.

## Endpoints

| Path | Description |
|---|---|
| `/` | Stat checker page |
| `/admin/` | Django admin (development only) |
| `/api/health` | Readiness check — also confirms the database is readable |
| `/api/names` | List of available character names |
| `/api/percentiles` | POST character stats, returns a percentile per stat |
| `/api/docs` | Interactive API documentation |

---

This project is an unofficial fan-made utility and is not affiliated with or endorsed by Nintendo or Intelligent Systems
