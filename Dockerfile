FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

# Export to requirements.txt
RUN pipenv requirements > requirements.txt


# ---- Final image ----
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=mysite.settings.prod

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# .gitattributes should keep this file LF-only, but a zip download or a client
# that ignores it can still introduce CRLF, which makes sh reject the script
# with "set: Illegal option -". Strip them defensively.
RUN sed -i 's/\r$//' docker-entrypoint.sh

# collectstatic loads production settings, which require a secret key. This one
# is used only for this build step and never at runtime.
RUN DJANGO_SECRET_KEY=build-only-not-a-secret \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# The game data is read-only at runtime; enforce it at the filesystem level too.
RUN chmod 444 db.sqlite3

# Drop privileges. Done after collectstatic so the build can write staticfiles,
# and appuser still owns /app so the entrypoint can refresh them on start.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).status == 200 else 1)"

# Invoked via sh so the script does not need an executable bit, which does not
# survive checkouts on Windows.
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]

CMD ["uvicorn", "combined_asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
