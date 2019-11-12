import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from pages import home_page, graph_page

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/pages/graph_page':
        return graph_page.layout
    else:
        return home_page.layout

if __name__ == '__main__':
    app.run_server(debug=True, port=8100)