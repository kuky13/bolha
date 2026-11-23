FROM python:3.12-slim
WORKDIR /app
COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bolha/__init__.py bolha/versioning.py bolha/reports.py bolha/
COPY service/report_gateway.py .
USER 65532:65532
CMD ["uvicorn", "report_gateway:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
