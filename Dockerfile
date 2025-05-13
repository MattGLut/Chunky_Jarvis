FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ backend/
COPY frontend/ frontend/
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
