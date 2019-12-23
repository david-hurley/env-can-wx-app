import celery
import pandas as pd
import os
import s3fs

celery_app = celery.Celery('download')
celery_app.conf.update(
    broker_url=os.environ['REDIS_URL'],
    result_backend=os.environ['REDIS_URL'],
    redis_max_connections=4)

@celery_app.task(bind=True)
def download_remote_data(self, station_id, start_year, start_month, end_year, end_month, frequency, url_raw):

    download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                   end=str(end_year) + '/' + str(end_month), freq='M')

    if frequency == 'Hourly':
        urls = [url_raw.format(station_id, date.year, date.month, 1) for date in download_dates]
        data = pd.concat((pd.read_csv(url) for url in urls))
    elif frequency == 'Daily':
        urls = [url_raw.format(station_id, date.year, date.month, 2) for date in download_dates]
        data = pd.concat((pd.read_csv(url) for url in urls))
    else:
        urls = [url_raw.format(station_id, date.year, date.month, 3) for date in download_dates]
        data = pd.concat((pd.read_csv(url) for url in urls))

    filename = 'ENV-CAN' + '-' + frequency + '-' + 'Station' + str(station_id) + '-' + str(start_year) + '-' + str(end_year) + '.csv'

    # Send data to S3
    s3 = s3fs.S3FileSystem(anon=False,
                           key=os.environ['AWS_ACCESS_KEY_ID'],
                           secret=os.environ['AWS_SECRET_ACCESS_KEY'])
    with s3.open(os.environ['S3_BUCKET']+'/'+filename, 'w') as f:
        data.to_csv(f)

    # Filter for memory storage
    data = data[[x for x in data if not x.endswith('Flag')]]
    cols_to_keep = ('Station Name', 'Climate ID', 'Date/Time', 'Temp', 'Wind', 'Mean', 'Total', 'Snow')
    data = data[[x for x in data if x.startswith(cols_to_keep)]]

    return data.to_dict('records')

