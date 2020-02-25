import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import tasks
from flask import redirect
import boto3
from celery.result import AsyncResult
from tasks import celery_app
import base64

from app import app

######################################### DATA INPUTS AND LINKS ########################################################

# Environment Canada - Station List and Metadata
df = pd.read_csv('station-metadata-processed.csv')
df.replace(np.nan, 'N/A', inplace=True)
today = datetime.today()
yearnow = today.year-1
df['Last Year'].loc[df['Last Year'] == yearnow] = yearnow+1
df['Last Year (Hourly)'].loc[df['Last Year (Hourly)'] == yearnow] = yearnow+1
df['Last Year (Daily)'].loc[df['Last Year (Daily)'] == yearnow] = yearnow+1
df['Last Year (Monthly)'].loc[df['Last Year (Monthly)'] == yearnow] = yearnow+1

# URL Path to Bulk Download Data from Environment Canada
bulk_data_pathname = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?' \
                     'format=csv&stationID={}&Year={}&Month={}&Day=1&timeframe={}'

# Preload Spinner to Base64 Encode
spinner = base64.b64encode(open(os.path.join('assets', 'spinner.gif'), 'rb').read())

######################################### HELPER FUNCTIONS #############################################################


def compute_great_circle_distance(lat_user, lon_user, lat_station, lon_station):

    lat1, lon1 = np.radians([np.float64(lat_user), np.float64(lon_user)])
    lat2, lon2 = np.radians([lat_station, lon_station])
    a = np.sin((lat2 - lat1) / 2.0) ** 2 + np.cos(lat1) * \
        np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2
    earth_radius_km = 6371
    return earth_radius_km * 2 * np.arcsin(np.sqrt(a))


######################################### PLOTS ########################################################################


# Plot the station map
def station_map(stations, lat_selected, lon_selected, name_selected, color):
    return {'data': [
        # Station Data
        {'type': 'scattermapbox',
         'lat': stations.Latitude,
         'lon': stations.Longitude,
         'name': '',
         'text': stations.Name,
         'marker': {'color': color}
         },
        # Highlight Selected Station With Red Dot
        {'type': 'scattermapbox',
         'lat': [lat_selected],
         'lon': [lon_selected],
         'name': '',
         'text': [name_selected],
         'marker': {'color': 'red'}
         }
    ], 'layout': {
        'showlegend': False,
        'uirevision': 'static',
        'height': 450,
        'mapbox': {
            'style': 'basic',
            'center': {'lat': 59, 'lon': -97},
            'zoom': 2.5,
            'accesstoken': os.environ['MAPBOX_TOKEN']
        },
        'margin': {
            'l': 0, 'r': 0, 'b': 0, 't': 0
        },
    }
    }


######################################### LAYOUT #######################################################################


layout = html.Div([
    # Hold task-id and task-status hidden
    html.Div(id='task-id', children='none', style={'display': 'none'}),
    html.Div(id='task-status', children='none', style={'display': 'none'}),
    html.Div(id='message-status', children='none', style={'display': 'none'}),
    # Update refresh interval to avoid Heroku timeout on preload spinner
    dcc.Interval(
        id='task-interval',
        interval=250,  # in milliseconds
        n_intervals=0
    ),
    # Title Block container
    html.Div([
        html.Div([
            html.H3("Weather History Canada")
        ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
        html.Div([
            dcc.Link('About', href='/pages/about')
        ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
    ], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'}),

    # Filtering, map, table, download container
    html.Div([
        # Map and table container
        html.Div([
            # Map container
            html.Div([
                # Map of stations
                dcc.Graph(id='station-map',
                          figure=station_map(df, [], [], [], 'blue'),
                          style={'border': '2px black solid'})
            ]),
            # Table container
            html.Div([
                html.H6('Click on station in map and select in table below prior to generating data', style={
                    'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                # List of selected station features
                dash_table.DataTable(id='selected-station',
                                     columns=[{"name": col, "id": col} for col in df.columns],
                                     data=[],
                                     style_table={'overflowX': 'scroll'},
                                     style_header={'border': '1px solid black',
                                                   'backgroundColor': 'rgb(200, 200, 200)'},
                                     style_cell={'border': '1px solid grey'},
                                     row_selectable='single'),
                html.Label('(Multiple stations at the same location may exist)',
                           style={'textAlign': 'left', 'font-weight': 'bold'})
            ], style={'margin-top': '1rem'}),
        ], className='seven columns', style={'margin-top': '1rem'}),

        # Filtering and download container
        html.Div([
            # Filtering container
            html.Div([
                html.Div([
                    html.Label("Station Name:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Input(id='station-name', value='', type='text', placeholder='Enter Station Name',
                              style={'width': '50%'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Province:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Dropdown(id='province',
                                 options=[{'label': province, 'value': province} for province in df.Province.unique()],
                                 style={'width': '90%'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Data Interval:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Dropdown(id='frequency',
                                 options=[{'label': frequency, 'value': frequency} for frequency in
                                          ['Hourly', 'Daily', 'Monthly']],
                                 style={'width': '90%'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Data Available Between:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='first-year',
                                     options=[{'label': str(year), 'value': str(year)} for year in
                                              range(1840, datetime.now().year + 1, 1)],
                                     placeholder='First Year')
                    ], style={'width': '40%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id='last-year',
                                     options=[{'label': str(year), 'value': str(year)} for year in
                                              range(1840, datetime.now().year + 1, 1)],
                                     placeholder='Last Year')
                    ], style={'width': '40%', 'display': 'inline-block', 'margin-left': '1rem'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Distance Filter:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Input(id='latitude', value='', type='text', placeholder='Latitude', style={'width': 150})
                    ], style={'display': 'inline-block', 'vertical-align': 'middle'}),
                    html.Div([
                        dcc.Input(id='longitude', value='', type='text', placeholder='Longitude', style={'width': 150})
                    ], style={'display': 'inline-block', 'margin-left': '1rem', 'vertical-align': 'middle'}),
                    html.Div([
                        dcc.Dropdown(id='radius',
                                     options=[{'label': radius, 'value': radius} for radius in
                                              ['10', '25', '50', '100']],
                                     placeholder='Kilometers From Location')
                    ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'middle',
                              'margin-left': '1rem'})
                ], style={'margin-left': '1rem', 'margin-bottom': '1rem'})
            ], style={'margin-bottom': '1rem', 'border': '2px black solid', 'textAlign': 'left'}),

            # Download Container
            html.Div([
                html.Div([
                    html.Label('Download Dates:',
                               style={'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='download-year-start',
                                     options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                     placeholder='Start Year')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-bottom': '1rem'}),
                    html.Div([
                        dcc.Dropdown(id='download-month-start',
                                     options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                     placeholder='Start Month')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem',
                              'margin-bottom': '1rem'}),
                    html.Div([
                        dcc.Dropdown(id='download-year-end',
                                     options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                     placeholder='End Year')
                    ], style={'width': '45%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id='download-month-end',
                                     options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                     placeholder='End Month')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem'}),
                    html.Div([
                        html.Label(id='download-message', children='')
                    ], style={'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}),
                ], style={'width': '55%', 'display': 'inline-block', 'margin-left': '1rem'}),
                html.Div([
                    html.Label('Download Interval:',
                               style={'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='download-frequency',
                                     options=[{'label': frequency, 'value': frequency} for frequency in
                                              ['Select A Station']],
                                     placeholder='Frequency')
                    ], style={'width': '85%', 'margin-bottom': '2rem'}),
                    html.Div([
                        html.A(id='generate-data-button', children='1. GENERATE DATA')
                    ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px red dashed', 'width': '85%',
                              'text-align': 'left'}),
                    html.Div(id='toggle-button-vis', children=[
                        html.Div([
                            html.A(id='download-data-button', children='2. DOWNLOAD DATA')
                        ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px green dashed', 'width': '85%',
                                  'text-align': 'left', 'margin-top': '1.5rem'}),
                        html.Div([
                            html.A('3. GRAPH DATA', id='graph-data-button', href="/pages/graph_page")
                        ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px blue dashed', 'width': '85%',
                                  'text-align': 'left', 'margin-top': '1.5rem'}),
                        ], style={'visibility': 'hidden'}),
                    html.Div(id='spinner', children=[html.Img(src='data:image/gif;base64,{}'.format(spinner.decode())),
                                                     html.Label('Please be patient. A 10 year download may take a few minutes.')],
                             style={'visibility': 'hidden'}),
                ], style={'width': '40%', 'display': 'inline-block', 'margin-left': '6rem'}),
            ], style={'display': 'flex'})
        ], className='five columns', style={'margin-top': '1rem'}),
    ], className='row')
])


######################################### INTERACTION CALLBACKS ########################################################

# Filter Data and Output to Station Map and Table Data
@app.callback(
    [Output(component_id='station-map', component_property='figure'),
     Output(component_id='selected-station', component_property='data')],
    [Input(component_id='province', component_property='value'),
     Input(component_id='frequency', component_property='value'),
     Input(component_id='first-year', component_property='value'),
     Input(component_id='last-year', component_property='value'),
     Input(component_id='latitude', component_property='value'),
     Input(component_id='longitude', component_property='value'),
     Input(component_id='radius', component_property='value'),
     Input(component_id='station-name', component_property='value'),
     Input(component_id='station-map', component_property='clickData')]
)
def data_filter(province, frequency, first_year, end_year, lat, lon, radius, station_name, on_map_click):
    # Don't use global variable to filter
    df_filter = df

    # Province Filter
    if province:
        df_filter = df_filter[df_filter.Province == province]
    else:
        df_filter = df_filter

    # Frequency Filter
    if frequency == 'Hourly':
        df_filter = df_filter[df_filter['First Year (Hourly)'] != 'N/A']
    elif frequency == 'Daily':
        df_filter = df_filter[df_filter['First Year (Daily)'] != 'N/A']
    elif frequency == 'Monthly':
        df_filter = df_filter[df_filter['First Year (Monthly)'] != 'N/A']
    else:
        df_filter = df_filter

    # Date Filter
    if first_year and end_year and frequency == 'Hourly':
        df_filter = df_filter[(df_filter['First Year (Hourly)'] <= np.int64(end_year)) & (df_filter['Last Year (Hourly)']>= np.int64(first_year))]
    elif first_year and end_year and frequency == 'Daily':
        df_filter = df_filter[(df_filter['First Year (Daily)'] <= np.int64(end_year)) & (df_filter['Last Year (Daily)'] >= np.int64(first_year))]
    elif first_year and end_year and frequency == 'Monthly':
        df_filter = df_filter[(df_filter['First Year (Monthly)'] <= np.int64(end_year)) & (df_filter['Last Year (Monthly)'] >= np.int64(first_year))]
    elif first_year and end_year:
        df_filter = df_filter[(df_filter['First Year'] <= np.int64(end_year)) & (df_filter['Last Year'] >= np.int64(first_year))]
    else:
        df_filter = df_filter

    # Distance Filter
    if lat and lon and radius:
        df_filter = df_filter[
            compute_great_circle_distance(lat, lon, df_filter.Latitude, df_filter.Longitude) <= np.float64(radius)]
    else:
        df_filter = df_filter

    # Name Filter
    if station_name:
        df_filter = df_filter[df_filter.Name.str.contains(station_name.upper())]
    else:
        df_filter = df_filter

    # Highlight Click Data on Map and Populate Table
    if on_map_click and not df_filter[(df_filter.Latitude == on_map_click['points'][0]['lat']) &
                                             (df_filter.Longitude == on_map_click['points'][0]['lon'])].empty:
        selected_lat = on_map_click['points'][0]['lat']
        selected_lon = on_map_click['points'][0]['lon']
        selected_station_name = on_map_click['points'][0]['text']
        table_data = df_filter[(df_filter.Latitude == on_map_click['points'][0]['lat']) &
                               (df_filter.Longitude == on_map_click['points'][0]['lon'])].to_dict('records')
    else:
        selected_lat = []
        selected_lon = []
        selected_station_name = []
        table_data = []

    return station_map(df_filter, selected_lat, selected_lon, selected_station_name, 'blue'), table_data

# Set download filters based on selected data
@app.callback(
    [Output(component_id='download-frequency', component_property='options'),
     Output(component_id='download-month-start', component_property='options'),
     Output(component_id='download-month-end', component_property='options'),
     Output(component_id='download-year-start', component_property='options'),
     Output(component_id='download-year-end', component_property='options')],
    [Input(component_id='selected-station', component_property='data'),
     Input(component_id='selected-station', component_property='selected_rows'),
     Input(component_id='download-frequency', component_property='value')]
)
def update_download_dropdowns(selected_station, selected_station_row, selected_frequency):
    if selected_station and selected_station_row:
        df_selected_data = pd.DataFrame(selected_station).iloc[selected_station_row[0]]
        available_frequency = df_selected_data[['First Year (Hourly)', 'First Year (Daily)', 'First Year (Monthly)']] \
            .replace('N/A', np.nan).dropna().index.to_list()
        download_frequency = [{'label': freq.split('(')[1][:-1], 'value': freq.split('(')[1][:-1]} for freq in available_frequency]

        download_month_start = [{'label': year, 'value': year} for year in range(1, 13, 1)]
        download_month_end = download_month_start # same month range for downloads

        if selected_frequency == 'Hourly':
            download_year_start = [{'label': year, 'value': year} for year in range(df_selected_data['First Year (Hourly)'],
                                                                     df_selected_data['Last Year (Hourly)'] + 1, 1)]
            download_year_end = download_year_start # same year range for downloads
        elif selected_frequency == 'Daily':
            download_year_start = [{'label': year, 'value': year} for year in range(df_selected_data['First Year (Daily)'],
                                                                     df_selected_data['Last Year (Daily)'] + 1, 1)]
            download_year_end = download_year_start # same year range for downloads
        elif selected_frequency == 'Monthly':
            download_year_start = [{'label': year, 'value': year} for year in range(df_selected_data['First Year (Monthly)'],
                                                                     df_selected_data['Last Year (Monthly)'] + 1, 1)]
            download_year_end = download_year_start # same year range for downloads
        else:
            download_year_start = [{'label': year, 'value': year} for year in range(df_selected_data['First Year'],
                                                                     df_selected_data['Last Year'] + 1, 1)]
            download_year_end = download_year_start # same year range for downloads

    else:
        no_station_selected = [{'label': year, 'value': year} for year in ['Select A Station']]
        download_frequency, download_month_start, download_month_end, download_year_start, download_year_end = \
            no_station_selected, no_station_selected, no_station_selected, no_station_selected, no_station_selected

    return download_frequency, download_month_start, download_month_end, download_year_start, download_year_end

# Set download message indicating to user what they will be getting
@app.callback(
    [Output(component_id='download-message', component_property='children'),
     Output(component_id='download-message', component_property='style'),
     Output(component_id='message-status', component_property='children')],
    [Input(component_id='selected-station', component_property='data'),
     Input(component_id='download-year-start', component_property='value'),
     Input(component_id='download-year-end', component_property='value'),
     Input(component_id='download-month-start', component_property='value'),
     Input(component_id='download-month-end', component_property='value'),
     Input(component_id='download-frequency', component_property='value')]
)
def update_download_message(selected_station, download_start_year, download_end_year, download_start_month, download_end_month, download_frequency):

    if selected_station and download_frequency and download_start_year and download_start_month and download_end_year and download_end_month:

        if download_start_year == download_end_year and download_start_month == download_end_month:
            message = 'Download dates must be different'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        elif download_start_year > download_end_year:
            message = 'Download start date must preceed download end date'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        elif download_start_year == download_end_year and download_start_month > download_end_month:
            message = 'Download start date must preceed download end date'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        else:
            df_selected_data = pd.DataFrame(selected_station)
            start_date = datetime.strptime(str(download_start_year) + str(download_start_month) + '1', '%Y%m%d').date()
            end_date = datetime.strptime(str(download_end_year) + str(download_end_month) + '1', '%Y%m%d').date() - timedelta(1)
            message = 'First select GENERATE DATA and once loading is complete select DOWNLOAD DATA to begin downloading {} ' \
                      'data from {} to {} for station {} (station ID {})' \
                    .format(download_frequency, start_date, end_date, df_selected_data.Name[0], df_selected_data['Station ID'][0])
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = 'PROCEED'
    else:
        message = []
        message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}
        message_status = None

    return message, message_style, message_status

# Send download to Celery background worker on Heroku and link to download button
@app.callback(
    [Output(component_id='download-data-button', component_property='href'),
     Output(component_id='task-id', component_property='children'),
     Output(component_id='filename-store', component_property='data'),
     Output(component_id='station-metadata-store', component_property='data')],
    [Input(component_id='selected-station', component_property='data'),
     Input(component_id='download-year-start', component_property='value'),
     Input(component_id='download-year-end', component_property='value'),
     Input(component_id='download-month-start', component_property='value'),
     Input(component_id='download-month-end', component_property='value'),
     Input(component_id='download-frequency', component_property='value'),
     Input(component_id='generate-data-button', component_property='n_clicks'),
     Input(component_id='message-status', component_property='children')]
)
def background_download_task(selected_station, download_start_year, download_end_year, download_start_month, download_end_month, download_frequency, generate_button_click, message_status):
    ctx = dash.callback_context  # Look for specific click event

    if selected_station and download_start_year and download_start_month and download_end_year and download_end_month and download_frequency and \
        ctx.triggered[0]['prop_id'] == 'generate-data-button.n_clicks' and generate_button_click and message_status:

        df_selected_data = pd.DataFrame(selected_station)

        filename = 'ENV-CAN' + '-' + download_frequency + '-' + 'Station' + str(df_selected_data['Station ID'][0]) + '-' + str(download_start_year) + '-' + str(download_end_year) + '.csv'
        relative_filename = os.path.join('download', filename)
        link_path = '/{}'.format(relative_filename)

        download_task = tasks.download_remote_data.apply_async([int(df_selected_data['Station ID'][0]), int(download_start_year),
                                                                   int(download_start_month), int(download_end_year), int(download_end_month), download_frequency,
                                                                   bulk_data_pathname])

        task_id = str(download_task.id)
        station_metadata = {k: v for v, k in enumerate([df_selected_data.Latitude[0], df_selected_data.Longitude[0], df_selected_data.Name[0], df_selected_data['Climate ID'][0]])}

    else:
        link_path = ''
        task_id = None
        filename = None
        station_metadata = None

    return link_path, task_id, filename, station_metadata

# Update Task Status
@app.callback(
    [Output(component_id='task-status', component_property='children'),
     Output(component_id='toggle-button-vis', component_property='style'),
     Output(component_id='column-name-store', component_property='data')],
    [Input(component_id='task-id', component_property='children'),
     Input(component_id='task-interval', component_property='n_intervals')]
)
def update_task_status(task_id, n_int):

    if task_id:
        current_task_status = AsyncResult(id=task_id, app=celery_app).state
        if current_task_status == 'SUCCESS':
            button_visibility = {'visibility': 'visible'}
            task_result = AsyncResult(id=task_id, app=celery_app).result
        else:
            button_visibility = {'visibility': 'visible'}
            task_result = {}
    else:
        current_task_status = None
        button_visibility = {'visibility': 'visible'}
        task_result = {}

    return current_task_status, button_visibility, task_result

# Update refresh interval
@app.callback(
    Output(component_id='task-interval', component_property='interval'),
    [Input(component_id='task-status', component_property='children')]
)
def update_interval(task_status):

    if task_status == 'PENDING':
        interval = 250
    else:
        interval = 24*60*60*1*1000

    return interval

# Control spinner visibility
@app.callback(
    Output(component_id='spinner', component_property='style'),
    [Input(component_id='task-status', component_property='children')]
)
def update_spinner(task_status):

    if task_status == 'PENDING':
        loading_div_viz = {'visibility': 'visible', 'text-align': 'center'}
    else:
        loading_div_viz = {'visibility': 'hidden'}

    return loading_div_viz

# Flask Magik
@app.server.route('/download/<filename>')
def serve_static(filename):
    s3 = boto3.client('s3', region_name='us-east-1',
                      aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                      aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    url = s3.generate_presigned_url('get_object', Params={'Bucket': os.environ['S3_BUCKET'], 'Key': filename}, ExpiresIn=100)
    return redirect(url, code=302)