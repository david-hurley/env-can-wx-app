web: gunicorn index:app.server -w 2 -k gevent
worker: celery -A tasks worker --loglevel=info
