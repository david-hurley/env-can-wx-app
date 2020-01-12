import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table

import pandas as pd
import os
import boto3
import io
import plotly.graph_objs as go

from app import app

######################################### PLOTS ########################################################################

# Plot Timeseries graph
def timeseries_plot(x, y, title, yname, xname):
    return {'data': [
            {'x': x,
             'y': y
             }
    ], 'layout': {
        'height': 300,
        'title': title,
        'yaxis':{'title': yname},
        'xaxis':{'title': xname}
    }
    }

# Plot Boxplot
def boxplot(x,y):
    return {
        'data': [
            go.Box(
                y=y,
                x=x
            )
        ]
    }

######################################### LAYOUT #######################################################################

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
                html.Div([dcc.Graph(id='download-data-graph1', figure=timeseries_plot([], [], 'No Data Selected', '', ''))],
                         style={'margin-top': '1rem', 'border': '2px black solid'}),
                html.Div([dcc.Graph(id='download-data-graph2', figure=boxplot([], []))],
                         style={'margin-top': '1rem', 'border': '2px black solid'})
            ], type='defualt')
        ], className='nine columns'),

        html.Div([
            html.Label("Variable to Graph:", style={'font-weight': 'bold', 'font-size': '18px'}),
            dcc.Dropdown(id='data-selector', options=[{'label': variable, 'value': variable} for variable in ['Select a Variable']],
                         placeholder='Variable To Plot', style={'margin-top': '1rem', 'margin-bottom': '15rem'}),
            dash_table.DataTable(id='wx-table', columns=[{"name": i, "id": i} for i in ['Min', '5th', '10th', '25th', 'Mean', '75th', '90th', '95th', 'Max']], data=[])
        ], className='three columns')

    ], className='row')
])

######################################### INTERACTION CALLBACKS ########################################################

# Trigger update on page click
@app.callback(
    [Output(component_id='interval-kickstart', component_property='interval'),
     Output(component_id='data-selector', component_property='options')],
    [Input(component_id='column-name-store', component_property='data'),
     Input(component_id='interval-kickstart', component_property='n_intervals')]
)
def update_interval_time(column_names, n_int):
    column_dropdown_options = [{'label': variable, 'value': variable} for variable in list(column_names.keys())[1:]]
    interval = 24*60*60*1*1000
    return interval, column_dropdown_options

# Fetch S3 data and graph
@app.callback(
    [Output(component_id='download-data-graph1', component_property='figure'),
     Output(component_id='download-data-graph2', component_property='figure'),
     Output(component_id='wx-table', component_property='data')],
    [Input(component_id='filename-store', component_property='data'),
     Input(component_id='station-metadata-store', component_property='data'),
     Input(component_id='data-selector', component_property='value'),
     Input(component_id='interval-kickstart', component_property='n_intervals')]
)
def update_data_graph(filename, station_metadata, column_name, n_int):
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
        if column_name == 'Wind Dir (10s deg)':
            df[column_name] = df[column_name]*10

        boxplot_months = pd.to_datetime(df['Date/Time']).dt.month

        table_key = ['Min', '5th', '10th', '25th', 'Mean', '75th', '90th', '95th', 'Max']
        table_value = [df[column_name].quantile(P) for P in [0, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1]]
        table_data = [dict(zip(table_key, table_value))]

        station_metadata = list(station_metadata.keys())
        figure1 = timeseries_plot(df['Date/Time'], df[column_name], '{}: {}N, {}W'.format(station_metadata[3], station_metadata[1], station_metadata[2]), column_name, 'Date')
        figure2 = boxplot(list(boxplot_months), list(df[column_name]))

    else:
        figure1 = timeseries_plot([], [], 'No Data Selected', '', '')
        figure2 = boxplot([], [])
        table_data = []

    return figure1, figure2, table_data