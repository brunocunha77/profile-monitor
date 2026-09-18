FROM python:3.12-slim
WORKDIR /app
COPY collectors/instagram/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY collectors/instagram ./collectors/instagram
ENV PYTHONUNBUFFERED=1 INSTAGRAM_SESSION_ROOT=/data/instagram
CMD ["python", "collectors/instagram/manager.py"]
