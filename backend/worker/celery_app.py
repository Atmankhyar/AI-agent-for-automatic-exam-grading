import os
from celery import Celery

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery("exam-corrector", broker=broker_url, backend=broker_url)

app.conf.task_routes = {"tasks.*": {"queue": "default"}}


@app.task
def ping():
    return "pong"
