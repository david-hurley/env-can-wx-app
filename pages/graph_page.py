import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os
import boto3
import io
import plotly.graph_objs as go

from dash.dependencies import Input, Output
from app import app

######################################### HELPER FUNCTIONS #############################################################

def query_csv_s3(s3, filename, sql_stmt, variable_name):

    #  request object data from S3 bucket
    req = s3.select_object_content(
        Bucket=os.environ['S3_BUCKET'],
        Key='tmp/' + filename,
        ExpressionType='SQL',
        Expression=sql_stmt,
        InputSerialization={'CSV': {"FileHeaderInfo": "Use"}},
        OutputSerialization={'CSV': {}},
    )

    #  create list of requested data in S3 object
    records = []
    for event in req['Payload']:
        if 'Records' in event:
            records.append(event['Records']['Payload'])

    #  store requested data from list as string in UTF-8
    file_str = ''.join(req.decode('utf-8') for req in records)

    #  read string to dataframe
    df = pd.read_csv(io.StringIO(file_str), names=['Date/Time', variable_name])

    return df
######################################### PLOTS ########################################################################


def timeseries_graph(x, y, title, yname, xname):
    return {'data': [
            {'x': x,
             'y': y
             }],
            'layout': {
                'height': 300,
                'title': title,
                'yaxis': {'title': yname},
                'xaxis': {'title': xname}
            }
    }


def boxplot_graph(x, y, title, yname, xname):
    data = go.Box(
        y=y,
        x=x
    )
    layout = go.Layout(
        title={'text': title, 'x': 0.5},
        yaxis={'title': yname},
        xaxis={'title': xname},
        height=400
    )
    return go.Figure(data=data, layout=layout)


def histogram_graph(x, title, xname):
    data = go.Histogram(
        x=x,
        histnorm='percent',
        nbinsx=30
    )
    layout = go.Layout(
        title={'text': title, 'x': 0.5},
        yaxis={'title': 'Percent (%)'},
        xaxis={'title': xname},
        height=500
    )
    return go.Figure(data=data, layout=layout)

######################################### LAYOUT #######################################################################


app_layout = html.Div(
    [
        # page refresh interval
        dcc.Interval(
            id='graph-refresh-interval',
            interval=500,  # in milliseconds
            n_intervals=0
        ),
        # header
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Weather History Canada"),
                    ], className='app_header_title',
                ),
                html.Div(
                    [
                        dcc.Link('Home Page', href='/pages/home_page')
                    ], className='app_header_link',
                ),
            ],
            className='twelve columns app_header',
        ),
        html.Div(
            [
                html.Div(
                    [
                        # time series graph
                        html.Div(
                            [
                                dcc.Loading(
                                    id='load-graph-time-series',
                                    children=
                                    [
                                        dcc.Graph(
                                            id='timeseries-graph',
                                            figure=timeseries_graph([], [], 'No Data Selected', '', ''))
                                    ], type='circle',
                                ),
                            ], className='graph_style', style={'height': '300px'},
                        ),
                        # boxplot graph
                        html.Div(
                            [
                                dcc.Loading(
                                    id='load-graph-box-plot',
                                    children=
                                    [
                                        dcc.Graph(
                                            id='boxplot-graph',
                                            figure=boxplot_graph([], [], 'No Data Selected', '', ''))
                                    ], type='circle',
                                ),
                            ], className='graph_style', style={'height': '400px'},
                        ),
                    ],
                    className='nine columns'
                ),
                html.Div(
                    [
                        # dropdown data selector
                        html.Div(
                            [
                                html.Label("Variable to Graph:", className='filter_box_labels'),
                                dcc.Dropdown(
                                    id='variable-selector',
                                    options=[{'label': variable, 'value': variable} for variable in ['Select a Variable']],
                                    placeholder='Variable To Plot',
                                ),
                            ], className='graph_variable_dropdown',
                        ),
                        # histogram graph
                        html.Div(
                            [
                                dcc.Loading(
                                    id='load-graph-histogram',
                                    children=
                                    [
                                        dcc.Graph(
                                            id='histogram-graph',
                                            figure=histogram_graph([], 'No Data Selected', ''))
                                    ], type='circle',
                                ),
                            ], className='graph_style', style={'height': '550px'}
                        ),
                    ],
                    className='three columns',
                ),
            ],
            className='row')
    ],
)

######################################### INTERACTION CALLBACKS ########################################################

@app.callback(
    [Output(component_id='graph-refresh-interval', component_property='interval'),
     Output(component_id='variable-selector', component_property='options')],
    [Input(component_id='variable-name-store', component_property='data'),
     Input(component_id='graph-refresh-interval', component_property='n_intervals')]
)
def update_interval_time(variable_names, n_int):

    variable_dropdown = [{'label': variable, 'value': variable} for variable in list(variable_names.keys())[1:]]
    interval = 24*60*60*1*1000  # in milliseconds

    return interval, variable_dropdown


@app.callback(
    [Output(component_id='timeseries-graph', component_property='figure'),
     Output(component_id='boxplot-graph', component_property='figure'),
     Output(component_id='histogram-graph', component_property='figure')],
    [Input(component_id='filename-store', component_property='data'),
     Input(component_id='station-metadata-store', component_property='data'),
     Input(component_id='variable-selector', component_property='value'),
     Input(component_id='graph-refresh-interval', component_property='n_intervals')]
)
def update_data_graph(filename, station_metadata, variable_name, n_int):

    if variable_name is None:
        raise dash.exceptions.PreventUpdate

    s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])

    #  sql statement to select date and chosen variable
    sql_stmt = 'SELECT \"{}\", \"{}\" FROM s3Object'.format('Date/Time', variable_name)

    # query data s3
    df = query_csv_s3(s3, filename, sql_stmt, variable_name)

    #  wind needs to be multiplied by 10 to be 0 >> 360
    if variable_name == 'Wind Dir (10s deg)':
        df[variable_name] = df[variable_name] * 10

    # subsample dataframe for boxplot speed
    df_box = df.copy()
    df_box = df_box.sample(frac=0.1)
    df_box.sort_values(by=['Date/Time'], inplace=True)

    #  boxplot months
    boxplot_months = pd.to_datetime(df_box['Date/Time']).dt.strftime('%b')

    # define metadata
    station_metadata = list(station_metadata.keys())

    #  assign data to graphs
    figure1 = timeseries_graph(df['Date/Time'],
                               df[variable_name],
                               '{}: {}N, {}W'.format(station_metadata[2], station_metadata[0], station_metadata[1]), variable_name, 'Date')

    figure2 = boxplot_graph(list(boxplot_months),
                            list(df_box[variable_name]),
                            '{}: {}N, {}W'.format(station_metadata[2], station_metadata[0], station_metadata[1]), variable_name, 'Month')

    figure3 = histogram_graph(df[variable_name],
                              '{}: {}N, {}W'.format(station_metadata[2], station_metadata[0], station_metadata[1]), variable_name)

    return figure1, figure2, figure3
