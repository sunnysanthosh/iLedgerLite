FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir alembic psycopg2-binary sqlalchemy

COPY alembic.ini .
COPY migrations/ migrations/

CMD ["alembic", "upgrade", "head"]
