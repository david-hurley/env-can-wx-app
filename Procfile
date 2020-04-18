web: gunicorn index:app.server -k gevent --worker-connections 100 --max-requests 600 --log-file=-
worker: celery -A tasks worker -Ofair --pool=gevent --loglevel=info