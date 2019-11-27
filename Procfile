web: gunicorn index:app.server -w 4 -k gevent
worker: celery -A tasks worker --loglevel=info
