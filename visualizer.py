#This works!

import pandas as pd
from urllib.request import urlopen
import plotly.express as px
import json
from dash import Dash, dcc, html, Input, Output

#Creating the geojson for Tennessee
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
pre_dict = [counties['features'][i] for i in range(len(counties['features'])) if counties['features'][i]['properties']['STATE'] == '47']
tn_counties_json = dict(pre_dict[0])

#create the make and model dataframe
ev_make_and_model = pd.read_csv('ev_make_and_model.csv')

def filter_geojson_by_state(geojson_data, state_code='47'):
    filtered_features = [feature for feature in geojson_data['features'] if feature['properties']['STATE'] == state_code]
    return {'type': 'FeatureCollection', 'features': filtered_features}

# Assuming `counties` is the original GeoJSON
tn_counties_filtered = filter_geojson_by_state(counties)

#Creating the dash app
app = Dash()

gdf_reshaped = pd.read_csv('gdf_reshaped.csv')
colors = {
    'background': '#D3D3D3',
    'text': '#141414'
}
phev_bev_type = ['BEV','PHEV','All']
metric_options = ['Vehicle Quantity','Vehicle Quantity Per Capita']

app.layout = html.Div(children=[
    html.H1(children='BEV/PHEV Registrations by County', style={'textAlign': 'center',
            'font-family': ['Open Sans']}), html.H5(children = 'Select a metric', style = {'font-family': ['Open Sans']}),
    dcc.RadioItems(id = 'metric_option', options = metric_options, value = 'Vehicle Quantity', inline = False,
                   style = {'font-family': ['Open Sans']}),
                   html.H5(children = 'Select a EV Technology', style = {'font-family': ['Open Sans']}),
    dcc.RadioItems(id = 'bev_phev_option', options = phev_bev_type, value = 'BEV', inline = False,
                   style = {'font-family': ['Open Sans']}),
    html.H5(children = 'Select a Year', style = {'font-family': ['Open Sans']}),
    dcc.Slider(2019,2024,1,
                marks={2019: '2019', 2020:'2020', 2021:'2021', 2022:'2022', 2023:'2023',2024:'2024'}, 
                id = 'year', value = 2019, tooltip={"placement": "bottom", "always_visible": True})
    ,dcc.Graph(
        id='graph', clickData = {'points': [{'location':'Davidson'}]}),
    dcc.Graph(
        id='tree_graph')
])
@app.callback(
    Output("graph", "figure"),
    Input('metric_option','value'),
    Input("bev_phev_option" ,'value'),
    Input('year', 'value'),)

def create_choropleths(metric_option, bev_phev_option , year):
    '''
    Creates an interactive plotly graph
    '''
    filtered_df = gdf_reshaped[(gdf_reshaped.Year == year)]
    fig = px.choropleth_mapbox(filtered_df, 
                               geojson = tn_counties_filtered, locations='County', color=bev_phev_option, 
                        featureidkey = 'properties.NAME',
                            color_continuous_scale="Blues", 
                            center={"lat": 35.5175, "lon": -86.5804}, mapbox_style="open-street-map",
                            labels={'County':'County '}, zoom = 6)
    fig.update_geos(fitbounds = 'locations', visible = True)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

@app.callback(
    Output('tree_graph','figure'), 
              Input('graph','clickData'), 
              Input('bev_phev_option','value'),
              Input('year','value'))

def create_treegraph(clickData, bev_phev_option, year):
    if clickData is None:
        county_name = 'Davidson'
    else:
        #print(clickData)
        county_name = clickData['points'][0]['location']
    
    county_df = ev_make_and_model[(ev_make_and_model['Technology'] == bev_phev_option.split(' ')[0]) 
                                  & (ev_make_and_model['Year'] == year) 
                                  & (ev_make_and_model['County'] == county_name)]
    fig = px.treemap(county_df, path = [px.Constant(f'{county_name} County Make and Model'), 'Make','Model'],
                     values = 'Vehicle Count', color = 'Vehicle Count', color_continuous_scale = 'Blues',
                     color_continuous_midpoint = np.average(county_df['Vehicle Count'], 
                                                            weights = county_df['Vehicle Count']))
    fig.update_traces(root_color = 'lightgrey')
    fig.update_layout(margin = dict(t = 50, l = 25, r= 25, b = 25))
    return fig
    
#save as an iframe

app.run(debug=True, port = 8500)