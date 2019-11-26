import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np
from datetime import datetime
import flask
import os
import tasks

from app import app

######################################### DATA INPUTS AND LINKS ########################################################

# Environment Canada Station Metadata
df = pd.read_csv('station-metadata-processed.csv')
df.replace(np.nan, 'N/A', inplace=True)

# URL Path to Bulk Data Download From Environment Canada
bulk_data_pathname = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?' \
                     'format=csv&stationID={}&Year={}&Month={}&Day=1&timeframe={}'

######################################### HELPER FUNCTIONS #############################################################

def compute_great_circle_distance(lat_user, lon_user, lat_station, lon_station):
    """
    Computes the distance between two locations using the Haversine Formula
    :param lat_user: user defined latitude (text)
    :param lon_user: user defined longitude (text)
    :param lat_station: station latitude (array, float64)
    :param lon_station: station longitude (array, float64)
    :return: distance from user locations to stations
    """
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
        # Highlight Selected Station
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

layout = html.Div([  # Overall container
    # Header container
    html.Div([
        html.Div([
            html.H3("Super Speedy Environment Canada Weather Download")
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
                dash_table.DataTable(id='selected-station-table',
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
                    dcc.Input(id='stn_name', value='', type='text', placeholder='Enter Station Name',
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
                        dcc.Dropdown(id='first_year',
                                     options=[{'label': str(year), 'value': str(year)} for year in
                                              range(1840, datetime.now().year + 1, 1)],
                                     placeholder='First Year')
                    ], style={'width': '40%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id='last_year',
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
                        dcc.Dropdown(id='download_year_start',
                                     options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                     placeholder='Start Year')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-bottom': '1rem'}),
                    html.Div([
                        dcc.Dropdown(id='download_month_start',
                                     options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                     placeholder='Start Month')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem',
                              'margin-bottom': '1rem'}),
                    html.Div([
                        dcc.Dropdown(id='download_year_end',
                                     options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                     placeholder='End Year')
                    ], style={'width': '45%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id='download_month_end',
                                     options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                     placeholder='End Month')
                    ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem'}),
                    html.Div([
                        html.Label(id='download_message', children='')
                    ], style={'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}),
                ], style={'width': '55%', 'display': 'inline-block', 'margin-left': '1rem'}),
                html.Div([
                    html.Label('Download Interval:',
                               style={'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='download_frequency',
                                     options=[{'label': frequency, 'value': frequency} for frequency in
                                              ['Select A Station']],
                                     placeholder='Frequency')
                    ], style={'width': '85%', 'margin-bottom': '2rem'}),
                    html.Div([
                        html.A(id='fetch-link', children='1. GENERATE DATA')
                    ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px red dashed', 'width': '85%',
                              'text-align': 'left'}),
                    html.Div(id='toggle_button_vis', children=[
                        html.Div([
                            html.A(id='download-link', children='2. DOWNLOAD DATA')
                        ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px green dashed', 'width': '85%',
                                  'text-align': 'left', 'margin-top': '1.5rem'}),
                        html.Div([
                            html.A('3. VIEW GRAPH DATA', id='graph-link', href="/pages/graph_page")
                        ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px blue dashed', 'width': '85%',
                                  'text-align': 'left', 'margin-top': '1.5rem'}),
                        ], style={'visibility': 'hidden'}),
                    html.Div(id='load-div', children=[
                        dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default"),
                    ], style={'visibility': 'hidden'})
                ], style={'width': '40%', 'display': 'inline-block', 'margin-left': '6rem'}),
            ], style={'display': 'flex'})
        ], className='five columns', style={'margin-top': '1rem'}),
    ], className='row')
])


######################################### INTERACTION CALLBACKS ########################################################

# Filter Data and Output to Station Map and Table
@app.callback(
    [Output(component_id='station-map', component_property='figure'),
     Output(component_id='selected-station-table', component_property='data')],
    [Input(component_id='province', component_property='value'),
     Input(component_id='frequency', component_property='value'),
     Input(component_id='first_year', component_property='value'),
     Input(component_id='last_year', component_property='value'),
     Input(component_id='latitude', component_property='value'),
     Input(component_id='longitude', component_property='value'),
     Input(component_id='radius', component_property='value'),
     Input(component_id='stn_name', component_property='value'),
     Input(component_id='station-map', component_property='clickData')]
)
def data_filter(province, frequency, start, end, lat, lon, radius, stn_name, click_highlight):
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
    if start and end and frequency == 'Hourly':
        df_filter = df_filter[(df_filter['First Year (Hourly)'] <= np.int64(end)) & (df_filter['Last Year (Hourly)'] >= np.int64(start))]
    elif start and end and frequency == 'Daily':
        df_filter = df_filter[(df_filter['First Year (Daily)'] <= np.int64(end)) & (df_filter['Last Year (Daily)'] >= np.int64(start))]
    elif start and end and frequency == 'Monthly':
        df_filter = df_filter[(df_filter['First Year (Monthly)'] <= np.int64(end)) & (df_filter['Last Year (Monthly)'] >= np.int64(start))]
    elif start and end:
        df_filter = df_filter[(df_filter['First Year'] <= np.int64(end)) & (df_filter['Last Year'] >= np.int64(start))]
    else:
        df_filter = df_filter

    # Distance Filter
    if lat and lon and radius:
        df_filter = df_filter[
            compute_great_circle_distance(lat, lon, df_filter.Latitude, df_filter.Longitude) <= np.float64(radius)]
    else:
        df_filter = df_filter

    # Name Filter
    if stn_name:
        df_filter = df_filter[df_filter.Name.str.contains(stn_name.upper())]
    else:
        df_filter = df_filter

    # Highlight Click Data on Map
    if click_highlight and not df_filter[(df_filter.Latitude == click_highlight['points'][0]['lat']) &
                                             (df_filter.Longitude == click_highlight['points'][0]['lon'])].empty:
        lat_highlight = click_highlight['points'][0]['lat']
        lon_highlight = click_highlight['points'][0]['lon']
        name_highlight = click_highlight['points'][0]['text']
    else:
        lat_highlight = []
        lon_highlight = []
        name_highlight = []

    # Get Table data as click data on map
    if click_highlight and not df_filter[(df_filter.Latitude == click_highlight['points'][0]['lat']) &
                                                (df_filter.Longitude == click_highlight['points'][0][
                                                    'lon'])].empty:
        table_data = df_filter[(df_filter.Latitude == click_highlight['points'][0]['lat']) &
                               (df_filter.Longitude == click_highlight['points'][0]['lon'])].to_dict('records')
    else:
        table_data = []

    return station_map(df_filter, lat_highlight, lon_highlight, name_highlight, 'blue'), table_data

# Set download frequency based on table data
@app.callback(
    [Output(component_id='download_frequency', component_property='options'),
     Output(component_id='download_month_start', component_property='options'),
     Output(component_id='download_month_end', component_property='options'),
     Output(component_id='download_year_start', component_property='options'),
     Output(component_id='download_year_end', component_property='options')],
    [Input(component_id='selected-station-table', component_property='data'),
     Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='download_frequency', component_property='value')]
)
def set_download_frequency_dropdown(data, selected_rows, selected_frequency):
    if data and selected_rows:
        df_selected_data = pd.DataFrame(data).iloc[selected_rows[0]]
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
    [Output(component_id='download_message', component_property='children'),
     Output(component_id='download_message', component_property='style')],
    [Input(component_id='selected-station-table', component_property='data'),
     Input(component_id='download_year_start', component_property='value'),
     Input(component_id='download_year_end', component_property='value'),
     Input(component_id='download_month_start', component_property='value'),
     Input(component_id='download_month_end', component_property='value'),
     Input(component_id='download_frequency', component_property='value')]
)
def set_download_message(selected_table_data, start_year, end_year, start_month, end_month, freq):

    if selected_table_data and freq:

        if start_year and start_month and end_year and end_month:
            df_selected_data = pd.DataFrame(selected_table_data)
            start_date = datetime.strptime(str(start_year) + str(start_month) + '1', '%Y%m%d').date()
            end_date = datetime.strptime(str(end_year) + str(end_month) + '1', '%Y%m%d').date()
            message = 'First select GENERATE DATA and once loading is complete select DOWNLOAD DATA to begin downloading "{} ' \
                      'data from {} to {} for station {} (station ID {})"' \
                    .format(freq, start_date, end_date, df_selected_data.Name[0], df_selected_data['Station ID'][0])
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem', 'border': '2px red dashed'}

        else:
            message = []
            message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}

    else:
        message = []
        message_style = {'width': '100%', 'margin-right': '1rem', 'margin-top': '1rem'}

    return message, message_style

# Be cheeky and hide the loading component
@app.callback(
    Output(component_id='load-div', component_property='style'),
    [Input(component_id='fetch-link', component_property='n_clicks')]
)
def show_load_div(clicks):
    ctx = dash.callback_context  # Look for specific click event

    if clicks:
        if ctx.triggered[0]['prop_id'] == 'fetch-link.n_clicks':
            div_style = {'visibility': 'visible'}
        else:
            div_style = {'visibility': 'hidden'}
    else:
        div_style = {'visibility': 'hidden'}
    return div_style

# Create and save file in /tmp and get server link
@app.callback(
    [Output(component_id='download-link', component_property='href'),
     Output(component_id='toggle_button_vis', component_property='style'),
     Output(component_id='create-data', component_property='data'),
     Output(component_id='loading-output-1', component_property='children')],
    [Input(component_id='selected-station-table', component_property='data'),
     Input(component_id='download_year_start', component_property='value'),
     Input(component_id='download_year_end', component_property='value'),
     Input(component_id='download_month_start', component_property='value'),
     Input(component_id='download_month_end', component_property='value'),
     Input(component_id='download_frequency', component_property='value'),
     Input(component_id='fetch-link', component_property='n_clicks')]
)
def set_download_message(selected_table_data, start_year, end_year, start_month, end_month, freq, clicks):
    ctx = dash.callback_context  # Look for specific click event

    if selected_table_data and start_year and start_month and end_year and end_month and freq and \
        ctx.triggered[0]['prop_id'] == 'fetch-link.n_clicks' and clicks:
        df_selected_data = pd.DataFrame(selected_table_data)
        start_date = datetime.strptime(str(start_year) + str(start_month) + '1', '%Y%m%d').date()
        end_date = datetime.strptime(str(end_year) + str(end_month) + '1', '%Y%m%d').date()
        relative_filename = os.path.join('tmp', '{}_{}_{}-download.csv'.format(df_selected_data.Name[0], start_date, end_date))
        absolute_filename = os.path.join(os.getcwd(), relative_filename)
        df_output_data = tasks.download_archived_data.apply_async([int(df_selected_data['Station ID'][0]), int(start_year),
                                                                   int(start_month), int(end_year), int(end_month), freq,
                                                                   bulk_data_pathname])
        df_output_data = df_output_data.get()
        df_output_data = pd.read_json(df_output_data, orient='split')
        df_output_data.to_csv(absolute_filename)
        link_path = '/{}'.format(relative_filename)
        df_output_data = {}
        download_graph_viz = {'visibility': 'visible'}

    else:
        link_path = ""
        df_output_data = {}
        download_graph_viz = {'visibility': 'hidden'}

    return link_path, download_graph_viz, df_output_data, ""

@app.server.route('/tmp/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return flask.send_from_directory(
        os.path.join(root_dir, 'tmp'), path
    )