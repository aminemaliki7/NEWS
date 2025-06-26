# celery_app.py
import os
from celery import Celery

def make_celery():
    return Celery(
        "realtalk",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/0")
    )

celery = make_celery()
