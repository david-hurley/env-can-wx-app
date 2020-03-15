import dash
import os

app = dash.Dash(__name__)
server=app.server
server.secret_key = os.environ.get('secret_key', 'secret')
app.config.suppress_callback_exceptions = True
app.title = 'Weather History Canada'