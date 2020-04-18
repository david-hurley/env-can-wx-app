import celery
import pandas as pd
import os
import s3fs
import numpy as np

celery_app = celery.Celery('download')
celery_app.conf.update(
    # settings for message broker
    broker_url=os.environ['CLOUDAMQP_URL'],
    broker_pool_limit=1,
    broker_heartbeat=None,
    broker_connection_timeout=30,
    event_queue_expires=60,
    worker_prefetch_multiplier=1,
    worker_concurrency=16,
    result_backend=os.environ['REDIS_URL'],
    redis_max_connections=20
)

@celery_app.task(bind=True, time_limit=1200)
def download_remote_data(self, station_id, start_year, start_month, end_year, end_month, frequency, url_raw):

    # create download dates and urls based on user selected download frequency
    if frequency == 'Hourly':
        download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                       end=str(end_year) + '/' + str(end_month), freq='M')
        urls = [url_raw.format(station_id, date.year, date.month, 1) for date in download_dates]

    elif frequency == 'Daily' and start_year == end_year:
        urls = [url_raw.format(station_id, start_year, start_month, 2)]

    elif frequency == 'Daily' and start_year < end_year:
        download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                       end=str(end_year + 1) + '/' + str(end_month), freq='Y')
        urls = [url_raw.format(station_id, date.year, date.month, 2) for date in download_dates]
    else:
        urls = [url_raw.format(station_id, start_year, start_month, 3)]

    # download csv data to dataframe from environment canada page
    data_temp = []
    for i, url in enumerate(urls):
        percent_complete = str(round((i / len(urls)) * 100, 0))
        self.update_state(state='PROGRESS', meta={'current_percent_complete': percent_complete})
        data_temp.append(pd.read_csv(url))
    data = pd.concat(data_temp)

    # we want the download data to match the user request so filter the data on download dates
    if frequency == 'Daily' and start_year < end_year:
        data = data[(pd.to_datetime(data['Date/Time']) >= pd.to_datetime(str(start_year) + '-' + str(start_month) + '-01'))
                    & (pd.to_datetime(data['Date/Time']) <= pd.to_datetime(str(end_year) + '-' + str(end_month) + '-01') - pd.DateOffset(1))]
    elif frequency == 'Monthly':
        data = data[(pd.to_datetime(data['Date/Time']) >= pd.to_datetime(str(start_year) + '-' + str(start_month)))
                    & (pd.to_datetime(data['Date/Time']) <= pd.to_datetime(str(end_year) + '-' + str(end_month)) - pd.DateOffset(1))]

    # create filename of download file
    filename = 'ENV-CAN' + '-' + frequency + '-' + 'Station' + str(station_id) + '-' + str(start_year) + '-' + str(end_year) + '.csv'

    # send data to S3 for user to download
    s3 = s3fs.S3FileSystem(anon=False,
                           key=os.environ['AWS_ACCESS_KEY_ID'],
                           secret=os.environ['AWS_SECRET_ACCESS_KEY'])
    with s3.open(os.environ['S3_BUCKET']+'/'+filename, 'w') as f:
        data.to_csv(f)

    # keep only relevant columns and store to plot in graphing and make flagged values NaN so plotting looks good
    data_filt = data[[x for x in data if not x.endswith('Flag')]]
    cols_to_keep = ('Date/Time', 'Temp', 'Wind', 'Mean', 'Total', 'Snow')
    data_filt = data_filt[[x for x in data_filt if x.startswith(cols_to_keep)]]
    vals_to_remove = ['B', 'E', 'M', 'S', 'T', 'A', 'C', 'F', 'L', 'N', 'Y']
    data_filt = data_filt.replace(vals_to_remove, np.nan)
    data_filt = data_filt.dropna(how='all', axis=1)
    data_filt_col_names = {c: i for i, c in enumerate(data_filt.columns)}
    data_filt_col_names['current_percent_complete'] = '100'  # include final percent complete

    return data_filt_col_names
