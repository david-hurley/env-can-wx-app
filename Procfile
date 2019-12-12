web: gunicorn index:app.server -w 4 -k gevent --log-file=-
worker: celery -A tasks worker --loglevel=info