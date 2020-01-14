web: gunicorn index:app.server -w 2 --worker-connections 100 -k gevent --log-file=-
worker: celery -A tasks worker --loglevel=info