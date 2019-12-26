import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
import os
import boto3
import io

from app import app

def download_data_graph(x,y, title):
    return {'data': [
            {'x': x,
             'y': y,
             'name': 'first plot'
             }
    ], 'layout': {
        'height': 350,
        'title': title
    }
    }


layout = html.Div([
    dcc.Interval(
        id='interval-kickstart',
        interval=250,  # in milliseconds
        n_intervals=0
    ),
    html.Div([
        html.Div([
            html.H3("Super Speedy Environment Canada Weather Download")
        ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
        html.Div([
            dcc.Link('Home Page', href='/pages/home_page')
        ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
    ], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'}),

    html.Div([
        html.Div([
            dcc.Loading(id='load-graph', children=[
                html.Div(dcc.Graph(id='download-data-graph1', figure=download_data_graph([], [], 'None')))], type='defualt')],className='six columns'),

        html.Div([
            html.Div([dcc.Graph(id='download-data-graph2', figure=download_data_graph([], [], 'None'))], style={'height': '70%'}),
            dcc.Dropdown(id='data-selector', options=[{'label': variable, 'value': variable} for variable in ['Select a Variable']],
                         placeholder='Variable To Plot')], className='six columns')
    ], className='row')
])

@app.callback(
    [Output(component_id='interval-kickstart', component_property='interval'),
     Output(component_id='data-selector', component_property='options')],
    [Input(component_id='column-name-store', component_property='data'),
     Input(component_id='interval-kickstart', component_property='n_intervals')]
)
def update_interval_time(column_names, n_int):
    column_dropdown_options = [{'label': variable, 'value': variable} for variable in column_names]
    interval = 24*60*60*1*1000
    return interval, column_dropdown_options

@app.callback(
    [Output(component_id='download-data-graph1', component_property='figure'),
     Output(component_id='download-data-graph2', component_property='figure')],
    [Input(component_id='filename-store', component_property='data'),
     Input(component_id='data-selector', component_property='value'),
     Input(component_id='interval-kickstart', component_property='n_intervals')]
)
def update_data_graph(filename, column_name, n_int):
    if column_name:
        s3 = boto3.client('s3', region_name='us-east-1',
                          aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                          aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        sql_stmt = 'SELECT \"{}\", \"{}\" FROM s3Object'.format('Date/Time', column_name)
        req = s3.select_object_content(
            Bucket=os.environ['S3_BUCKET'],
            Key=filename,
            ExpressionType='SQL',
            Expression=sql_stmt,
            InputSerialization={'CSV': {"FileHeaderInfo": "Use"}},
            OutputSerialization={'CSV': {}},
        )
        records = []
        for event in req['Payload']:
            if 'Records' in event:
                records.append(event['Records']['Payload'])

        file_str = ''.join(req.decode('utf-8') for req in records)
        df = pd.read_csv(io.StringIO(file_str), names=['Date/Time', column_name])

        figure = download_data_graph(df['Date/Time'], df[column_name], column_name)

    else:
        figure = download_data_graph([], [], 'Some')

    return figure, figure