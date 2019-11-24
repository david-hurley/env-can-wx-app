import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app

layout = html.Div([
    html.H3('Graph Page'),
    html.H6('Under Construction'),
    dcc.Link('Go To Home Page', href='/pages/home_page'),
    html.Button('Click', id='button'),
    html.Label(id='test', children='HERE')
])

@app.callback(
    Output(component_id='test', component_property='children'),
    [Input(component_id='button', component_property='n_clicks')],
    [State(component_id='create-data', component_property='data')]
)
def plotting(click, data):
    print(data)
    if click:
        d = 'THERE'
    else:
        d = 'THAR'

    return d

