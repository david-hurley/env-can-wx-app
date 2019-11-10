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
df.replace(-999,'N/A',inplace=True)

# URL Path to Bulk Data Download From Environment Canada
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

def station_map(stations, lat_selected, lon_selected, name_selected, color):
    return {'data': [
                {'type': 'scattermapbox',
                 'lat': stations.Latitude,
                 'lon': stations.Longitude,
                 'name': '',
                 'text': stations.Name,
                 'marker': {'color': color}
                },

                {'type': 'scattermapbox',
                 'lat': [lat_selected],
                 'lon': [lon_selected],
                 'name': '',
                 'text': [name_selected],
                 'marker': {'color': 'red'}
                 }
            ],
        'layout': {
            'showlegend': False,
            'uirevision': 'static',
            'height': 500,
            'mapbox': {
                'style': 'basic',
                'center': {'lat': 59, 'lon': -97},
                'zoom': 2.5,
                'accesstoken': 'pk.eyJ1IjoiZGxodXJsZXkiLCJhIjoiY2sya2xrMTJqMWFjMzNucXB3bnp1MXd0ZyJ9.UBKniAsr5Li1Yv5dJOP5yQ'
                },
            'margin': {
                'l': 0, 'r': 0, 'b': 0, 't': 0
            },
        }
    }

######################################### LAYOUT #######################################################################

app.css.append_css({
    'external_url': "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

layout = html.Div([
    # Title Row
    html.Div([
        # Title Column
        html.Div([
            html.H2("Super Speedy Environment Canada Weather Download",
                    style={'display': 'inline-block'}),
            ], className='twelve columns', style={'textAlign': 'center'})
    ], className='row', style={'background': '#DCDCDC', 'border': '2px black solid'}),

    # Map and Toggles Row
    html.Div([
        # Map Column
        html.Div([
            # Map of stations
            dcc.Graph(id='station-map',
                      figure=station_map(df, [], [], [], 'blue'),
                      style={'border': '2px black solid'}),
            html.Br(),
            html.Label(id='selected-station', children='Select a Station',
                    style={'textAlign': 'left', 'font-weight':'bold'}),
            dash_table.DataTable(id='selected-station-table',
                                 columns=[{"name": col, "id": col} for col in df.columns[1:]],
                                 data=[{col: '' for col in df.columns[1:]}],
                                 style_table={'overflowX': 'scroll'},
                                 style_header={'border': '1px solid black',
                                               'backgroundColor': 'rgb(200, 200, 200)'},
                                 style_cell={'border': '1px solid grey'},
                                 row_selectable='single'),
        ], className='seven columns'),

        # Toggles Column
        html.Div([
            html.Div([
                html.H6("Station Name:"),
                dcc.Input(id='stn_name',value='',type='text',placeholder='Enter Station Name', style={'width': '300px'}),
                html.H6("Province:"),
                dcc.Dropdown(id='province',
                             options=[{'label': province, 'value': province} for province in df.Province.unique()],
                             style={'width': '400px'}),
                html.H6("Data Frequency:"),
                dcc.Dropdown(id='frequency',
                             options=[{'label': frequency, 'value': frequency} for frequency in ['Hourly', 'Daily',
                                                                                                 'Monthly']],
                             style={'width': '400px'}),
                html.H6("Data Available Between:"),
                dcc.Dropdown(id='first_year',
                             options=[{'label': str(year), 'value': str(year)} for year in
                                      range(1840,datetime.now().year+1,1)],
                             placeholder='First Year',
                             style={'width': '250px', 'display': 'inline-block'}),
                dcc.Dropdown(id='last_year',
                             options=[{'label': str(year), 'value': str(year)} for year in
                                      range(1840, datetime.now().year + 1, 1)],
                             placeholder='Last Year',
                             style={'width': '250px', 'display': 'inline-block', 'padding-left': '20px'}),
                html.H6("Distance Filter:"),
                dcc.Input(id='latitude',value='',type='text',placeholder='Latitude',
                          style={'width': '100px', 'display': 'inline-block'}),
                dcc.Input(id='longitude',value='',type='text',placeholder='Longitude',
                          style={'width': '100px', 'display': 'inline-block'}),
                dcc.Dropdown(id='radius',
                             options=[{'label': radius, 'value': radius} for radius in ['10', '25', '50', '100']],
                             placeholder='Kilometers Away From',
                             style={'width':'100px', 'display': 'inline-block'})
            ], style={'textAlign': 'left'})
        ], className='five columns', style={'border': '2px black solid', 'padding-left': '20px'}),

        # Data Download Column
        html.Div([
            html.Div([
                html.H6('Download Records for Selected Station'),
            ], style={'textAlign': 'center'}),
            html.Div([
                dcc.DatePickerRange(
                    start_date_placeholder_text="Start Period",
                    end_date_placeholder_text="End Period",
                    calendar_orientation='vertical',
                )
            ])
        ], className='five columns')
    ], className='row', style={'padding-top': '10px'}),
])


######################################### INTERACTION CALLBACKS ########################################################
@app.callback(
    Output(component_id='station-map',component_property='figure'),
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
def map_filter(province,frequency,start,end,lat,lon,radius,stn_name,click_highlight):

    # Province Filter
    if province is None:
        df_map_filter = df
    else:
        df_map_filter = df[df.Province == province]

    # Frequency Filter
    if frequency == 'Hourly':
        df_map_filter = df_map_filter[df_map_filter['First Year (Hourly)'] != 'N/A']
    elif frequency == 'Daily':
        df_map_filter = df_map_filter[df_map_filter['First Year (Daily)'] != 'N/A']
    elif frequency == 'Monthly':
        df_map_filter = df_map_filter[df_map_filter['First Year (Monthly)'] != 'N/A']
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

    # Name Filter
    if stn_name:
        df_map_filter = df_map_filter[df_map_filter.Name.str.contains(stn_name.upper())]
    else:
        df_map_filter = df_map_filter

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

@app.callback(
    Output(component_id='selected-station-table', component_property='data'),
    [Input(component_id='station-map', component_property='clickData'),
     Input(component_id='frequency', component_property='value')]
)
def populate_table(selected_station,frequency):
    try:
        df_stn_info = df[(df.Latitude == selected_station['points'][0]['lat']) &
                         (df.Longitude == selected_station['points'][0]['lon'])]
        if frequency == 'Hourly':
            return df_stn_info[df_stn_info['First Year (Hourly)'] != 'N/A'].loc[1:].to_dict('records')
        elif frequency == 'Daily':
            return df_stn_info[df_stn_info['First Year (Daily)'] != 'N/A'].loc[1:].to_dict('records')
        elif frequency == 'Monthly':
            return df_stn_info[df_stn_info['First Year (Monthly)'] != 'N/A'].loc[1:].to_dict('records')
        else:
            return df_stn_info.loc[1:].to_dict('records')
    except:
        df_stn_info = [{col: '' for col in df.columns[1:]}]
        return df_stn_info

@app.callback(
    Output(component_id='selected-station', component_property='children'),
    [Input(component_id='selected-station-table', component_property='data')]
)
def update_table_name(table_data):
    try:
        length_table_data = len(table_data)
        if length_table_data == 1:
            return 'Selected Station Name: "{}"'.format(table_data[0]['Name'])
        else:
            return 'Selected Station Name: "{}" (Multiple Records Exist at This Location)'.format(table_data[0]['Name'])
    except:
        return 'Select a Station'