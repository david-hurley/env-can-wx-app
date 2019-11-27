web: gunicorn -w 1 index:app.server --worker-class=gevent
worker: celery -A tasks worker -1 --loglevel=info --concurrency 2