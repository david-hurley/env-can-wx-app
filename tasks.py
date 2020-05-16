import celery
import pandas as pd
import os
import boto3
import numpy as np

from io import StringIO

######################################### HELPER FUNCTIONS #############################################################

#  function to query column names of s3 file
def query_header_name_s3(s3, filename):

    resp = s3.select_object_content(
        Bucket=os.environ['S3_BUCKET'],
        Key=filename,
        ExpressionType='SQL',
        Expression='SELECT * FROM s3object s LIMIT 1',
        InputSerialization={'CSV': {"FileHeaderInfo": "None"}},
        OutputSerialization={'CSV': {}},
    )

    records = []
    for event in resp['Payload']:
        if 'Records' in event:
            records.append(event['Records']['Payload'])

    file_str = ''.join(req.decode('utf-8') for req in records)

    headers = pd.read_csv(StringIO(file_str), index_col=0).columns

    return headers

#  function to query data from s3 file
def query_data_s3(s3, filename, sql_stmt, col_names):

    resp = s3.select_object_content(
        Bucket=os.environ['S3_BUCKET'],
        Key=filename,
        ExpressionType='SQL',
        Expression=sql_stmt,
        InputSerialization={'CSV': {"FileHeaderInfo": "Use"}},
        OutputSerialization={'CSV': {}},
    )

    records = []
    for event in resp['Payload']:
        if 'Records' in event:
            records.append(event['Records']['Payload'])

    file_str = ''.join(req.decode('utf-8') for req in records)

    df = pd.read_csv(StringIO(file_str), index_col=None, dtype={'Weather': 'str'}, names=list(col_names))

    return df

#  function to upload file to s3
def upload_csv_S3(df, filename):

    csv_buffer = StringIO()
    df.to_csv(csv_buffer)

    s3_resource = boto3.resource('s3')
    obj = s3_resource.Object(os.environ['S3_BUCKET'], 'tmp/' + filename)
    obj.put(Body=csv_buffer.getvalue())

######################################### CELERY TASK ##################################################################

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
    worker_enable_remote_control=False,  # need this to reduce connections
    result_backend=os.environ['REDIS_URL'],
    redis_max_connections=20
)

@celery_app.task(bind=True, time_limit=180)
def download_remote_data(self, station_name, station_id, start_year, start_month, end_year, end_month, frequency):

    #  setup s3 client
    s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                      aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])

    #  user requested download dates
    start_date = pd.to_datetime('-'.join([start_year, start_month]))
    end_date = pd.to_datetime('-'.join([end_year, end_month]))

    #  format sql statement
    sql_stmt = "SELECT * FROM s3object s WHERE s.\"Date/Time\" BETWEEN '{}' AND '{}'".format(start_date, end_date)

    if frequency == 'Hourly':

        input_filename = '_'.join([station_id, 'hourly.csv'])
        output_filename = '_'.join([station_name.replace(' ', '_'), station_id, start_year, end_year, 'hourly.csv'])

    elif frequency == 'Daily':

        input_filename = '_'.join([station_id, 'daily.csv'])
        output_filename = '_'.join([station_name.replace(' ', '_'), station_id, start_year, end_year, 'daily.csv'])

    else:

        input_filename = '_'.join([station_id, 'monthly.csv'])
        output_filename = '_'.join([station_name.replace(' ', '_'), station_id, start_year, end_year, 'monthly.csv'])

    #  download file headers and csv from s3
    self.update_state(state='PROGRESS', meta={'status': 'WORKING'})

    file_headers = query_header_name_s3(s3, input_filename)
    df = query_data_s3(s3, input_filename, sql_stmt, file_headers)

    #  send csv to s3
    upload_csv_S3(df, output_filename)

    #  keep only relevant columns and store to plot in graphing and make flagged values NaN so plotting looks good
    df_filt = df[[x for x in df if not x.endswith('Flag')]]
    cols_to_keep = ('Date/Time', 'Temp', 'Wind', 'Mean', 'Total', 'Snow')
    df_filt = df_filt[[x for x in df_filt if x.startswith(cols_to_keep)]]
    vals_to_remove = ['B', 'E', 'M', 'S', 'T', 'A', 'C', 'F', 'L', 'N', 'Y']
    df_filt = df_filt.replace(vals_to_remove, np.nan)
    df_filt = df_filt.dropna(how='all', axis=1)
    df_filt_col_names = {c: i for i, c in enumerate(df_filt.columns)}
    df_filt_col_names['status'] = 'COMPLETE'

    return df_filt_col_names
