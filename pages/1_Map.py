from streamlit_app import sidebar, geography_changed

import streamlit as st
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import math
import os
from os.path import isfile, join

from typing import Tuple, Optional, List

import random
print(f'Map {random.randint(0,99)}')

###############################################################
########################## MAPS ###############################
###############################################################

@st.cache_data # will hash on function arguments...
#def get_map() -> Tuple[folium.Map, folium.FeatureGroup]:
def get_map() -> folium.Map:
    # TODO: configure more...
    print('get_map')
    m=folium.Map(zoom_start=1, min_zoom=1, tiles='cartodbpositron', prefer_canvas=True) 
    #fg=folium.FeatureGroup(name="Geolocation Data")#.add_to(m)
    #return (m, fg)
    return m

def create_feature_group() -> folium.FeatureGroup:
    fg=folium.FeatureGroup(name="Geolocation Data")#.add_to(m)
    return fg

@st.cache_data # will hash on function arguments...
def get_markers(file: Optional[str], 
                lat_range: Tuple[float, float], 
                lon_range: Tuple[float, float]) -> [folium.Marker]:
    print(f'get_markers {file} {lat_range} {lon_range}')

    def create_marker_at(location: Tuple[float, float]) -> folium.Marker:
        return folium.Circle([location[0], location[1]], radius=4, fill_color="green", fill_opacity=0.4, color="black", weight=1)

    def is_inside(location: Tuple[float, float], lat_range: Tuple[float, float], lon_range: Tuple[float, float]) -> bool:
        return (location[0] >= lat_range[0]) and (location[0] <= lat_range[1]) and (location[1] >= lon_range[0]) and (location[1] <= lon_range[1])

    #locations=st.session_state.geolocation_data.loc[:, ['latitude', 'longitude']]
    locations=list(zip(st.session_state.geolocation_data['latitude'], st.session_state.geolocation_data['longitude']))
    markers = [create_marker_at(location) for location in locations if is_inside(location, lat_range, lon_range)]
    return markers

def center(state = st.session_state) -> Optional[Tuple[float, float]]:

    # Nota bene: Robert Norris - st_folium makes multiple calls on startup, only the last of
    # which contains 'center'...

    if 'center' not in state.st_folium_data: return None

    lat = state.st_folium_data['center']['lat']
    lng = state.st_folium_data['center']['lng']
    return (lat, lng)

def lat_range(state=st.session_state, step=10) -> Tuple[int, int]:
    if 'bounds' in state.st_folium_data:
        bounds=state.st_folium_data['bounds']
        if all(key in bounds for key in ['_southWest', '_northEast']) and not bounds['_southWest'] is None and not bounds['_northEast'] is None:
            min_lat = math.ceil(bounds['_southWest']['lat'])
            max_lat = math.ceil(bounds['_northEast']['lat'])
            return ((min_lat//step)*step, (max_lat//step)*step)

    return state.lat_range

def lon_range(state=st.session_state, step=10) -> Tuple[int, int]:
    if 'bounds' in state.st_folium_data:
        bounds=state.st_folium_data['bounds']
        if all(key in bounds for key in ['_southWest', '_northEast']) and not bounds['_southWest'] is None and not bounds['_northEast'] is None:
            min_lng = math.ceil(bounds['_southWest']['lng'])
            max_lng = math.ceil(bounds['_northEast']['lng'])
            return ((min_lng//step)*step, (max_lng//step)*step)
    
    return state.lon_range

def filter_data(state = st.session_state):

    state.lat_range = lat_range(state)
    state.lon_range = lon_range(state)

    geography_changed(state)

#--------------------------------------------------------------

st.sidebar.header('Map')

#st.subheader("Assets: visualized")

st.write("In the map below, you can see the visualized location of the assets in your selected geography.")

# tiles: ['openstreetmap', 'MapQuest Open Aerial', 'mapquestopen']

m = get_map()
markers = get_markers(st.session_state.geolocation_file, 
                      st.session_state.lat_range,
                      st.session_state.lon_range)

fg = create_feature_group()
for marker in markers:
    fg.add_child(marker)  

with st.form(key='map'):
    # Nota bene: Robert Norris - creating a folium.FeatureGroup is enough to reset the map
    # unless we embed st_folium in an st.form!
    st.session_state.st_folium_data = st_folium(m, height=500,
        feature_group_to_add=fg,
        key='geolocation_map') # change key to re-render map...
    
    _ = st.form_submit_button('Filter', on_click=filter_data)

#st.session_state.center=center()
st.session_state.zoom=st.session_state.st_folium_data['zoom']

#st.toast(st.session_state.geolocation_data.head(10))
#st.map(st.session_state.geolocation_data[['latitude', 'longitude']], color = forest)

# maps.write("WHY IS COLOR BY SECTOR IN CHART NOT WORKING OUT?!")
# maps.write("WHY IS THE MAP NOT ZOOMING IN AUTOMATICALLY? 🥲")

# # Sector color map
# sector_color_map = {
#     "wind power": [255, 0, 0],   # Red
#     1: [0, 255, 0],   # Green
#     2: [0, 0, 255],   # Blue
#     3: [255, 255, 0], # Yellow
#     4: [255, 0, 255], # Magenta
#     5: [0, 255, 255], # Cyan    
#     6: [128, 0, 0],   # Maroon
#     7: [0, 128, 0],   # Green (dark)
#     8: [0, 0, 128],   # Blue (dark)
#     9: [128, 128, 0], # Olive
#     10: [128, 0, 128] # Purple
# }

# # Function to get color based on sector
# def get_color(sector):
#     return sector_color_map.get(sector, [255, 128, 128]) 

# # Function to calculate zoom level
# def calculate_zoom_level(lat_range, lon_range):
#     """
#     Calculate the appropriate zoom level based on the selected latitude and longitude ranges.
#     """
#     # Example calculation - you may need to adjust this based on your specific requirements
#     lat_span = lat_range[1] - lat_range[0]
#     lon_span = lon_range[1] - lon_range[0]
#     max_span = max(lat_span, lon_span)
#     zoom_level = 14 - max_span  # Adjust 14 based on your preference for initial zoom level
#     return zoom_level

#--------------------------------------------------------------
st.subheader("Sample asset")
st.write("would sth like this be possible? how to do? would be imo interesting to go from the 'general' to the 'specific'.")

sidebar()