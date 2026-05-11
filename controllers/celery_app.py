import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

app = Celery("travelpipe", broker=BROKER_URL, backend=RESULT_BACKEND)

app.conf.update(
    task_default_queue="parquet_writes",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

app.autodiscover_tasks(["controllers"])
