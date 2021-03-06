import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import pandas as pd
import numpy as np
import json

import plotly.express as px
import plotly.graph_objects as go

# App settings
tabtitle='efterled'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = tabtitle

background_color = '#242424'
land_color = '#2e2e2e'
accent_color = '#6b6b6b'
text_color = '#BBBBBB'

#Heroku branch
githublink='https://github.com/Baranoi/ortnamn.git'

# Nicer default colors for better contrast on dark background
colorway = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000']

def get_polygon_xy(jdata):
    # Convert geojson data to coordinate list
    pts = []#list of points defining boundaries of polygons
    for  feature in jdata['features']:
        if feature['geometry']['type'] == 'Polygon':
            pts.extend(feature['geometry']['coordinates'][0])    
            pts.append([None, None])#mark the end of a polygon   
            
        elif feature['geometry']['type'] == 'MultiPolygon':
            for polyg in feature['geometry']['coordinates']:
                pts.extend(polyg[0])
                pts.append([None, None])#end of polygon
        elif feature['geometry']['type'] == 'LineString': 
            points.extend(feature['geometry']['coordinates'])
            points.append([None, None])
        else: pass           
        #else: raise ValueError("geometry type irrelevant for map")
    x, y = zip(*pts)  
    return x, y

# Prepare geometry data
with open('./static/svenska-landskap.geo.json', 'r') as fp:
    jdata = json.load( fp)
x, y = get_polygon_xy(jdata)

#Initiate figure with background
fig = go.Figure()
fig.update_layout(#width=600,  
                height=900, 
                yaxis=dict(scaleanchor="x", 
                           scaleratio=1.8,
                           showgrid=False,
                           zeroline=False,
                           visible=False),
                xaxis=dict(showgrid=False,
                           zeroline=False,
                           visible=False,
                           range=[11,24]),
                legend=dict(x=0.7,
                            y=0.1,
                            traceorder="normal",
                            font=dict(
                                family="sans-serif",
                                size=17,
                                color=accent_color,
                            )
                        ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                colorway = colorway,
                margin={"r":0,"t":0,"l":0,"b":0},
                 )


def get_map_trace():
    # Get background trace of regions
    trace = go.Scatter(x=x, 
                    y=y, 
                    mode='lines', 
                    line_color=accent_color, 
                    line_width=1.0, 
                    fill='toself', 
                    fillcolor=land_color,
                    showlegend=False,
                    hoverinfo='skip'
    )
    return trace

def get_el_trace(el, visible):
    # Get suffix trace
    if el in el_unique:
        el_df = df[df['efterled'] == el]
    else:
        #If not already categorized
        el_df = df[df['ortnamn'].str.endswith(el)]
    
    trace = go.Scatter(x=el_df.longitude, 
                    y=el_df.latitude, 
                    mode='markers',
                    marker=dict(size=3),
                    name='-'+el + '   ('+str(len(el_df.index))+')',
                    hovertext=el_df.ortnamn,
                    hoverinfo='text',
                    visible=visible
    )
    return trace

fig.add_trace(get_map_trace()) #Init background map

# Sort after top suffixes on init and pic
df = pd.read_csv('./static/wiki_ortnamn_heroku.csv')
df_el = df.groupby('efterled').count().reset_index()
df_el.sort_values('ortnamn', inplace=True, ascending=False)
el_unique = df_el['ortnamn'].unique()

# Build counts of suffixes to make suggestion list and top 15
el_count = []
for i, row in df_el.iterrows():
    el = row['efterled']
    d = {}
    d['label'] = '-'+el + '   ('+str(row['ortnamn'])+')'
    d['value'] = el
    el_count.append(d)

top_el = df_el['efterled'][:15]

# Plot default suffixes
for el in top_el:
    if el in ['arp', 'fors','sund','ås']: # Fun examples on init
        visible = True
    else:
        visible = 'legendonly'
    
    fig.add_trace(get_el_trace(el,visible))


# App layout
app.layout = html.Div(children=[

    html.Div(
        dcc.Graph(
            id='map-plot',
            figure=fig,
            ),
    style={'width': '29%', 'height': '100%', 'display': 'inline-block'}),

    html.Div([
        html.Div(children='Interaktiv karta för efterled i svenska ortnamn', style={'color': accent_color, 'font-size': '30px'}),
        
        html.Div([
            html.Div(children='Sök efter eget:', style={'color': accent_color, 'font-size': '16px'}),
            dcc.Input(
                id='input-field',
                type='text',
                placeholder='berg',
                style={'width':'130px', 'margin-bottom':'5px'}
            ),
            html.Button('Lägg till', id='submit-button', style={'margin-top':'5px', 'display':'none'}),
            dcc.Dropdown(id='suggestion-dropdown', options=el_count, placeholder='Förslag', style=dict(width='130px')),
            html.Button('Rensa', id='clear-button', style={'margin-top':'5px', 'width':'130px'}),
            ], style={'width': '200px', 'display': 'inline-block', 'vertical-align':'top', 'margin-top': '50px'})
        
        
        
    ],style={'width': '69%', 'height':'100%', 'display': 'inline-block', 'vertical-align':'top', 'margin-top': '50px'}),
    html.Div(id='last-clear-clicks', children='0')

],className='row', style={'backgroundColor':background_color})


# Update map callback if new input
@app.callback(
    [Output('map-plot', 'figure'),
     Output('input-field', 'value'),
     Output('last-clear-clicks', 'children')],
    [Input('submit-button', 'n_clicks'),
     Input('clear-button', 'n_clicks'),
     Input('input-field', 'n_submit'),
     Input('suggestion-dropdown', 'value')],
    [State('input-field','value'),
    State('map-plot', 'figure'),
    State('last-clear-clicks', 'children')]
)
def add_new(n_clicks, clear_clicks, n_submit, suggestion_el, input_el, map_fig, last_clear_clicks):

    # Keep track of if clear button has been clicked and clear
    if clear_clicks is not None and clear_clicks > int(last_clear_clicks):
        last_clear_clicks = clear_clicks
        map_fig['data'] = [get_map_trace()]
    
    # If manual input
    elif input_el != '' and input_el is not None:
        trace = get_el_trace(input_el.strip('-'), visible=True)
        map_fig['data'].append(trace)
    
    # If chosen from sggestion dropdown
    elif suggestion_el is not None:
        trace = get_el_trace(suggestion_el, visible=True)
        map_fig['data'].append(trace)
    return map_fig, '', last_clear_clicks


if __name__ == '__main__':
    app.run_server()
