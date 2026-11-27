FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY wsgi.py gunicorn.conf.py ./

FROM base AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pytest.ini .
COPY tests tests
CMD ["pytest", "-v"]

FROM base AS runtime
ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ARG FAULT_RATE=0
ENV APP_VERSION=${APP_VERSION} GIT_SHA=${GIT_SHA} FAULT_RATE=${FAULT_RATE}
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin eventhub
USER 10001
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
