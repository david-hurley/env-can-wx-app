web: gunicorn index:app.server --log-file=-
worker: celery -A tasks worker -1 --loglevel=info --concurrency=4