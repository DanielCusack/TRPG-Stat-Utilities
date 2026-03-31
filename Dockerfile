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

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "combined_asgi:application", "--host", "0.0.0.0", "--port", "8000"]

