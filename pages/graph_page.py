import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd

from app import app

def download_data_graph(x,y, title):
    return {'data': [
            {'x': x,
             'y': y
             },
    ], 'layout': {
        'title': title
    }
    }

layout = html.Div([
    html.H6('Under Construction'),
    dcc.Link('Go To Home Page', href='/pages/home_page'),
    dcc.Graph(id='download-data-graph',
              figure=download_data_graph([], [], 'None'))
])

@app.callback(
    Output(component_id='download-data-graph', component_property='figure'),
    [Input(component_id='data-store', component_property='data')]
)

def update_data_graph(data):
    download_data = pd.DataFrame(data)
    return download_data_graph(download_data['Date/Time'], download_data['Temp (°C)'], download_data.columns[0])



