FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user
RUN addgroup --system exobios && adduser --system --ingroup exobios exobios

COPY pyproject.toml ./
COPY app/ app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN chown -R exobios:exobios /app

USER exobios

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
