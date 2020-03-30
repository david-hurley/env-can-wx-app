import dash_core_components as dcc
import dash_html_components as html

app_layout = html.Div([
    html.Div([
        html.Div([
            html.H3("Weather History Canada")
        ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
        html.Div([
            dcc.Link('Home Page', href='/pages/home_page')
        ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
    ], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'}),

    html.Div([
        html.Div([

            html.H4("What is Weather History Canada?", style={'font-weight': 'bold'}),
            html.Label(['Weather History Canada is an open source web application tool for accessing historical weather data '
                        'from over 8000 active and inactive Environment and Climate Change Canada (ECCC) maintained weather stations '
                        'going as far back as 1840. With a few clicks of the mouse you can search, download, and visualize '
                        'hourly, daily, and monthly ECCC weather data for any desired record length. The goal of Weather History Canada '
                        'is to better the user experience by making it easier and quicker to download and interpret large amounts '
                        'of historical weather data.']),

            html.H4("Why is Weather History Canada needed?", style={'font-weight': 'bold'}),
            html.Label(['Presently, historical weather data is accessed through the official ECCC ',
                        html.A('historical data portal', href='https://climate.weather.gc.ca/historical_data/search_historic_data_e.html'),
                        '. While ECCC does an excellent job of collecting and hosting the data, the portal itself lacks certain search '
                        'and download features. For example, since there is no way to visualize weather station locations on a map the '
                        'user needs to know the station they are looking for in advance. The portal also limits downloading of hourly, '
                        'monthly, and yearly weather data to small time frames. In the case of hourly weather data the portal limits downloads '
                        'to one month increments meaning a user needing 10 years of hourly data from a select station would need to download 120 separate '
                        'files. Additionally, the portal has no way to visualize the data once downloaded. All of this combined makes the user '
                        'experience of searching, downloading, and visualizing data arduous.']),


            html.H4("Who is Weather History Canada for?", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada is for anyone looking to download and visualize historical weather data '
                       'from ECCC FAST! Whether you are an academic, industry professional, or outdoor enthusiast this site '
                       'will allow you to begin making decisions with regards to historical weather data without the previous overhead.'),

            html.H4("Where did Weather History Canada come from?", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada was born out of a desire to make the process of searching for, downloading, and visualizing '
                       'historical Canadian weather data faster and easier. As someone with a background in meteorology and experience in the environmental '
                       'consulting services, I know how important it is to have quick access to historical weather data when making operational '
                       'decisions. However, I often found myself and co-workers spending multiple hours downloading weather station data from the ECCC '
                       'portal, combining the datasets, and visualizing the data only to realize at the end that we needed something different and had to '
                       'start over. Eventually, I became frustrated with the current system and as it goes "necessity is the mother of invention" so Weather '
                       'History Canada was born.'),

            html.H4("Limitations of Weather History Canada", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada is a tool for more quickly downloading and visualizing weather data from ECCC '
                       'maintained weather stations. Weather History Canada makes no warranty, express or implied, and assumes '
                       'no liability with respect to the use of weather data obtained from this site. Weather History Canada '
                       'provides no assurance as to the quality or completeness of ECCC maintained weather data sets.')

        ], className='seven columns', style={'margin-left': '1rem'}),

        html.Div([
            html.H6("Contact Weather History Canada", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada is a work in progress with a goal of continuing to improve the user experience. '
                       'All comments/suggestions and questions are welcome. Additionally, data downloaded from ECCC is open source, and in '
                       'keeping with this, the code for Weather History Canada is freely available on GitHub along with a more in depth description of the app.'),
            html.Label(['Email: ', html.A('weatherhistorycanada@gmail.com', href='weatherhistorycanada@gmail.com')], style={'margin-top': '2rem'}),
            html.Label(['GitHub Link: ', html.A('GET THE CODE', href='https://github.com/david-hurley/env-can-wx-app')])
        ], className='four columns', style={'margin-top': '2rem', 'margin-left': '13rem', 'border': '2px black solid', 'text-align': 'left'})

    ], className='row')
])
