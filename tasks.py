import celery
import os
import pandas as pd

celery_app = celery.Celery('query')

celery_app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

@celery_app.task()
def download_archived_data(station_id, start_year, start_month, end_year, end_month, frequency, url):
    """
    Downloads the requested station data
    :param station_id: Station ID from Env Can
    :param start_year: User selected first year
    :param start_month: User selected first month
    :param end_year: User selected end year
    :param end_month: User selected end month
    :param frequency: User selected data interval
    :param url: url path to station of interest
    :return: Data Frame for station spanning defined period
    """
    download_dates = pd.date_range(start=str(start_year) + '/' + str(start_month),
                                   end=str(end_year) + '/' + str(end_month), freq='M')
    li = []
    for date in download_dates:
        if frequency == 'Hourly':
            li.append(pd.read_csv(url.format(str(station_id), date.year, date.month, 1)))
        elif frequency == 'Daily':
            li.append(pd.read_csv(url.format(str(station_id), date.year, date.month, 2)))
        else:
            li.append(pd.read_csv(url.format(str(station_id), date.year, date.month, 3)))
    return pd.concat(li).to_json(date_format='iso', orient='split')