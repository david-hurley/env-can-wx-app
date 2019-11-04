import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd

df = pd.read_csv('station-metadata-processed.csv')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H3('Environment Canada Weather Stations'),
            dcc.Graph(
                id='graph',
                style={'height': 600
                       },
                figure={
                        'data': [{
                            'lat': df.Latitude, 'lon': df.Longitude, 'type': 'scattermapbox','text': df.Name
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
            html.H6('Station Name'),
            dcc.Input(id='stname',value='Select or Enter Station Name',type='text'),
            html.H6('Province'),
            dcc.Dropdown(
                id='province',
                options=[
                    {'label': "Alberta",'value':"AB"},
                    {'label': "British Columbia",'value':"BC"},
                    {'label': "Manitoba",'value':"MB"},
                    {'label': "New Brunswick",'value':"NB"},
                    {'label': "Newfoundland and Labrador",'value':"NL"},
                    {'label': "Northwest Territories", 'value': "NT"},
                    {'label': "Nova Scotia",'value':"NS"},
                    {'label': "Nunavut", 'value': "NU"},
                    {'label': "Ontario",'value':"ON"},
                    {'label': "Prince Edward Island",'value':"PE"},
                    {'label': "Quebec",'value':"QC"},
                    {'label': "Saskatchewan",'value':"SK"},
                    {'label': "Yukon",'value':"YT"},
                ]
            ),
            html.H6('Frequency'),
            dcc.Dropdown(
                id='freq',
                options=[
                    {'label':"Hourly",'value':"HR"},
                    {'label':"Daily",'value':"DY"},
                    {'label':"Monthly",'value':"MT"}
                ]
            ),
            html.H6('Start Year'),
            dcc.Input(id='startyear',value='Enter a Start Year',type='text'),
            html.H6('End Year'),
            dcc.Input(id='endyear', value='Enter a End Year', type='text'),
            ], className="six columns"),

        html.Div([
            html.Button('Download Data', id='button')
        ], className="six columns")
        ], className="row")
    ])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

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
    Output(component_id='graph',component_property='figure'),
    [Input(component_id='province',component_property='value')]
)
def update_graph(options):
    if options is None:
        return 'None'
    else:
        df_filter = df[df.Province==options]
        return go.Scattermapbox(lat=df_filter.Latitude,lon=df_filter.Longitude,text=df_filter.Name)

if __name__ == '__main__':
    app.run_server(debug=True)
