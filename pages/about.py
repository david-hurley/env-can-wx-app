import dash_core_components as dcc
import dash_html_components as html

layout = html.Div([
    html.Div([
        html.Div([
            html.H3("Weather History Canada")
        ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
        html.Div([
            dcc.Link('Home Page', href='/pages/home_page')
        ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
    ], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'}),
    html.Div([
        html.H4("What is Weather History Canada?", style={'font-weight': 'bold'}),
        html.Label(['Weather History Canada is an open source web application for accessing historical weather data from '
                   'Environment and Climate Change Canada maintained weather stations. Presently, historical weather data'
                    'is accessed through the official Environment and Climate Change Canada',
                    html.A(' historical data portal', href='https://climate.weather.gc.ca/historical_data/search_historic_data_e.html'),
                    '. However, the current portal lacks a map search feature and only allows for downloading of data in '
                    'monthly (for hourly data) and yearly (for daily and monthly data) increments. This means to download'
                    '20 years of hourly data a user would need to download 240 seperate files and then combine them!']),
        html.H4("Who is Weather History Canada for?", style={'font-weight': 'bold'}),
        html.Label('Weather History Canada is for anyone looking to access and visualize historical weather data FAST! As'
                   'someone with a background in meteorology and experience in environmental consulting services, I know '
                   'how important it is to have quick access to historical weather data. Some users may be academics looking '
                   'for additional datasets to support environmental modelling, others may be consultants looking to calculate design '
                   'wind and flood conditions, and some might just have an interest in climate data. Regardless of the background, '
                   'Weather History Canada is built to assist all users with accessing and viewing data quickly. '),
        html.H4("Where did Weather History Canada come from?", style={'font-weight': 'bold'}),
        html.Label('Weather History Canada was born out of a desire to '),
        html.H4("Contact Weather History Canada", style={'font-weight': 'bold'})
    ], className='six columns')
])
