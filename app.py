import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np

df = pd.read_csv('station-metadata-processed.csv')
url_env_can = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?'
format_url_env_can = 'format=csv&stationID=1706&Year=2019&Month=10&Day=14&timeframe=1'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H3('Environment Canada Weather Station Map'),
            dcc.Graph(
                id='graph',
                style={'height': 600
                       },
                figure={
                        'data': [{
                            'lat': df.Latitude, 'lon': df.Longitude, 'type': 'scattermapbox', 'text': df.Name
                        }],
                        'layout': {
                            'mapbox': {
                                'style': 'basic',
                                'center': {'lat':59,'lon':-97},
                                'zoom': 2.5,
                                'accesstoken': 'pk.eyJ1IjoiZGxodXJsZXkiLCJhIjoiY2sya2xrMTJqMWFjMzNucXB3bnp1MXd0ZyJ9.UBKniAsr5Li1Yv5dJOP5yQ'
                            },
                            'margin': {
                                'l': 0, 'r': 0, 'b': 0, 't': 0
                            },
                        }
                    }
            )], className="six columns"),

        html.Div([
            html.H3('Map Toggles'),
            html.H6('Province:'),
            dcc.Dropdown(
                id='province',
                options=[{'label': province, 'value': province} for province in df.Province.unique()
                ]
            ),
            html.H6('Data Frequency:'),
            dcc.Dropdown(
                id='freq',
                options=[{'label': frequency, 'value': frequency} for frequency in ['Hourly', 'Daily', 'Monthly']
                ]
            ),
            html.H6('Data Available Between:'),
            dcc.Input(id='start_year', value='1840', type='text'),
            dcc.Input(id='end_year', value='2019', type='text'),
            html.H6('Distance Filter:'),
            dcc.Input(id='lat',value='49.50',type='text'),
            dcc.Input(id='lon',value='-123.50',type='text'),
            dcc.Dropdown(
                id='radius',
                options=[{'label':radius, 'value': radius} for radius in ['10','25','50','100']],
                placeholder='Kilometers Away From'
            ),
            html.H6('Station Name:'),
            dcc.Input(id='stname', value='Select or Enter Station Name', type='text', autoComplete='on'),
            ], className="six columns"),

        html.Div([
            html.H3('Data Download'),
            html.A('Download Data', id='button')
        ], className="six columns")
        ], className="row")
    ])

@app.callback(
    Output(component_id='stname',component_property='value'),
    [Input(component_id='graph',component_property='clickData')]
)
def update_output_div(clickData):
    if clickData is None:
        return 'Select or Enter Station Name'
    else:
        return clickData['points'][0]['text']

@app.callback(
    Output(component_id='graph', component_property='figure'),
    [Input(component_id='province', component_property='value'),
     Input(component_id='start_year', component_property='value'),
     Input(component_id='end_year', component_property='value'),
     Input(component_id='freq', component_property='value'),
     Input(component_id='lat', component_property='value'),
     Input(component_id='lon', component_property='value'),
     Input(component_id='radius', component_property='value')]
)
def update_graph(prov, start_year, end_year, freq, lat_filter, lon_filter, radius_filter):
    if start_year and end_year:
        df_filter = df[(df['First Year'] <= np.int64(end_year)) & (df['Last Year'] >= np.int64(start_year))]
    else:
        df_filter = df

    if prov is None:
        df_filter = df_filter
    else:
        df_filter = df_filter[df_filter.Province == prov]

    if freq == 'Hourly':
        df_filter = df_filter[df_filter['HLY First Year'] > 0]
    elif freq == 'Daily':
        df_filter = df_filter[df_filter['DLY First Year'] > 0]
    elif freq == 'Monthly':
        df_filter = df_filter[df_filter['MLY First Year'] > 0]
    else:
        df_filter = df_filter

    if radius_filter and lat_filter and lon_filter:
        try:
            lat1, lon1 = np.radians([np.float64(lat_filter),np.float64(lon_filter)])
            lat2, lon2 = np.radians([df_filter.Latitude, df_filter.Longitude])
            a = np.sin((lat2 - lat1) / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2.0) ** 2
            distance = 6371 * 2 * np.arcsin(np.sqrt(a))
            df_filter = df_filter[distance <= np.float64(radius_filter)]
        except:
            print('No Stations')
    else:
        df_filter = df_filter

    return {
        'data': [{
            'lat': df_filter.Latitude, 'lon': df_filter.Longitude, 'type': 'scattermapbox', 'text': df_filter.Name
        }],
        'layout': {
            'mapbox': {
                'style': 'basic',
                'center': {'lat':59,'lon':-97},
                'zoom': 2.5,
                'accesstoken': 'pk.eyJ1IjoiZGxodXJsZXkiLCJhIjoiY2sya2xrMTJqMWFjMzNucXB3bnp1MXd0ZyJ9.UBKniAsr5Li1Yv5dJOP5yQ'
            },
            'margin': {
                'l': 0, 'r': 0, 'b': 0, 't': 0
            },
        }
    }

@app.callback(
    Output(component_id='button', component_property= 'href'),
    [Input(component_id= 'button', component_property= 'n_clicks')]
)
def download_data(filter_value):
    df_output = pd.read_csv(url_env_can + format_url_env_can)
    return df_output.to_csv('DownloadedData.csv')



if __name__ == '__main__':
    app.run_server(debug=True, port=8000)
