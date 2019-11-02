import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([
    html.H1('Environment Canada Weather App'),
    html.Iframe(id='map',srcDoc=open('station_locations.html','r').read(),width='70%',height='600')
])

if __name__ == '__main__':
    app.run_server(debug=True)