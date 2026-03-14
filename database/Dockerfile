# python:3.12-slim — digest pinned 2026-03-14; update with: docker manifest inspect python:3.12-slim
FROM python:3.12-slim@sha256:ccc7089399c8bb65dd1fb3ed6d55efa538a3f5e7fca3f5988ac3b5b87e593bf0

WORKDIR /app

RUN pip install --no-cache-dir alembic psycopg2-binary sqlalchemy

COPY alembic.ini .
COPY migrations/ migrations/

CMD ["alembic", "upgrade", "head"]
