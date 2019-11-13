import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from app import app

import pandas as pd
import numpy as np
from datetime import datetime

######################################### DATA INPUTS AND LINKS ########################################################

# Environment Canada Station Metadata
df = pd.read_csv('station-metadata-processed.csv')
df.replace(np.nan, 'N/A', inplace=True)

# URL Path to Bulk Data Download From Environment Canada
url_bulk_data_link = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?' \
                'format=csv&stationID={}&Year={}&Month={}&Day={}&timeframe={}'

######################################### HELPER FUNCTIONS #############################################################

def great_circle_distance(lat_user, lon_user, lat_station, lon_station):
    '''
    Computes the distance between two locations using the Haversine Formula
    :param lat_user: user defined latitude (text)
    :param lon_user: user defined longitude (text)
    :param lat_station: station latitude (array, float64)
    :param lon_station: station longitude (array, float64)
    :return: distance from user locations to stations
    '''
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
                'accesstoken':
                    'pk.eyJ1IjoiZGxodXJsZXkiLCJhIjoiY2sya2xrMTJqMWFjMzNucXB3bnp1MXd0ZyJ9.UBKniAsr5Li1Yv5dJOP5yQ'
                },
            'margin': {
                'l': 0, 'r': 0, 'b': 0, 't': 0
            },
        }
    }

######################################### LAYOUT #######################################################################

layout = html.Div([ #Overall container
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
                html.Label('Click on a station to view data and select in table to download', style={
                    'textAlign': 'left', 'font-weight': 'bold'}),
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
            #Filtering container
            html.Div([
                html.Div([
                    html.Label("Station Name:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Input(id='stn_name', value='', type='text', placeholder='Enter Station Name',
                              style={'width': '50%'})
                ], style={'margin-left': '1rem','margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Province:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Dropdown(id='province',
                                 options=[{'label': province, 'value': province} for province in df.Province.unique()],
                                 style={'width': '90%'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Data Frequency:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    dcc.Dropdown(id='frequency',
                                 options=[{'label': frequency, 'value': frequency} for frequency in ['Hourly', 'Daily', 'Monthly']],
                                 style={'width': '90%'})
                ], style={'margin-left': '1rem', 'margin-bottom': '0.5rem'}),
                html.Div([
                    html.Label("Data Available Between:", style={'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='first_year',
                                     options=[{'label': str(year), 'value': str(year)} for year in range(1840, datetime.now().year+1, 1)],
                                     placeholder='First Year')
                    ], style={'width': '40%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(id='last_year',
                                     options=[{'label': str(year), 'value': str(year)} for year in range(1840, datetime.now().year + 1, 1)],
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
                                     options=[{'label': radius, 'value': radius} for radius in ['10', '25', '50', '100']],
                                     placeholder='Kilometers From Location')
                    ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'middle', 'margin-left': '1rem'})
                ], style={'margin-left': '1rem', 'margin-bottom': '1rem'})
            ], style={'margin-bottom': '1rem', 'border': '2px black solid', 'textAlign': 'left'}),

            # Download Container
                html.Div([
                    html.Div([
                        html.Label('Download Dates:', style={'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                        html.Div([
                            dcc.Dropdown(id='download_year_start',
                                         options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                         placeholder='Start Year')
                        ], style={'width': '45%', 'display': 'inline-block', 'margin-bottom': '1rem'}),
                        html.Div([
                            dcc.Dropdown(id='download_month_start',
                                         options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                         placeholder='Start Month')
                        ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem', 'margin-bottom': '1rem'}),
                        html.Div([
                            dcc.Dropdown(id='download_year_end',
                                         options=[{'label': year, 'value': year} for year in ['Select A Station']],
                                         placeholder='End Year')
                        ], style={'width': '45%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Dropdown(id='download_month_end',
                                         options=[{'label': month, 'value': month} for month in ['Select A Station']],
                                         placeholder='End Month')
                        ], style={'width': '45%', 'display': 'inline-block', 'margin-left': '0.5rem'})
                ], style={'width': '55%', 'display': 'inline-block','margin-left': '1rem'}),
                html.Div([
                    html.Label('Download Interval:', style={'textAlign': 'left', 'font-weight': 'bold', 'font-size': '18px'}),
                    html.Div([
                        dcc.Dropdown(id='download_frequency',
                                     options=[{'label': frequency, 'value': frequency} for frequency in ['Select A Station']],
                                     placeholder='Frequency')
                    ], style={'width': '85%', 'margin-bottom': '2rem'}),
                    html.Div([
                        html.A('DOWNLOAD DATA', id='download-link', href="")
                    ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px red dashed', 'width': '85%', 'text-align': 'center'}),
                    html.Div([
                        dcc.Link('GRAPH DATA', id='download-link', href="")
                    ], style={'font-weight': 'bold', 'font-size': '16px', 'border': '2px green dashed', 'width': '85%',
                              'text-align': 'center','margin-top': '1.5rem'})
                ], style={'width': '40%', 'display': 'inline-block', 'margin-left': '6rem'})
            ], style={'display': 'flex'})
        ], className='five columns', style={'margin-top': '1rem'}),
        html.Div(id='hidden-storage', style={'display': 'none'}),
        html.Div(id='hidden-storage-01', style={'display': 'none'})
    ], className='row')
])


######################################### INTERACTION CALLBACKS ########################################################

# Data Filter
@app.callback(
    Output(component_id='hidden-storage', component_property='children'),
    [Input(component_id='province', component_property='value'),
     Input(component_id='frequency', component_property='value'),
     Input(component_id='first_year', component_property='value'),
     Input(component_id='last_year', component_property='value'),
     Input(component_id='latitude', component_property='value'),
     Input(component_id='longitude', component_property='value'),
     Input(component_id='radius', component_property='value'),
     Input(component_id='stn_name', component_property='value')]
)
def data_filter(province, frequency, start, end, lat, lon, radius, stn_name):
    # Province Filter
    if province is None:
        df_filter = df
    else:
        df_filter = df[df.Province == province]

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
    if start and end:
        df_filter = df_filter[(df_filter['First Year'] <= np.int64(end)) & (df_filter['Last Year'] >= np.int64(start))]
    else:
        df_filter = df_filter

    # Distance Filter
    if lat and lon and radius:
        try:
            df_filter = df_filter[
                great_circle_distance(lat, lon, df_filter.Latitude, df_filter.Longitude) <= np.float64(radius)]
        except:
            df_map_filter = []

    # Name Filter
    if stn_name:
        df_filter = df_filter[df_filter.Name.str.contains(stn_name.upper())]
    else:
        df_filter = df_filter

    return df_filter.to_json(date_format='iso', orient='split')

# Apply Filter Controls to Map
@app.callback(
    Output(component_id='station-map',component_property='figure'),
    [Input(component_id='hidden-storage', component_property='children'),
     Input(component_id='station-map', component_property='clickData')]
)
def map_filter(filter_data, click_highlight):

    df_map_filter = pd.read_json(filter_data, orient='split')

    # Highlight Click Data
    if click_highlight and not df_map_filter[(df_map_filter.Latitude == click_highlight['points'][0]['lat']) &
                                             (df_map_filter.Longitude == click_highlight['points'][0]['lon'])].empty:
        lat_selected = click_highlight['points'][0]['lat']
        lon_selected = click_highlight['points'][0]['lon']
        name_selected = click_highlight['points'][0]['text']
    else:
        lat_selected = []
        lon_selected = []
        name_selected = []

    return station_map(df_map_filter, lat_selected, lon_selected, name_selected, 'blue')

# Apply Filter Controls to Table
@app.callback(
    Output(component_id='selected-station-table', component_property='data'),
    [Input(component_id='station-map', component_property='clickData'),
     Input(component_id='hidden-storage', component_property='children')]
)
def table_filter(selected_station, filter_data):

    df_table_filter = pd.read_json(filter_data, orient='split')

    if selected_station and not df_table_filter[(df_table_filter.Latitude == selected_station['points'][0]['lat']) &
                           (df_table_filter.Longitude == selected_station['points'][0]['lon'])].empty:
        return df_table_filter[(df_table_filter.Latitude == selected_station['points'][0]['lat']) &
                               (df_table_filter.Longitude == selected_station['points'][0]['lon'])].to_dict('records')
    else:
        return []

# Start Year Range to Download Control

@app.callback(
    Output(component_id='download_frequency', component_property='options'),
    [Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='selected-station-table', component_property='data')]
)
def download_frequency(selected_rows, data):
    df_selected = pd.DataFrame(data)

    if selected_rows and data:
        print(pd.DataFrame(df_selected[['First Year (Hourly)', 'First Year (Daily)', 'First Year (Monthly)']].
              replace('N/A',np.nan).dropna(axis=1).columns))
        return []
    else:
        return []

@app.callback(
    Output(component_id='download_year_start', component_property='options'),
    [Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='selected-station-table', component_property='data'),
     Input(component_id='download_frequency', component_property='value')]
)
def download_start_year(selected_rows, data, freq):
    df_selected = pd.DataFrame(data)

    if selected_rows and data and freq == 'Hourly':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Hourly)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Hourly)']+1, 1)]
    elif selected_rows and data and freq == 'Daily':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Daily)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Daily)']+1, 1)]
    elif selected_rows and data and freq == 'Monthly':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Monthly)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Monthly)']+1, 1)]
    elif selected_rows and data:
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year']+1, 1)]
    else:
        return [{'label': year, 'value': year} for year in ['Select A Station']]

@app.callback(
    Output(component_id='download_year_end', component_property='options'),
    [Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='selected-station-table', component_property='data'),
     Input(component_id='download_frequency', component_property='value')]
)
def download_end_year(selected_rows, data, freq):
    df_selected = pd.DataFrame(data)

    if selected_rows and data and freq == 'Hourly':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Hourly)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Hourly)']+1, 1)]
    elif selected_rows and data and freq == 'Daily':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Daily)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Daily)']+1, 1)]
    elif selected_rows and data and freq == 'Monthly':
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year (Monthly)'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year (Monthly)']+1, 1)]
    elif selected_rows and data:
        return [{'label': year, 'value': year} for year in range(df_selected.iloc[selected_rows[0]]['First Year'],
                                                                 df_selected.iloc[selected_rows[0]]['Last Year']+1, 1)]
    else:
        return [{'label': year, 'value': year} for year in ['Select A Station']]

@app.callback(
    Output(component_id='download_month_start', component_property='options'),
    [Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='selected-station-table', component_property='data')]
)
def download_start_month(selected_rows, data):
    if selected_rows and data:
        return [{'label': year, 'value': year} for year in range(1, 13, 1)]
    else:
        return [{'label': year, 'value': year} for year in ['Select A Station']]

@app.callback(
    Output(component_id='download_month_end', component_property='options'),
    [Input(component_id='selected-station-table', component_property='selected_rows'),
     Input(component_id='selected-station-table', component_property='data')]
)
def download_end_month(selected_rows, data):
    if selected_rows and data:
        return [{'label': year, 'value': year} for year in range(1, 13, 1)]
    else:
        return [{'label': year, 'value': year} for year in ['Select A Station']]