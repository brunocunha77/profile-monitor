FROM python:3.12-slim
WORKDIR /app
COPY collector/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY collector ./collector
ENV PYTHONUNBUFFERED=1 MONITOR_SESSION_ROOT=/data/state
CMD ["python", "collector/manager.py"]