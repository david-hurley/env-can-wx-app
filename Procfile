web: gunicorn index:app.server --log-file=-
worker: celery -A tasks worker --loglevel=info