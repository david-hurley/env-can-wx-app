import dash_core_components as dcc
import dash_html_components as html

layout = html.Div([
    html.H3('About Page'),
    html.H6('Under Construction'),
    dcc.Link('Go To Home Page', href='/pages/home_page'),
])