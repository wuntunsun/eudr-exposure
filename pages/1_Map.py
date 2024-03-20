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



@st.cache_data # will hash on function arguments...
#def get_map() -> Tuple[folium.Map, folium.FeatureGroup]:
def get_map() -> folium.Map:
    # TODO: configure more...
    m=folium.Map(zoom_start=1, min_zoom=1, tiles='cartodbpositron', prefer_canvas=True) 
    return m

def create_feature_group(markers: List[folium.Marker]) -> folium.FeatureGroup:
    fg=folium.FeatureGroup(name="Geolocation Data")
    for marker in markers:
        fg.add_child(marker)  
    return fg

@st.cache_data # will hash on function arguments...
def get_markers(file: Optional[str], 
                lat_range: Tuple[float, float], 
                lon_range: Tuple[float, float]) -> [folium.Marker]:

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
    try:
        min_lat = math.ceil(state.st_folium_data['bounds']['_southWest']['lat'])
        max_lat = math.ceil(state.st_folium_data['bounds']['_northEast']['lat'])
        return ((min_lat//step)*step, (max_lat//step)*step)
    except:
        pass

    return state.lat_range

def lon_range(state=st.session_state, step=10) -> Tuple[int, int]:
    try:
        min_lng = math.ceil(state.st_folium_data['bounds']['_southWest']['lng'])
        max_lng = math.ceil(state.st_folium_data['bounds']['_northEast']['lng'])
        return ((min_lng//step)*step, (max_lng//step)*step)
    except:
        pass

    return state.lon_range

def filter_data(state = st.session_state):

    state.lat_range = lat_range(state)
    state.lon_range = lon_range(state)

    geography_changed(state)

st.sidebar.header('Map')

st.write("In the map below, you can see the visualized location of the assets in your selected geography.")

with st.form(key='map'):

    m = get_map()
    markers = get_markers(st.session_state.geolocation_file, 
                          st.session_state.lat_range,
                          st.session_state.lon_range)
    # Nota bene: Robert Norris - creating a folium.FeatureGroup is enough to reset the map
    # unless we embed st_folium in an st.form!
    st.session_state.st_folium_data = st_folium(m, height=500,
        feature_group_to_add=create_feature_group(markers),
        key='geolocation_map') # change key to re-render map...
    
    _ = st.form_submit_button('Filter', on_click=filter_data)

st.session_state.zoom=st.session_state.st_folium_data['zoom']

sidebar()