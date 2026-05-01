FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY apps/osint_orchestrator /app/apps/osint_orchestrator
COPY shared /app/shared
COPY core /app/core
CMD ["python", "-m", "apps.osint_orchestrator.main"]
