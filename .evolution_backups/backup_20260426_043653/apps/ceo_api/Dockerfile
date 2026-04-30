FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY apps/ceo_api /app/apps/ceo_api
COPY shared /app/shared
COPY core /app/core
CMD ["uvicorn", "apps.ceo_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
