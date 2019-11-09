import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from app import app

import pandas as pd
import numpy as np
from datetime import datetime

######################################### DATA INPUTS AND LINKS ########################################################

# Environment Canada Station Metadata
df = pd.read_csv('station-metadata-processed.csv')

url_bulk_data_link = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?' \
                'format=csv&stationID={}&Year={}&Month={}&Day={}&timeframe={}'

######################################### HELPER FUNCTIONS #############################################################

def great_circle_distance(lat_user, lon_user, lat_station, lon_station):
    '''
    Computes the distance between two locations using the Haversine Formula
    :param lat_user: user defined latitude (text)
    :param lon_user: user defined longitude (text)
    :param lat_stations: station latitude (array, float64)
    :param lon_stations: station longitude (array, float64)
    :return: distance from user locations to stations
    '''
    lat1, lon1 = np.radians([np.float64(lat_user), np.float64(lon_user)])
    lat2, lon2 = np.radians([lat_station, lon_station])
    a = np.sin((lat2 - lat1) / 2.0) ** 2 + np.cos(lat1) * \
        np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2
    earth_radius_km = 6371
    return earth_radius_km * 2 * np.arcsin(np.sqrt(a))

######################################### PLOTS ########################################################################

def station_map(stations):
    return {
        'data': [
                {'type': 'scattermapbox',
                 'lat': stations.Latitude,
                 'lon': stations.Longitude,
                 'text': stations.Name
                }
            ],
        'layout': {
            'mapbox': {
                'style': 'basic',
                'center': {'lat': 59, 'lon': -97},
                'zoom': 2.5,
                'accesstoken': 'pk.eyJ1IjoiZGxodXJsZXkiLCJhIjoiY2sya2xrMTJqMWFjMzNucXB3bnp1MXd0ZyJ9.UBKniAsr5Li1Yv5dJOP5yQ'
                },
            'margin': {
                'l': 10, 'r': 0, 'b': 0, 't': 0
            },
        }
    }

######################################### LAYOUT #######################################################################

app.css.append_css({
    'external_url': "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Page 1", href="#")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Page 2", href="#"),
                dbc.DropdownMenuItem("Page 3", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="NavbarSimple",
    brand_href="#",
    color="primary",
    dark=True,
)

layout = html.Div([
    # Title Row
    html.Div([
        # Title Column
        html.Div([
            html.H1("Super Speedy Environment Canada Weather Download",
                    style={'textAlign': 'center'})
            ], className='twelve columns')
    ], className='row', style={'background': '#DCDCDC'}),

    # Map and Toggles Row
    html.Div([
        # Map Column
        html.Div([
            html.H3("Environment Canada Station Map",
                    style={'textAlign': 'center'}),
            # Map of stations
            dcc.Graph(id='station-map',
                      figure=station_map(df)),
            html.Br(),
            html.Label(id='selected-station', children='Select a Station',
                    style={'textAlign': 'left'}),
            dash_table.DataTable(id='selected-station-table',
                                 columns=[{"name": col, "id": col} for col in df.columns[1:]],
                                 data=[{col: '' for col in df.columns[1:]}],
                                 style_table={'overflowX': 'scroll'})
        ], className='seven columns'),

        # Toggles Column
        html.Div([
            html.H3("Map Toggles",
                    style={'textAlign': 'center'}),
            html.Div([
                html.H6("Province:"),
                dcc.Dropdown(id='province',
                             options=[{'label': province, 'value': province} for province in df.Province.unique()]),
                html.H6("Data Frequency:"),
                dcc.Dropdown(id='frequency',
                             options=[{'label': frequency, 'value': frequency} for frequency in ['Hourly', 'Daily',
                                                                                                 'Monthly']]),
                html.H6("Data Available Between:"),
                dcc.Dropdown(id='first_year',
                             options=[{'label': str(year), 'value': str(year)} for year in
                                      range(1840,datetime.now().year+1,1)],
                             placeholder='First Year',
                             style={'width': '200px', 'display': 'inline-block'}),
                dcc.Dropdown(id='last_year',
                             options=[{'label': str(year), 'value': str(year)} for year in
                                      range(1840, datetime.now().year + 1, 1)],
                             placeholder='Last Year',
                             style={'width': '200px', 'display': 'inline-block', 'padding-left': '20px'}),
                html.H6("Distance Filter:"),
                dcc.Input(id='latitude',value='',type='text',placeholder='Latitude',
                          style={'width': '200px', 'display': 'inline-block'}),
                dcc.Input(id='longitude',value='',type='text',placeholder='Longitude',
                          style={'width': '200px', 'display': 'inline-block'}),
                dcc.Dropdown(id='radius',
                             options=[{'label': radius, 'value': radius} for radius in ['10', '25', '50', '100']],
                             placeholder='Kilometers Away From')
            ], style={'textAlign': 'left'})
        ], className='five columns')
    ], className='row'),
])


######################################### INTERACTION CALLBACKS ########################################################

@app.callback(
    Output(component_id='selected-station-table', component_property='data'),
    [Input(component_id='station-map', component_property='clickData')]
)
def populate_table(selected_station):
    if selected_station is None:
        df_stn_info = [{col: '' for col in df.columns[1:]}]
        return df_stn_info
    else:
        df_stn_info = df[df.Name == selected_station['points'][0]['text']][1:].to_dict('records')
        return df_stn_info

@app.callback(
    Output(component_id='selected-station', component_property='children'),
    [Input(component_id='station-map', component_property='clickData')]
)
def update_table_name(station_name):
    if station_name is None:
        return 'Select a Station'
    else:
        return 'Station Name: "{}"'.format(station_name['points'][0]['text'])

@app.callback(
    Output(component_id='station-map',component_property='figure'),
    [Input(component_id='province', component_property='value'),
     Input(component_id='frequency', component_property='value'),
     Input(component_id='first_year', component_property='value'),
     Input(component_id='last_year', component_property='value'),
     Input(component_id='latitude', component_property='value'),
     Input(component_id='longitude', component_property='value'),
     Input(component_id='radius', component_property='value')]
)
def map_filter(province,frequency,start,end,lat,lon,radius):

    # Province Filter
    if province is None:
        df_map_filter = df
    else:
        df_map_filter = df[df.Province == province]

    # Frequency Filter
    if frequency == 'Hourly':
        df_map_filter = df_map_filter[df_map_filter['HLY First Year'] > 0]
    elif frequency == 'Daily':
        df_map_filter = df_map_filter[df_map_filter['DLY First Year'] > 0]
    elif frequency == 'Monthly':
        df_map_filter = df_map_filter[df_map_filter['MLY First Year'] > 0]
    else:
        df_map_filter = df_map_filter

    # Date Filter
    if start and end:
        df_map_filter = df_map_filter[(df_map_filter['First Year'] <= np.int64(end)) & (df_map_filter['Last Year'] >= np.int64(start))]
    else:
        df_map_filter = df_map_filter

    # Distance Filter
    if lat and lon and radius:
        try:
            df_map_filter = df_map_filter[
                great_circle_distance(lat,lon,df_map_filter.Latitude,df_map_filter.Longitude) <= np.float64(radius)]
        except:
            print('No Stations')

    return station_map(df_map_filter)