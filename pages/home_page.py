import dash
import dash_table
from dash.dependencies import Input, Output, State
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
import time


from app import app

######################################### DATA INPUTS AND LINKS ########################################################

# create dataframe of weather station locations and available years of data
df = pd.read_csv('station-metadata-processed.csv')
df.replace(np.nan, 'N/A', inplace=True)

# weather station dataframe stops at 2019, if data was available
# in 2019 we assume it's available in the current year
today = datetime.today()
yearnow = today.year
df['Last Year'].loc[df['Last Year'] == 2019] = yearnow
df['Last Year (Hourly)'].loc[df['Last Year (Hourly)'] == 2019] = yearnow
df['Last Year (Daily)'].loc[df['Last Year (Daily)'] == 2019] = yearnow
df['Last Year (Monthly)'].loc[df['Last Year (Monthly)'] == 2019] = yearnow

# url path to bulk download weather data from environment canada
bulk_data_pathname = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?' \
                     'format=csv&stationID={}&Year={}&Month={}&Day=1&timeframe={}'

# preload spinner to base64 encode
spinner = base64.b64encode(open(os.path.join('assets', 'spinner.gif'), 'rb').read())

######################################### HELPER FUNCTIONS #############################################################

# this function computes the distance between two locations on the earths surface
def compute_great_circle_distance(lat_user, lon_user, lat_station, lon_station):

    lat1, lon1 = np.radians([np.float64(lat_user), np.float64(lon_user)])
    lat2, lon2 = np.radians([lat_station, lon_station])
    a = np.sin((lat2 - lat1) / 2.0) ** 2 + np.cos(lat1) * \
        np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2
    earth_radius_km = 6371
    return earth_radius_km * 2 * np.arcsin(np.sqrt(a))


######################################### PLOTS ########################################################################


# add the weather station dataframe locations to a map
def station_map(stations, lat_selected, lon_selected, name_selected, color):
    return {'data': [
        # weather station locations
        {'type': 'scattermapbox',
         'lat': stations.Latitude,
         'lon': stations.Longitude,
         'name': '',
         'text': stations.Name,
         'marker': {'color': color}
         },
        # highlight selected weather station in red
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
    # hold task-id and task-status hidden
    html.Div(id='task-id', children=None, style={'display': 'none'}),
    html.Div(id='task-status', children=None, style={'display': 'none'}),
    html.Div(id='message-status', children=None, style={'display': 'none'}),
    # update refresh interval to check celery task status and avoid Heroku timeout
    dcc.Interval(
        id='task-interval',
        interval=24*60*60*1*1000,  # in milliseconds
        n_intervals=0
    ),
    # title block
    html.Div([
        html.Div([
            html.H3("Weather History Canada")
        ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
        html.Div([
            dcc.Link('About', href='/pages/about')
        ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
    ], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'}),

    # add map filter and download data functionality and a selected station table
    html.Div([
        # map and table container
        html.Div([
            # map container
            html.Div([
                # map of weather stations is populated in callbacks
                dcc.Graph(id='station-map',
                          figure=station_map(df, [], [], [], 'blue'),
                          style={'border': '2px black solid'})
            ]),
            # table container
            html.Div([
                html.H6('Click on station in map and select in table below prior to generating data', style={
                    'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                # list of user selected station data availability
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

        # map filtering and download container
        html.Div([
            # map filtering container
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

            # download container
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
                                  'text-align': 'left', 'margin-top': '1.5rem'})],
                             style={'display': 'none'}),
                    html.Div(id='spinner', children=[html.Img(src='data:image/gif;base64,{}'.format(spinner.decode())),
                                                     html.Label(id='spinner-label', children='Download Progress: Pending....',
                                                     style={'font-weight': 'bold', 'font-size': '16px'})],
                             style={'display': 'none'}),
                ], style={'width': '40%', 'display': 'inline-block', 'margin-left': '6rem'}),
            ], style={'display': 'flex'})
        ], className='five columns', style={'margin-top': '1rem'}),
    ], className='row')
])


######################################### INTERACTION CALLBACKS ########################################################

# map filter and selected station table callback
@app.callback(
    [Output(component_id='station-map', component_property='figure'),
     Output(component_id='selected-station', component_property='data'),
     Output(component_id='selected-station', component_property='selected_rows'),
     Output(component_id='download-frequency', component_property='value'),
     Output(component_id='download-month-start', component_property='value'),
     Output(component_id='download-month-end', component_property='value'),
     Output(component_id='download-year-start', component_property='value'),
     Output(component_id='download-year-end', component_property='value')],
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
    # don't use global variable to filter weather station data on map
    df_filter = df

    # filter to limit mapped data by province
    if province:
        df_filter = df_filter[df_filter.Province == province]
    else:
        df_filter = df_filter

    # filter to limit mapped data by data frequency
    if frequency == 'Hourly':
        df_filter = df_filter[df_filter['First Year (Hourly)'] != 'N/A']
    elif frequency == 'Daily':
        df_filter = df_filter[df_filter['First Year (Daily)'] != 'N/A']
    elif frequency == 'Monthly':
        df_filter = df_filter[df_filter['First Year (Monthly)'] != 'N/A']
    else:
        df_filter = df_filter

    # filter to limit mapped data between specified dates
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

    # filter to limit mapped data by radius from a specified point
    if lat and lon and radius:
        df_filter = df_filter[
            compute_great_circle_distance(lat, lon, df_filter.Latitude, df_filter.Longitude) <= np.float64(radius)]
    else:
        df_filter = df_filter

    # filter to limit mapped data by search name
    if station_name:
        df_filter = df_filter[df_filter.Name.str.contains(station_name.upper())]
    else:
        df_filter = df_filter

    # highlight selected station and populate selected station data to a table
    if on_map_click and not df_filter[(df_filter.Latitude == on_map_click['points'][0]['lat']) &
                                             (df_filter.Longitude == on_map_click['points'][0]['lon'])].empty:
        selected_lat = on_map_click['points'][0]['lat']
        selected_lon = on_map_click['points'][0]['lon']
        selected_station_name = on_map_click['points'][0]['text']
        table_data = df_filter[(df_filter.Latitude == on_map_click['points'][0]['lat']) &
                               (df_filter.Longitude == on_map_click['points'][0]['lon'])].to_dict('records')
        selected_row = []

    else:
        selected_lat = []
        selected_lon = []
        selected_station_name = []
        table_data = []
        selected_row = []

    return station_map(df_filter, selected_lat, selected_lon, selected_station_name, 'blue'), table_data, selected_row, \
           None, None, None, None, None

# download options based on selected station callback
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

        # attributes of selected station
        df_selected_data = pd.DataFrame(selected_station).iloc[selected_station_row[0]]

        # populate dropdown tab with available frequency of data to download
        available_frequency = df_selected_data[['First Year (Hourly)', 'First Year (Daily)', 'First Year (Monthly)']] \
            .replace('N/A', np.nan).dropna().index.to_list()
        download_frequency = [{'label': freq.split('(')[1][:-1], 'value': freq.split('(')[1][:-1]} for freq in available_frequency]

        # populate dropdown tab with available months of data to download
        download_month_start = [{'label': year, 'value': year} for year in range(1, 13, 1)]
        download_month_end = download_month_start # same month range for downloads

        # populate dropdown tab with available years of data to download corresponding to map filter data frequency
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

# download message based on download settings selected callback
@app.callback(
    [Output(component_id='download-message', component_property='children'),
     Output(component_id='download-message', component_property='style'),
     Output(component_id='message-status', component_property='children')],
    [Input(component_id='selected-station', component_property='data'),
     Input(component_id='download-year-start', component_property='value'),
     Input(component_id='download-year-end', component_property='value'),
     Input(component_id='download-month-start', component_property='value'),
     Input(component_id='download-month-end', component_property='value'),
     Input(component_id='download-frequency', component_property='value'),
     Input(component_id='selected-station', component_property='selected_rows')]
)
def update_download_message(selected_station, download_start_year, download_end_year, download_start_month, download_end_month, download_frequency, selected_station_row):

    # if all the necessary download settings have been selected then display download message
    if selected_station and download_frequency and download_start_year and download_start_month and download_end_year and download_end_month:

        # if the same start and end data are chose advise user to select something else
        if download_start_year == download_end_year and download_start_month == download_end_month:
            message = 'Download dates must be different'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        # if the start year is after the end year advise the user to select something else
        elif download_start_year > download_end_year:
            message = 'Download start date must preceed download end date'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        # if the start date is after the end date advise the user to select something else
        elif download_start_year == download_end_year and download_start_month > download_end_month:
            message = 'Download start date must preceed download end date'
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}
            message_status = None

        # if no station is selected remove message
        elif not selected_station_row:
            message = []
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}
            message_status = None

        # if all the options are correct and present then provide the download message
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
     Output(component_id='station-metadata-store', component_property='data'),
     Output(component_id='task-status', component_property='children'),
     Output(component_id='task-interval', component_property='interval'),
     Output(component_id='toggle-button-vis', component_property='style'),
     Output(component_id='spinner', component_property='style'),
     Output(component_id='column-name-store', component_property='data'),
     Output(component_id='spinner-label', component_property='children')],
    [Input(component_id='selected-station', component_property='data'),
     Input(component_id='download-year-start', component_property='value'),
     Input(component_id='download-year-end', component_property='value'),
     Input(component_id='download-month-start', component_property='value'),
     Input(component_id='download-month-end', component_property='value'),
     Input(component_id='download-frequency', component_property='value'),
     Input(component_id='generate-data-button', component_property='n_clicks'),
     Input(component_id='message-status', component_property='children'),
     Input(component_id='task-interval', component_property='n_intervals')],
    [State(component_id='task-status', component_property='children'),
     State(component_id='task-id', component_property='children')]
)
def background_download_task(selected_station, download_start_year, download_end_year, download_start_month,
                             download_end_month, download_frequency, generate_button_click, message_status,
                             n_int, task_status_state, task_id_state):

    # Look for specific click event
    ctx = dash.callback_context

    # If the user has set the download timeframe, frequency, and no current task is running then launch celery
    if selected_station and download_start_year and download_start_month and download_end_year and download_end_month and download_frequency and \
        ctx.triggered[0]['prop_id'] == 'generate-data-button.n_clicks' and generate_button_click and message_status and not task_status_state:

        df_selected_data = pd.DataFrame(selected_station)

        filename = 'ENV-CAN' + '-' + download_frequency + '-' + 'Station' + str(df_selected_data['Station ID'][0]) + '-' + str(download_start_year) + '-' + str(download_end_year) + '.csv'
        relative_filename = os.path.join('download', filename)
        link_path = '/{}'.format(relative_filename)

        download_task = tasks.download_remote_data.apply_async([int(df_selected_data['Station ID'][0]), int(download_start_year),
                                                                   int(download_start_month), int(download_end_year), int(download_end_month), download_frequency,
                                                                   bulk_data_pathname])
        # task id of current celery task
        task_id = download_task.id
        time.sleep(0.5)  # Need a short sleep for task_id to catch up
        station_metadata = {k: v for v, k in enumerate([df_selected_data.Latitude[0], df_selected_data.Longitude[0], df_selected_data.Name[0], df_selected_data['Climate ID'][0]])}
        current_task_status = AsyncResult(id=task_id, app=celery_app).state
        current_task_progress = 'Download Progress: 0.0%'
        interval = 250  # set refresh interval short and to update task status
        button_visibility = {'display': 'none'}
        loading_div_viz = {'display': 'inline-block', 'text-align': 'center'}
        task_result = {}

        return link_path, task_id, filename, station_metadata, current_task_status, interval, button_visibility, loading_div_viz, task_result, current_task_progress
    elif task_status_state == 'PROGRESS':
        # while task is running continue to update task status
        task = AsyncResult(id=task_id_state, app=celery_app)
        current_task_status = task.state
        current_task_progress = 'Download Progress: {}%'.format(task.info.get('current_percent_complete', 0))

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, current_task_status, dash.no_update, dash.no_update, dash.no_update, dash.no_update, current_task_progress

    # once task is succesful remove task status, output results, and forget celery task
    elif task_status_state == 'SUCCESS':
        current_task_status = None
        interval = 24*60*60*1*1000
        button_visibility = {'display': 'block'}
        loading_div_viz = {'display': 'none'}
        task_result = AsyncResult(id=task_id_state, app=celery_app).result
        task_result.pop('current_percent_complete', None)  # remove percent complete key
        forget = AsyncResult(id=task_id_state, app=celery_app).forget()

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, current_task_status, interval, button_visibility, loading_div_viz, task_result, dash.no_update

    elif task_status_state == 'FAILURE':
        current_task_progress = 'Download Failed. Please Try Again.'
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, current_task_progress

    elif message_status:
        button_visibility = {'display': 'none'}

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, button_visibility, dash.no_update, dash.no_update, dash.no_update

    else:
        raise dash.exceptions.PreventUpdate

# create a presigned url to download weather data from s3
@app.server.route('/download/<filename>')
def serve_static(filename):
    s3 = boto3.client('s3', region_name='us-east-1',
                      aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                      aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    url = s3.generate_presigned_url('get_object', Params={'Bucket': os.environ['S3_BUCKET'], 'Key': filename}, ExpiresIn=100)
    return redirect(url, code=302)