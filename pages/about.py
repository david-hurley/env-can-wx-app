import dash_core_components as dcc
import dash_html_components as html

layout = html.Div([
    html.Div([
        html.H3("Super Speedy Environment Canada Weather Download")
    ], style={'display': 'inline-block', 'align-self': 'center', 'margin': '0 auto'}),
    html.Div([
        dcc.Link('Home Page', href='/pages/home_page')
    ], style={'textAlign': 'right', 'display': 'inline-block', 'margin-right': '2rem', 'font-size': '20px'})
], className='twelve columns', style={'background': '#DCDCDC', 'border': '2px black solid', 'display': 'flex'})
