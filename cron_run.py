import asyncio
import schedule
import time
from app.run import run_cron_job

print('CRONJOB START !!!')

def task():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_cron_job())
    loop.close()
    # asyncio.run(run_cron_job())

schedule.every(15).minutes.do(task)

while True:
    schedule.run_pending()
    time.sleep(1)  
