web: gunicorn -w 1 index:app.server --worker-class=gevent
worker: celery -A tasks worker --loglevel=info