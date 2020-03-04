import celery
import pandas as pd
import os
import s3fs
import numpy as np

celery_app = celery.Celery('download')
celery_app.conf.update(
    broker_url=os.environ['REDIS_URL'],
    result_backend=os.environ['REDIS_URL'],
    redis_max_connections=4,
    broker_transport_options={
        'max_connections': 4
    },
    broker_pool_limit=0)

@celery_app.task(bind=True, soft_time_limit=1200)
def download_remote_data(self, station_id, start_year, start_month, end_year, end_month, frequency, url_raw):

    if frequency == 'Hourly':
        download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                       end=str(end_year) + '/' + str(end_month), freq='M')
        urls = [url_raw.format(station_id, date.year, date.month, 1) for date in download_dates]
        data = pd.concat((pd.read_csv(url) for url in urls))
    elif frequency == 'Daily':
        if start_year == end_year:
            url = url_raw.format(station_id, start_year, start_month, 2)
            data = pd.read_csv(url)
        else:
            download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                           end=str(end_year+1) + '/' + str(end_month), freq='Y')
            urls = [url_raw.format(station_id, date.year, date.month, 2) for date in download_dates]
            data = pd.concat((pd.read_csv(url) for url in urls))
        data = data[(pd.to_datetime(data['Date/Time']) >= pd.to_datetime(str(start_year)+'-'+str(start_month)+'-01'))
                    & (pd.to_datetime(data['Date/Time']) <= pd.to_datetime(str(end_year)+'-'+str(end_month)+'-01')-pd.DateOffset(1))]
    else:
        url = url_raw.format(station_id, start_year, start_month, 3)
        data = pd.read_csv(url)
        data = data[(pd.to_datetime(data['Date/Time']) >= pd.to_datetime(str(start_year)+'-'+str(start_month)))
                    & (pd.to_datetime(data['Date/Time']) <= pd.to_datetime(str(end_year)+'-'+str(end_month))-pd.DateOffset(1))]

    filename = 'ENV-CAN' + '-' + frequency + '-' + 'Station' + str(station_id) + '-' + str(start_year) + '-' + str(end_year) + '.csv'

    # Send data to S3
    s3 = s3fs.S3FileSystem(anon=False,
                           key=os.environ['AWS_ACCESS_KEY_ID'],
                           secret=os.environ['AWS_SECRET_ACCESS_KEY'])
    with s3.open(os.environ['S3_BUCKET']+'/'+filename, 'w') as f:
        data.to_csv(f)

    # Filter for memory storage
    data_filt = data[[x for x in data if not x.endswith('Flag')]]
    cols_to_keep = ('Date/Time', 'Temp', 'Wind', 'Mean', 'Total', 'Snow')
    data_filt = data_filt[[x for x in data_filt if x.startswith(cols_to_keep)]]
    vals_to_remove = ['B', 'E', 'M', 'S', 'T', 'A', 'C', 'F', 'L', 'N', 'Y']
    data_filt = data_filt.replace(vals_to_remove, np.nan)
    data_filt = data_filt.dropna(how='all', axis=1)
    data_filt_col_names = {c: i for i, c in enumerate(data_filt.columns)}

    return data_filt_col_names

