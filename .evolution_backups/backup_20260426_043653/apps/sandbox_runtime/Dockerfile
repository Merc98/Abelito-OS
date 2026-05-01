FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY apps/sandbox_runtime /app/apps/sandbox_runtime
COPY core /app/core
COPY shared /app/shared
CMD ["python", "-m", "apps.sandbox_runtime.main"]
