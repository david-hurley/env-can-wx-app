web: gunicorn index:app.server --log-file=-
worker: celery -A tasks workers 2 --loglevel=info --concurrency=4 -k gevent --timeout 600