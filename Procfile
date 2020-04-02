web: gunicorn index:app.server --workers 3 -k gevent --worker-connections 100 --max-requests 600 --log-file=-
worker: celery -A tasks worker -Ofair --pool=gevent --concurrency=100 --loglevel=info