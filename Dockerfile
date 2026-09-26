FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install -r requirements.lock
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-deps . && useradd --uid 10001 --create-home appuser
COPY data ./data
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "release_catalog.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
