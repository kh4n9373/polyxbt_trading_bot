FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cron_run.py .  
COPY app/ app/  

CMD ["python", "-u", "cron_run.py"]