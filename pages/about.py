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
                       'from ECCC FAST! This site will allow you to begin making decisions with regards to historical weather data without the previous overhead!'),

            html.H4("Where did Weather History Canada come from?", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada was born out of a desire to make the process of searching for, downloading, and visualizing '
                       'historical Canadian weather data faster and easier. As someone with a background in meteorology and experience in the environmental '
                       'consulting services, I know how important it is to have quick access to historical weather data. '
                       'However, I often found myself spending multiple hours downloading weather station data from the ECCC '
                       'portal, combining the datasets, and visualizing the data only to realize at the end that I needed something different.'
                       ' Eventually, I became frustrated with the current system and as it goes "necessity is the mother of invention" so Weather '
                       'History Canada was born.'),

            html.H4("Limitations of Weather History Canada", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada is a tool for more quickly downloading and visualizing weather data from ECCC '
                       'maintained weather stations. Weather History Canada makes no warranty, express or implied, and assumes '
                       'no liability with respect to the use of weather data obtained from this site.'),
            html.Br(),
            html.Label('Additionally, "Environment and Climate Change Canada does not warrant the quality, accuracy, or completeness of '
                       'any information, data or product from these web pages. It is provided "AS IS" without warranty or condition of '
                       'any nature. Environment and Climate Change Canada disclaims all other warranties, either expressed or implied, '
                       'including but not limited to implied warranties of merchantability and fitness for a particular purpose, '
                       'with respect to the information, data, product or accompanying materials retrieved from this website."')

        ], className='seven columns', style={'margin-left': '1rem'}),

        html.Div([
            html.H6("Contact Weather History Canada", style={'font-weight': 'bold'}),
            html.Label('Weather History Canada is a work in progress with a goal of continuing to improve the user experience. '
                       'All comments/suggestions and questions are welcome.'),
            html.Label(['Email: ', html.A('weatherhistorycanada@gmail.com', href='weatherhistorycanada@gmail.com')], style={'margin-top': '2rem'}),
        ], className='four columns', style={'margin-top': '2rem', 'margin-left': '13rem', 'border': '2px black solid', 'text-align': 'left'}),

        html.Div([

            html.H6("Note About Data Processing", style={'font-weight': 'bold'}),
            html.Label(['In order to reduce download and rendering times, the data from ECCC has been modified to remove the DATA FLAG columns.'
                        ' The DATA FLAG values accompany missing data and explain why it is missing. At this time there is no plan to include these data.'
                        ' More information on the meaning of the DATA FLAG columns can be found in the ',
                        html.A('Technical Documentation PDF', href='https://climate.weather.gc.ca/doc/Technical_Documentation.pdf'),
                        ' and a description of the downloaded data parameters is available ',
                        html.A('on the ECCC webpage.', href='https://climate.weather.gc.ca/glossary_e.html')])
        ], className='four columns', style={'margin-top': '2rem', 'margin-left': '13rem', 'text-align': 'left'})

    ], className='row')
])
